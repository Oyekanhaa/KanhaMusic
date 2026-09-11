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

package platforms

import (
	"context"
	"errors"
	"fmt"
	"os"

	"KanhaMusic/kanha/logger"

	td "github.com/Kanha/Meow"

	"KanhaMusic/config"
	state "KanhaMusic/kanha/core/models"
)

const PlatformMeowApi state.PlatformName = "MeowApi"

// MeowApiPlatform is a download-only backend that streams YouTube audio/video
// through the Meow API (`/stream/{video_id}?key=...&type=...&quality=...`).
// It does not resolve search queries or URLs itself; it only downloads
// tracks that some other platform (YouTube) has already resolved.
type MeowApiPlatform struct{}

func init() {
	Register(&MeowApiPlatform{})
}

func (m *MeowApiPlatform) Name() state.PlatformName { return PlatformMeowApi }
func (m *MeowApiPlatform) Priority() int             { return 85 }

func (m *MeowApiPlatform) CanGet(_ string) bool { return false }

func (m *MeowApiPlatform) Get(_ string, _ bool) ([]*state.Track, error) {
	return nil, errors.New("meowapi platform does not support search")
}

func (m *MeowApiPlatform) CanDownload(source state.PlatformName) bool {
	if config.MeowAPIURL == "" || config.MeowAPIKey == "" {
		return false
	}
	return source == PlatformYouTube
}

func (m *MeowApiPlatform) Download(
	ctx context.Context,
	track *state.Track,
	_ *td.Message,
) (string, error) {
	if p := findFile(track); p != "" {
		logger.Debug("MeowApi: cache hit " + p)
		return p, nil
	}

	if track.ID == "" {
		return "", errors.New("meowapi: missing video id")
	}

	dtype, quality, ext := "audio", "128", ".mp3"
	if track.Video {
		dtype, quality, ext = "video", "480", ".mp4"
	}

	path := getPath(track, ext)

	streamURL := fmt.Sprintf(
		"%s/stream/%s?key=%s&type=%s&quality=%s",
		config.MeowAPIURL, track.ID, config.MeowAPIKey, dtype, quality,
	)

	r, err := rc.R().
		SetContext(ctx).
		SetResponseSaveFileName(path).
		Get(streamURL)
	if err != nil {
		os.Remove(path)
		if isDownloadCancelled(err) {
			return "", err
		}
		return "", sanitizeAPIError(
			fmt.Errorf("meowapi request failed: %w", err),
			config.MeowAPIKey,
		)
	}
	if r.IsStatusFailure() {
		os.Remove(path)
		return "", sanitizeAPIError(fmt.Errorf(
			"meowapi returned %d", r.StatusCode(),
		), config.MeowAPIKey)
	}

	if !fileExists(path) {
		return "", errors.New("meowapi returned empty file")
	}

	return path, nil
}
