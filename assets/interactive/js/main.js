// Main Sovereign Game Wallpaper Coordinator
const bgImage = document.getElementById('bgImage');
const bgVideo = document.getElementById('bgVideo');
const canvas = document.getElementById('wallpaperCanvas');
const ctx = canvas.getContext('2d');

const scenes = [
    { id: "citadel", image: "01_citadel_twilight_4k.jpg", file: "01_citadel_twilight_live.mp4", name: "VALERIUS CITADEL TWILIGHT" },
    { id: "shrine", image: "02_mystical_forest_shrine_4k.jpg", file: "02_mystical_forest_shrine_live.mp4", name: "ELDERTREE MYSTICAL SHRINE" },
    { id: "aurora", image: "03_mountain_aurora_fortress_4k.jpg", file: "03_mountain_aurora_snow_live.mp4", name: "FROSTPEAK AURORA FORTRESS" },
    { id: "dunes", image: "04_celestial_dunes_oasis_4k.jpg", file: "04_celestial_dunes_oasis_live.mp4", name: "CELESTIAL DUNES OASIS" },
    { id: "sky_citadel", image: "05_floating_sky_citadel_4k.jpg", file: "05_floating_sky_citadel_live.mp4", name: "AETHERIA SKY CITADEL" },
    { id: "forge", image: "06_volcanic_obsidian_forge_4k.jpg", file: "06_volcanic_obsidian_forge_live.mp4", name: "OBSIDIAN VOLCANIC FORGE" },
    { id: "atlantis", image: "07_sunken_coral_atlantis_4k.jpg", file: "07_sunken_coral_atlantis_live.mp4", name: "SUNKEN CORAL ATLANTIS" },
    { id: "cyber", image: "08_cyber_aegis_megacity_4k.jpg", file: "08_cyber_aegis_megacity_live.mp4", name: "CYBER-AEGIS BASTION" },
    { id: "valley", image: "09_autumn_dragon_valley_4k.jpg", file: "09_autumn_dragon_valley_v2_live.mp4", name: "AUTUMN DRAGON VALLEY" },
    { id: "starfall", image: "10_celestial_starfall_spire_4k.jpg", file: "10_celestial_starfall_spire_live.mp4", name: "STARFALL OBSERVATORY" },
    { id: "dreamscript", image: "11_ethereal_dreamscript_4k.jpg", file: "11_ethereal_dreamscript_live.mp4", name: "ETHEREAL DREAMSCRIPT NEXUS" },
    { id: "titan_dunes", image: "12_celestial_dunes_titan_4k.jpg", file: "12_celestial_dunes_titan_live.mp4", name: "CELESTIAL TITAN DUNES" },
    { id: "octopath", image: "13_octopath_hd2d_coastal_citadel_4k.jpg", file: "13_octopath_hd2d_coastal_citadel_live.mp4", name: "OCTOPATH HD-2D HARBOR CITADEL" },
    { id: "ffvii", image: "14_ffvii_rebirth_cosmo_canyon_mako_4k.jpg", file: "14_ffvii_rebirth_cosmo_canyon_mako_live.mp4", name: "FFVII REBIRTH COSMO CANYON" },
    { id: "ghibli", image: "15_ghibli_overgrown_sanctuary_4k.jpg", file: "15_ghibli_overgrown_sanctuary_live.mp4", name: "GHIBLI WATERMILL SANCTUARY" },
    { id: "gundam", image: "16_gundam_relic_overgrown_meadow_4k.jpg", file: "16_gundam_relic_overgrown_meadow_live.mp4", name: "THE SLEEPING GUNDAM RELIC" },
    { id: "wanzer", image: "17_front_mission_wanzer_relic_4k.jpg", file: "17_front_mission_wanzer_relic_live.mp4", name: "FRONT MISSION 5: WANZER RELIC" },
    { id: "ff_resonance", image: "18_ff_resonance_crystal_citadel_4k.jpg", file: "18_ff_resonance_crystal_citadel_live.mp4", name: "FINAL FANTASY RESONANCE CITADEL" },
    { id: "fm5_vanguard", image: "19_front_mission_5_wanzer_vanguard_4k.jpg", file: "19_front_mission_5_wanzer_vanguard_live.mp4", name: "FRONT MISSION 5: WANZER VANGUARD" },
    { id: "fm3_remaster", image: "20_front_mission_3_wanzer_zenith_4k.jpg", file: "20_front_mission_3_wanzer_zenith_live.mp4", name: "FRONT MISSION 3: ZENITH REMASTER" },
    { id: "gundam_nu", image: "21_gundam_nu_psychoframe_resonance_4k.jpg", file: "21_gundam_nu_psychoframe_resonance_live.mp4", name: "RX-93 NU GUNDAM PSYCHO-FRAME" },
    { id: "srw_alteisen", image: "22_srw_og_alteisen_revolver_stake_4k.jpg", file: "22_srw_og_alteisen_revolver_stake_live.mp4", name: "SUPER ROBOT WARS OG: ALTEISEN" },
    { id: "srw_cybuster", image: "23_srw_og_cybuster_wind_elemental_4k.jpg", file: "23_srw_og_cybuster_wind_elemental_live.mp4", name: "SRW OG: CYBUSTER WIND ELEMENTAL" },
    { id: "srw_daizenghar", image: "24_srw_og_daizenghar_zankantou_4k.jpg", file: "24_srw_og_daizenghar_zankantou_live.mp4", name: "SRW OG: DAIZENGHAR ZANKANTOU" },
    { id: "srw_soulgain", image: "25_srw_og_soulgain_kirin_fist_4k.jpg", file: "25_srw_og_soulgain_kirin_fist_live.mp4", name: "SRW OG: SOULGAIN MARTIAL FIST" }
];

