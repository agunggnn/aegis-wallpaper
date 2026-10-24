use anyhow::{Context, Result};
use std::fs;
use std::path::{Path, PathBuf};

pub struct ScaffolderOptions {
    pub target_dir: PathBuf,
    pub title: String,
    pub background_image: Option<PathBuf>,
    pub default_sound_pack: String, // "Rune Chime", "Mechanical Switch", "Water Droplet", "Cyber Pulse"
    pub default_volume: u32,
    pub firefly_count: u32,
    pub show_clock: bool,
}

impl Default for ScaffolderOptions {
    fn default() -> Self {
        Self {
            target_dir: PathBuf::from("C:\\Users\\agung\\Pictures\\Wallpapers\\Interactive_Fantasy_Suite"),
            title: "Sovereign Interactive Fantasy Suite".to_string(),
            background_image: None,
            default_sound_pack: "Fantasy Rune Chime".to_string(),
            default_volume: 60,
            firefly_count: 50,
            show_clock: false,
        }
    }
}

pub fn scaffold_interactive_wallpaper(opts: &ScaffolderOptions) -> Result<PathBuf> {
    let out = &opts.target_dir;
    let js_dir = out.join("js");
    fs::create_dir_all(&js_dir).context("Failed to create wallpaper directory structure")?;

    // Copy or set background image if provided
    if let Some(ref bg_path) = opts.background_image {
        if bg_path.exists() {
            let ext = bg_path.extension().and_then(|s| s.to_str()).unwrap_or("jpg");
            let bg_rel_name = format!("background.{}", ext);
            let dest = out.join(&bg_rel_name);
            let _ = fs::copy(bg_path, &dest);
        }
    } else {
        // Fallback: look for Citadel in Pictures/Wallpapers
        let default_src = Path::new("C:\\Users\\agung\\Pictures\\Wallpapers\\Fantasy_RPG_Collection\\01_citadel_twilight_4k.jpg");
        if default_src.exists() {
            let dest = out.join("background.jpg");
            let _ = fs::copy(default_src, dest);
        }
    }

    // Copy live video files and 4K images if available
    let collection_dir = Path::new("C:\\Users\\agung\\Pictures\\Wallpapers\\Fantasy_RPG_Collection");
    if collection_dir.exists() {
        for file in &[
            "01_citadel_twilight_live.mp4",
            "02_mystical_forest_shrine_live.mp4",
            "03_mountain_aurora_snow_live.mp4",
            "04_celestial_dunes_oasis_live.mp4",
            "05_floating_sky_citadel_live.mp4",
            "06_volcanic_obsidian_forge_live.mp4",
            "07_sunken_coral_atlantis_live.mp4",
            "08_cyber_aegis_megacity_live.mp4",
            "09_autumn_dragon_valley_live.mp4",
            "10_celestial_starfall_spire_live.mp4",
            "11_ethereal_dreamscript_live.mp4",
            "01_citadel_twilight_4k.jpg",
            "02_mystical_forest_shrine_4k.jpg",
            "03_mountain_aurora_fortress_4k.jpg",
            "04_celestial_dunes_oasis_4k.jpg",
            "05_floating_sky_citadel_4k.jpg",
            "06_volcanic_obsidian_forge_4k.jpg",
            "07_sunken_coral_atlantis_4k.jpg",
            "08_cyber_aegis_megacity_4k.jpg",
            "09_autumn_dragon_valley_4k.jpg",
            "10_celestial_starfall_spire_4k.jpg",
            "11_ethereal_dreamscript_4k.jpg",
        ] {
            let src = collection_dir.join(file);
            if src.exists() {
                let _ = fs::copy(&src, out.join(file));
            }
        }
    }

    // 1. LivelyInfo.json
    let lively_info = serde_json::json!({
        "AppVersion": "2.2.1.0",
        "Title": opts.title,
        "Thumbnail": "thumbnail.jpg",
        "Preview": "preview.gif",
        "Desc": "Interactive Live Wallpaper with live 4K video, tactile click audio, 2D fluid ripple physics, and reactive fireflies.",
        "Author": "Aegis Fleet",
        "License": "MIT",
        "Contact": "https://github.com/agunggnn/aegis-wallpaper",
        "Type": 1,
        "Arguments": "--audio --pause-event true",
        "FileName": "index.html"
    });
    fs::write(out.join("LivelyInfo.json"), serde_json::to_string_pretty(&lively_info)?)?;

    let default_pack_idx = match opts.default_sound_pack.as_str() {
        "Mechanical Switch" | "Mechanical" => 1,
        "Water Droplet" | "Water" => 2,
        "Cyber Pulse" | "Pulse" => 3,
        "Muted" => 4,
        _ => 0,
    };

    // 2. LivelyProperties.json
    let lively_props = serde_json::json!({
        "activeScene": {
            "type": "dropdown",
            "value": 0,
            "items": [
                "01 - Citadel Twilight Live (Flowing River & Sun Rays)",
                "02 - Mystical Forest Shrine Live (Pulsing Runes & Mist)",
                "03 - Mountain Aurora Fortress Live (Northern Lights & Snow)",
                "04 - Celestial Dunes Oasis (Desert Waters & Twin Moons)",
                "05 - Floating Sky Citadel of Aetheria (Cloud Falls & Godrays)",
                "06 - Volcanic Obsidian Forge (Molten Magma & Rising Embers)",
                "07 - Sunken Coral Atlantis (Abyssal Caustics & Drifting Plankton)",
                "08 - Cyber-Aegis Neo-Tokyo Bastion (Holo Shield & Wet Reflections)",
                "09 - Autumn Dragon Valley (Cascading Falls & Swirling Maple)",
                "10 - Celestial Starfall Observatory (Nebula Breath & Streaking Meteors)",
                "11 - Ethereal Dreamscript Nexus (PS5 Cosmic Ribbon & FFXII Sky City)"
            ],
            "text": "Live 4K Animated Scene"
        },
        "ultraLightMode": {
            "type": "checkbox",
            "value": true,
            "text": "Ultra-Lightweight / Eco Mode (0% CPU, Auto-Pause on Fullscreen)"
        },
        "soundPack": {
            "type": "dropdown",
            "value": default_pack_idx,
            "items": ["Fantasy Rune Chime", "Mechanical Switch", "Water Droplet", "Cyber Pulse", "Muted"],
            "text": "Click Sound Effect"
        },
        "soundVolume": {
            "type": "slider",
            "value": opts.default_volume,
            "min": 0,
            "max": 100,
            "text": "Click Sound Volume"
        },
        "rippleEffect": {
            "type": "checkbox",
            "value": true,
            "text": "Fluid Water Ripple on Click"
        },
        "fireflyCount": {
            "type": "slider",
            "value": opts.firefly_count,
            "min": 0,
            "max": 150,
            "text": "Interactive Firefly Density"
        },
        "showClock": {
            "type": "checkbox",
            "value": opts.show_clock,
            "text": "Show Clock & Date HUD"
        }
    });
    fs::write(out.join("LivelyProperties.json"), serde_json::to_string_pretty(&lively_props)?)?;

    // 3. index.html
    let index_html = r#"<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Aegis Interactive Live Wallpaper</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <video id="bgVideo" autoplay loop muted playsinline preload="auto">
        <source src="01_citadel_twilight_live.mp4" type="video/mp4">
    </video>
    
    <canvas id="wallpaperCanvas"></canvas>
    
    <div id="hudClock" class="hud-container hidden">
        <div id="timeDisplay">12:00</div>
        <div id="dateDisplay">Wednesday, October 21</div>
    </div>

    <script src="js/audio.js"></script>
    <script src="js/ripple.js"></script>
    <script src="js/particles.js"></script>
    <script src="js/main.js"></script>
</body>
</html>"#;
    fs::write(out.join("index.html"), index_html)?;

    // 4. style.css
    let style_css = r#"* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
    user-select: none;
    -webkit-user-select: none;
}

