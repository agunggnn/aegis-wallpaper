// ==============================================================================
// 🛡️ Aegis Sovereign Realm Dynamic FX Engine (HTML5 Canvas 60FPS)
// High-performance, ultra-lightweight procedural atmospheric physics for all
// 10 Sovereign Fantasy Realms. Zero MP4 compression artifacts.
// ==============================================================================

class RealmFXEngine {
    constructor() {
        this.currentRealm = 0;
        this.width = window.innerWidth;
        this.height = window.innerHeight;
        this.time = 0;
        this.enabled = true;
        this.ultraLight = false;

        // Particle & effect storage
        this.meteors = [];
        this.stars = [];
        this.leaves = [];
        this.embers = [];
        this.bubbles = [];
        this.rainDrops = [];
        this.clouds = [];
        this.caustics = [];
        this.wisps = [];
        this.snowFlakes = [];

        this.initAll();
    }

    resize(w, h) {
        this.width = w;
        this.height = h;
        this.initAll();
    }

    setRealm(idx) {
        this.currentRealm = idx;
        this.initRealm(idx);
    }

    initAll() {
        this.initRealm(this.currentRealm);
    }

    initRealm(idx) {
        const w = this.width;
        const h = this.height;

        // Reset particle arrays
        this.meteors = [];
        this.stardust = [];
        this.bursts = [];
        this.stars = [];
        this.leaves = [];
        this.embers = [];
        this.bubbles = [];
        this.rainDrops = [];
        this.snowFlakes = [];
        this.wisps = [];

        // -------------------------------------------------------------
        // Realm 10 (idx = 9): Celestial Starfall Observatory
        // Radial Radiant Stream Meteor Shower + Twinkling Stars + Nebula
        // -------------------------------------------------------------
        if (idx === 9) {
            // Radiant point: Core of the cosmic galaxy/nebula in upper sky
            this.radiantX = w * 0.50;
            this.radiantY = h * 0.245;

            // Pre-seed background cosmic starfield (85 stars)
            for (let i = 0; i < 85; i++) {
                this.stars.push({
                    x: Math.random() * w,
                    y: Math.random() * (h * 0.58), // Only in sky region
                    baseAlpha: 0.3 + Math.random() * 0.6,
                    twinkleSpeed: 0.8 + Math.random() * 2.5,
                    phase: Math.random() * Math.PI * 2,
                    radius: 0.8 + Math.random() * 1.5,
                    hasCross: Math.random() < 0.15, // Bright diffraction spike stars
                    color: Math.random() < 0.3 ? '#a8d8ff' : (Math.random() < 0.5 ? '#ffe8a8' : '#ffffff')
                });
            }

            // Pool of shooting stars
            this.meteorTimer = 0;
        }

        // -------------------------------------------------------------
        // Realm 04 (idx = 3): Celestial Dunes Oasis
        // -------------------------------------------------------------
        else if (idx === 3) {
            for (let i = 0; i < (this.ultraLight ? 20 : 45); i++) {
                this.wisps.push({
                    x: Math.random() * w,
                    y: h * 0.4 + Math.random() * (h * 0.55),
                    vx: -0.3 + Math.random() * 0.6,
                    vy: -0.2 - Math.random() * 0.4,
                    radius: 1.5 + Math.random() * 2.5,
                    alpha: 0.4 + Math.random() * 0.5,
                    color: i % 2 === 0 ? 'rgba(255, 215, 120, ' : 'rgba(120, 230, 255, '
                });
            }
        }

        // -------------------------------------------------------------
        // Realm 05 (idx = 4): Floating Sky Citadel of Aetheria
        // -------------------------------------------------------------
        else if (idx === 4) {
            for (let i = 0; i < (this.ultraLight ? 15 : 40); i++) {
                this.wisps.push({
                    x: w * 0.35 + Math.random() * (w * 0.3),
                    y: h * 0.45 + Math.random() * (h * 0.45),
                    vy: 1.2 + Math.random() * 2.0,
                    vx: -0.2 + Math.random() * 0.4,
                    radius: 1.5 + Math.random() * 3.0,
                    alpha: 0.2 + Math.random() * 0.4
                });
            }
        }

        // -------------------------------------------------------------
        // Realm 06 (idx = 5): Volcanic Obsidian Forge
        // Rising Turbulent Ash & Fiery Magma Embers
        // -------------------------------------------------------------
        else if (idx === 5) {
            for (let i = 0; i < (this.ultraLight ? 25 : 55); i++) {
                this.embers.push({
                    x: w * 0.2 + Math.random() * (w * 0.6),
                    y: h * 0.6 + Math.random() * (h * 0.4),
                    vy: -(1.5 + Math.random() * 2.5),
                    vx: -0.5 + Math.random() * 1.0,
                    size: 1.2 + Math.random() * 2.8,
                    life: Math.random(),
                    decay: 0.004 + Math.random() * 0.008,
                    heat: 1.0,
                    turbPhase: Math.random() * Math.PI * 2
                });
            }
        }

        // -------------------------------------------------------------
        // Realm 07 (idx = 6): Sunken Coral Atlantis
        // Oceanic Bubbles & Bioluminescent Deep-Sea Plankton
        // -------------------------------------------------------------
        else if (idx === 6) {
            for (let i = 0; i < (this.ultraLight ? 15 : 35); i++) {
                this.bubbles.push({
                    x: Math.random() * w,
                    y: Math.random() * h,
                    radius: 2.0 + Math.random() * 5.0,
                    speed: 0.6 + Math.random() * 1.6,
                    wobbleSpeed: 1.5 + Math.random() * 2.0,
                    wobbleAmp: 1.0 + Math.random() * 2.5,
                    alpha: 0.3 + Math.random() * 0.5
                });
            }
        }

        // -------------------------------------------------------------
        // Realm 08 (idx = 7): Cyber-Aegis Neo-Tokyo Bastion
        // Atmospheric Cyber Rain & Traffic Energy Trails
        // -------------------------------------------------------------
        else if (idx === 7) {
            for (let i = 0; i < (this.ultraLight ? 40 : 80); i++) {
                this.rainDrops.push({
                    x: Math.random() * (w + 200) - 100,
                    y: Math.random() * h,
                    length: 12 + Math.random() * 22,
                    speed: 12 + Math.random() * 10,
                    alpha: 0.25 + Math.random() * 0.45,
                    color: Math.random() < 0.4 ? 'rgba(80, 240, 255,' : (Math.random() < 0.7 ? 'rgba(255, 80, 210,' : 'rgba(220, 240, 255,')
                });
            }
        }

        // -------------------------------------------------------------
        // Realm 09 (idx = 8): Autumn Dragon Valley
        // Ultra-Calm, Serene Japanese Momiji Maple Drift (Thermal Float)
        // -------------------------------------------------------------
        else if (idx === 8) {
            const count = (typeof renderEngineMode !== 'undefined' && renderEngineMode === 1) ? 6 : (this.ultraLight ? 6 : 12);
            for (let i = 0; i < count; i++) {
                this.leaves.push({
                    x: Math.random() * w,
                    y: Math.random() * h,
                    vx: 0.15 + Math.random() * 0.25,          // Calm horizontal drift (0.15 - 0.40 px/frame)
                    vy: 0.20 + Math.random() * 0.35,          // Slow, gentle descent (0.20 - 0.55 px/frame)
                    size: 7 + Math.random() * 6,              // Delicate Momiji leaf size
                    angle: Math.random() * Math.PI * 2,
                    spinSpeed: (Math.random() - 0.5) * 0.012, // Lazy tilt rotation
                    tumble: Math.random() * Math.PI * 2,
                    tumbleSpeed: 0.01 + Math.random() * 0.015,
                    swayOffset: Math.random() * Math.PI * 2,
                    color: Math.random() < 0.45 ? '#c0392b' : (Math.random() < 0.75 ? '#d35400' : '#f39c12')
                });
            }
        }

        // -------------------------------------------------------------
        // Realm 01 (idx = 0): Citadel of Valerius
        // -------------------------------------------------------------
        else if (idx === 0) {
            for (let i = 0; i < (this.ultraLight ? 15 : 35); i++) {
                this.wisps.push({
                    x: Math.random() * w,
                    y: h * 0.5 + Math.random() * (h * 0.48),
                    vx: 0.2 + Math.random() * 0.5,
                    vy: -0.3 - Math.random() * 0.5,
                    radius: 1.5 + Math.random() * 2.5,
                    alpha: 0.3 + Math.random() * 0.4,
                    color: 'rgba(255, 200, 100, '
                });
            }
        }

        // -------------------------------------------------------------
        // Realm 02 (idx = 1): Mystical Forest Shrine
        // -------------------------------------------------------------
        else if (idx === 1) {
            for (let i = 0; i < (this.ultraLight ? 15 : 40); i++) {
                this.wisps.push({
                    x: w * 0.2 + Math.random() * (w * 0.6),
                    y: h * 0.35 + Math.random() * (h * 0.55),
                    vx: -0.3 + Math.random() * 0.6,
                    vy: -0.2 + Math.random() * 0.4,
                    radius: 1.8 + Math.random() * 3.0,
                    alpha: 0.4 + Math.random() * 0.5,
                    color: Math.random() < 0.5 ? 'rgba(100, 255, 230, ' : 'rgba(230, 255, 140, '
                });
            }
        }

        // -------------------------------------------------------------
        // Realm 03 (idx = 2): Mountain Aurora Fortress
        // Ultra-Slow, Calm Mountain Snowfall (Serene Flurries)
        // -------------------------------------------------------------
        else if (idx === 2) {
            for (let i = 0; i < (this.ultraLight ? 25 : 55); i++) {
                const depth = Math.random(); // 0: distant, 1: foreground
                this.snowFlakes.push({
                    x: Math.random() * w,
                    y: Math.random() * h,
                    radius: 1.0 + depth * 3.0,
                    speed: 0.12 + depth * 0.35,      // Ultra-slow, peaceful descent
                    drift: 0.15 + depth * 0.35,      // Gentle horizontal sway
                    alpha: 0.30 + depth * 0.55,
                    wobbleSpeed: 0.4 + Math.random() * 0.6
                });
            }
        }
    }

