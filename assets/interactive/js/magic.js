// Arcane Magic Rune & Game Combat Visual Effects Engine
class MagicEngine {
    constructor() {
        this.runes = [];
        this.slashes = [];
        this.sparks = [];
        this.enabled = true;
    }

    add(x, y) {
        if (!this.enabled) return;

        // 1. Arcane Magic Circle Burst
        this.runes.push({
            x: x,
            y: y,
            radius: 10,
            maxRadius: 65,
            rotation: Math.random() * Math.PI * 2,
            rotSpeed: (Math.random() - 0.5) * 0.1,
            alpha: 1.0,
            color: this.getRandomMagicColor()
        });

        // 2. Crescent Blade Slash Arc
        const angle = Math.random() * Math.PI * 2;
        this.slashes.push({
            x: x,
            y: y,
            angle: angle,
            length: 80,
            progress: 0,
            alpha: 1.0,
            color: "#e0f2fe"
        });

        // 3. Radiant Mana Sparks
        const count = 10;
        for (let i = 0; i < count; i++) {
            const spd = 2 + Math.random() * 5;
            const theta = (Math.PI * 2 / count) * i + Math.random() * 0.4;
            this.sparks.push({
                x: x,
                y: y,
                vx: Math.cos(theta) * spd,
                vy: Math.sin(theta) * spd,
                size: 2 + Math.random() * 3,
                alpha: 1.0,
                color: Math.random() > 0.4 ? "#38bdf8" : "#fef08a"
            });
        }
    }

    getRandomMagicColor() {
        const colors = [
            "rgba(56, 189, 248, ",   // Cyan Mana
            "rgba(250, 204, 21, ",   // Golden Divine
            "rgba(192, 132, 252, ",  // Violet Arcane
            "rgba(45, 212, 191, "    // Emerald Spirit
        ];
        return colors[Math.floor(Math.random() * colors.length)];
    }

    update() {
        // Update Runes
        for (let i = this.runes.length - 1; i >= 0; i--) {
            const r = this.runes[i];
            r.radius += (r.maxRadius - r.radius) * 0.18;
            r.rotation += r.rotSpeed;
            r.alpha -= 0.035;
            if (r.alpha <= 0) this.runes.splice(i, 1);
        }

        // Update Slashes
        for (let i = this.slashes.length - 1; i >= 0; i--) {
            const s = this.slashes[i];
            s.progress += 0.12;
            s.alpha -= 0.06;
            if (s.alpha <= 0 || s.progress >= 1.0) this.slashes.splice(i, 1);
        }

        // Update Sparks
        for (let i = this.sparks.length - 1; i >= 0; i--) {
            const p = this.sparks[i];
            p.x += p.vx;
            p.y += p.vy;
            p.vx *= 0.94;
            p.vy *= 0.94;
            p.alpha -= 0.03;
            if (p.alpha <= 0) this.sparks.splice(i, 1);
        }
    }

    render(ctx) {
        if (!this.enabled) return;

        // Render Arcane Circles
        for (let r of this.runes) {
            ctx.save();
            ctx.translate(r.x, r.y);
            ctx.rotate(r.rotation);

            // Outer Magic Ring
            ctx.strokeStyle = r.color + r.alpha + ")";
            ctx.lineWidth = 2.5;
            ctx.shadowBlur = 15;
            ctx.shadowColor = r.color + "1)";
            ctx.beginPath();
            ctx.arc(0, 0, r.radius, 0, Math.PI * 2);
            ctx.stroke();

            // Inner Runic Inscription Ring
            ctx.beginPath();
            ctx.arc(0, 0, r.radius * 0.65, 0, Math.PI * 2);
            ctx.setLineDash([6, 6]);
            ctx.lineWidth = 1.5;
            ctx.stroke();

            // Runic Diamond Accents
            const points = 4;
            for (let p = 0; p < points; p++) {
                const a = (Math.PI * 2 / points) * p;
                const px = Math.cos(a) * r.radius;
                const py = Math.sin(a) * r.radius;
                ctx.fillStyle = "#ffffff";
                ctx.beginPath();
                ctx.arc(px, py, 2, 0, Math.PI * 2);
                ctx.fill();
            }

            ctx.restore();
        }

        // Render Crescent Slashes
        for (let s of this.slashes) {
            ctx.save();
            ctx.translate(s.x, s.y);
            ctx.rotate(s.angle);

            ctx.strokeStyle = `rgba(255, 255, 255, ${s.alpha})`;
            ctx.lineWidth = 3 * (1.0 - s.progress);
            ctx.shadowBlur = 20;
            ctx.shadowColor = "#38bdf8";

            ctx.beginPath();
            ctx.arc(0, 0, s.length * s.progress, -0.6, 0.6);
            ctx.stroke();

            ctx.restore();
        }

        // Render Mana Sparks
        for (let p of this.sparks) {
            ctx.save();
            ctx.fillStyle = p.color;
            ctx.globalAlpha = p.alpha;
            ctx.shadowBlur = 10;
            ctx.shadowColor = p.color;
            ctx.beginPath();
            ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
            ctx.fill();
            ctx.restore();
        }
    }
}

window.magicEngine = new MagicEngine();
