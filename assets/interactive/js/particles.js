// Reactive Firefly Particle Engine
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
