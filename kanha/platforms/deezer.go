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
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/http"
	"regexp"
	"strconv"
	"strings"
	"time"

	td "github.com/Kanha/Meow"

	"KanhaMusic/config"
	state "KanhaMusic/kanha/core/models"
	"KanhaMusic/kanha/utils"
)

const PlatformDeezer state.PlatformName = "Deezer"

// DeezerPlatform resolves deezer.com links (track, album, playlist) into
// tracks using Deezer's public API, which needs no credentials. The audio
// itself (FLAC / MP3) is streamed by the Meow API (see MeowApiPlatform).
type DeezerPlatform struct {
	cache *utils.Cache[string, []*state.Track]
}

var (
	deezerEntityRe = regexp.MustCompile(
		`(?i)deezer\.com/(?:[a-z]{2}(?:-[a-z]{2})?/)?(track|album|playlist)/(\d+)`,
	)
	deezerHTTP  = &http.Client{Timeout: 15 * time.Second}
)

type deezerTrack struct {
	ID       int64  `json:"id"`
	Title    string `json:"title"`
	Duration int    `json:"duration"`
	Artist   struct {
		Name string `json:"name"`
	} `json:"artist"`
	Album struct {
		CoverXL  string `json:"cover_xl"`
		CoverBig string `json:"cover_big"`
		Cover    string `json:"cover_medium"`
	} `json:"album"`
	Error *deezerError `json:"error"`
}

type deezerCollection struct {
	Title    string `json:"title"`
	CoverXL  string `json:"cover_xl"`
	CoverBig string `json:"cover_big"`
	Tracks   struct {
		Data []deezerTrack `json:"data"`
	} `json:"tracks"`
	Error *deezerError `json:"error"`
}

// Deezer reports errors with HTTP 200 and an "error" object in the body.
type deezerError struct {
	Type    string `json:"type"`
	Message string `json:"message"`
}

func init() {
	Register(&DeezerPlatform{
		cache: utils.NewCache[string, []*state.Track](1 * time.Hour),
	})
}

func (d *DeezerPlatform) Name() state.PlatformName { return PlatformDeezer }
func (d *DeezerPlatform) Priority() int            { return 80 }

func (d *DeezerPlatform) CanGet(query string) bool {
	q := strings.TrimSpace(query)
	return deezerEntityRe.MatchString(q)
}

// Get resolves a Deezer link. Deezer is audio only, so video is ignored.
func (d *DeezerPlatform) Get(query string, _ bool) ([]*state.Track, error) {
	link := strings.TrimSpace(query)

	m := deezerEntityRe.FindStringSubmatch(link)
	if m == nil {
		return nil, errors.New("deezer: unsupported link")
	}
	kind, id := strings.ToLower(m[1]), m[2]

	cacheKey := kind + ":" + id
	if cached, ok := d.cache.Get(cacheKey); ok && len(cached) > 0 {
		return cloneTracks(cached), nil
	}

	var (
		tracks []*state.Track
		err    error
	)
	if kind == "track" {
		tracks, err = d.fetchTrack(id)
	} else {
		tracks, err = d.fetchCollection(kind, id)
	}
	if err != nil {
		return nil, fmt.Errorf("deezer: %w", err)
	}
	if len(tracks) == 0 {
		return nil, errors.New("deezer: no tracks found")
	}

	d.cache.Set(cacheKey, tracks)
	return cloneTracks(tracks), nil
}

// CanDownload is false on purpose: the Meow API platform streams Deezer
// tracks, this platform only resolves metadata.
func (d *DeezerPlatform) CanDownload(_ state.PlatformName) bool { return false }

func (d *DeezerPlatform) Download(_ context.Context, _ *state.Track, _ *td.Message) (string, error) {
	return "", errors.New("deezer platform does not support downloading")
}

func (d *DeezerPlatform) fetchTrack(id string) ([]*state.Track, error) {
	var dt deezerTrack
	if err := deezerGet("track/"+id, &dt); err != nil {
		return nil, err
	}
	if dt.Error != nil {
		return nil, errors.New(dt.Error.Message)
	}

	t := deezerToTrack(&dt, "")
	if t == nil {
		return nil, errors.New("track not found")
	}
	return []*state.Track{t}, nil
}

func (d *DeezerPlatform) fetchCollection(kind, id string) ([]*state.Track, error) {
	var col deezerCollection
	if err := deezerGet(kind+"/"+id, &col); err != nil {
		return nil, err
	}
	if col.Error != nil {
		return nil, errors.New(col.Error.Message)
	}

	// Album tracks carry no cover of their own, use the album's.
	cover := firstNonEmpty(col.CoverXL, col.CoverBig)

	limit := config.QueueLimit
	if limit <= 0 {
		limit = 15
	}

	tracks := make([]*state.Track, 0, len(col.Tracks.Data))
	for i := range col.Tracks.Data {
		if t := deezerToTrack(&col.Tracks.Data[i], cover); t != nil {
			tracks = append(tracks, t)
		}
		if len(tracks) >= limit {
			break
		}
	}
	return tracks, nil
}

func deezerToTrack(dt *deezerTrack, fallbackCover string) *state.Track {
	if dt == nil || dt.ID <= 0 || strings.TrimSpace(dt.Title) == "" {
		return nil
	}

	id := strconv.FormatInt(dt.ID, 10)
	title := dt.Title
	if a := strings.TrimSpace(dt.Artist.Name); a != "" {
		title += " - " + a
	}

	return &state.Track{
		ID:       id,
		Title:    title,
		Duration: dt.Duration,
		Artwork:  firstNonEmpty(dt.Album.CoverXL, dt.Album.CoverBig, dt.Album.Cover, fallbackCover),
		URL:      "https://www.deezer.com/track/" + id,
		Source:   PlatformDeezer,
	}
}

func deezerGet(path string, out any) error {
	req, err := http.NewRequest(http.MethodGet, "https://api.deezer.com/"+path, nil)
	if err != nil {
		return err
	}
	req.Header.Set("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")

	resp, err := deezerHTTP.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("api returned %d", resp.StatusCode)
	}
	return json.NewDecoder(io.LimitReader(resp.Body, 8<<20)).Decode(out)
}
