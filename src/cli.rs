use clap::{Parser, Subcommand};
use std::path::PathBuf;

#[derive(Parser, Debug)]
#[command(
    name = "aegis-wallpaper",
    author = "Aegis Fleet <agung@aegis.dev>",
    version = env!("CARGO_PKG_VERSION"),
    about = "Sovereign Windows Live Wallpaper Engine and Native MCP Server"
)]
pub struct Cli {
    /// Launch in Model Context Protocol (MCP) server mode over stdio for AI agents
    #[arg(long)]
    pub mcp: bool,

    /// Show current wallpaper engine status and active wallpaper
    #[arg(long)]
    pub status: bool,

    /// List all installed wallpapers in library
    #[arg(short, long)]
    pub list: bool,

    /// Switch active wallpaper by ID, title, or folder name
    #[arg(short = 's', long)]
    pub switch: Option<String>,

    /// Switch live RPG realm (1 to 25)
    #[arg(long)]
    pub realm: Option<u32>,

    /// Skip to next live RPG realm
    #[arg(long)]
    pub next: bool,

    /// Open live interactive 4K wallpaper preview in browser (supports all keyboard hotkeys & F11 fullscreen)
    #[arg(long)]
    pub preview: bool,

    /// Restart Lively Wallpaper engine on active desktop
    #[arg(long)]
    pub restart: bool,

    /// Deploy a new interactive HTML5 live wallpaper suite
    #[arg(long)]
    pub deploy_interactive: bool,

    /// Background image path to use for interactive wallpaper deployment
    #[arg(long)]
    pub background: Option<PathBuf>,

    /// Set click sound pack: 'Rune Chime', 'Mechanical', 'Water Droplet', 'Cyber Pulse', 'Muted'
    #[arg(long)]
    pub set_sound: Option<String>,

    /// Set global wallpaper audio volume (0-100)
    #[arg(long)]
    pub volume: Option<u32>,

    /// Test-play an audio click profile ('mechanical', 'rune_chime', 'water_drop', 'cyber_pulse')
    #[arg(long)]
    pub test_sound: Option<String>,

    #[command(subcommand)]
    pub command: Option<Commands>,
}

#[derive(Subcommand, Debug)]
pub enum Commands {
    /// Start the Model Context Protocol (MCP) server over stdio
    Mcp,
    /// Query current status
    Status,
    /// List all library wallpapers
    List,
    /// Switch active wallpaper
    Switch { identifier: String },
    /// Run real-time desktop click input bridge & tactile audio synthesizer
    Bridge {
        /// Optional path to WAV sound file to play on click
        #[arg(long)]
        sound: Option<String>,
    },
    /// Deploy interactive wallpaper suite
    Deploy {
        #[arg(long)]
        background: Option<PathBuf>,
        #[arg(long, default_value = "Fantasy Rune Chime")]
        sound: String,
        #[arg(long, default_value_t = 60)]
        volume: u32,
    },
}