    // =========================================================================
    // Main 60FPS Render Dispatcher
    // =========================================================================
    updateAndRender(ctx) {
        if (!this.enabled) return;
        this.time += 0.016;

        switch (this.currentRealm) {
            case 9: this.renderRealm10_Starfall(ctx); break;
            case 3: this.renderRealm04_Dunes(ctx); break;
            case 4: this.renderRealm05_SkyCitadel(ctx); break;
            case 5: this.renderRealm06_ObsidianForge(ctx); break;
            case 6: this.renderRealm07_Atlantis(ctx); break;
            case 7: this.renderRealm08_CyberMegacity(ctx); break;
            case 8: this.renderRealm09_AutumnValley(ctx); break;
            case 0: this.renderRealm01_Citadel(ctx); break;
            case 1: this.renderRealm02_ForestShrine(ctx); break;
            case 2: this.renderRealm03_MountainAurora(ctx); break;
        }
    }

    // =========================================================================
    // REALM 10: Celestial Starfall Observatory
    // NATURAL CELESTIAL METEOR SHOWER (Aligned with Artwork Trajectory)
    // =========================================================================
    renderRealm10_Starfall(ctx) {
        const w = this.width;
        const h = this.height;

        // 1. Subtle Cosmic Nebula Breath (Ultraviolet & Starlight glow across galactic core)
        const nebulaPulse = Math.sin(this.time * 0.5) * 0.5 + 0.5;
        const coreX = w * 0.50;
        const coreY = h * 0.245;
        const nebGrad = ctx.createRadialGradient(coreX, coreY, 15, coreX, coreY, w * 0.35);
        nebGrad.addColorStop(0, `rgba(175, 75, 255, ${0.07 * nebulaPulse})`);
        nebGrad.addColorStop(0.5, `rgba(60, 140, 255, ${0.035 * nebulaPulse})`);
        nebGrad.addColorStop(1, 'rgba(0, 0, 0, 0)');
        ctx.fillStyle = nebGrad;
        ctx.fillRect(0, 0, w, h * 0.65);

        // Subtle brass dome starlight reflection
        const domeX = w * 0.50;
        const domeY = h * 0.63;
        const domeGlow = ctx.createRadialGradient(domeX, domeY, 5, domeX, domeY, w * 0.16);
        domeGlow.addColorStop(0, `rgba(255, 215, 120, ${0.08 * (Math.sin(this.time * 1.0) * 0.5 + 0.5)})`);
        domeGlow.addColorStop(1, 'rgba(0, 0, 0, 0)');
        ctx.fillStyle = domeGlow;
        ctx.fillRect(domeX - w * 0.16, domeY - w * 0.16, w * 0.32, w * 0.32);

        // 2. Delicate Twinkling Cosmic Stars in Upper Sky
        for (const s of this.stars) {
            const twinkle = Math.sin(this.time * s.twinkleSpeed + s.phase) * 0.5 + 0.5;
            const curAlpha = s.baseAlpha * (0.35 + 0.65 * twinkle);

            ctx.fillStyle = s.color;
            ctx.globalAlpha = curAlpha;
            ctx.beginPath();
            ctx.arc(s.x, s.y, s.radius, 0, Math.PI * 2);
            ctx.fill();

            if (s.hasCross && curAlpha > 0.6) {
                ctx.strokeStyle = s.color;
                ctx.lineWidth = 0.7;
                const spikeLen = s.radius * 3.5;
                ctx.beginPath();
                ctx.moveTo(s.x - spikeLen, s.y);
                ctx.lineTo(s.x + spikeLen, s.y);
                ctx.moveTo(s.x, s.y - spikeLen);
                ctx.lineTo(s.x + spikeLen, s.y);
                ctx.stroke();
            }
        }
        ctx.globalAlpha = 1.0;

        // 3. Natural Celestial Meteor Shower along Artwork Trajectory
        // Artwork streaks fall diagonally: upper-right -> lower-left at ~142° (slope ≈ -0.8)
        this.meteorTimer = (this.meteorTimer || 0) + 0.016;
        const spawnInterval = this.ultraLight ? 0.8 : 0.42;

        if (this.meteorTimer > spawnInterval) {
            this.meteorTimer = 0;

            // Spawn across upper right sky panorama
            const spawnX = w * 0.15 + Math.random() * (w * 0.95);
            const spawnY = Math.random() * (h * 0.35);

            // Natural celestial angle matching painted streaks (138° to 146°)
            const angleDeg = 138 + Math.random() * 8;
            const angleRad = (angleDeg * Math.PI) / 180;
            const isBolide = Math.random() < 0.15; // 15% bright bolide

            const speed = (isBolide ? 1350 : 1100) + Math.random() * 500;
            const trailLen = (isBolide ? 180 : 120) + Math.random() * 80;

            this.meteors.push({
                x: spawnX,
                y: spawnY,
                vx: Math.cos(angleRad) * speed,
                vy: Math.sin(angleRad) * speed,
                angle: angleRad,
                cos: Math.cos(angleRad),
                sin: Math.sin(angleRad),
                trailLen: trailLen,
                life: 0,
                maxLife: (trailLen + Math.max(w, h) * 0.6) / speed,
                isBolide: isBolide,
                colorType: isBolide ? 'gold' : (Math.random() < 0.5 ? 'cyan' : 'violet'),
                brightness: 0.8 + Math.random() * 0.2
            });
        }

        // Render each natural celestial shooting star
        ctx.save();
        ctx.globalCompositeOperation = 'lighter';

        for (let i = this.meteors.length - 1; i >= 0; i--) {
            const m = this.meteors[i];
            m.x += m.vx * 0.016;
            m.y += m.vy * 0.016;
            m.life += 0.016;

            if (m.life >= m.maxLife || m.x < -100 || m.y > h * 0.85) {
                this.meteors.splice(i, 1);
                continue;
            }

            // Head and Tail coordinates on the diagonal path
            const headX = m.x;
            const headY = m.y;
            const tailX = m.x - m.cos * m.trailLen;
            const tailY = m.y - m.sin * m.trailLen;

            // Smooth fade-in, peak, fade-out
            const progress = m.life / m.maxLife;
            let alpha = m.brightness;
            if (progress < 0.15) alpha *= (progress / 0.15);
            else if (progress > 0.70) alpha *= (1.0 - (progress - 0.70) / 0.30);

            if (alpha <= 0.01) continue;

            // Gradient meteor trail: White hot tip -> Chromatic ionization -> Transparent
            const grad = ctx.createLinearGradient(headX, headY, tailX, tailY);
            if (m.colorType === 'gold') {
                grad.addColorStop(0, `rgba(255, 255, 255, ${alpha})`);
                grad.addColorStop(0.2, `rgba(255, 220, 130, ${alpha * 0.9})`);
                grad.addColorStop(0.6, `rgba(255, 140, 50, ${alpha * 0.4})`);
                grad.addColorStop(1, 'rgba(180, 50, 20, 0)');
            } else if (m.colorType === 'cyan') {
                grad.addColorStop(0, `rgba(255, 255, 255, ${alpha})`);
                grad.addColorStop(0.2, `rgba(130, 240, 255, ${alpha * 0.9})`);
                grad.addColorStop(0.6, `rgba(60, 130, 255, ${alpha * 0.4})`);
                grad.addColorStop(1, 'rgba(30, 40, 160, 0)');
            } else {
                grad.addColorStop(0, `rgba(255, 255, 255, ${alpha})`);
                grad.addColorStop(0.2, `rgba(230, 170, 255, ${alpha * 0.9})`);
                grad.addColorStop(0.6, `rgba(150, 70, 255, ${alpha * 0.4})`);
                grad.addColorStop(1, 'rgba(70, 20, 150, 0)');
            }

            ctx.strokeStyle = grad;
            ctx.lineWidth = m.isBolide ? 2.6 : 1.6;
            ctx.lineCap = 'round';
            ctx.beginPath();
            ctx.moveTo(headX, headY);
            ctx.lineTo(tailX, tailY);
            ctx.stroke();

            // Luminous glowing head
            const headR = m.isBolide ? 3.0 : 1.8;
            const flare = ctx.createRadialGradient(headX, headY, 0, headX, headY, headR * 3.0);
            flare.addColorStop(0, `rgba(255, 255, 255, ${alpha})`);
            flare.addColorStop(0.5, m.colorType === 'gold' ? `rgba(255, 200, 100, ${alpha * 0.6})` : `rgba(120, 220, 255, ${alpha * 0.6})`);
            flare.addColorStop(1, 'rgba(0, 0, 0, 0)');
            ctx.fillStyle = flare;
            ctx.beginPath();
            ctx.arc(headX, headY, headR * 3.0, 0, Math.PI * 2);
            ctx.fill();
        }

        ctx.restore();
    }

