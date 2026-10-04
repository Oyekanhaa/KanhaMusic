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
	"net/url"
	"regexp"
	"strings"
	"time"

	"KanhaMusic/kanha/logger"

	td "github.com/Kanha/Meow"

	"KanhaMusic/config"
	state "KanhaMusic/kanha/core/models"
	"KanhaMusic/kanha/utils"
)

const (
	PlatformSpotify state.PlatformName = "Spotify"
	spotifyUA                           = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
)

// SpotifyPlatform resolves open.spotify.com links (track, album, playlist)
// into tracks. Metadata comes from Spotify's public embed page, no API
// credentials needed. The audio itself is streamed by the Meow API
// (see MeowApiPlatform), so this platform never downloads anything.
type SpotifyPlatform struct {
	cache *utils.Cache[string, []*state.Track]
}

var (
	spotifyEntityRe = regexp.MustCompile(
		`(?i)open\.spotify\.com/(?:intl-[a-z-]+/)?(?:embed/)?(track|album|playlist)/([A-Za-z0-9]{22})`,
	)
	spotifyNextDataRe = regexp.MustCompile(
		`(?s)<script id="__NEXT_DATA__" type="application/json">(.*?)</script>`,
	)
	spotifyHTTP  = &http.Client{Timeout: 15 * time.Second}
)

func init() {
	Register(&SpotifyPlatform{
		cache: utils.NewCache[string, []*state.Track](1 * time.Hour),
	})
}

func (s *SpotifyPlatform) Name() state.PlatformName { return PlatformSpotify }
func (s *SpotifyPlatform) Priority() int            { return 80 }

func (s *SpotifyPlatform) CanGet(query string) bool {
	q := strings.TrimSpace(query)
	return spotifyEntityRe.MatchString(q)
}

// Get resolves a Spotify link. Spotify is audio only, so video is ignored.
func (s *SpotifyPlatform) Get(query string, _ bool) ([]*state.Track, error) {
	link := strings.TrimSpace(query)

	m := spotifyEntityRe.FindStringSubmatch(link)
	if m == nil {
		return nil, errors.New("spotify: unsupported link")
	}
	kind, id := strings.ToLower(m[1]), m[2]

	cacheKey := kind + ":" + id
	if cached, ok := s.cache.Get(cacheKey); ok && len(cached) > 0 {
		return cloneTracks(cached), nil
	}

	var (
		tracks []*state.Track
		err    error
	)
	if kind == "track" {
		tracks, err = s.fetchTrack(id)
	} else {
		tracks, err = s.fetchCollection(kind, id)
	}
	if err != nil {
		return nil, fmt.Errorf("spotify: %w", err)
	}
	if len(tracks) == 0 {
		return nil, errors.New("spotify: no tracks found")
	}

	s.cache.Set(cacheKey, tracks)
	return cloneTracks(tracks), nil
}

// CanDownload is false on purpose: the Meow API platform streams Spotify
// tracks, this platform only resolves metadata.
func (s *SpotifyPlatform) CanDownload(_ state.PlatformName) bool { return false }

func (s *SpotifyPlatform) Download(_ context.Context, _ *state.Track, _ *td.Message) (string, error) {
	return "", errors.New("spotify platform does not support downloading")
}

func (s *SpotifyPlatform) fetchTrack(id string) ([]*state.Track, error) {
	entity, err := s.fetchEntity("track", id)
	if err == nil {
		if t := spotifyTrackFromEntity(entity, id); t != nil {
			return []*state.Track{t}, nil
		}
		err = errors.New("track data missing in embed page")
	}
	logger.Warnf("[Spotify] embed lookup failed for %s: %v, trying oembed", id, err)

	// Fallback: oEmbed only knows the title and the cover (no artist or
	// duration), but it is enough to play the track.
	t, oerr := s.fetchOEmbed(id)
	if oerr != nil {
		return nil, fmt.Errorf("%v; oembed: %v", err, oerr)
	}
	return []*state.Track{t}, nil
}

func (s *SpotifyPlatform) fetchCollection(kind, id string) ([]*state.Track, error) {
	entity, err := s.fetchEntity(kind, id)
	if err != nil {
		return nil, err
	}

	list, _ := entity["trackList"].([]any)
	cover := spotifyCover(entity)

	limit := config.QueueLimit
	if limit <= 0 {
		limit = 15
	}

	tracks := make([]*state.Track, 0, len(list))
	for _, item := range list {
		it, ok := item.(map[string]any)
		if !ok {
			continue
		}
		uri := safeStr(it["uri"])
		tid := uri[strings.LastIndex(uri, ":")+1:]
		if len(tid) != 22 {
			continue
		}
		if playable, ok := it["isPlayable"].(bool); ok && !playable {
			continue
		}

		tracks = append(tracks, &state.Track{
			ID:       tid,
			Title:    spotifyTitle(safeStr(it["title"]), safeStr(it["subtitle"])),
			Duration: int(spotifyNum(it["duration"]) / 1000),
			Artwork:  cover,
			URL:      "https://open.spotify.com/track/" + tid,
			Source:   PlatformSpotify,
		})
		if len(tracks) >= limit {
			break
		}
	}
	return tracks, nil
}

