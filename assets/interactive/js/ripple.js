// ==============================================================================
// 🛡️ Sovereign Realm-Aware Elemental Impact Engine
// Context-intelligent interactive click physics. Each fantasy realm features its
// own authentic elemental physics (Magma, Cyber, Frost, Stardust, Flora, etc.)
// instead of generic water ripples on non-water maps.
// ==============================================================================

class RippleFX {
    constructor() {
        this.impacts = [];
        this.sparks = [];
        this.enabled = true;
    }

    add(x, y) {
        if (!this.enabled) return;
        const realm = (typeof window.currentSceneIdx === 'number') ? window.currentSceneIdx : 9;

        // Configuration based on realm theme
        let config = {
            type: 'cosmic',
            colorOuter: 'rgba(168, 85, 247, ',
            colorInner: 'rgba(236, 72, 153, ',
            crest: '#fae8ff',
            speed: 6.5,
            maxRadius: Math.min(window.innerWidth, window.innerHeight) * 0.35,
            particleColor: '#f472b6',
            particleCount: 8,
            shape: 'circle'
        };

        switch (realm) {
            case 0: // Citadel Twilight: Royal Arcane Ring
                config = {
                    type: 'twilight',
                    colorOuter: 'rgba(167, 139, 250, ',
                    colorInner: 'rgba(216, 180, 254, ',
                    crest: '#ffffff',
                    speed: 5.5,
                    maxRadius: Math.min(window.innerWidth, window.innerHeight) * 0.32,
                    particleColor: '#c084fc',
                    particleCount: 6,
                    shape: 'circle'
                };
                break;
            case 1: // Forest Shrine: Emerald Nature Flora Pulse
                config = {
                    type: 'nature',
                    colorOuter: 'rgba(34, 197, 94, ',
                    colorInner: 'rgba(74, 222, 128, ',
                    crest: '#dcfce7',
                    speed: 4.5,
                    maxRadius: Math.min(window.innerWidth, window.innerHeight) * 0.30,
                    particleColor: '#4ade80',
                    particleCount: 10,
                    shape: 'leaf'
                };
                break;
            case 2: // Aurora Fortress: Frost Ice Crystal Shatter
                config = {
                    type: 'frost',
                    colorOuter: 'rgba(56, 189, 248, ',
                    colorInner: 'rgba(186, 230, 253, ',
                    crest: '#ffffff',
                    speed: 6.0,
                    maxRadius: Math.min(window.innerWidth, window.innerHeight) * 0.32,
                    particleColor: '#e0f2fe',
                    particleCount: 8,
                    shape: 'crystal'
                };
                break;
            case 3: // Celestial Dunes: Golden Sand Mote Swirl
                config = {
                    type: 'sand',
                    colorOuter: 'rgba(234, 179, 8, ',
                    colorInner: 'rgba(250, 204, 21, ',
                    crest: '#fef08a',
                    speed: 4.8,
                    maxRadius: Math.min(window.innerWidth, window.innerHeight) * 0.30,
                    particleColor: '#facc15',
                    particleCount: 9,
                    shape: 'mote'
                };
                break;
            case 4: // Sky Citadel: Celestial Wind Gust
                config = {
                    type: 'wind',
                    colorOuter: 'rgba(224, 242, 254, ',
                    colorInner: 'rgba(254, 240, 138, ',
                    crest: '#ffffff',
                    speed: 6.8,
                    maxRadius: Math.min(window.innerWidth, window.innerHeight) * 0.36,
                    particleColor: '#fef9c3',
                    particleCount: 7,
                    shape: 'wind'
                };
                break;
            case 5: // Volcanic Obsidian Forge: Fiery Magma Blast & Molten Embers
                config = {
                    type: 'magma',
                    colorOuter: 'rgba(239, 68, 68, ',
                    colorInner: 'rgba(249, 115, 22, ',
                    crest: '#fef08a',
                    speed: 6.0,
                    maxRadius: Math.min(window.innerWidth, window.innerHeight) * 0.32,
                    particleColor: '#fb923c',
                    particleCount: 14,
                    shape: 'ember'
                };
                break;
            case 6: // Sunken Atlantis: Abyssal Deep Sea Water Pulse & Bubbles
                config = {
                    type: 'water',
                    colorOuter: 'rgba(6, 182, 212, ',
                    colorInner: 'rgba(56, 189, 248, ',
                    crest: '#e0f2fe',
                    speed: 4.2,
                    maxRadius: Math.min(window.innerWidth, window.innerHeight) * 0.38,
                    particleColor: '#38bdf8',
                    particleCount: 8,
                    shape: 'bubble'
                };
                break;
            case 7: // Cyber Megacity: Holographic Hexagonal Shield Pulse & Digital Sparks
                config = {
                    type: 'cyber',
                    colorOuter: 'rgba(6, 182, 212, ',
                    colorInner: 'rgba(217, 70, 239, ',
                    crest: '#67e8f9',
                    speed: 8.0,
                    maxRadius: Math.min(window.innerWidth, window.innerHeight) * 0.34,
                    particleColor: '#06b6d4',
                    particleCount: 10,
                    shape: 'hex'
                };
                break;
            case 8: // Autumn Dragon Valley: Crimson Maple Leaf Vortex
                config = {
                    type: 'autumn',
                    colorOuter: 'rgba(220, 38, 38, ',
                    colorInner: 'rgba(234, 88, 12, ',
                    crest: '#fed7aa',
                    speed: 5.0,
                    maxRadius: Math.min(window.innerWidth, window.innerHeight) * 0.32,
                    particleColor: '#ea580c',
                    particleCount: 10,
                    shape: 'leaf'
                };
                break;
            case 9: // Starfall Observatory: Cosmic Gravitational Nova
            default:
                config = {
                    type: 'cosmic',
                    colorOuter: 'rgba(168, 85, 247, ',
                    colorInner: 'rgba(192, 132, 252, ',
                    crest: '#fae8ff',
                    speed: 6.5,
                    maxRadius: Math.min(window.innerWidth, window.innerHeight) * 0.36,
                    particleColor: '#e879f9',
                    particleCount: 10,
                    shape: 'stardust'
                };
                break;
        }

        // Add main impact wave
        this.impacts.push({
            x: x,
            y: y,
            radius: 4,
            maxRadius: config.maxRadius,
            strength: 1.0,
            speed: config.speed,
            config: config
        });

        // Add elemental burst sparks
        for (let i = 0; i < config.particleCount; i++) {
            const angle = (Math.PI * 2 * i) / config.particleCount + (Math.random() - 0.5) * 0.5;
            const pSpeed = (config.speed * 0.5) + Math.random() * (config.speed * 0.7);
            this.sparks.push({
                x: x,
                y: y,
                vx: Math.cos(angle) * pSpeed,
                vy: Math.sin(angle) * pSpeed,
                life: 1.0,
                decay: 0.035 + Math.random() * 0.025,
                color: config.particleColor,
                size: 1.5 + Math.random() * 2.5,
                shape: config.shape
            });
        }
    }