html, body {
    width: 100%;
    height: 100%;
    overflow: hidden;
    background-color: #050811;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", sans-serif;
}

#bgVideo {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    object-fit: cover;
    z-index: 1;
    display: block;
}

#wallpaperCanvas {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    z-index: 2;
    display: block;
    cursor: default;
    background: transparent;
}

.hud-container {
    position: fixed;
    top: 80px;
    right: 80px;
    z-index: 3;
    color: rgba(255, 255, 255, 0.95);
    text-align: right;
    pointer-events: none;
    text-shadow: 0 4px 20px rgba(0, 0, 0, 0.8), 0 0 40px rgba(80, 180, 255, 0.5);
    transition: opacity 0.5s ease;
}

.hud-container.hidden {
    opacity: 0;
}

#timeDisplay {
    font-size: 5rem;
    font-weight: 200;
    letter-spacing: -2px;
}

#dateDisplay {
    font-size: 1.25rem;
    font-weight: 300;
    color: rgba(210, 235, 255, 0.85);
    letter-spacing: 2px;
    text-transform: uppercase;
}
"#;
    fs::write(out.join("style.css"), style_css)?;

    // 5. js/audio.js - Web Audio API Synthesizer
    let audio_js = r#"// Web Audio API Synthesizer (Zero-latency, 100% offline acoustic engine)
