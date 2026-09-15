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

	"KanhaMusic/kanha/logger"

	"KanhaMusic/kanha/core"
	state "KanhaMusic/kanha/core/models"
	"KanhaMusic/kanha/locales"
	"KanhaMusic/kanha/platforms"
	"KanhaMusic/kanha/utils"
	"KanhaMusic/ntgcalls"
)

// callDiscardedHandler fires when Telegram tears down the group call itself
// (voice chat ended/kicked/etc.), as opposed to our own stream just finishing.
// The native ntgcalls call is already gone at this point, so the room's
// "playing" state must be reconciled here — otherwise commands like /seek
// keep trying to talk to a call that no longer exists.
func callDiscardedHandler(chatID int64) {
	r, ok := core.RoomFor(chatID)
	if !ok {
		return
	}

	logger.Debugf("[callDiscardedHandler] Group call discarded in chat %d", chatID)

	scheduleOldPlayingMessage(r)
	cid := r.ChatID
	core.DropRoom(chatID)

	if _, err := core.Bot.SendTextMessage(cid, F(cid, "call_discarded"), nil); err != nil {
		logger.Error(err)
	}
}

func streamEndHandler(
	chatID int64,
	streamType ntgcalls.StreamType,
	_ ntgcalls.StreamDevice,
) {
	if streamType == ntgcalls.VideoStream {
		logger.Debug("[onStreamEndHandler] Video stream ended, returning")
		return
	}

	logger.Debugf("[onStreamEndHandler] Stream ended in chat %d", chatID)
	r, ok := core.RoomFor(chatID)
	if !ok {
		return
	}
	scheduleOldPlayingMessage(r)

	c := core.Bot
	cid := r.ChatID
	r.Parse()

	var t *state.Track
	var wasLooping bool
	if len(r.Queue()) == 0 && r.Loop() == 0 {
		if autoplay := pickAutoplayTrack(r, r.Track()); autoplay != nil {
			r.AddTracks([]*state.Track{autoplay})
		}

		if len(r.Queue()) == 0 {
			core.DropRoom(chatID)
			if _, err := c.SendTextMessage(cid, F(cid, "stream_queue_finished"), nil); err != nil {
				logger.Error(err)
			}
			return
		}
	}

	wasLooping = r.Loop() > 0
	t = r.NextTrack()

	statusText := F(cid, "stream_downloading_next")
	if wasLooping && t != nil && r.FilePath() != "" {
		statusText = F(cid, "cb_replaying")
	} else if t != nil && (t.IsAutoplay || t.Requester == F(cid, "autoplay_requester")) {
		statusText = F(cid, "stream_autoplay_next", locales.Arg{
			"title": utils.EscapeHTML(utils.ShortTitle(t.Title, 25)),
		})
	}

	statusMsg, err := c.SendTextMessage(cid, statusText, nil)
	if err != nil {
		logger.Errorf("[call.go] Failed to send msg: %v", err)
	}

	var filePath string
	if wasLooping && t != nil && r.FilePath() != "" {
		filePath = r.FilePath()
	} else {
		filePath, err = platforms.Download(context.Background(), t, statusMsg)
	}

	if err != nil {
		logger.Errorf(
			"[onStreamEndHandler] Download failed for %s: %v",
			t.URL,
			err,
		)
		utils.EOR(c, statusMsg, F(cid, "stream_download_fail", locales.Arg{
			"error": err.Error(),
		}), nil)
		core.DropRoom(chatID)

		return
	}

	if err := r.Play(t, filePath, true); err != nil {
		logger.Errorf(
			"[onStreamEndHandler] Play failed for %s: %v",
			t.URL,
			err,
		)
		utils.EOR(c, statusMsg, F(cid, "stream_play_fail"), nil)
		core.DropRoom(chatID)

		return
	}

	statusMsg = sendNowPlaying(c, statusMsg, cid, r, t)
	r.SetStatusMsg(statusMsg)
}