    // =========================================================================
    // REALM 04: Celestial Dunes Oasis
    // =========================================================================
    renderRealm04_Dunes(ctx) {
        const w = this.width;
        const h = this.height;

        // Oasis water pool specular shimmer (Center bottom)
        const poolX = w * 0.50;
        const poolY = h * 0.72;
        const poolGlow = ctx.createRadialGradient(poolX, poolY, 10, poolX, poolY, w * 0.22);
        const caustPulse = Math.sin(this.time * 1.5) * 0.5 + 0.5;
        poolGlow.addColorStop(0, `rgba(100, 230, 255, ${0.12 * caustPulse})`);
        poolGlow.addColorStop(0.6, `rgba(40, 180, 220, ${0.05 * caustPulse})`);
        poolGlow.addColorStop(1, 'rgba(0, 0, 0, 0)');
        ctx.fillStyle = poolGlow;
        ctx.fillRect(poolX - w * 0.25, poolY - h * 0.15, w * 0.5, h * 0.3);

        // Golden & Azure Stardust Motes
        for (const wisp of this.wisps) {
            wisp.x += wisp.vx;
            wisp.y += wisp.vy;
            if (wisp.y < h * 0.35) {
                wisp.y = h * 0.95;
                wisp.x = Math.random() * w;
            }
            if (wisp.x < 0) wisp.x = w;
            if (wisp.x > w) wisp.x = 0;

            const flicker = Math.sin(this.time * 2.0 + wisp.x) * 0.3 + 0.7;
            ctx.fillStyle = wisp.color + (wisp.alpha * flicker) + ')';
            ctx.beginPath();
            ctx.arc(wisp.x, wisp.y, wisp.radius, 0, Math.PI * 2);
            ctx.fill();
        }
    }

