mod cli;
mod engine;
mod lively;
mod mcp;
mod scaffolder;

use anyhow::Result;
use clap::Parser;
use cli::{Cli, Commands};
use lively::LivelyBridge;
use mcp::McpServer;
use scaffolder::{scaffold_interactive_wallpaper, ScaffolderOptions};
use std::path::PathBuf;

#[tokio::main]
async fn main() -> Result<()> {
    // In MCP mode, keep stdout pure for JSON-RPC 2.0 messages
    let is_mcp = std::env::args().any(|a| a == "--mcp" || a == "mcp");
    if is_mcp {
        env_logger::Builder::from_env(env_logger::Env::default().default_filter_or("warn"))
            .target(env_logger::Target::Stderr)
            .init();
    } else {
        env_logger::Builder::from_env(env_logger::Env::default().default_filter_or("info")).init();
    }

    let cli = Cli::parse();
    let bridge = LivelyBridge::new()?;

    // 1. MCP Mode
    if cli.mcp || matches!(cli.command, Some(Commands::Mcp)) {
        let server = McpServer::new()?;
        server.run_stdio().await?;
        return Ok(());
    }

    // 2. Status
    if cli.status || matches!(cli.command, Some(Commands::Status)) {
        println!("🛡️ Aegis Wallpaper Engine Status");
        println!("================================");
        match bridge.get_active_wallpaper() {
            Ok(Some(active)) => {
                println!("Active Wallpaper : {}", active.title);
                println!("Wallpaper ID     : {}", active.id);
                println!("Type             : {}", active.wallpaper_type);
                println!("Folder           : {}", active.folder_path);
            }
            Ok(None) => println!("Active Wallpaper : None detected"),
            Err(e) => println!("Active Wallpaper : Error ({})", e),
        }
        let vol = bridge.get_global_volume().unwrap_or(75);
        println!("Global Volume    : {}%", vol);
        return Ok(());
    }

    // 3. List
    if cli.list || matches!(cli.command, Some(Commands::List)) {
        println!("📚 Installed Wallpapers in Library");
        println!("===================================");
        let list = bridge.list_wallpapers()?;
        for wp in list {
            let active_mark = if wp.is_active { " [ACTIVE]" } else { "" };
            println!("• {}{} ({})", wp.title, active_mark, wp.wallpaper_type);
            println!("  ID: {} | Path: {}", wp.id, wp.folder_path);
        }
        return Ok(());
    }

    // 4. Switch
    let switch_target = cli.switch.or_else(|| match &cli.command {
        Some(Commands::Switch { identifier }) => Some(identifier.clone()),
        _ => None,
    });
    if let Some(target) = switch_target {
        println!("🔄 Switching wallpaper to: {}", target);
        let switched = bridge.switch_wallpaper(&target)?;
        println!("✅ Successfully switched to: {}", switched.title);
        return Ok(());
    }

    // 4a. Live RPG Realm Switching
    if let Some(realm) = cli.realm {
        let actual = bridge.set_realm(realm)?;
        let realm_names = [
            "01 - Valerius Twilight Citadel",
            "02 - Eldertree Mystical Shrine",
            "03 - Frostpeak Aurora Fortress",
            "04 - Celestial Dunes Oasis",
            "05 - Floating Sky Citadel of Aetheria",
            "06 - Volcanic Obsidian Forge",
            "07 - Sunken Coral Atlantis",
            "08 - Cyber-Aegis Neo-Tokyo Bastion",
            "09 - Autumn Dragon Valley",
            "10 - Celestial Starfall Observatory",
            "11 - Ethereal Dreamscript Nexus",
            "12 - Celestial Titan Dunes",
            "13 - Octopath HD-2D Coastal Citadel",
            "14 - FFVII Rebirth Cosmo Canyon Mako",
            "15 - Studio Ghibli Sanctuary",
            "16 - The Sleeping Titan Gundam Relic",
            "17 - Front Mission 5: Wanzer Battle Relic",
            "18 - Final Fantasy Resonance Citadel",
            "19 - Front Mission 5: Strike Wanzer Vanguard",
            "20 - Front Mission 3: Zenith Remaster",
            "21 - Mobile Suit Gundam: RX-93 Nu Psycho-Frame",
            "22 - Super Robot Taisen: OG Alteisen Revolver Stake",
            "23 - Super Robot Taisen: Cybuster (Elemental Lord of the Wind)",
            "24 - Super Robot Taisen: Daizenghar (The Sword That Cleaves Evil)",
            "25 - Super Robot Taisen: Soulgain (Axel Almer's Ultimate Martial Arts)",
            "26 - Super Robot Taisen: Neo Granzon (Shu Shirakawa's Armored Deity of Destruction)",
            "27 - Super Robot Taisen: SRX (Super Robot X-Type Telekinetic Blade)",
            "28 - Super Robot Taisen: Zweizergandt (Shadow Mirror Emperor Vindel Mauser)",
        ];
        let name = realm_names.get((actual as usize).saturating_sub(1)).unwrap_or(&"Unknown Realm");
        println!("🌌 Switched Live Realm to [{}]: {}", actual, name);
        println!("💡 Tip: If desktop doesn't update instantly, click any desktop Hotbar button or run --restart");
        return Ok(());
    }

    if cli.next {
        let actual = bridge.next_realm()?;
        println!("🌌 Advanced to next Live Realm: [{}]", actual);
        return Ok(());
    }

    // 4b. Live Fullscreen Browser Preview
    if cli.preview {
        let html_path = "C:\\Users\\agung\\Pictures\\Wallpapers\\Interactive_Fantasy_Suite\\index.html";
        println!("🌐 Opening Sovereign 4K Live Wallpaper in browser preview...");
        let _ = std::process::Command::new("cmd")
            .args(["/c", "start", "", html_path])
            .spawn();
        println!("✨ Press F11 in browser for Fullscreen immersion!");
        println!("🎮 All keyboard shortcuts [1]-[9], [0], [N], [P], [L] work interactively!");
        return Ok(());
    }

    // 4c. Restart Lively Wallpaper
    if cli.restart {
        println!("🔄 Restarting Lively Wallpaper on Default desktop...");
        let _ = std::process::Command::new("powershell")
            .args(["-NoProfile", "-Command", "Get-Process -Name Lively* -ErrorAction SilentlyContinue | Stop-Process -Force"])
            .status();
        std::thread::sleep(std::time::Duration::from_millis(500));
        let _ = std::process::Command::new("powershell")
            .args(["-NoProfile", "-Command", "Start-Process 'shell:AppsFolder\\12030rocksdanister.LivelyWallpaper_97hta09mmv6hy!App'"])
            .spawn();
        println!("✅ Lively Wallpaper restarted.");
        return Ok(());
    }

    // 4b. Input Bridge
    if let Some(Commands::Bridge { sound }) = &cli.command {
        println!("🛡️ Starting Sovereign Desktop Input Bridge & Telemetry Server...");
        let workerw = engine::workerw::Win32DesktopHook::locate_or_spawn_workerw()?;
        let snd_path = sound.as_deref();
        println!("🎯 WorkerW HWND: {:?}", workerw);
        if let Some(snd) = snd_path {
            println!("🔊 Click Sound Profile: {}", snd);
        } else {
            println!("🔇 Click Sound Profile: Muted (Silent Mode)");
        }

        // Spawn loopback telemetry server on 127.0.0.1:48123 for live CPU, MEM, DISK stats
        if let Err(e) = engine::telemetry::TelemetryServer::spawn_loopback_service(48123) {
            eprintln!("⚠️ Telemetry server notice: {}", e);
        } else {
            println!("📊 Telemetry service active: http://127.0.0.1:48123/stats");
        }

        println!("⚡ Bridge active. Click on your desktop to trigger visual effects!");
        engine::bridge::DesktopInputBridge::run(workerw, snd_path)?;
        return Ok(());
    }

    // 5. Deploy Interactive
    if cli.deploy_interactive || matches!(cli.command, Some(Commands::Deploy { .. })) {
        println!("🚀 Scaffolding Aegis Interactive Live Wallpaper Suite...");
        let bg = cli.background.or_else(|| match &cli.command {
            Some(Commands::Deploy { background, .. }) => background.clone(),
            _ => None,
        });
        let sound = match &cli.command {
            Some(Commands::Deploy { sound, .. }) => sound.clone(),
            _ => "Fantasy Rune Chime".to_string(),
        };
        let vol = match &cli.command {
            Some(Commands::Deploy { volume, .. }) => *volume,
            _ => 60,
        };

        let opts = ScaffolderOptions {
            target_dir: PathBuf::from("C:\\Users\\agung\\Pictures\\Wallpapers\\Interactive_Fantasy_Suite"),
            title: "Sovereign Interactive Fantasy Suite".to_string(),
            background_image: bg,
            default_sound_pack: sound,
            default_volume: vol,
            firefly_count: 50,
            show_clock: false,
        };

        let out = scaffold_interactive_wallpaper(&opts)?;
        println!("✅ Deployed to: {}", out.display());
        println!("👉 You can now import this folder into Lively Wallpaper or switch to it via aegis-wallpaper!");
        return Ok(());
    }

    // 6. Set Sound Pack
    if let Some(sound) = cli.set_sound {
        println!("🔊 Setting click sound pack to: {}", sound);
        let idx = match sound.as_str() {
            "Fantasy Rune Chime" | "Rune Chime" => 0,
            "Mechanical Switch" | "Mechanical" => 1,
            "Water Droplet" | "Water" => 2,
            "Cyber Pulse" | "Pulse" => 3,
            "Muted" => 4,
            _ => 0,
        };
        bridge.set_property(None, "soundPack", serde_json::json!(idx))?;
        println!("✅ Click sound pack set to {} (index {})", sound, idx);
        return Ok(());
    }

    // 7. Set Volume
    if let Some(vol) = cli.volume {
        let actual = bridge.set_global_volume(vol)?;
        println!("✅ Global volume set to {}%", actual);
        return Ok(());
    }

    // 8. Test Sound
    if let Some(sound) = cli.test_sound {
        let (freq, dur) = match sound.as_str() {
            "mechanical" => (1800, 30),
            "rune_chime" => (880, 150),
            "water_drop" => (1200, 60),
            "cyber_pulse" => (500, 40),
            _ => (1000, 50),
        };
        unsafe {
            let _ = windows::Win32::System::Diagnostics::Debug::Beep(freq, dur);
        }
        println!("🔊 Auditioned '{}' ({} Hz, {} ms)", sound, freq, dur);
        return Ok(());
    }

    // Default: print status
    println!("🛡️ Aegis Wallpaper Engine (Rust + MCP) v{}", env!("CARGO_PKG_VERSION"));
    println!("Run with --help for command line options, or --mcp to start the agent protocol server.");
    let _ = bridge.get_active_wallpaper().map(|active| {
        if let Some(a) = active {
            println!("Current Desktop: {} ({})", a.title, a.wallpaper_type);
        }
    });

    Ok(())
}
