// Main Sovereign Game Wallpaper Coordinator
const bgImage = document.getElementById('bgImage');
const bgVideo = document.getElementById('bgVideo');
const canvas = document.getElementById('wallpaperCanvas');
const ctx = canvas.getContext('2d');

// Initialize High-Performance WebGL Living Shader Engine
let livingEngine = null;
try {
    if (window.LivingShaderEngine) {
        livingEngine = new LivingShaderEngine('livingCanvas');
        window.livingEngine = livingEngine;
    }
} catch (e) {
    console.warn('[Aegis] WebGL Living Shader fallback:', e);
}

const scenes = [
    { id: "citadel", image: "01_citadel_twilight_4k.jpg", file: "01_citadel_twilight_live.mp4", name: "VALERIUS CITADEL TWILIGHT" },
    { id: "shrine", image: "02_mystical_forest_shrine_4k.jpg", file: "02_mystical_forest_shrine_live.mp4", name: "ELDERTREE MYSTICAL SHRINE" },
    { id: "aurora", image: "03_mountain_aurora_fortress_4k.jpg", file: "03_mountain_aurora_snow_live.mp4", name: "FROSTPEAK AURORA FORTRESS" },
    { id: "dunes", image: "04_celestial_dunes_oasis_4k.jpg", file: "04_celestial_dunes_oasis_live.mp4", name: "CELESTIAL DUNES OASIS" },
    { id: "sky_citadel", image: "05_floating_sky_citadel_4k.jpg", file: "05_floating_sky_citadel_live.mp4", name: "AETHERIA SKY CITADEL" },
    { id: "forge", image: "06_volcanic_obsidian_forge_4k.jpg", file: "06_volcanic_obsidian_forge_live.mp4", name: "OBSIDIAN VOLCANIC FORGE" },
    { id: "atlantis", image: "07_sunken_coral_atlantis_4k.jpg", file: "07_sunken_coral_atlantis_live.mp4", name: "SUNKEN CORAL ATLANTIS" },
    { id: "cyber", image: "08_cyber_aegis_megacity_4k.jpg", file: "08_cyber_aegis_megacity_live.mp4", name: "CYBER-AEGIS BASTION" },
    { id: "valley", image: "09_autumn_dragon_valley_4k.jpg", file: "09_autumn_dragon_valley_live.mp4", name: "AUTUMN DRAGON VALLEY" },
    { id: "starfall", image: "10_celestial_starfall_spire_4k.jpg", file: "10_celestial_starfall_spire_live.mp4", name: "STARFALL OBSERVATORY" },
    { id: "dreamscript", image: "11_ethereal_dreamscript_4k.jpg", file: "11_ethereal_dreamscript_live.mp4", name: "ETHEREAL DREAMSCRIPT NEXUS" }
];

let currentSceneIdx = 0;
let autoRotateEnabled = true;
let rotateIntervalMinutes = 30;
let lastRotationTime = Date.now();
let ultraLightMode = true; // Eco / Ultra-Lightweight by default!
let renderEngineMode = 1;  // 0: Pure 4K Canvas FX (Default), 1: Video MP4

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
    idx = (idx + scenes.length) % scenes.length;
    currentSceneIdx = idx;
    window.currentSceneIdx = idx;
    lastRotationTime = Date.now();

    const scene = scenes[idx];

    if (renderEngineMode === 0) {
        // Mode 0: Pure 4K Lossless Canvas FX
        if (bgImage) {
            bgImage.src = scene.image;
            bgImage.classList.add('active');
        }
        if (bgVideo) {
            bgVideo.classList.remove('active');
            bgVideo.pause();
        }
    } else {
        // Mode 1: Video Loop
        if (bgVideo) {
            bgVideo.src = scene.file;
            bgVideo.classList.add('active');
            bgVideo.load();
            bgVideo.play().catch(() => {});
        }
        if (bgImage) {
            bgImage.classList.remove('active');
        }
    }

    // Notify WebGL Living Shader Engine (Vortex Swirl, Flowing Rivers, Magma Churn, Parallax)
    

    // Notify dedicated Realm FX Engine
    if (window.realmFX) {
        window.realmFX.setRealm(idx);
    }

    const realmElem = document.getElementById('realmName');
    if (realmElem) realmElem.textContent = scene.name;

    // Update active hotbar button
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

// Hotbar Button Bindings
for (let i = 0; i < 10; i++) {
    document.getElementById('btnRealm' + i)?.addEventListener('click', () => setScene(i));
}
document.getElementById('btnNextRealm')?.addEventListener('click', nextScene);

// Keyboard Shortcuts: [N] Next, [P] Prev, [1]-[9],[0] Direct Realm, [L] Eco Mode, [H] HUD Toggle
window.addEventListener('keydown', (e) => {
    if (e.target && (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA')) return;
    if (e.key === 'n' || e.key === 'N') nextScene();
    else if (e.key === 'p' || e.key === 'P') prevScene();
    else if (e.key >= '1' && e.key <= '9') {
        const target = parseInt(e.key) - 1;
        if (target < scenes.length) setScene(target);
    } else if (e.key === '0') {
        if (scenes.length >= 10) setScene(9);
    } else if (e.key === 'l' || e.key === 'L') {
        ultraLightMode = !ultraLightMode;
        if (window.fireflyEngine) {
            window.fireflyEngine.maxFireflies = ultraLightMode ? 12 : 50;
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
        // Prevent clicking HUD buttons or YouTube widget from triggering canvas burst
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
            if (window.fireflyEngine) window.fireflyEngine.setCount(val);
            break;
        case "livingMotion":
            if (window.livingEngine) window.livingEngine.motionEnabled = !!val;
            break;
        case "parallaxDepth":
            if (window.livingEngine) window.livingEngine.parallaxStrength = (parseFloat(val) || 50) / 50.0;
            break;
        case "flowSpeed":
            if (window.livingEngine) window.livingEngine.flowSpeed = (parseFloat(val) || 100) / 100.0;
            break;
        case "renderEngine":
            setRenderEngine(val);
            break;
        case "ultraLightMode":
            ultraLightMode = !!val;
            if (window.fireflyEngine) {
                window.fireflyEngine.setCount(ultraLightMode ? 10 : 50);
            }
            if (window.rippleFX) {
                window.rippleFX.enabled = !ultraLightMode;
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
// 60FPS Physics Render Loop (Eco/Ultra-Lightweight Aware)
// ============================================================
function render() {
    if (document.hidden) {
        requestAnimationFrame(render);
        return;
    }

    // Render WebGL Living 4K Shader (Pixel motions: Galaxy Vortex, Rivers, Magma, Sway)
    

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // 0. Dedicated Sovereign Atmospheric Realm FX (Starfall Radial Shower, Ash, Rain, Leaves)
    if (window.realmFX) {
        window.realmFX.updateAndRender(ctx);
    }

    // 1. Fluid Water Ripple Physics
    if (window.rippleFX && window.rippleFX.enabled) {
        window.rippleFX.update();
        window.rippleFX.render(ctx);
    }

    // 2. Arcane Magic Runes & Blade Slashes
    if (window.magicEngine && window.magicEngine.enabled) {
        window.magicEngine.update();
        window.magicEngine.render(ctx);
    }

    // 3. Floating Mana Fireflies
    if (window.fireflyEngine && window.fireflyEngine.enabled) {
        window.fireflyEngine.update();
        window.fireflyEngine.render(ctx);
    }

    requestAnimationFrame(render);
}

// Initialize on active scene at launch (Default: Realm 10 Starfall Observatory)
const initialScene = 8;
setScene(initialScene);
requestAnimationFrame(render);
