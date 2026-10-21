use anyhow::Result;
use serde_json::{json, Value};
use std::path::PathBuf;
use tokio::io::{AsyncBufReadExt, AsyncWriteExt, BufReader};

use super::protocol::{
    ImplementationInfo, InitializeResult, JsonRpcError, JsonRpcRequest, JsonRpcResponse,
    ServerCapabilities, ToolCallResult, ToolsCapability,
};
use super::tools::get_tool_definitions;
use crate::lively::LivelyBridge;
use crate::scaffolder::{scaffold_interactive_wallpaper, ScaffolderOptions};

pub struct McpServer {
    bridge: LivelyBridge,
}

impl McpServer {
    pub fn new() -> Result<Self> {
        let bridge = LivelyBridge::new()?;
        Ok(Self { bridge })
    }

    pub async fn run_stdio(&self) -> Result<()> {
        let stdin = tokio::io::stdin();
        let mut stdout = tokio::io::stdout();
        let mut reader = BufReader::new(stdin).lines();

        while let Some(line) = reader.next_line().await? {
            let line = line.trim();
            if line.is_empty() {
                continue;
            }

            if let Ok(req) = serde_json::from_str::<JsonRpcRequest>(line) {
                let resp = self.handle_request(req).await;
                if let Some(resp) = resp {
                    let mut serialized = serde_json::to_string(&resp)?;
                    serialized.push('\n');
                    stdout.write_all(serialized.as_bytes()).await?;
                    stdout.flush().await?;
                }
            }
        }

        Ok(())
    }

    pub async fn handle_request(&self, req: JsonRpcRequest) -> Option<JsonRpcResponse> {
        let id = req.id.clone();

        match req.method.as_str() {
            "initialize" => {
                let init_result = InitializeResult {
                    protocol_version: "2024-11-05".into(),
                    capabilities: ServerCapabilities {
                        tools: ToolsCapability {
                            list_changed: false,
                        },
                    },
                    server_info: ImplementationInfo {
                        name: "aegis-wallpaper".into(),
                        version: env!("CARGO_PKG_VERSION").into(),
                    },
                };

                Some(JsonRpcResponse {
                    jsonrpc: "2.0".into(),
                    id,
                    result: Some(serde_json::to_value(init_result).unwrap()),
                    error: None,
                })
            }
            "notifications/initialized" => None,
            "tools/list" => {
                let tools = get_tool_definitions();
                Some(JsonRpcResponse {
                    jsonrpc: "2.0".into(),
                    id,
                    result: Some(json!({ "tools": tools })),
                    error: None,
                })
            }
            "tools/call" => {
                let params = req.params.unwrap_or(Value::Null);
                let tool_name = params.get("name").and_then(|v| v.as_str()).unwrap_or("");
                let args = params.get("arguments").cloned().unwrap_or(json!({}));

                let tool_result = self.execute_tool(tool_name, args).await;
                Some(JsonRpcResponse {
                    jsonrpc: "2.0".into(),
                    id,
                    result: Some(serde_json::to_value(tool_result).unwrap()),
                    error: None,
                })
            }
            _ => Some(JsonRpcResponse {
                jsonrpc: "2.0".into(),
                id,
                result: None,
                error: Some(JsonRpcError {
                    code: -32601,
                    message: format!("Method not found: {}", req.method),
                    data: None,
                }),
            }),
        }
    }

    pub async fn execute_tool(&self, name: &str, args: Value) -> ToolCallResult {
        match name {
            "wallpaper_status" => self.handle_wallpaper_status().await,
            "wallpaper_list" => self.handle_wallpaper_list().await,
            "wallpaper_switch" => self.handle_wallpaper_switch(args).await,
            "wallpaper_set_property" => self.handle_wallpaper_set_property(args).await,
            "wallpaper_deploy_interactive" => self.handle_wallpaper_deploy_interactive(args).await,
            "wallpaper_control" => self.handle_wallpaper_control(args).await,
            "wallpaper_play_sound" => self.handle_wallpaper_play_sound(args).await,
            _ => ToolCallResult::error(format!("Unknown tool: {}", name)),
        }
    }