    update() {
        // Update primary shockwaves
        for (let i = this.impacts.length - 1; i >= 0; i--) {
            const imp = this.impacts[i];
            imp.radius += imp.speed;
            imp.strength *= 0.955;
            if (imp.strength <= 0.015 || imp.radius >= imp.maxRadius) {
                this.impacts.splice(i, 1);
            }
        }

        // Update elemental burst sparks
        for (let i = this.sparks.length - 1; i >= 0; i--) {
            const p = this.sparks[i];
            p.x += p.vx;
            p.y += p.vy;
            p.vx *= 0.96;
            p.vy *= 0.96;
            p.life -= p.decay;
            if (p.life <= 0) {
                this.sparks.splice(i, 1);
            }
        }
    }

    render(ctx) {
        if (this.impacts.length === 0 && this.sparks.length === 0) return;
        ctx.save();

        // 1. Render Elemental Shockwaves
        for (const imp of this.impacts) {
            const c = imp.config;

            // Outer elemental aura
            const grad = ctx.createRadialGradient(imp.x, imp.y, Math.max(0, imp.radius - 14), imp.x, imp.y, imp.radius + 14);
            grad.addColorStop(0, `rgba(255, 255, 255, 0)`);
            grad.addColorStop(0.5, `${c.colorOuter}${imp.strength * 0.45})`);
            grad.addColorStop(1, `${c.colorInner}0)`);

            ctx.lineWidth = 14;
            ctx.strokeStyle = grad;

            if (c.shape === 'hex') {
                // Cyber: Hexagonal digital shield
                this.drawPolygon(ctx, imp.x, imp.y, imp.radius, 6);
                ctx.stroke();

                ctx.lineWidth = 1.8;
                ctx.strokeStyle = `rgba(103, 232, 249, ${imp.strength * 0.9})`;
                this.drawPolygon(ctx, imp.x, imp.y, imp.radius, 6);
                ctx.stroke();
            } else if (c.shape === 'crystal') {
                // Frost: Octagonal frost crystal
                this.drawPolygon(ctx, imp.x, imp.y, imp.radius, 8);
                ctx.stroke();

                ctx.lineWidth = 2.0;
                ctx.strokeStyle = `rgba(255, 255, 255, ${imp.strength * 0.85})`;
                this.drawPolygon(ctx, imp.x, imp.y, imp.radius, 8);
                ctx.stroke();
            } else {
                // Circular shockwave
                ctx.beginPath();
                ctx.arc(imp.x, imp.y, imp.radius, 0, Math.PI * 2);
                ctx.stroke();

                // Sharp crest line
                ctx.beginPath();
                ctx.arc(imp.x, imp.y, imp.radius, 0, Math.PI * 2);
                ctx.lineWidth = 2.0;
                ctx.strokeStyle = c.crest.startsWith('#') ?
                    `rgba(255, 255, 255, ${imp.strength * 0.85})` :
                    `${c.crest}${imp.strength * 0.85})`;
                ctx.stroke();
            }
        }

        // 2. Render Elemental Burst Sparks
        for (const p of this.sparks) {
            ctx.globalAlpha = p.life;
            ctx.fillStyle = p.color;

            if (p.shape === 'hex') {
                ctx.fillRect(p.x - p.size, p.y - p.size, p.size * 2, p.size * 2);
            } else {
                ctx.beginPath();
                ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
                ctx.fill();
            }
        }

        ctx.restore();
    }

    drawPolygon(ctx, cx, cy, radius, sides) {
        ctx.beginPath();
        for (let i = 0; i < sides; i++) {
            const angle = (i * 2 * Math.PI) / sides;
            const px = cx + radius * Math.cos(angle);
            const py = cy + radius * Math.sin(angle);
            if (i === 0) ctx.moveTo(px, py);
            else ctx.lineTo(px, py);
        }
        ctx.closePath();
    }
}

window.rippleFX = new RippleFX();