    // =========================================================================
    // REALM 05: Floating Sky Citadel of Aetheria
    // =========================================================================
    renderRealm05_SkyCitadel(ctx) {
        const w = this.width;
        const h = this.height;

        // Cascading water mist particles
        for (const wisp of this.wisps) {
            wisp.y += wisp.vy;
            wisp.x += wisp.vx;
            if (wisp.y > h * 0.92) {
                wisp.y = h * 0.45;
                wisp.x = w * 0.36 + Math.random() * (w * 0.28);
            }
            ctx.fillStyle = `rgba(230, 245, 255, ${wisp.alpha})`;
            ctx.beginPath();
            ctx.arc(wisp.x, wisp.y, wisp.radius, 0, Math.PI * 2);
            ctx.fill();
        }

        // Golden hour sunray shimmer in top sky
        const rayAlpha = (Math.sin(this.time * 0.8) * 0.5 + 0.5) * 0.08;
        const sunRay = ctx.createLinearGradient(w * 0.5, 0, w * 0.4, h * 0.6);
        sunRay.addColorStop(0, `rgba(255, 225, 140, ${rayAlpha})`);
        sunRay.addColorStop(1, 'rgba(255, 225, 140, 0)');
        ctx.fillStyle = sunRay;
        ctx.fillRect(0, 0, w, h * 0.7);
    }

