use serde_json::json;
use crate::mcp::protocol::ToolDefinition;

pub fn get_tool_definitions() -> Vec<ToolDefinition> {
    vec![
        ToolDefinition {
            name: "wallpaper_status".into(),
            description: "Get current desktop wallpaper status, including active wallpaper title, type, resolution, volume, and Lively engine state.".into(),
            input_schema: json!({
                "type": "object",
                "properties": {}
            }),
        },
        ToolDefinition {
            name: "wallpaper_list".into(),
            description: "List all installed live and static wallpapers in the library with their titles, IDs, types, authors, and paths.".into(),
            input_schema: json!({
                "type": "object",
                "properties": {}
            }),
        },
        ToolDefinition {
            name: "wallpaper_switch".into(),
            description: "Switch the active desktop wallpaper immediately to another wallpaper by its title, ID, or file/folder path.".into(),
            input_schema: json!({
                "type": "object",
                "properties": {
                    "identifier": {
                        "type": "string",
                        "description": "Title, ID, or folder path of the wallpaper to activate (e.g. 'Citadel', 'Fluids', 'Rain', or folder name)."
                    }
                },
                "required": ["identifier"]
            }),
        },
        ToolDefinition {
            name: "wallpaper_set_property".into(),
            description: "Dynamically customize active wallpaper properties in real time (e.g. active video scene, click sound pack, volume, ripple effect, particle count, clock).".into(),
            input_schema: json!({
                "type": "object",
                "properties": {
                    "active_scene": {
                        "type": "integer",
                        "minimum": 0,
                        "maximum": 21,
                        "description": "Index of live animated 4K video scene (0: Citadel, 16: Front Mission 5 Relic, 18: FM5 Vanguard, 19: FM3 Zenith Remaster, 20: RX-93 Nu Gundam, 21: SRW OG Alteisen)."
                    },
                    "sound_pack": {
                        "type": "string",
                        "enum": ["Fantasy Rune Chime", "Mechanical Switch", "Water Droplet", "Cyber Pulse", "Muted"],
                        "description": "Audio profile triggered upon desktop mouse clicks."
                    },
                    "sound_volume": {
                        "type": "integer",
                        "minimum": 0,
                        "maximum": 100,
                        "description": "Volume percentage (0-100) for click sound effects."
                    },
                    "ripple_effect": {
                        "type": "boolean",
                        "description": "Enable or disable fluid concentric water ripples upon mouse clicks."
                    },
                    "firefly_count": {
                        "type": "integer",
                        "minimum": 0,
                        "maximum": 150,
                        "description": "Number of floating interactive firefly particles."
                    },
                    "show_clock": {
                        "type": "boolean",
                        "description": "Display or hide the sleek digital clock & date HUD."
                    },
                    "custom_properties": {
                        "type": "object",
                        "description": "Arbitrary key-value pairs to set in LivelyProperties.json."
                    }
                }
            }),
        },
        ToolDefinition {
            name: "wallpaper_deploy_interactive".into(),
            description: "Scaffold, compile, and deploy a brand new interactive HTML5/Canvas live wallpaper suite with click sound synthesis, fluid ripple physics, and reactive fireflies.".into(),
            input_schema: json!({
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Display title for the new interactive wallpaper."
                    },
                    "background_image": {
                        "type": "string",
                        "description": "Absolute path to background image (e.g. 4K Citadel, Forest Shrine, or Aurora Fortress)."
                    },
                    "default_sound_pack": {
                        "type": "string",
                        "enum": ["Fantasy Rune Chime", "Mechanical Switch", "Water Droplet", "Cyber Pulse"],
                        "description": "Default audio profile on click."
                    },
                    "default_volume": {
                        "type": "integer",
                        "minimum": 0,
                        "maximum": 100,
                        "description": "Default volume percentage (0-100)."
                    },
                    "firefly_count": {
                        "type": "integer",
                        "minimum": 0,
                        "maximum": 150,
                        "description": "Default number of reactive fireflies."
                    },
                    "show_clock": {
                        "type": "boolean",
                        "description": "Whether to display the minimalist clock HUD by default."
                    }
                }
            }),
        },
        ToolDefinition {
            name: "wallpaper_control".into(),
            description: "Control desktop wallpaper playback state (set global volume, mute, or unmute).".into(),
            input_schema: json!({
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["mute", "unmute", "set_volume"],
                        "description": "Action to perform."
                    },
                    "volume": {
                        "type": "integer",
                        "minimum": 0,
                        "maximum": 100,
                        "description": "Global audio volume percentage (0-100) when action is set_volume."
                    }
                },
                "required": ["action"]
            }),
        },
        ToolDefinition {
            name: "wallpaper_play_sound".into(),
            description: "Test/audition a click sound effect directly through the desktop system speakers.".into(),
            input_schema: json!({
                "type": "object",
                "properties": {
                    "sound_type": {
                        "type": "string",
                        "enum": ["mechanical", "rune_chime", "water_drop", "cyber_pulse"],
                        "description": "Sound profile to test."
                    }
                },
                "required": ["sound_type"]
            }),
        },
    ]
}