    async fn handle_wallpaper_status(&self) -> ToolCallResult {
        let active = match self.bridge.get_active_wallpaper() {
            Ok(Some(w)) => w,
            Ok(None) => return ToolCallResult::success("No active wallpaper currently detected in Lively."),
            Err(e) => return ToolCallResult::error(format!("Failed to query active wallpaper: {}", e)),
        };

        let volume = self.bridge.get_global_volume().unwrap_or(75);
        let props = self.bridge.get_properties(None).unwrap_or_default();

        let report = json!({
            "status": "Active",
            "engine": "Lively Wallpaper Bridge",
            "active_wallpaper": {
                "id": active.id,
                "title": active.title,
                "type": active.wallpaper_type,
                "author": active.author,
                "folder": active.folder_path,
            },
            "volume": volume,
            "properties": props
        });

        ToolCallResult::success(serde_json::to_string_pretty(&report).unwrap_or_default())
    }

    async fn handle_wallpaper_list(&self) -> ToolCallResult {
        match self.bridge.list_wallpapers() {
            Ok(list) => {
                let serialized = serde_json::to_string_pretty(&list).unwrap_or_default();
                ToolCallResult::success(serialized)
            }
            Err(e) => ToolCallResult::error(format!("Failed to list wallpapers: {}", e)),
        }
    }

    async fn handle_wallpaper_switch(&self, args: Value) -> ToolCallResult {
        let identifier = match args.get("identifier").and_then(|v| v.as_str()) {
            Some(id) => id,
            None => return ToolCallResult::error("Missing required parameter 'identifier'"),
        };

        match self.bridge.switch_wallpaper(identifier) {
            Ok(switched) => {
                let msg = json!({
                    "success": true,
                    "message": format!("Successfully switched desktop wallpaper to: {}", switched.title),
                    "wallpaper": switched
                });
                ToolCallResult::success(serde_json::to_string_pretty(&msg).unwrap_or_default())
            }
            Err(e) => ToolCallResult::error(format!("Failed to switch wallpaper: {}", e)),
        }
    }

    async fn handle_wallpaper_set_property(&self, args: Value) -> ToolCallResult {
        let mut updated = Vec::new();

        // Sound pack: 0: Rune Chime, 1: Mechanical Switch, 2: Water Droplet, 3: Cyber Pulse, 4: Muted
        if let Some(sound_pack) = args.get("sound_pack").and_then(|v| v.as_str()) {
            let idx = match sound_pack {
                "Fantasy Rune Chime" => 0,
                "Mechanical Switch" => 1,
                "Water Droplet" => 2,
                "Cyber Pulse" => 3,
                "Muted" => 4,
                _ => 0,
            };
            if let Ok(_) = self.bridge.set_property(None, "soundPack", json!(idx)) {
                updated.push(format!("soundPack = {} ({})", sound_pack, idx));
            }
        }

        if let Some(vol) = args.get("sound_volume").and_then(|v| v.as_u64()) {
            if let Ok(_) = self.bridge.set_property(None, "soundVolume", json!(vol)) {
                updated.push(format!("soundVolume = {}%", vol));
            }
        }

        if let Some(ripple) = args.get("ripple_effect").and_then(|v| v.as_bool()) {
            if let Ok(_) = self.bridge.set_property(None, "rippleEffect", json!(ripple)) {
                updated.push(format!("rippleEffect = {}", ripple));
            }
        }

        if let Some(fireflies) = args.get("firefly_count").and_then(|v| v.as_u64()) {
            if let Ok(_) = self.bridge.set_property(None, "fireflyCount", json!(fireflies)) {
                updated.push(format!("fireflyCount = {}", fireflies));
            }
        }

        if let Some(clock) = args.get("show_clock").and_then(|v| v.as_bool()) {
            if let Ok(_) = self.bridge.set_property(None, "showClock", json!(clock)) {
                updated.push(format!("showClock = {}", clock));
            }
        }

        if let Some(custom) = args.get("custom_properties").and_then(|v| v.as_object()) {
            for (k, v) in custom {
                if let Ok(_) = self.bridge.set_property(None, k, v.clone()) {
                    updated.push(format!("{} = {}", k, v));
                }
            }
        }

        if updated.is_empty() {
            ToolCallResult::error("No valid properties provided to update.")
        } else {
            ToolCallResult::success(format!("Successfully updated live properties: {}", updated.join(", ")))
        }
    }