class SoundEngine {
    constructor() {
        this.ctx = null;
        this.soundPack = 0; // 0: Rune Chime, 1: Mechanical, 2: Water Droplet, 3: Cyber Pulse, 4: Muted
        this.volume = 0.6;
        this.initContext();
    }

    initContext() {
        try {
            const AudioContext = window.AudioContext || window.webkitAudioContext;
            this.ctx = new AudioContext();
        } catch (e) {
            console.error("Web Audio not supported:", e);
        }
    }

    resume() {
        if (this.ctx && this.ctx.state === 'suspended') {
            this.ctx.resume();
        }
    }

    setPack(index) {
        this.soundPack = parseInt(index) || 0;
    }

    setVolume(volPercent) {
        this.volume = Math.max(0, Math.min(1, volPercent / 100));
    }

    playClick() {
        if (this.soundPack === 4 || this.volume <= 0.001) return;
        this.resume();
        if (!this.ctx) return;

        const now = this.ctx.currentTime;

        switch (this.soundPack) {
            case 0:
                this.playRuneChime(now);
                break;
            case 1:
                this.playMechanicalClick(now);
                break;
            case 2:
                this.playWaterDroplet(now);
                break;
            case 3:
                this.playCyberPulse(now);
                break;
            default:
                this.playRuneChime(now);
        }
    }

    playRuneChime(now) {
        const freqs = [880, 1320, 1760]; // A5, E6, A6 harmonics
        freqs.forEach((freq, idx) => {
            const osc = this.ctx.createOscillator();
            const gain = this.ctx.createGain();

            osc.type = 'sine';
            osc.frequency.setValueAtTime(freq, now);

            const baseVol = (this.volume * 0.15) / (idx + 1);
            gain.gain.setValueAtTime(baseVol, now);
            gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.35 + idx * 0.08);

            osc.connect(gain);
            gain.connect(this.ctx.destination);

            osc.start(now);
            osc.stop(now + 0.45);
        });
    }

    playMechanicalClick(now) {
        // High-frequency tactile switch transient
        const osc = this.ctx.createOscillator();
        const gain = this.ctx.createGain();
        const filter = this.ctx.createBiquadFilter();

        osc.type = 'square';
        osc.frequency.setValueAtTime(2400, now);
        osc.frequency.exponentialRampToValueAtTime(600, now + 0.025);

        filter.type = 'bandpass';
        filter.frequency.setValueAtTime(3200, now);
        filter.Q.setValueAtTime(3.0, now);

        gain.gain.setValueAtTime(this.volume * 0.25, now);
        gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.035);

        osc.connect(filter);
        filter.connect(gain);
        gain.connect(this.ctx.destination);

        osc.start(now);
        osc.stop(now + 0.04);

        // Body thud
        const thud = this.ctx.createOscillator();
        const thudGain = this.ctx.createGain();
        thud.type = 'triangle';
        thud.frequency.setValueAtTime(140, now);
        thud.frequency.exponentialRampToValueAtTime(50, now + 0.04);

        thudGain.gain.setValueAtTime(this.volume * 0.3, now);
        thudGain.gain.exponentialRampToValueAtTime(0.0001, now + 0.045);

        thud.connect(thudGain);
        thudGain.connect(this.ctx.destination);

        thud.start(now);
        thud.stop(now + 0.05);
    }

    playWaterDroplet(now) {
        const osc = this.ctx.createOscillator();
        const gain = this.ctx.createGain();

        osc.type = 'sine';
        osc.frequency.setValueAtTime(650, now);
        osc.frequency.exponentialRampToValueAtTime(1400, now + 0.08);

        gain.gain.setValueAtTime(this.volume * 0.28, now);
        gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.14);

        osc.connect(gain);
        gain.connect(this.ctx.destination);

        osc.start(now);
        osc.stop(now + 0.15);
    }

    playCyberPulse(now) {
        const osc = this.ctx.createOscillator();
        const gain = this.ctx.createGain();

        osc.type = 'sawtooth';
        osc.frequency.setValueAtTime(1200, now);
        osc.frequency.exponentialRampToValueAtTime(200, now + 0.06);

        gain.gain.setValueAtTime(this.volume * 0.18, now);
        gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.08);

        osc.connect(gain);
        gain.connect(this.ctx.destination);

        osc.start(now);
        osc.stop(now + 0.09);
    }
}
window.soundEngine = new SoundEngine();
"#;
    fs::write(js_dir.join("audio.js"), audio_js)?;

    // 6. js/ripple.js - 2D Fluid Ripple Simulation
    let ripple_js = r#"// 2D Fluid Concentric Ripple Simulator