let currentSceneIdx = 10;
let autoRotateEnabled = true;
let rotateIntervalMinutes = 30;
let lastRotationTime = Date.now();
let ultraLightMode = false; // Default: balanced liveliness with reactive fireflies
let renderEngineMode = 1;  // 0: Pure 4K Canvas FX, 1: Hardware Live Video MP4 (Default)

function resizeCanvas() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
    if (window.realmFX) {
        window.realmFX.resize(canvas.width, canvas.height);
    }
}
window.addEventListener('resize', resizeCanvas);
resizeCanvas();

// ============================================================
// Scene Switching & Auto-Rotation Logic
// ============================================================
function setScene(idx) {
    idx = ((idx % scenes.length) + scenes.length) % scenes.length;
    currentSceneIdx = idx;
    window.currentSceneIdx = idx;
    lastRotationTime = Date.now();

    const scene = scenes[idx];

    if (renderEngineMode === 0 || !scene.file) {
        // Mode 0 or Image-only: Pure 4K Lossless Canvas FX
        if (bgImage) {
            bgImage.onerror = () => {
                console.warn(`[Aegis] Failed to load image plate: ${scene.image}. Falling back to video loop.`);
                if (bgVideo && scene.file) {
                    bgVideo.src = scene.file;
                    bgVideo.classList.add('active');
                    bgImage.classList.remove('active');
                    bgVideo.play().catch(() => {});
                }
            };
            bgImage.src = scene.image;
            bgImage.classList.add('active');
        }
        if (bgVideo) {
            bgVideo.classList.remove('active');
            bgVideo.pause();
        }
    } else {
        // Mode 1: Hardware Live Video MP4 Loop
        if (bgImage) {
            bgImage.onerror = () => {
                console.warn(`[Aegis] Poster image missing: ${scene.image}`);
            };
            bgImage.src = scene.image; // Keep matching poster underneath during transitions
            bgImage.classList.remove('active');
        }
        if (bgVideo) {
            bgVideo.onerror = () => {
                console.warn(`[Aegis] Failed to play video: ${scene.file}. Falling back to image.`);
                if (bgImage) {
                    bgImage.src = scene.image;
                    bgImage.classList.add('active');
                    bgVideo.classList.remove('active');
                }
            };
            if (!bgVideo.src.endsWith(scene.file)) {
                bgVideo.src = scene.file;
                bgVideo.load();
            }
            bgVideo.classList.add('active');
            bgVideo.play().catch(() => {
                if (bgImage) bgImage.classList.add('active');
                bgVideo.classList.remove('active');
            });
        }
    }

    // Notify dedicated Realm FX Engine (used when renderEngineMode === 0)
    if (window.realmFX) {
        window.realmFX.setRealm(idx);
    }

    const realmElem = document.getElementById('realmName');
    if (realmElem) realmElem.textContent = scene.name;

    // Update active hotbar button across all 11 realms
    for (let i = 0; i < scenes.length; i++) {
        const btn = document.getElementById('btnRealm' + i);
        if (btn) {
            if (i === idx) btn.classList.add('active');
            else btn.classList.remove('active');
        }
    }

    document.title = "Aegis Live | Realm: " + scene.name;
}