    // =========================================================================
    // REALM 06: Volcanic Obsidian Forge
    // =========================================================================
    renderRealm06_ObsidianForge(ctx) {
        const w = this.width;
        const h = this.height;

        // Magma caldera heat breathing pulse (Center lower chasm)
        const caldPulse = Math.sin(this.time * 1.8) * 0.5 + 0.5;
        const caldGlow = ctx.createRadialGradient(w * 0.5, h * 0.78, 10, w * 0.5, h * 0.78, w * 0.35);
        caldGlow.addColorStop(0, `rgba(255, 80, 20, ${0.16 * caldPulse})`);
        caldGlow.addColorStop(0.5, `rgba(220, 40, 10, ${0.08 * caldPulse})`);
        caldGlow.addColorStop(1, 'rgba(0, 0, 0, 0)');
        ctx.fillStyle = caldGlow;
        ctx.fillRect(0, h * 0.4, w, h * 0.6);

        // Rising embers & fiery ash sparks
        for (const e of this.embers) {
            e.y += e.vy;
            e.x += e.vx + Math.sin(this.time * 3.0 + e.turbPhase) * 0.8;
            e.life -= e.decay;

            if (e.life <= 0 || e.y < h * 0.25) {
                e.life = 1.0;
                e.y = h * 0.75 + Math.random() * (h * 0.22);
                e.x = w * 0.25 + Math.random() * (w * 0.5);
            }

            const alpha = e.life * 0.85;
            ctx.fillStyle = e.life > 0.6 ? `rgba(255, 230, 120, ${alpha})` : (e.life > 0.3 ? `rgba(255, 100, 20, ${alpha})` : `rgba(180, 40, 10, ${alpha * 0.6})`);
            ctx.beginPath();
            ctx.arc(e.x, e.y, e.size * e.life, 0, Math.PI * 2);
            ctx.fill();
        }
    }