class RippleFX {
    constructor() {
        this.ripples = [];
        this.enabled = true;
    }

    add(x, y) {
        if (!this.enabled) return;
        this.ripples.push({
            x: x,
            y: y,
            radius: 2,
            maxRadius: Math.max(window.innerWidth, window.innerHeight) * 0.35,
            strength: 1.0,
            speed: 3.5
        });
    }

    update() {
        for (let i = this.ripples.length - 1; i >= 0; i--) {
            const r = this.ripples[i];
            r.radius += r.speed;
            r.strength *= 0.96;
            if (r.strength <= 0.01 || r.radius >= r.maxRadius) {
                this.ripples.splice(i, 1);
            }
        }
    }

    render(ctx) {
        if (this.ripples.length === 0) return;
        ctx.save();
        for (const r of this.ripples) {
            // Refractive wave ring
            const grad = ctx.createRadialGradient(r.x, r.y, Math.max(0, r.radius - 8), r.x, r.y, r.radius + 8);
            grad.addColorStop(0, `rgba(255, 255, 255, 0)`);
            grad.addColorStop(0.5, `rgba(140, 210, 255, ${r.strength * 0.35})`);
            grad.addColorStop(1, `rgba(40, 120, 255, 0)`);

            ctx.beginPath();
            ctx.arc(r.x, r.y, r.radius, 0, Math.PI * 2);
            ctx.lineWidth = 14;
            ctx.strokeStyle = grad;
            ctx.stroke();

            // Inner glowing ripple line
            ctx.beginPath();
            ctx.arc(r.x, r.y, r.radius, 0, Math.PI * 2);
            ctx.lineWidth = 2;
            ctx.strokeStyle = `rgba(220, 245, 255, ${r.strength * 0.6})`;
            ctx.stroke();
        }
        ctx.restore();
    }
}
window.rippleFX = new RippleFX();
"#;
    fs::write(js_dir.join("ripple.js"), ripple_js)?;

    // 7. js/particles.js - Reactive Fireflies
    let particles_js = r#"// Reactive Firefly Particle Engine
class FireflyEngine {
    constructor(count = 50) {
        this.targetCount = count;
        this.particles = [];
        this.mouseX = -1000;
        this.mouseY = -1000;
        this.init();
    }

    init() {
        this.particles = [];
        for (let i = 0; i < this.targetCount; i++) {
            this.particles.push(this.createParticle());
        }
    }

    setCount(count) {
        this.targetCount = count;
        while (this.particles.length < this.targetCount) {
            this.particles.push(this.createParticle());
        }
        if (this.particles.length > this.targetCount) {
            this.particles.length = this.targetCount;
        }
    }

    createParticle() {
        return {
            x: Math.random() * window.innerWidth,
            y: Math.random() * window.innerHeight,
            vx: (Math.random() - 0.5) * 0.8,
            vy: (Math.random() - 0.5) * 0.8,
            size: Math.random() * 2.5 + 1.5,
            hue: Math.random() > 0.5 ? 45 : 185, // Amber warm or Cyan magical
            phase: Math.random() * Math.PI * 2,
            pulseSpeed: Math.random() * 0.04 + 0.02
        };
    }

    scatter(clickX, clickY) {
        for (const p of this.particles) {
            const dx = p.x - clickX;
            const dy = p.y - clickY;
            const dist = Math.sqrt(dx * dx + dy * dy);
            if (dist < 350) {
                const force = (350 - dist) / 350 * 12;
                p.vx += (dx / (dist + 0.1)) * force;
                p.vy += (dy / (dist + 0.1)) * force;
            }
        }
    }

