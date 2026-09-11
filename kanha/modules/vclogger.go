/*
 * ● KanhaMusic
 * ○ A high-performance engine for streaming music in Telegram voicechats.
 *
 * Copyright (C) 2026 Kanha
 *
 * This program is free software: you can redistribute it and/or modify it under the
 * terms of the GNU General Public License as published by the Free Software Foundation,
 * either version 3 of the License, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful, but WITHOUT ANY
 * WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
 * PARTICULAR PURPOSE. See the GNU General Public License for more details.
 *
 * Repository: https://github.com/Oyekanhaa/KanhaMusic
 */

package modules

import (
	"context"
	"fmt"
	"strings"
	"sync"
	"time"

	td "github.com/Kanha/Meow"
	tg "github.com/amarnathcjd/gogram/telegram"

	"KanhaMusic/kanha/core"
	"KanhaMusic/kanha/database"
	"KanhaMusic/kanha/logger"
	"KanhaMusic/kanha/utils"
)

type vcLoggerState struct {
	mu            sync.RWMutex
	activeChats   map[int64]context.CancelFunc
	activeUsers   map[int64]map[int64]bool
	userJoinCount map[string]int
}

var vcLogger = &vcLoggerState{
	activeChats:   make(map[int64]context.CancelFunc),
	activeUsers:   make(map[int64]map[int64]bool),
	userJoinCount: make(map[string]int),
}

func init() {
	helpTexts["/vclogger"] = `<i>Toggle voice chat join/leave alerts in your group.</i>

<u>Usage:</u>
<b>/vclogger</b> — Check current VC logger status
<b>/vclogger on</b> — Enable voice chat alerts
<b>/vclogger off</b> — Disable voice chat alerts
<b>/vcstatus</b> — View detailed VC logger and monitor metrics

<b>⚙️ Behavior:</b>
• Tracks participants joining and leaving the voice chat
• Automatically cleans up alert messages after 5 seconds
• Displays user's name, ID, username, and total VC count

<b>🔒 Restrictions:</b>
• Only <b>chat admins</b> or <b>authorized users</b> can use this`
}

func (s *vcLoggerState) start(chatID int64) bool {
	s.mu.Lock()
	if _, running := s.activeChats[chatID]; running {
		s.mu.Unlock()
		return false
	}
	ctx, cancel := context.WithCancel(context.Background())
	s.activeChats[chatID] = cancel
	s.mu.Unlock()

	go s.monitor(ctx, chatID)
	return true
}

func (s *vcLoggerState) stop(chatID int64) bool {
	s.mu.Lock()
	cancel, running := s.activeChats[chatID]
	if running {
		cancel()
		delete(s.activeChats, chatID)
		delete(s.activeUsers, chatID)
	}
	s.mu.Unlock()
	return running
}

func (s *vcLoggerState) isRunning(chatID int64) bool {
	s.mu.RLock()
	defer s.mu.RUnlock()
	_, running := s.activeChats[chatID]
	return running
}

func (s *vcLoggerState) userCount(chatID int64) int {
	s.mu.RLock()
	defer s.mu.RUnlock()
	if users, ok := s.activeUsers[chatID]; ok {
		return len(users)
	}
	return 0
}

func (s *vcLoggerState) monitor(ctx context.Context, chatID int64) {
	logger.Debugf("[vclogger] monitor loop started for chat %d", chatID)
	ticker := time.NewTicker(5 * time.Second)
	defer ticker.Stop()

	errorCount := 0
	maxErrors := 3

	for {
		select {
		case <-ctx.Done():
			logger.Debugf("[vclogger] monitor stopped for chat %d", chatID)
			return
		case <-ticker.C:
			ass, err := core.Assistants.ForChat(chatID)
			if err != nil || ass == nil || ass.Client == nil {
				continue
			}

			participants, err := fetchVCParticipants(ass, chatID)
			if err != nil {
				if tg.MatchError(err, "CHANNEL_INVALID") || tg.MatchError(err, "CHAT_ID_INVALID") {
					logger.Warnf("[vclogger] chat %d invalid, stopping: %v", chatID, err)
					_ = database.SetVCLoggerStatus(chatID, false)
					s.stop(chatID)
					return
				}
				errorCount++
				logger.Debugf("[vclogger] error fetching participants for %d [%d/%d]: %v", chatID, errorCount, maxErrors, err)
				if errorCount >= maxErrors {
					logger.Warnf("[vclogger] too many errors for chat %d, stopping monitor", chatID)
					s.stop(chatID)
					return
				}
				continue
			}
			errorCount = 0

			newUsers := make(map[int64]bool)
			for _, p := range participants {
				if p != nil && !p.Left {
					uid := getParticipantUserID(p.Peer)
					if uid != 0 {
						newUsers[uid] = true
					}
				}
			}

			s.mu.Lock()
			oldUsers, exists := s.activeUsers[chatID]
			if !exists {
				s.activeUsers[chatID] = newUsers
				s.mu.Unlock()
				continue
			}
			s.activeUsers[chatID] = newUsers
			s.mu.Unlock()

			total := len(newUsers)

			// Joined users
			for uid := range newUsers {
				if !oldUsers[uid] {
					go sendVCLog(chatID, uid, ass, true, total)
				}
			}

			// Left users
			for uid := range oldUsers {
				if !newUsers[uid] {
					go sendVCLog(chatID, uid, ass, false, total)
				}
			}
		}
	}
}