    // =========================================================================
    // REALM 07: Sunken Coral Atlantis
    // =========================================================================
    renderRealm07_Atlantis(ctx) {
        const w = this.width;
        const h = this.height;

        // Underwater sunlight shafts
        const sunShaft = (Math.sin(this.time * 0.7) * 0.5 + 0.5) * 0.07;
        const shaftGrad = ctx.createLinearGradient(w * 0.3, 0, w * 0.45, h * 0.8);
        shaftGrad.addColorStop(0, `rgba(120, 230, 255, ${sunShaft})`);
        shaftGrad.addColorStop(1, 'rgba(40, 120, 220, 0)');
        ctx.fillStyle = shaftGrad;
        ctx.fillRect(0, 0, w, h);

        // Ascending air bubbles with specular crescent
        for (const b of this.bubbles) {
            b.y -= b.speed;
            b.x += Math.sin(this.time * b.wobbleSpeed) * b.wobbleAmp * 0.2;

            if (b.y < -10) {
                b.y = h + 10;
                b.x = Math.random() * w;
            }

            ctx.strokeStyle = `rgba(180, 240, 255, ${b.alpha})`;
            ctx.lineWidth = 1.2;
            ctx.beginPath();
            ctx.arc(b.x, b.y, b.radius, 0, Math.PI * 2);
            ctx.stroke();

            // Bubble highlight
            ctx.fillStyle = `rgba(255, 255, 255, ${b.alpha * 0.8})`;
            ctx.beginPath();
            ctx.arc(b.x - b.radius * 0.3, b.y - b.radius * 0.3, b.radius * 0.3, 0, Math.PI * 2);
            ctx.fill();
        }
    }