    update() {
        const w = window.innerWidth;
        const h = window.innerHeight;

        for (const p of this.particles) {
            p.phase += p.pulseSpeed;

            // Gentle wander
            p.vx += (Math.random() - 0.5) * 0.1;
            p.vy += (Math.random() - 0.5) * 0.1;

            // Gentle cursor attraction when hovering nearby
            const dx = this.mouseX - p.x;
            const dy = this.mouseY - p.y;
            const dist = Math.sqrt(dx * dx + dy * dy);
            if (dist < 200 && dist > 30) {
                p.vx += (dx / dist) * 0.05;
                p.vy += (dy / dist) * 0.05;
            }

            // Damping
            p.vx *= 0.98;
            p.vy *= 0.98;

            p.x += p.vx;
            p.y += p.vy;

            // Screen wrap
            if (p.x < -20) p.x = w + 20;
            if (p.x > w + 20) p.x = -20;
            if (p.y < -20) p.y = h + 20;
            if (p.y > h + 20) p.y = -20;
        }
    }

    render(ctx) {
        ctx.save();
        for (const p of this.particles) {
            const glow = Math.sin(p.phase) * 0.4 + 0.6;
            const r = p.size * (0.8 + glow * 0.4);

            const grad = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, r * 4);
            const color = p.hue === 45 ? `255, 220, 120` : `120, 240, 255`;
            grad.addColorStop(0, `rgba(${color}, ${glow})`);
            grad.addColorStop(0.3, `rgba(${color}, ${glow * 0.5})`);
            grad.addColorStop(1, `rgba(${color}, 0)`);

            ctx.fillStyle = grad;
            ctx.beginPath();
            ctx.arc(p.x, p.y, r * 4, 0, Math.PI * 2);
            ctx.fill();

            // Core bright dot
            ctx.fillStyle = `rgba(255, 255, 255, ${glow})`;
            ctx.beginPath();
            ctx.arc(p.x, p.y, r * 0.5, 0, Math.PI * 2);
            ctx.fill();
        }
        ctx.restore();
    }
}
window.fireflyEngine = new FireflyEngine(50);
"#;
    fs::write(js_dir.join("particles.js"), particles_js)?;

    // 8. js/main.js - Event coordination and Lively Property Listener
    let main_js = r#"// Main Coordinator for Aegis Interactive Live Wallpaper
const bgVideo = document.getElementById('bgVideo');
const canvas = document.getElementById('wallpaperCanvas');
const ctx = canvas.getContext('2d');

const scenes = [
    "01_citadel_twilight_live.mp4",
    "02_mystical_forest_shrine_live.mp4",
    "03_mountain_aurora_snow_live.mp4"
];

function resizeCanvas() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
}
window.addEventListener('resize', resizeCanvas);
resizeCanvas();

// User Interaction Listeners (Click & Move)
window.addEventListener('pointerdown', (e) => {
    window.soundEngine.playClick();
    window.rippleFX.add(e.clientX, e.clientY);
    window.fireflyEngine.scatter(e.clientX, e.clientY);
});

window.addEventListener('pointermove', (e) => {
    window.fireflyEngine.mouseX = e.clientX;
    window.fireflyEngine.mouseY = e.clientY;
});

// Clock HUD
function updateClock() {
    const now = new Date();
    const timeElem = document.getElementById('timeDisplay');
    const dateElem = document.getElementById('dateDisplay');
    if (timeElem && dateElem) {
        timeElem.textContent = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        dateElem.textContent = now.toLocaleDateString([], { weekday: 'long', month: 'long', day: 'numeric' });
    }
}
setInterval(updateClock, 1000);
updateClock();

// Lively Property Listener API
function livelyPropertyListener(name, val) {
    switch (name) {
        case "activeScene":
            const idx = parseInt(val) || 0;
            if (scenes[idx]) {
                bgVideo.src = scenes[idx];
                bgVideo.play().catch(e => console.log("Video play error:", e));
            }
            break;
        case "soundPack":
            window.soundEngine.setPack(val);
            break;
        case "soundVolume":
            window.soundEngine.setVolume(val);
            break;
        case "rippleEffect":
            window.rippleFX.enabled = !!val;
            break;
        case "fireflyCount":
            window.fireflyEngine.setCount(val);
            break;
        case "showClock":
            const hud = document.getElementById('hudClock');
            if (hud) {
                if (val) hud.classList.remove('hidden');
                else hud.classList.add('hidden');
            }
            break;
    }
}

// 60FPS Physics Render Loop on top of live video
function render() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Update & Render Physics Layers (Ripple and Fireflies)
    window.rippleFX.update();
    window.rippleFX.render(ctx);

    window.fireflyEngine.update();
    window.fireflyEngine.render(ctx);

    requestAnimationFrame(render);
}
requestAnimationFrame(render);
"#;
    fs::write(js_dir.join("main.js"), main_js)?;

    Ok(out.to_path_buf())
}
