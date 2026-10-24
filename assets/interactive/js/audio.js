// Tactile Sound Player (Muted by default per user preference)
class SoundEngine {
    constructor() {
        this.soundPack = 4; // 4: Muted by default
        this.volume = 0.0;
        this.audioElements = {
            0: new Audio('audio/rune_chime.wav'),
            1: new Audio('audio/mechanical.wav'),
            2: new Audio('audio/water_drop.wav'),
            3: new Audio('audio/cyber_pulse.wav')
        };

        for (let key in this.audioElements) {
            this.audioElements[key].preload = 'none';
            this.audioElements[key].volume = 0.0;
        }
    }

    setPack(val) {
        this.soundPack = parseInt(val) || 4;
    }

    setVolume(val) {
        this.volume = Math.max(0, Math.min(1, val / 100));
        for (let key in this.audioElements) {
            this.audioElements[key].volume = this.volume;
        }
    }

    playClick() {
        // Strict guard: If sound is muted or volume is zero, exit immediately
        if (this.soundPack === 4 || this.volume <= 0.001) return;
        const snd = this.audioElements[this.soundPack];
        if (snd) {
            try {
                snd.currentTime = 0;
                snd.volume = this.volume;
                snd.play().catch(() => {});
            } catch (err) {}
        }
    }
}
window.soundEngine = new SoundEngine();