func fetchVCParticipants(ass *core.Assistant, chatID int64) ([]*tg.GroupCallParticipant, error) {
	peer, err := ass.Client.ResolvePeer(chatID)
	if err != nil {
		return nil, err
	}

	var call tg.InputGroupCall
	switch p := peer.(type) {
	case *tg.InputPeerChannel:
		full, err := ass.Client.ChannelsGetFullChannel(&tg.InputChannelObj{
			ChannelID:  p.ChannelID,
			AccessHash: p.AccessHash,
		})
		if err != nil {
			return nil, err
		}
		if ch, ok := full.FullChat.(*tg.ChannelFull); ok {
			call = ch.Call
		}
	case *tg.InputPeerChat:
		full, err := ass.Client.MessagesGetFullChat(p.ChatID)
		if err != nil {
			return nil, err
		}
		if ch, ok := full.FullChat.(*tg.ChatFullObj); ok {
			call = ch.Call
		}
	}

	if call == nil {
		return nil, nil
	}

	res, err := ass.Client.PhoneGetGroupParticipants(
		call,
		[]tg.InputPeer{},
		[]int32{},
		"",
		100,
	)
	if err != nil {
		return nil, err
	}

	return res.Participants, nil
}

func getParticipantUserID(peer tg.Peer) int64 {
	switch p := peer.(type) {
	case *tg.PeerUser:
		return p.UserID
	case *tg.PeerChannel:
		return p.ChannelID
	case *tg.PeerChat:
		return p.ChatID
	}
	return 0
}

func sendVCLog(chatID, userID int64, ass *core.Assistant, joined bool, total int) {
	name := "Unknown"
	username := "Iɢɴᴏʀᴇᴅ"

	if u, err := core.Bot.GetUser(userID); err == nil && u != nil {
		name = utils.EscapeHTML(u.FirstName)
		if u.LastName != "" {
			name += " " + utils.EscapeHTML(u.LastName)
		}
		if u.Usernames != nil && len(u.Usernames.ActiveUsernames) > 0 {
			username = "@" + u.Usernames.ActiveUsernames[0]
		}
	} else if ass != nil && ass.Client != nil {
		users, err := ass.Client.UsersGetUsers([]tg.InputUser{&tg.InputUserObj{UserID: userID}})
		if err == nil && len(users) > 0 {
			if uo, ok := users[0].(*tg.UserObj); ok {
				name = utils.EscapeHTML(uo.FirstName)
				if uo.LastName != "" {
					name += " " + utils.EscapeHTML(uo.LastName)
				}
				if uo.Username != "" {
					username = "@" + uo.Username
				}
			}
		}
	}

	var text string
	if joined {
		key := fmt.Sprintf("%d:%d", chatID, userID)
		vcLogger.mu.Lock()
		vcLogger.userJoinCount[key]++
		count := vcLogger.userJoinCount[key]
		vcLogger.mu.Unlock()

		text = fmt.Sprintf(
			"<b>🟢 #𝐉𝛐𝛊𝛈𝐕𝛊ᴅ𝛆𝛐𝐂ʜ𝛂𝛕</b>\n<blockquote><b>𝚴𝛂ϻ𝛆 ➛ <a href=\"tg://user?id=%d\">%s</a>\n𝚰𝛛 ➛ <code>%d</code>\n𝐔𝛅𝛆𝛑𝛈𝛂ϻ𝛆 ➛ %s\n👥 𝐓𝐨𝐭𝐚𝐥 𝐕𝐂 ➛ <code>%d</code></b></blockquote>",
			userID, name, userID, username, total,
		)
		if count > 1 {
			text += fmt.Sprintf("\n🔁 𝐉𝛐𝛊𝛈 𝐂𝛐𝛍𝛈𝛕 ➛ <code>%d</code>", count)
		}
	} else {
		text = fmt.Sprintf(
			"<b>🔴 #𝐋𝛆𝛏𝛕𝐕𝛊ᴅ𝛆𝛐𝐂ʜ𝛂𝛕</b>\n<blockquote><b>𝚴𝛂ϻ𝛆 ➛ <a href=\"tg://user?id=%d\">%s</a>\n𝚰𝛛 ➛ <code>%d</code>\n𝐔𝛅𝛆𝛑𝛈𝛂ϻ𝛆 ➛ %s\n👥 𝐓𝐨𝐭𝐚𝐥 𝐕𝐂 ➛ <code>%d</code></b></blockquote>",
			userID, name, userID, username, total,
		)
	}

	sent, err := core.Bot.SendTextMessage(chatID, text, &td.SendTextMessageOpts{
		ParseMode: "HTML",
	})
	if err == nil && sent != nil {
		time.AfterFunc(5*time.Second, func() {
			_ = core.Bot.DeleteMessages(chatID, []int64{sent.Id}, &td.DeleteMessagesOpts{Revoke: true})
		})
	}
}