// fetchEntity loads open.spotify.com/embed/<kind>/<id> and returns the
// "entity" object from the page's __NEXT_DATA__ json.
func (s *SpotifyPlatform) fetchEntity(kind, id string) (map[string]any, error) {
	req, err := http.NewRequest(http.MethodGet, "https://open.spotify.com/embed/"+kind+"/"+id, nil)
	if err != nil {
		return nil, err
	}
	req.Header.Set("User-Agent", spotifyUA)
	req.Header.Set("Accept-Language", "en-US,en;q=0.9")

	resp, err := spotifyHTTP.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("embed page returned %d", resp.StatusCode)
	}

	body, err := io.ReadAll(io.LimitReader(resp.Body, 4<<20))
	if err != nil {
		return nil, err
	}

	m := spotifyNextDataRe.FindSubmatch(body)
	if m == nil {
		return nil, errors.New("embed data not found")
	}

	var data map[string]any
	if err := json.Unmarshal(m[1], &data); err != nil {
		return nil, fmt.Errorf("embed data invalid: %w", err)
	}

	for _, path := range [][]any{
		{"props", "pageProps", "state", "data", "entity"},
		{"props", "pageProps", "data", "entity"},
	} {
		if entity, ok := dig(data, path...).(map[string]any); ok && len(entity) > 0 {
			return entity, nil
		}
	}
	return nil, errors.New("entity not found in embed data")
}

func (s *SpotifyPlatform) fetchOEmbed(id string) (*state.Track, error) {
	trackURL := "https://open.spotify.com/track/" + id
	req, err := http.NewRequest(
		http.MethodGet,
		"https://open.spotify.com/oembed?url="+url.QueryEscape(trackURL),
		nil,
	)
	if err != nil {
		return nil, err
	}
	req.Header.Set("User-Agent", spotifyUA)

	resp, err := spotifyHTTP.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("returned %d", resp.StatusCode)
	}

	var out struct {
		Title     string `json:"title"`
		Thumbnail string `json:"thumbnail_url"`
	}
	if err := json.NewDecoder(io.LimitReader(resp.Body, 1<<20)).Decode(&out); err != nil {
		return nil, err
	}
	if strings.TrimSpace(out.Title) == "" {
		return nil, errors.New("empty title")
	}

	return &state.Track{
		ID:      id,
		Title:   out.Title,
		Artwork: out.Thumbnail,
		URL:     trackURL,
		Source:  PlatformSpotify,
	}, nil
}

func spotifyTrackFromEntity(e map[string]any, id string) *state.Track {
	name := firstNonEmpty(safeStr(e["name"]), safeStr(e["title"]))
	if name == "" {
		return nil
	}

	var artists []string
	if list, ok := e["artists"].([]any); ok {
		for _, a := range list {
			if n := safeStr(dig(a, "name")); n != "" {
				artists = append(artists, n)
			}
		}
	}
	artist := strings.Join(artists, ", ")
	if artist == "" {
		artist = safeStr(e["subtitle"])
	}

	return &state.Track{
		ID:       id,
		Title:    spotifyTitle(name, artist),
		Duration: int(spotifyNum(e["duration"]) / 1000),
		Artwork:  spotifyCover(e),
		URL:      "https://open.spotify.com/track/" + id,
		Source:   PlatformSpotify,
	}
}

// spotifyTitle gives "Song - Artist", which reads well in the player and
// also makes the title a good search query for autoplay.
func spotifyTitle(name, artist string) string {
	name, artist = strings.TrimSpace(name), strings.TrimSpace(artist)
	if name == "" {
		return artist
	}
	if artist == "" {
		return name
	}
	return name + " - " + artist
}

// spotifyCover picks the widest image from the entity's cover art.
func spotifyCover(e map[string]any) string {
	sources, _ := dig(e, "coverArt", "sources").([]any)
	best, bestW := "", -1.0
	for _, src := range sources {
		sm, ok := src.(map[string]any)
		if !ok {
			continue
		}
		imgURL := safeStr(sm["url"])
		if imgURL == "" {
			continue
		}
		if w := spotifyNum(sm["width"]); w > bestW {
			best, bestW = imgURL, w
		}
	}
	return best
}

func spotifyNum(v any) float64 {
	switch n := v.(type) {
	case float64:
		return n
	case int:
		return float64(n)
	}
	return 0
}

func cloneTracks(in []*state.Track) []*state.Track {
	out := make([]*state.Track, 0, len(in))
	for _, t := range in {
		if t == nil {
			continue
		}
		c := *t
		out = append(out, &c)
	}
	return out
}
