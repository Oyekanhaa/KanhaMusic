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

package core

import (
	"fmt"
	"math/rand"
	"strings"

	td "github.com/Kanha/Meow"

	"KanhaMusic/config"
	"KanhaMusic/kanha/locales"
	"KanhaMusic/kanha/utils"
)

var F func(chatID int64, key string, values ...locales.Arg) string // overwritten from main.go

// Bot is the Meow client, set from main.go.
var Bot *td.Client

func botUsername() string {
	if Bot == nil || Bot.Me == nil || Bot.Me.Usernames == nil {
		return ""
	}
	usernames := Bot.Me.Usernames.ActiveUsernames
	if len(usernames) == 0 {
		return ""
	}
	return usernames[0]
}

// ── button colours ────────────────────────────────────────────────────────────

const (
	ColourRed   = "red"
	ColourBlue  = "blue"
	ColourGreen = "green"
)

var buttonColours = []string{ColourRed, ColourBlue, ColourGreen}

// randomColour returns a random button colour from red/blue/green.
func randomColour() string {
	return buttonColours[rand.Intn(len(buttonColours))]
}

func urlBtn(text, url string) td.InlineKeyboardButton {
	return td.InlineKeyboardButton{
		Text: text,
		Type: &td.InlineKeyboardButtonTypeUrl{Url: url},
	}
}

func dataBtn(text, cb string) td.InlineKeyboardButton {
	return td.InlineKeyboardButton{
		Text: text,
		Type: &td.InlineKeyboardButtonTypeCallback{Data: []byte(cb)},
	}
}

// styleBtn builds a callback ("Data") button with an explicit colour.
func styleBtn(text, cb, colour string) td.InlineKeyboardButton {
	b := dataBtn(text, cb)

	if config.DisableColour {
		return b
	}

	switch strings.ToLower(colour) {
	case ColourRed:
		b.Style = td.ButtonStyleDanger{}
	case ColourBlue:
		b.Style = td.ButtonStylePrimary{}
	case ColourGreen:
		b.Style = td.ButtonStyleSuccess{}
	}

	return b
}

// styleURLBtn builds a URL button with an explicit colour.
func styleURLBtn(text, url, colour string) td.InlineKeyboardButton {
	b := urlBtn(text, url)

	if config.DisableColour {
		return b
	}

	switch strings.ToLower(colour) {
	case ColourRed:
		b.Style = td.ButtonStyleDanger{}
	case ColourBlue:
		b.Style = td.ButtonStylePrimary{}
	case ColourGreen:
		b.Style = td.ButtonStyleSuccess{}
	}

	return b
}

// DataBtn is a callback button with a random colour — used wherever a
// button's colour doesn't need to carry meaning (i.e. everywhere below).
// Exported so other packages (e.g. modules) can use it for one-off
// buttons built outside buttons.go.
func DataBtn(text, cb string) td.InlineKeyboardButton {
	return styleBtn(text, cb, randomColour())
}

// UrlBtn is a URL button with a random colour.
func UrlBtn(text, url string) td.InlineKeyboardButton {
	return styleURLBtn(text, url, randomColour())
}

func AddMeMarkup(chatID int64) td.ReplyMarkup {
	return &td.ReplyMarkupInlineKeyboard{
		Rows: [][]td.InlineKeyboardButton{
			{
				UrlBtn(
					F(chatID, "ADD_ME_BTN"),
					"https://t.me/"+botUsername()+"?startgroup&admin=invite_users",
				),
			},
		},
	}
}

func GetCancelKeyboard(chatID int64) td.ReplyMarkup {
	return &td.ReplyMarkupInlineKeyboard{
		Rows: [][]td.InlineKeyboardButton{
			{
				DataBtn(F(chatID, "DOWNLOAD_CANCEL_BTN"), "cancel"),
			},
		},
	}
}

func GetBroadcastCancelKeyboard(chatID int64) td.ReplyMarkup {
	return &td.ReplyMarkupInlineKeyboard{
		Rows: [][]td.InlineKeyboardButton{
			{
				DataBtn(F(chatID, "BROADCAST_CANCEL_BTN"), "bcast_cancel"),
			},
		},
	}
}

func SuppMarkup(chatID int64) td.ReplyMarkup {
	return &td.ReplyMarkupInlineKeyboard{
		Rows: [][]td.InlineKeyboardButton{{
			UrlBtn(F(chatID, "SUPPORT_BTN"), config.SupportChat),
		}},
	}
}

func GetStopConfirmMarkup(
	chatID int64,
	r *RoomState,
	isPaused bool,
) td.ReplyMarkup {
	prefix := fmt.Sprintf("room:%d:", r.ID)

	text, cb := "CONFIRM_UNMUTE_BTN", prefix+"unmute"

	if isPaused {
		text, cb = "CONFIRM_RESUME_BTN", prefix+"resume"
	}

	return &td.ReplyMarkupInlineKeyboard{
		Rows: [][]td.InlineKeyboardButton{
			{
				DataBtn(F(chatID, text), cb),
				DataBtn(F(chatID, "CONFIRM_STOP_BTN"), prefix+"stop"),
			},
		},
	}
}