func vcloggerHandler(c *td.Client, m *td.Message) error {
	if !isSuperGroup(c, m) {
		return nil
	}

	chatID := m.ChatID()
	senderID := m.SenderID()

	if senderID == 0 {
		// Anonymous admin
		args := strings.Fields(m.Args())
		if len(args) == 0 {
			_, err := m.ReplyText(c, "⚠️ ᴀɴᴏɴʏᴍᴏᴜs ᴀᴅᴍɪɴ\n\nᴜsᴇ: <code>/vclogger on</code> ᴏʀ <code>/vclogger off</code>", &td.SendTextMessageOpts{
				ParseMode: "HTML",
			})
			return err
		}
		arg := strings.ToLower(args[0])
		if arg == "on" || arg == "enable" || arg == "yes" {
			if vcLogger.isRunning(chatID) {
				_, err := m.ReplyText(c, "ℹ️ <b>𝐕ᴄ 𝐋σɢɢєꝛ 𝐈s 𝐀ʟꝛєᴧᴅʏ 𝐀ᴄᴛɪᴠє 𝐈η 𝐓ʜɪs 𝐆ꝛσυᴘ.</b>", &td.SendTextMessageOpts{
					ParseMode: "HTML",
				})
				return err
			}
			_ = database.SetVCLoggerStatus(chatID, true)
			vcLogger.start(chatID)
			_, err := m.ReplyText(c, "✅ <b>𝐕ᴄ 𝐋σɢɢєꝛ 𝐇ᴧs 𝐁єєη 𝐄ηᴧʙʟєᴅ!</b>", &td.SendTextMessageOpts{
				ParseMode: "HTML",
			})
			return err
		} else if arg == "off" || arg == "disable" || arg == "no" {
			_ = database.SetVCLoggerStatus(chatID, false)
			vcLogger.stop(chatID)
			_, err := m.ReplyText(c, "🚫 <b>𝐕ᴄ 𝐋σɢɢєꝛ 𝐇ᴧs 𝐁єєη 𝐃ɪsᴧʙʟєᴅ!</b>", &td.SendTextMessageOpts{
				ParseMode: "HTML",
			})
			return err
		}
	}

	if !canUseAdminCommand(c, chatID, senderID) {
		_, err := m.ReplyText(c, "❌ <b>𝐏єꝛϻɪssɪση 𝐃єηɪєᴅ!</b>\n\n👮 <b>𝐎ηʟʏ 𝐀ᴅϻɪη 𝐎ꝛ 𝐎ᴡηєꝛs 𝐂ᴧη 𝐔sє 𝐕ᴄ 𝐋σɢɢєꝛ.</b>", &td.SendTextMessageOpts{
			ParseMode: "HTML",
		})
		return err
	}

	args := strings.Fields(m.Args())
	if len(args) == 0 {
		enabled, _ := database.IsVCLoggerEnabled(chatID)
		state := "𝐄ηᴧʙʟєᴅ ✅"
		if !enabled {
			state = "𝐃ɪsᴧʙʟєᴅ ❌"
		}
		text := fmt.Sprintf(
			"🎙 <b>𝐕ᴄ 𝐋σɢɢєꝛ 𝐒ᴛᴧᴛυs</b>\n\n➜ <b>𝐂υꝛꝛєηᴛ 𝐒ᴛᴧᴛє :</b> %s\n\n➜ <b>𝐔sᴧɢє :</b> <code>/vclogger [on / off]</code>",
			state,
		)
		_, err := m.ReplyText(c, text, &td.SendTextMessageOpts{
			ParseMode: "HTML",
		})
		return err
	}

	arg := strings.ToLower(args[0])
	switch arg {
	case "on", "enable", "yes":
		if vcLogger.isRunning(chatID) {
			_, err := m.ReplyText(c, "ℹ️ <b>𝐕ᴄ 𝐋σɢɢєꝛ 𝐈s 𝐀ʟꝛєᴧᴅʏ 𝐀ᴄᴛɪᴠє 𝐈η 𝐓ʜɪs 𝐆ꝛσυᴘ.</b>", &td.SendTextMessageOpts{
				ParseMode: "HTML",
			})
			return err
		}
		_ = database.SetVCLoggerStatus(chatID, true)
		vcLogger.start(chatID)
		_, err := m.ReplyText(c, "✅ <b>𝐕ᴄ 𝐋σɢɢєꝛ 𝐇ᴧs 𝐁єєη 𝐄ηᴧʙʟєᴅ!</b>", &td.SendTextMessageOpts{
			ParseMode: "HTML",
		})
		return err

	case "off", "disable", "no":
		_ = database.SetVCLoggerStatus(chatID, false)
		vcLogger.stop(chatID)
		_, err := m.ReplyText(c, "🚫 <b>𝐕ᴄ 𝐋σɢɢєꝛ 𝐇ᴧs 𝐁єєη 𝐃ɪsᴧʙʟєᴅ!</b>", &td.SendTextMessageOpts{
			ParseMode: "HTML",
		})
		return err

	default:
		_, err := m.ReplyText(c, "❌ <b>𝐈ηᴠᴧʟɪᴅ 𝐀ꝛɢυϻєηᴛ</b>\n\n➜ <b>𝐔sᴧɢє :</b> <code>/vclogger [on / off]</code>", &td.SendTextMessageOpts{
			ParseMode: "HTML",
		})
		return err
	}
}