    // =========================================================================
    // REALM 08: Cyber-Aegis Neo-Tokyo Bastion
    // =========================================================================
    renderRealm08_CyberMegacity(ctx) {
        const w = this.width;
        const h = this.height;

        // Slanted atmospheric rain streaks
        ctx.lineWidth = 1.0;
        for (const r of this.rainDrops) {
            r.y += r.speed;
            r.x += r.speed * 0.2; // 12-degree angle
            if (r.y > h) {
                r.y = -r.length;
                r.x = Math.random() * (w + 200) - 100;
            }

            ctx.strokeStyle = r.color + r.alpha + ')';
            ctx.beginPath();
            ctx.moveTo(r.x, r.y);
            ctx.lineTo(r.x + r.length * 0.2, r.y + r.length);
            ctx.stroke();
        }

        // Holographic Aegis Shield frequency pulse on spires
        const shieldPulse = (Math.sin(this.time * 3.5) * 0.5 + 0.5) * 0.09;
        const shieldGlow = ctx.createRadialGradient(w * 0.5, h * 0.35, 10, w * 0.5, h * 0.35, w * 0.3);
        shieldGlow.addColorStop(0, `rgba(40, 240, 255, ${shieldPulse})`);
        shieldGlow.addColorStop(0.7, `rgba(255, 40, 200, ${shieldPulse * 0.5})`);
        shieldGlow.addColorStop(1, 'rgba(0, 0, 0, 0)');
        ctx.fillStyle = shieldGlow;
        ctx.fillRect(w * 0.2, 0, w * 0.6, h * 0.6);
    }

    // =========================================================================
    // REALM 09: Autumn Dragon Valley
    // =========================================================================
    renderRealm09_AutumnValley(ctx) {
        const w = this.width;
        const h = this.height;

        // Serene Drifting Japanese Maple Leaves (Gentle pendulum sway)
        for (const leaf of this.leaves) {
            leaf.x += leaf.vx + Math.sin(this.time * 0.8 + leaf.swayOffset) * 0.25;
            leaf.y += leaf.vy;
            leaf.angle += leaf.spinSpeed;
            leaf.tumble += leaf.tumbleSpeed;

            if (leaf.y > h + 20) {
                leaf.y = -20;
                leaf.x = Math.random() * (w * 0.9);
            }
            if (leaf.x > w + 20) leaf.x = -20;

            const scaleX = Math.cos(leaf.tumble) * 0.8; // 3D tumbling compression
            const scaleY = 1.0;

            ctx.save();
            ctx.translate(leaf.x, leaf.y);
            ctx.rotate(leaf.angle);
            ctx.scale(scaleX, scaleY);

            // Draw Delicate Maple Leaf Contour
            ctx.fillStyle = leaf.color;
            ctx.globalAlpha = 0.55; // Soft translucent watercolor aesthetic
            ctx.beginPath();
            const s = leaf.size;
            ctx.moveTo(0, -s);
            ctx.quadraticCurveTo(s * 0.5, -s * 0.5, s, -s * 0.2);
            ctx.quadraticCurveTo(s * 0.6, s * 0.2, s * 0.8, s * 0.8);
            ctx.quadraticCurveTo(s * 0.2, s * 0.5, 0, s);
            ctx.quadraticCurveTo(-s * 0.2, s * 0.5, -s * 0.8, s * 0.8);
            ctx.quadraticCurveTo(-s * 0.6, s * 0.2, -s, -s * 0.2);
            ctx.quadraticCurveTo(-s * 0.5, -s * 0.5, 0, -s);
            ctx.fill();

            ctx.restore();
        }
        ctx.globalAlpha = 1.0;
    }

