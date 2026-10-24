// Sovereign YouTube Audio Lounge Widget Controller (with Native Win32 Clipboard & History Playlist)
(function() {
    let ytPlayer = null;
    let isReady = false;
    let isPlaying = false;
    let userRequestedPlay = false;
    let currentTrack = {
        id: "jfKfPfyJRdk",
        title: "Lo-Fi Hip Hop Radio",
        desc: "Lofi Girl 24/7 Relaxing Stream"
    };

    const STORAGE_KEY = "aegis_yt_playlist_v3";
    let defaultPlaylist = [
        { id: "jfKfPfyJRdk", title: "Lo-Fi Hip Hop Radio", desc: "Lofi Girl 24/7 Relaxing Stream" },
        { id: "4xDzrJKXOOY", title: "Synthwave / Chill Beats", desc: "Lofi Girl Synth Radio" },
        { id: "WPni755-Krg", title: "Fantasy RPG Orchestral BGM", desc: "Medieval Tavern & Field" },
        { id: "TURbeWK2wwg", title: "Ghibli Relaxing Piano", desc: "Nature & Studio Ghibli" },
        { id: "tfbvGvVj6i8", title: "Peaceful Japanese Garden", desc: "Ambient Asian Lofi" }
    ];

    let playlist = loadPlaylist();

    // DOM Elements
    const widget = document.getElementById('ytMusicWidget');
    const minibar = document.getElementById('ytMinibar');
    const btnPlayPause = document.getElementById('btnYtPlayPause');
    const btnExpand = document.getElementById('btnYtExpand');
    const btnCollapse = document.getElementById('btnYtCollapse');
    const ytMiniTitle = document.getElementById('ytMiniTitle');
    const ytMiniArtist = document.getElementById('ytMiniArtist');
    const ytEqBars = document.getElementById('ytEqBars');
    const volSlider = document.getElementById('ytVolSlider');
    const volPct = document.getElementById('ytVolPct');
    const volIcon = document.getElementById('ytVolIcon');
    const statusMsg = document.getElementById('ytStatusMsg');

    // Clipboard Banner Elements
    const clipBanner = document.getElementById('ytClipBanner');
    const clipUrl = document.getElementById('ytClipUrl');
    const btnClipPlayNow = document.getElementById('btnClipPlayNow');
    const btnClipAddList = document.getElementById('btnClipAddList');
    const btnClipDismiss = document.getElementById('btnClipDismiss');

    // Action Bar Elements
    const btnPaste = document.getElementById('btnYtPaste');
    const btnPrompt = document.getElementById('btnYtPrompt');
    const btnAddCurrent = document.getElementById('btnYtAddCurrent');

    // Playlist Elements
    const playlistList = document.getElementById('ytPlaylistList');
    const playlistBadgeCount = document.getElementById('ytPlaylistBadgeCount');
    const btnPlPrev = document.getElementById('btnPlPrev');
    const btnPlNext = document.getElementById('btnPlNext');
    const btnPlShuffle = document.getElementById('btnPlShuffle');
    const btnPlClear = document.getElementById('btnPlClear');

    // Neutralize background tab / window blur auto-pause in WebView2
    try {
        Object.defineProperty(document, 'hidden', { get: () => false, configurable: true });
        Object.defineProperty(document, 'visibilityState', { get: () => 'visible', configurable: true });
        document.addEventListener('visibilitychange', (e) => {
            e.stopImmediatePropagation();
        }, true);
    } catch (_) {}

    window.livelyWallpaperPlaybackChanged = function(data) {
        if (userRequestedPlay && ytPlayer && ytPlayer.playVideo) {
            ytPlayer.playVideo();
        }
    };
    window.ytKeepPlaying = function() {
        if (userRequestedPlay && ytPlayer && ytPlayer.playVideo) {
            ytPlayer.playVideo();
        }
    };

    // Watchdog: When user opens other apps, ensure YouTube music keeps playing
    setInterval(() => {
        if (userRequestedPlay && isReady && ytPlayer && ytPlayer.getPlayerState) {
            const state = ytPlayer.getPlayerState();
            // 2: PAUSED (externally triggered by focus loss or WebView2 throttling)
            if (state === 2) {
                ytPlayer.playVideo();
            }
        }
    }, 400);

    function setStatus(text, isError = false) {
        if (!statusMsg) return;
        statusMsg.textContent = text;
        statusMsg.style.color = isError ? "#ef4444" : "#38bdf8";
        if (text && !isError) {
            setTimeout(() => {
                if (statusMsg.textContent === text) statusMsg.textContent = "";
            }, 5000);
        }
    }

    // 1. Playlist Management
    function loadPlaylist() {
        try {
            const raw = localStorage.getItem(STORAGE_KEY);
            if (raw) {
                const parsed = JSON.parse(raw);
                if (Array.isArray(parsed) && parsed.length > 0) {
                    return parsed;
                }
            }
        } catch (_) {}
        return [...defaultPlaylist];
    }

    function savePlaylist() {
        try {
            localStorage.setItem(STORAGE_KEY, JSON.stringify(playlist));
        } catch (_) {}
        renderPlaylist();
    }

    function addToPlaylist(id, title, desc, prepend = true) {
        if (!id) return;
        // Check if already in playlist
        const existingIdx = playlist.findIndex(item => item.id === id);
        if (existingIdx !== -1) {
            if (prepend) {
                // Move to top
                const [item] = playlist.splice(existingIdx, 1);
                playlist.unshift(item);
            }
        } else {
            const newItem = {
                id,
                title: title || "YouTube Track",
                desc: desc || "Added from Stream"
            };
            if (prepend) playlist.unshift(newItem);
            else playlist.push(newItem);
        }

        // Cap to 30 items
        if (playlist.length > 30) playlist = playlist.slice(0, 30);
        savePlaylist();
    }

    function removeFromPlaylist(idx) {
        if (idx >= 0 && idx < playlist.length) {
            playlist.splice(idx, 1);
            savePlaylist();
        }
    }

    function renderPlaylist() {
        if (!playlistList) return;
        playlistList.innerHTML = "";

        if (playlistBadgeCount) {
            playlistBadgeCount.textContent = playlist.length;
        }

        if (playlist.length === 0) {
            playlistList.innerHTML = `<div style="padding: 12px; font-size: 11px; color: #94a3b8; text-align: center;">Playlist is empty. Click [Paste from Clipboard] or [Type / Search] to add tracks.</div>`;
            return;
        }

        playlist.forEach((item, idx) => {
            const el = document.createElement('div');
            el.className = `yt-playlist-item ${item.id === currentTrack.id ? 'active' : ''}`;
            el.setAttribute('data-id', item.id);
            el.setAttribute('data-idx', idx);

            const thumbUrl = `https://img.youtube.com/vi/${item.id}/mqdefault.jpg`;

            el.innerHTML = `
                <img class="yt-item-thumb" src="${thumbUrl}" alt="thumb" onerror="this.style.display='none'">
                <div class="yt-item-info">
                    <span class="yt-item-title">${item.title}</span>
                    <span class="yt-item-sub">${item.id === currentTrack.id ? '▶ NOW PLAYING' : (item.desc || item.id)}</span>
                </div>
                <div class="yt-item-actions">
                    <button class="yt-btn yt-item-btn yt-item-play" title="Play Track">▶</button>
                    <button class="yt-btn yt-item-btn yt-item-del" title="Remove Track">✕</button>
                </div>
            `;

            // Click row or play button to play
            el.addEventListener('click', (e) => {
                e.stopPropagation();
                if (e.target && e.target.classList.contains('yt-item-del')) {
                    removeFromPlaylist(idx);
                } else {
                    playVideoId(item.id, item.title, item.desc);
                }
            });

            playlistList.appendChild(el);
        });
    }

    function playNext() {
        if (playlist.length === 0) return;
        const currentIdx = playlist.findIndex(item => item.id === currentTrack.id);
        const nextIdx = (currentIdx + 1) % playlist.length;
        const item = playlist[nextIdx];
        playVideoId(item.id, item.title, item.desc);
    }

    function playPrev() {
        if (playlist.length === 0) return;
        const currentIdx = playlist.findIndex(item => item.id === currentTrack.id);
        const prevIdx = (currentIdx - 1 + playlist.length) % playlist.length;
        const item = playlist[prevIdx];
        playVideoId(item.id, item.title, item.desc);
    }

    function shufflePlay() {
        if (playlist.length <= 1) return;
        let randIdx;
        do {
            randIdx = Math.floor(Math.random() * playlist.length);
        } while (playlist[randIdx].id === currentTrack.id && playlist.length > 1);

        const item = playlist[randIdx];
        playVideoId(item.id, item.title, item.desc);
    }

    // 2. Load YouTube IFrame API asynchronously
    const tag = document.createElement('script');
    tag.src = "https://www.youtube.com/iframe_api";
    const firstScriptTag = document.getElementsByTagName('script')[0];
    firstScriptTag.parentNode.insertBefore(tag, firstScriptTag);

    window.onYouTubeIframeAPIReady = function() {
        ytPlayer = new YT.Player('ytPlayerIframe', {
            host: 'https://www.youtube-nocookie.com',
            height: '180',
            width: '100%',
            videoId: currentTrack.id,
            playerVars: {
                'playsinline': 1,
                'autoplay': 0,
                'controls': 1,
                'modestbranding': 1,
                'rel': 0,
                'enablejsapi': 1,
                'origin': 'https://www.youtube-nocookie.com'
            },
            events: {
                'onReady': onPlayerReady,
                'onStateChange': onPlayerStateChange,
                'onError': onPlayerError
            }
        });
    };

    function onPlayerError(event) {
        console.warn("[YouTube Lounge] Player error code:", event.data);
        if (event.data === 101 || event.data === 150) {
            setStatus("⚠️ Embed restricted by owner. Auto-advancing to next track...", true);
            setTimeout(playNext, 1200);
        } else if (event.data === 100 || event.data === 2) {
            setStatus("⚠️ Video unavailable. Skipping...", true);
            setTimeout(playNext, 1200);
        }
    }

    function onPlayerReady(event) {
        isReady = true;
        if (volSlider) {
            ytPlayer.setVolume(parseInt(volSlider.value) || 80);
        }
        if (ytMiniTitle) ytMiniTitle.textContent = currentTrack.title;
        if (ytMiniArtist) ytMiniArtist.textContent = currentTrack.desc;
        renderPlaylist();
    }

    function onPlayerStateChange(event) {
        if (event.data === YT.PlayerState.PLAYING) {
            isPlaying = true;
            if (btnPlayPause) btnPlayPause.textContent = "⏸";
            if (ytEqBars) ytEqBars.classList.add('active');
        } else {
            isPlaying = false;
            if (btnPlayPause) btnPlayPause.textContent = "▶";
            if (ytEqBars) ytEqBars.classList.remove('active');
        }
    }

    function togglePlayPause() {
        if (!isReady || !ytPlayer) return;
        if (isPlaying) {
            userRequestedPlay = false;
            ytPlayer.pauseVideo();
        } else {
            userRequestedPlay = true;
            ytPlayer.playVideo();
        }
    }

    function toggleExpand(expand) {
        if (!widget) return;
        if (expand !== undefined) {
            if (expand) widget.classList.remove('collapsed');
            else widget.classList.add('collapsed');
        } else {
            widget.classList.toggle('collapsed');
        }
        if (!widget.classList.contains('collapsed')) {
            renderPlaylist();
            checkClipboard();
        }
    }

    function playVideoId(id, title, desc) {
        if (!id) return;
        currentTrack = {
            id,
            title: title || currentTrack.title,
            desc: desc || "YouTube Stream"
        };
        userRequestedPlay = true;
        if (ytMiniTitle) ytMiniTitle.textContent = currentTrack.title;
        if (ytMiniArtist) ytMiniArtist.textContent = currentTrack.desc;

        if (isReady && ytPlayer && ytPlayer.loadVideoById) {
            ytPlayer.loadVideoById(id);
            ytPlayer.playVideo();
        }

        // Add to history playlist and refresh highlight
        addToPlaylist(id, currentTrack.title, currentTrack.desc, true);
        setStatus(`▶ Playing: ${currentTrack.title}`);
    }

    function playPlaylistId(id, title) {
        if (!id) return;
        userRequestedPlay = true;
        if (ytMiniTitle && title) ytMiniTitle.textContent = title;
        if (ytMiniArtist) ytMiniArtist.textContent = "YouTube Playlist Stream";

        if (isReady && ytPlayer && ytPlayer.loadPlaylist) {
            ytPlayer.loadPlaylist({
                list: id,
                listType: 'playlist',
                index: 0,
                startSeconds: 0
            });
            ytPlayer.playVideo();
        }
        setStatus(`▶ Playing Playlist: ${title || id}`);
    }

    async function handleTargetInput(raw) {
        if (!raw) return;
        raw = raw.trim();
        if (!raw) return;

        // 1. Direct 11-char ID
        if (/^[a-zA-Z0-9_-]{11}$/.test(raw)) {
            playVideoId(raw, "YouTube Track", "Custom Video Stream");
            return;
        }

        // 2. Direct Watch URL
        const matchWatch = raw.match(/[?&]v=([a-zA-Z0-9_-]{11})/);
        if (matchWatch) {
            playVideoId(matchWatch[1], "YouTube Track", "Custom Video Stream");
            return;
        }

        // 3. Shortlink youtu.be
        const matchShort = raw.match(/youtu\.be\/([a-zA-Z0-9_-]{11})/);
        if (matchShort) {
            playVideoId(matchShort[1], "YouTube Track", "Custom Video Stream");
            return;
        }

        // 4. Direct Playlist
        const matchPl = raw.match(/[?&]list=([a-zA-Z0-9_-]+)/);
        if (matchPl && !raw.includes("v=")) {
            playPlaylistId(matchPl[1], "YouTube Playlist");
            return;
        }

        // 5. Channel link (@handle, channel/UC..., c/...), or Search Query
        setStatus("🔍 Resolving via Sovereign Telemetry Engine...");
        try {
            const res = await fetch(`http://127.0.0.1:48123/resolve?q=${encodeURIComponent(raw)}`);
            if (res.ok) {
                const data = await res.json();
                if (data.status === "ok") {
                    if (data.target_type === "playlist" && data.playlist_id) {
                        playPlaylistId(data.playlist_id, data.title || "YouTube Playlist");
                    } else if (data.video_id) {
                        playVideoId(data.video_id, data.title || "YouTube Stream", raw);
                    }
                    return;
                }
            }
        } catch (_) {}

        // Fallback for well-known queries
        if (raw.toLowerCase().includes("octopath")) {
            playVideoId("349cnjiNqqI", "Octopath Traveler II Chill Music", "Selected OST Stream");
            return;
        }
        if (raw.toLowerCase().includes("lofi")) {
            playVideoId("jfKfPfyJRdk", "Lo-Fi Hip Hop Radio", "Lofi Girl 24/7 Stream");
            return;
        }

        setStatus("❌ Could not resolve link or query", true);
    }

    // 3. Native Win32 Clipboard Reading
    async function readNativeClipboard() {
        try {
            const res = await fetch('http://127.0.0.1:48123/clipboard', { cache: 'no-store' });
            if (res.ok) {
                const data = await res.json();
                if (data.text && data.text.trim()) {
                    return data.text.trim();
                }
            }
        } catch (_) {}

        if (navigator.clipboard && navigator.clipboard.readText) {
            try {
                const text = await navigator.clipboard.readText();
                if (text && text.trim()) return text.trim();
            } catch (_) {}
        }
        return null;
    }

    // 4. Zero-Typing 1-Click Paste & Play
    async function oneClickPaste() {
        setStatus("📋 Ingesting Windows clipboard...");
        const text = await readNativeClipboard();
        if (text) {
            setStatus(`📋 Clipboard: ${text.substring(0, 45)}...`);
            await handleTargetInput(text);
        } else {
            setStatus("⚠️ Clipboard is empty or contains non-text", true);
        }
    }

    // 5. Native Windows GUI Input Box (`/prompt`)
    async function openNativePrompt() {
        setStatus("✏️ Spawning Windows Input Dialog...");
        try {
            const clipText = await readNativeClipboard();
            const defaultParam = clipText ? `?default=${encodeURIComponent(clipText)}` : "";
            const res = await fetch(`http://127.0.0.1:48123/prompt${defaultParam}`);
            if (res.ok) {
                const data = await res.json();
                if (data.status === "ok" && data.text) {
                    await handleTargetInput(data.text);
                    return;
                }
            }
        } catch (_) {}
        setStatus("Prompt closed or cancelled");
    }

    // 6. Auto-Detection Clipboard Banner Loop
    let lastDetectedClip = "";
    let dismissedClip = "";

    async function checkClipboard() {
        if (!clipBanner) return;
        const text = await readNativeClipboard();
        if (!text) {
            clipBanner.classList.remove('visible');
            return;
        }

        const isYtTarget = text.includes("youtube.com") ||
                            text.includes("youtu.be") ||
                            text.startsWith("@") ||
                            /^[a-zA-Z0-9_-]{11}$/.test(text);

        if (isYtTarget && text !== currentTrack.id && text !== dismissedClip) {
            lastDetectedClip = text;
            if (clipUrl) clipUrl.textContent = text;
            clipBanner.classList.add('visible');
        } else {
            clipBanner.classList.remove('visible');
        }
    }

    // Poller for clipboard detection
    setInterval(() => {
        if (widget && !widget.classList.contains('collapsed')) {
            checkClipboard();
        }
    }, 1500);

    // Banner Buttons
    if (btnClipPlayNow) {
        btnClipPlayNow.addEventListener('click', (e) => {
            e.stopPropagation();
            if (lastDetectedClip) {
                clipBanner.classList.remove('visible');
                handleTargetInput(lastDetectedClip);
            }
        });
    }

    if (btnClipAddList) {
        btnClipAddList.addEventListener('click', async (e) => {
            e.stopPropagation();
            if (lastDetectedClip) {
                clipBanner.classList.remove('visible');
                setStatus("➕ Adding track to playlist...");
                await handleTargetInput(lastDetectedClip);
            }
        });
    }

    if (btnClipDismiss) {
        btnClipDismiss.addEventListener('click', (e) => {
            e.stopPropagation();
            dismissedClip = lastDetectedClip;
            clipBanner.classList.remove('visible');
        });
    }

    // Action Bar Event Listeners
    if (btnPaste) {
        btnPaste.addEventListener('click', (e) => {
            e.stopPropagation();
            oneClickPaste();
        });
    }

    if (btnPrompt) {
        btnPrompt.addEventListener('click', (e) => {
            e.stopPropagation();
            openNativePrompt();
        });
    }

    if (btnAddCurrent) {
        btnAddCurrent.addEventListener('click', (e) => {
            e.stopPropagation();
            addToPlaylist(currentTrack.id, currentTrack.title, currentTrack.desc, true);
            setStatus(`★ Saved "${currentTrack.title}" to History Playlist`);
        });
    }

    // Playlist Tool Event Listeners
    if (btnPlPrev) {
        btnPlPrev.addEventListener('click', (e) => {
            e.stopPropagation();
            playPrev();
        });
    }

    if (btnPlNext) {
        btnPlNext.addEventListener('click', (e) => {
            e.stopPropagation();
            playNext();
        });
    }

    if (btnPlShuffle) {
        btnPlShuffle.addEventListener('click', (e) => {
            e.stopPropagation();
            shufflePlay();
        });
    }

    if (btnPlClear) {
        btnPlClear.addEventListener('click', (e) => {
            e.stopPropagation();
            playlist = [];
            savePlaylist();
            setStatus("🗑️ Playlist cleared");
        });
    }

    // Minibar & Header Controls
    if (btnPlayPause) {
        btnPlayPause.addEventListener('click', (e) => {
            e.stopPropagation();
            togglePlayPause();
        });
    }

    if (btnExpand) {
        btnExpand.addEventListener('click', (e) => {
            e.stopPropagation();
            toggleExpand(true);
        });
    }

    if (btnCollapse) {
        btnCollapse.addEventListener('click', (e) => {
            e.stopPropagation();
            toggleExpand(false);
        });
    }

    if (minibar) {
        minibar.addEventListener('click', (e) => {
            if (e.target && (e.target.id === 'btnYtPlayPause' || e.target.closest('#btnYtPlayPause'))) return;
            toggleExpand(true);
        });
    }

        // Open External in Browser button
    const btnOpenExternal = document.getElementById('btnYtOpenExternal');
    if (btnOpenExternal) {
        btnOpenExternal.addEventListener('click', (e) => {
            e.stopPropagation();
            if (currentTrack && currentTrack.id) {
                window.open(`https://www.youtube.com/watch?v=${currentTrack.id}`, '_blank');
            }
        });
    }

    // Volume Slider
    if (volSlider) {
        volSlider.addEventListener('input', (e) => {
            e.stopPropagation();
            const val = parseInt(volSlider.value);
            if (volPct) volPct.textContent = val + '%';
            if (isReady && ytPlayer && ytPlayer.setVolume) {
                ytPlayer.setVolume(val);
            }
            if (volIcon) {
                if (val === 0) volIcon.textContent = "🔇";
                else if (val < 50) volIcon.textContent = "🔉";
                else volIcon.textContent = "🔊";
            }
        });
    }

    // Global Hotkey: Press [M] to toggle Audio Lounge expand / collapse
    window.addEventListener('keydown', (e) => {
        if (e.key === 'm' || e.key === 'M') {
            toggleExpand();
        }
    });

    // Prevent interactions within widget from bubbling to canvas desktop clicks
    if (widget) {
        ['mousedown', 'click', 'pointerdown'].forEach(evt => {
            widget.addEventListener(evt, (e) => {
                e.stopPropagation();
            });
        });
    }

    // Initial render
    renderPlaylist();
})();
