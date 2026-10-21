# 🛡️ Aegis Wallpaper Engine (Rust + Native MCP)

[![Rust](https://img.shields.io/badge/rust-1.99%2B-orange.svg)](https://www.rust-lang.org)
[![Platform](https://img.shields.io/badge/platform-windows%2010%20%7C%2011-blue.svg)](https://microsoft.com/windows)
[![MCP](https://img.shields.io/badge/protocol-MCP%202024--11--05-brightgreen.svg)](https://modelcontextprotocol.io)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

A sovereign, high-performance Windows Live Wallpaper Engine and native **Model Context Protocol (MCP)** server written in Rust. 

Empowers AI coding assistants (**Google Antigravity**, **Claude Desktop**, **Cursor**, **Gemini**) to programmatically inspect, switch, customize, and deploy interactive 4K live desktop wallpapers with tactile click audio, 2D fluid ripple physics, and reactive particle companions.

---

## 🏛️ System Architecture

```
                    ┌───────────────────────────────────────────────┐
                    │  AI AGENT CONTROL PLANE (Antigravity / Claude) │
                    └───────────────────────┬───────────────────────┘
                                            │ JSON-RPC 2.0 (stdio)
                                            ▼
                    ┌───────────────────────────────────────────────┐
                    │        AEGIS WALLPAPER ENGINE (RUST)          │
                    │  ┌──────────────────┐  ┌────────────────────┐ │
                    │  │ MCP Tool Router  │  │ Scaffolding Engine │ │
                    │  └────────┬─────────┘  └─────────┬──────────┘ │
                    │           │                      │            │
                    │  ┌────────▼──────────────────────▼──────────┐ │
                    │  │          Lively Bridge & WorkerW         │ │
                    │  └──────────────────┬───────────────────────┘ │
                    └─────────────────────┼─────────────────────────┘
                                          │
                   ┌──────────────────────┴──────────────────────┐
                   │                                             │
                   ▼                                             ▼
┌──────────────────────────────────────┐     ┌──────────────────────────────────────┐
│       MODE A: LIVELY BRIDGE          │     │    MODE B: NATIVE WORKERW ENGINE     │
│ • Reads/writes active layout & props │     │ • Win32 Progman/WorkerW Hook         │
│ • Zero-downtime hot reloading        │     │ • Hardware DirectComposition         │
│ • Integrates with 4K MPV video       │     │ • <20MB RAM, zero bloat              │
└──────────────────┬───────────────────┘     └──────────────────┬───────────────────┘
                   │                                            │
                   └──────────────────────┬─────────────────────┘
                                          │
                                          ▼
                ┌──────────────────────────────────────────────────┐
                │             ACTIVE DESKTOP INTERFACE             │
                │  • 4K RPG Fantasy Canvas (Citadel, Forest, Snow) │
                │  • Acoustic Web Audio Synthesizer (Click Sound)  │
                │  • 2D Concentric Wave Equation Ripples           │
                │  • Reactive Wandering Firefly Particles          │
                └──────────────────────────────────────────────────┘
```

---

## ⚡ Key Features

- **Built-in MCP Server (`--mcp`)**: Seamlessly connects to AI agents over standard I/O with standard JSON-RPC 2.0 protocol.
- **Interactive Click Audio Synthesizer**: Zero-latency mathematical sound generation via Web Audio API with selectable acoustic profiles:
  - 🔮 **Fantasy Rune Chime**: Harmonic crystalline resonance (880Hz, 1320Hz, 1760Hz).
  - ⌨️ **Mechanical Switch**: Crisp mechanical tactile click (2400Hz bandpass snap + 140Hz body thud).
  - 💧 **Water Droplet Plop**: Frequency-swept organic aquatic droplet (650Hz -> 1400Hz).
  - ⚡ **Cyber Pulse**: Futuristic sawtooth UI pulse.
- **Interactive Fluid Ripple Physics**: Real-time concentric wave equation propagating outward on mouse clicks.
- **Reactive Particle Swarms**: 50+ luminous fireflies/wisps that wander organically, attract to cursor hover, and burst scatter on click.
- **Dual Engine Operation**:
  - **Lively Bridge Mode**: Gives instant agent superpowers to existing Lively Wallpaper installations.
  - **Native Engine Mode**: Single lightweight Rust binary (<20MB RAM) with Win32 `WorkerW` desktop pinning.

---

## 🛠️ MCP Tools Reference

When running as an MCP server, `aegis-wallpaper` exposes 7 high-level tools:

| Tool Name | Description | Parameters |
|---|---|---|
| `wallpaper_status` | Returns active wallpaper name, type, resolution, volume, and properties | *(none)* |
| `wallpaper_list` | Lists all installed wallpapers in library with IDs, titles, and paths | *(none)* |
| `wallpaper_switch` | Instantly switches active desktop wallpaper | `identifier`: string (title, ID, or path) |
| `wallpaper_set_property` | Dynamically updates sound pack, volume, ripple, fireflies, or clock | `sound_pack`, `sound_volume`, `ripple_effect`, `firefly_count`, `show_clock` |
| `wallpaper_deploy_interactive` | Scaffolds and registers a new interactive live wallpaper suite | `title`, `background_image`, `default_sound_pack`, `default_volume`, `firefly_count` |
| `wallpaper_control` | Adjusts global playback state | `action`: `"mute"` \| `"unmute"` \| `"set_volume"`, `volume`: 0-100 |
| `wallpaper_play_sound` | Auditions test click sound profile through system speakers | `sound_type`: `"mechanical"` \| `"rune_chime"` \| `"water_drop"` \| `"cyber_pulse"` |

---

## 🚀 CLI Usage

```powershell
# Query engine status & active wallpaper
aegis-wallpaper --status

# List all library wallpapers
aegis-wallpaper --list

# Switch active wallpaper
aegis-wallpaper --switch aegis_interactive
aegis-wallpaper --switch "01_citadel_twilight_live"

# Deploy new interactive suite with custom 4K background
aegis-wallpaper --deploy-interactive --background "C:\path\to\wallpaper.jpg"

# Set click sound pack
aegis-wallpaper --set-sound "Mechanical Switch"
aegis-wallpaper --set-sound "Fantasy Rune Chime"

# Adjust global wallpaper volume
aegis-wallpaper --volume 80

# Audition audio click profiles
aegis-wallpaper --test-sound mechanical
aegis-wallpaper --test-sound rune_chime

# Launch MCP server for AI agents
aegis-wallpaper --mcp
```

---

## 🔌 Agent MCP Registration

Add to `mcp_config.json` (Antigravity, Claude Desktop, Cursor):

```json
{
  "mcpServers": {
    "aegis-wallpaper": {
      "command": "E:\\GitHub\\aegis-wallpaper\\target\\release\\aegis-wallpaper.exe",
      "args": ["--mcp"]
    }
  }
}
```

---

## 🧪 Verification & Building

```powershell
# Run automated test suite
cargo test

# Build optimized release binary
cargo build --release
```

---

*Part of the Aegis Fleet Sovereign Ecosystem.*