    // =========================================================================
    // REALM 01: Valerius Citadel Twilight
    // =========================================================================
    renderRealm01_Citadel(ctx) {
        const w = this.width;
        const h = this.height;

        // Sunset Godrays
        const sunX = w * 0.48;
        const sunY = h * 0.22;
        const rayAlpha = (Math.sin(this.time * 0.9) * 0.5 + 0.5) * 0.10;
        const rayGlow = ctx.createRadialGradient(sunX, sunY, 15, sunX, sunY, w * 0.45);
        rayGlow.addColorStop(0, `rgba(255, 215, 120, ${rayAlpha})`);
        rayGlow.addColorStop(0.6, `rgba(255, 140, 60, ${rayAlpha * 0.5})`);
        rayGlow.addColorStop(1, 'rgba(0, 0, 0, 0)');
        ctx.fillStyle = rayGlow;
        ctx.fillRect(0, 0, w, h * 0.7);

        // Golden sunset embers
        for (const wisp of this.wisps) {
            wisp.x += wisp.vx;
            wisp.y += wisp.vy;
            if (wisp.y < h * 0.3) {
                wisp.y = h * 0.92;
                wisp.x = Math.random() * w;
            }
            ctx.fillStyle = wisp.color + wisp.alpha + ')';
            ctx.beginPath();
            ctx.arc(wisp.x, wisp.y, wisp.radius, 0, Math.PI * 2);
            ctx.fill();
        }
    }

    // =========================================================================
    // REALM 02: Mystical Forest Shrine
    // =========================================================================
    renderRealm02_ForestShrine(ctx) {
        const w = this.width;
        const h = this.height;

        // Altar Rune Glow Pulse
        const shrineX = w * 0.50;
        const shrineY = h * 0.65;
        const runePulse = (Math.sin(this.time * 1.5) * 0.5 + 0.5) * 0.15;
        const runicGlow = ctx.createRadialGradient(shrineX, shrineY, 5, shrineX, shrineY, w * 0.22);
        runicGlow.addColorStop(0, `rgba(60, 240, 220, ${runePulse})`);
        runicGlow.addColorStop(0.5, `rgba(40, 140, 255, ${runePulse * 0.5})`);
        runicGlow.addColorStop(1, 'rgba(0, 0, 0, 0)');
        ctx.fillStyle = runicGlow;
        ctx.fillRect(shrineX - w * 0.25, shrineY - w * 0.25, w * 0.5, w * 0.5);

        // Ethereal forest spirits
        for (const wisp of this.wisps) {
            wisp.x += wisp.vx;
            wisp.y += wisp.vy;
            if (wisp.y < h * 0.2) wisp.y = h * 0.85;
            if (wisp.x < 0) wisp.x = w;
            if (wisp.x > w) wisp.x = 0;

            const glow = Math.sin(this.time * 3.0 + wisp.x) * 0.3 + 0.7;
            ctx.fillStyle = wisp.color + (wisp.alpha * glow) + ')';
            ctx.beginPath();
            ctx.arc(wisp.x, wisp.y, wisp.radius, 0, Math.PI * 2);
            ctx.fill();
        }
    }

    // =========================================================================
    // REALM 03: Mountain Aurora Fortress
    // =========================================================================
    renderRealm03_MountainAurora(ctx) {
        const w = this.width;
        const h = this.height;

        // Undulating Northern Lights Curtains (Emerald green & violet)
        const auroraTime = this.time * 0.6;
        for (let i = 0; i < 3; i++) {
            const waveY = h * (0.18 + i * 0.08) + Math.sin(auroraTime + i * 1.5) * (h * 0.04);
            const aurGrad = ctx.createLinearGradient(0, waveY - h * 0.12, 0, waveY + h * 0.12);
            const col = i === 1 ? '160, 60, 240' : '40, 230, 160';
            aurGrad.addColorStop(0, `rgba(${col}, 0)`);
            aurGrad.addColorStop(0.5, `rgba(${col}, ${0.11 - i * 0.02})`);
            aurGrad.addColorStop(1, `rgba(${col}, 0)`);

            ctx.fillStyle = aurGrad;
            ctx.fillRect(0, waveY - h * 0.12, w, h * 0.24);
        }

        // Parallax Snowfall
        for (const snow of this.snowFlakes) {
            snow.y += snow.speed;
            snow.x += Math.sin(this.time * snow.wobbleSpeed) * snow.drift;

            if (snow.y > h + 5) {
                snow.y = -5;
                snow.x = Math.random() * w;
            }

            ctx.fillStyle = `rgba(240, 248, 255, ${snow.alpha})`;
            ctx.beginPath();
            ctx.arc(snow.x, snow.y, snow.radius, 0, Math.PI * 2);
            ctx.fill();
        }
    }
}

// Attach globally
window.realmFX = new RealmFXEngine();