    async fn handle_wallpaper_deploy_interactive(&self, args: Value) -> ToolCallResult {
        let title = args
            .get("title")
            .and_then(|v| v.as_str())
            .unwrap_or("Sovereign Interactive Fantasy Suite")
            .to_string();

        let bg_image = args
            .get("background_image")
            .and_then(|v| v.as_str())
            .map(PathBuf::from);

        let sound_pack = args
            .get("default_sound_pack")
            .and_then(|v| v.as_str())
            .unwrap_or("Fantasy Rune Chime")
            .to_string();

        let volume = args
            .get("default_volume")
            .and_then(|v| v.as_u64())
            .unwrap_or(60) as u32;

        let fireflies = args
            .get("firefly_count")
            .and_then(|v| v.as_u64())
            .unwrap_or(50) as u32;

        let show_clock = args
            .get("show_clock")
            .and_then(|v| v.as_bool())
            .unwrap_or(false);

        let target_dir = PathBuf::from("C:\\Users\\agung\\Pictures\\Wallpapers\\Interactive_Fantasy_Suite");

        let opts = ScaffolderOptions {
            target_dir,
            title,
            background_image: bg_image,
            default_sound_pack: sound_pack,
            default_volume: volume,
            firefly_count: fireflies,
            show_clock,
        };

        match scaffold_interactive_wallpaper(&opts) {
            Ok(path) => {
                let msg = json!({
                    "success": true,
                    "deployed_path": path.to_string_lossy(),
                    "instructions": "Interactive live wallpaper deployed! You can import this folder directly into Lively Wallpaper or switch to it."
                });
                ToolCallResult::success(serde_json::to_string_pretty(&msg).unwrap_or_default())
            }
            Err(e) => ToolCallResult::error(format!("Failed to deploy interactive wallpaper: {}", e)),
        }
    }

    async fn handle_wallpaper_control(&self, args: Value) -> ToolCallResult {
        let action = match args.get("action").and_then(|v| v.as_str()) {
            Some(a) => a,
            None => return ToolCallResult::error("Missing required parameter 'action'"),
        };

        match action {
            "mute" => {
                let _ = self.bridge.set_global_volume(0);
                ToolCallResult::success("Global wallpaper volume muted.")
            }
            "unmute" => {
                let _ = self.bridge.set_global_volume(75);
                ToolCallResult::success("Global wallpaper volume unmuted (set to 75%).")
            }
            "set_volume" => {
                let vol = args.get("volume").and_then(|v| v.as_u64()).unwrap_or(75) as u32;
                let _ = self.bridge.set_global_volume(vol);
                ToolCallResult::success(format!("Global wallpaper volume set to {}%.", vol))
            }
            _ => ToolCallResult::error(format!("Unsupported action: {}", action)),
        }
    }

    async fn handle_wallpaper_play_sound(&self, args: Value) -> ToolCallResult {
        let sound_type = args.get("sound_type").and_then(|v| v.as_str()).unwrap_or("mechanical");
        
        // Execute a quick Windows beep / waveform
        let (freq, duration) = match sound_type {
            "mechanical" => (1800, 30),
            "rune_chime" => (880, 150),
            "water_drop" => (1200, 60),
            "cyber_pulse" => (500, 40),
            _ => (1000, 50),
        };

        unsafe {
            let _ = windows::Win32::System::Diagnostics::Debug::Beep(freq, duration);
        }

        ToolCallResult::success(format!("Played test sound profile '{}' ({} Hz, {} ms)", sound_type, freq, duration))
    }
}