func vcstatsHandler(c *td.Client, m *td.Message) error {
	if !isSuperGroup(c, m) {
		return nil
	}

	chatID := m.ChatID()
	senderID := m.SenderID()
	if senderID != 0 && !canUseAdminCommand(c, chatID, senderID) {
		_, err := m.ReplyText(c, "❌ <b>ᴀᴅᴍɪɴ ᴏɴʟʏ!</b>", &td.SendTextMessageOpts{
			ParseMode: "HTML",
		})
		return err
	}

	enabled, _ := database.IsVCLoggerEnabled(chatID)
	running := vcLogger.isRunning(chatID)
	count := vcLogger.userCount(chatID)

	enabledText := "❌ 𝐃ɪsᴧʙʟєᴅ"
	if enabled {
		enabledText = "✅ 𝐄ηᴧʙʟєᴅ"
	}

	runningText := "🔴 𝐒ᴛσᴘᴘєᴅ"
	if running {
		runningText = "🟢 𝐑υηηɪηɢ"
	}

	text := fmt.Sprintf(
		"📊 <b>𝐕ᴄ 𝐋σɢɢєꝛ 𝐒ᴛᴧᴛs</b>\n\n➜ <b>𝐋σɢɢєꝛ  :</b> %s\n➜ <b>𝐌σηɪᴛσꝛ :</b> %s\n➜ <b>𝐔sєꝛ 𝐈η 𝐕𝐂 :</b> <code>%d</code>",
		enabledText, runningText, count,
	)

	_, err := m.ReplyText(c, text, &td.SendTextMessageOpts{
		ParseMode: "HTML",
	})
	return err
}

func RestoreVCLoggerSessions() {
	time.Sleep(10 * time.Second)
	chats, err := database.GetEnabledVCLoggerChats()
	if err != nil {
		logger.Warnf("[vclogger] failed to query enabled chats: %v", err)
		return
	}

	for _, chatID := range chats {
		if !vcLogger.isRunning(chatID) {
			vcLogger.start(chatID)
			logger.Debugf("[vclogger] restored session for chat %d", chatID)
		}
	}
	logger.Infof("[vclogger] restored %d VC logger sessions", len(chats))
}