func GetPlayMarkup(chatID int64, r *RoomState, queued bool) td.ReplyMarkup {
	prefix := fmt.Sprintf("room:%d:", r.ID)
	track := r.Track()
	duration := 0
	if track != nil {
		duration = track.Duration
	}

	progress := utils.GetProgressBar(r.Position(), duration)
	progress = utils.FormatTime(
		r.Position(),
	) + " " + progress + " " + utils.FormatTime(
		duration,
	)

	rows := make([][]td.InlineKeyboardButton, 0, 4)

	if !queued {
		rows = append(rows, []td.InlineKeyboardButton{
			DataBtn(progress, "progress"),
		})
	}

	rows = append(rows, []td.InlineKeyboardButton{
		DataBtn("▷", prefix+"resume"),
		DataBtn("II", prefix+"pause"),
		DataBtn("⟳", prefix+"replay"),
		DataBtn("‣‣I", prefix+"skip"),
		DataBtn("▢", prefix+"stop"),
	})

	rows = append(rows, []td.InlineKeyboardButton{
		DataBtn("↩ 15s", prefix+"seekback_15"),
		DataBtn("15s ↪", prefix+"seek_15"),
	})

	rows = append(rows, []td.InlineKeyboardButton{
		DataBtn(F(chatID, "CLOSE_BTN"), "close"),
	})

	return &td.ReplyMarkupInlineKeyboard{Rows: rows}
}

func GetGroupHelpKeyboard(chatID int64) td.ReplyMarkup {
	return &td.ReplyMarkupInlineKeyboard{
		Rows: [][]td.InlineKeyboardButton{
			{
				UrlBtn(
					F(chatID, "GC_HELP_BTN"),
					"https://t.me/"+botUsername()+"?start=pm_help",
				),
			},
		},
	}
}

func GetStartMarkup(chatID int64) td.ReplyMarkup {
	return &td.ReplyMarkupInlineKeyboard{
		Rows: [][]td.InlineKeyboardButton{
			{
				UrlBtn(
					F(chatID, "ADD_ME_BTN"),
					"https://t.me/"+botUsername()+"?startgroup&admin=invite_users",
				),
			},
			{
				DataBtn(F(chatID, "START_HELP_BTN"), "help_cb"),
			},
			{
				UrlBtn(F(chatID, "UPDATES_BTN"), config.SupportChannel),
				UrlBtn(F(chatID, "SUPPORT_BTN"), config.SupportChat),
			},
			{
				UrlBtn(F(chatID, "SOURCE_BTN"), "https://github.com/Oyekanhaa/KanhaMusic"),
			},
		},
	}
}

func GetHelpKeyboard(chatID int64) td.ReplyMarkup {
	return &td.ReplyMarkupInlineKeyboard{
		Rows: [][]td.InlineKeyboardButton{
			{
				DataBtn(F(chatID, "HELP_ADMIN_BTN"), "help:admin"),
				DataBtn(F(chatID, "HELP_AUTH_BTN"), "help:auth"),
				DataBtn(F(chatID, "HELP_BCAST_BTN"), "help:bcast"),
			},
			{
				DataBtn(F(chatID, "HELP_PLAY_BTN"), "help:play"),
				DataBtn(F(chatID, "HELP_SUDO_BTN"), "help:sudo"),
				DataBtn(F(chatID, "HELP_RESTRICT_BTN"), "help:restrict"),
			},
			{
				DataBtn(F(chatID, "HELP_THUMB_BTN"), "help:thumb"),
				DataBtn(F(chatID, "HELP_START_BTN"), "help:start"),
				DataBtn(F(chatID, "HELP_AUTOPLAY_BTN"), "help:autoplay"),
			},
			{
				DataBtn(F(chatID, "HELP_PLAYLIST_BTN"), "help:playlist"),
				DataBtn(F(chatID, "HELP_VCLOGS_BTN"), "help:vclogs"),
				DataBtn(F(chatID, "HELP_INLINE_BTN"), "help:inline"),
			},
			{
				DataBtn(F(chatID, "BACK_BTN"), "start"),
			},
		},
	}
}

func GetBackKeyboard(chatID int64) td.ReplyMarkup {
	return &td.ReplyMarkupInlineKeyboard{
		Rows: [][]td.InlineKeyboardButton{
			{
				DataBtn(F(chatID, "BACK_BTN"), "help:main"),
			},
		},
	}
}

func GetRestartConfirmMarkup(chatID int64) td.ReplyMarkup {
	return &td.ReplyMarkupInlineKeyboard{
		Rows: [][]td.InlineKeyboardButton{
			{
				DataBtn(F(chatID, "restart_btn_bot"), "restart:bot"),
				DataBtn(F(chatID, "restart_btn_replay"), "restart:replay"),
			},
		},
	}
}