function setRenderEngine(mode) {
    renderEngineMode = parseInt(mode) || 0;
    setScene(currentSceneIdx);
}

function nextScene() {
    setScene(currentSceneIdx + 1);
}

function prevScene() {
    setScene(currentSceneIdx - 1);
}

// Hotbar Button Bindings (All 11 Realms)
for (let i = 0; i < scenes.length; i++) {
    document.getElementById('btnRealm' + i)?.addEventListener('click', () => setScene(i));
}
document.getElementById('btnNextRealm')?.addEventListener('click', nextScene);

// Keyboard Shortcuts: [N] Next, [P] Prev, [1]-[9],[0],[-] Direct Realm, [L] Eco Mode, [H] HUD Toggle
window.addEventListener('keydown', (e) => {
    if (e.target && (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA')) return;
    if (e.key === 'n' || e.key === 'N') nextScene();
    else if (e.key === 'p' || e.key === 'P') prevScene();
    else if (e.key >= '1' && e.key <= '9') {
        const target = parseInt(e.key) - 1;
        if (target < scenes.length) setScene(target);
    } else if (e.key === '0') {
        if (scenes.length >= 10) setScene(9);
    } else if (e.key === '-' || e.key === '=') {
        if (scenes.length >= 11) setScene(10);
    } else if (e.key === 'l' || e.key === 'L') {
        ultraLightMode = !ultraLightMode;
        if (window.fireflyEngine) {
            window.fireflyEngine.setCount(ultraLightMode ? 0 : 20);
        }
        console.log("⚡ [Aegis] Ultra-Lightweight Mode:", ultraLightMode ? "ON" : "OFF");
    } else if (e.key === 'h' || e.key === 'H') {
        const hud = document.getElementById('gameHud');
        if (hud) hud.classList.toggle('hidden');
    }
});

// Auto-Rotation Watchdog (Checks every second)
setInterval(() => {
    if (!autoRotateEnabled) return;
    const elapsedMs = Date.now() - lastRotationTime;
    const totalMs = rotateIntervalMinutes * 60 * 1000;
    const remainingSec = Math.max(0, Math.round((totalMs - elapsedMs) / 1000));

    const badge = document.getElementById('autoTimerBadge');
    if (badge) {
        const remMin = Math.floor(remainingSec / 60);
        const remSec = remainingSec % 60;
        badge.textContent = `Auto-Next in ${remMin}m ${remSec < 10 ? '0' : ''}${remSec}s`;
    }

    if (elapsedMs >= totalMs) {
        nextScene();
    }
}, 1000);

// ============================================================
// User Interaction & Game Combat Visual Effects (Zero Click Sound)
// ============================================================
let lastClickTime = 0;
let clickCounter = 0;

function handleDesktopClick(x, y) {
    const now = Date.now();
    if (now - lastClickTime < 35) return;
    lastClickTime = now;
    clickCounter++;

    // 1. Spawns Arcane Magic Rune Circle & Blade Slash Visuals
    if (window.magicEngine) window.magicEngine.add(x, y);

    // 2. Spawns 2D Fluid Ripple Displacement
    if (window.rippleFX) window.rippleFX.add(x, y);

    // 3. Reactive Firefly Mana Burst
    if (window.fireflyEngine) window.fireflyEngine.scatter(x, y);

    // 4. Resource Monitor Telemetry Micro-Pulse
    if (window.pulseResourceMonitor) {
        window.pulseResourceMonitor();
    }
}

// Bind interaction listeners to window, document, and canvas
['mousedown', 'pointerdown', 'click'].forEach(evt => {
    window.addEventListener(evt, (e) => {
        if (e.target && (e.target.tagName === 'BUTTON' || e.target.tagName === 'INPUT' || e.target.closest('#ytMusicWidget'))) return;
        handleDesktopClick(e.clientX, e.clientY);
    });
    document.addEventListener(evt, (e) => {
        if (e.target && (e.target.tagName === 'BUTTON' || e.target.tagName === 'INPUT' || e.target.closest('#ytMusicWidget'))) return;
        handleDesktopClick(e.clientX, e.clientY);
    });
    if (canvas) canvas.addEventListener(evt, (e) => handleDesktopClick(e.clientX, e.clientY));
});

function handleDesktopMove(x, y) {
    if (window.fireflyEngine) {
        window.fireflyEngine.mouseX = x;
        window.fireflyEngine.mouseY = y;
    }
}
window.addEventListener('mousemove', (e) => handleDesktopMove(e.clientX, e.clientY));
window.addEventListener('pointermove', (e) => handleDesktopMove(e.clientX, e.clientY));

// ============================================================
// Clock HUD
// ============================================================
function updateClock() {
    const now = new Date();
    const clockElem = document.getElementById('realmClock');
    if (clockElem) {
        clockElem.textContent = now.toLocaleTimeString([], { hour12: false });
    }
}
setInterval(updateClock, 1000);
updateClock();

// ============================================================
// Lively Property Listener API
// ============================================================
function livelyPropertyListener(name, val) {
    switch (name) {
        case "activeScene":
            setScene(parseInt(val) || 0);
            break;
        case "autoRotate":
            autoRotateEnabled = !!val;
            const badge = document.getElementById('autoTimerBadge');
            if (badge) badge.style.display = autoRotateEnabled ? 'inline-block' : 'none';
            break;
        case "rotateInterval":
            const intervals = [15, 30, 60, 120, 180];
            rotateIntervalMinutes = intervals[parseInt(val)] || 30;
            lastRotationTime = Date.now();
            break;
        case "gameHud":
            const hud = document.getElementById('gameHud');
            if (hud) {
                if (val) hud.classList.remove('hidden');
                else hud.classList.add('hidden');
            }
            break;
        case "magicFx":
            if (window.magicEngine) window.magicEngine.enabled = !!val;
            break;
        case "rippleEffect":
            if (window.rippleFX) window.rippleFX.enabled = !!val;
            break;
        case "fireflyCount":
            if (window.fireflyEngine) window.fireflyEngine.setCount(parseInt(val) || 0);
            break;
        case "renderEngine":
            setRenderEngine(val);
            break;
        case "ultraLightMode":
            ultraLightMode = !!val;
            if (window.fireflyEngine && renderEngineMode === 1) {
                window.fireflyEngine.setCount(ultraLightMode ? 0 : 16);
            }
            if (window.realmFX) {
                window.realmFX.ultraLight = ultraLightMode;
            }
            break;
        case "btnNextScene":
            nextScene();
            break;
    }
}

// ============================================================
// 60FPS Physics Render Loop
// ============================================================
function render() {
    if (document.hidden) {
        requestAnimationFrame(render);
        return;
    }

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // 0. Atmospheric Canvas Realm FX ONLY in Mode 0 (Static 4K Image mode).
    // In Mode 1 (Hardware Live Video MP4), the MP4 already renders the deterministic
    // scene motion, so we never draw duplicate canvas particles/gradients on top.
    if (renderEngineMode === 0 && window.realmFX) {
        window.realmFX.updateAndRender(ctx);
    }

    // 1. Fluid Water Ripple Physics on Click
    if (window.rippleFX && window.rippleFX.enabled) {
        window.rippleFX.update();
        window.rippleFX.render(ctx);
    }

    // 2. Arcane Magic Runes & Blade Slashes on Click
    if (window.magicEngine && window.magicEngine.enabled) {
        window.magicEngine.update();
        window.magicEngine.render(ctx);
    }

    // 3. Optional Mana Fireflies (only when count > 0 and either Mode 0 or explicitly enabled)
    if (window.fireflyEngine && window.fireflyEngine.enabled && window.fireflyEngine.particles.length > 0) {
        window.fireflyEngine.update();
        window.fireflyEngine.render(ctx);
    }

    requestAnimationFrame(render);
}

// Initialize balanced liveliness: provide tasteful ambient fireflies (20 motes) that react to mouse hover/clicks
if (window.fireflyEngine && renderEngineMode === 1) {
    window.fireflyEngine.setCount(ultraLightMode ? 0 : 20);
}

const initialScene = 10;
setScene(initialScene);
requestAnimationFrame(render);
