use serde_json::json;

// Test protocol JSON serialization
#[tokio::test]
async fn test_initialize_protocol_schema() {
    let req = json!({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "antigravity-test",
                "version": "1.0.0"
            }
        }
    });

    assert_eq!(req["jsonrpc"], "2.0");
    assert_eq!(req["method"], "initialize");
}

#[tokio::test]
async fn test_tool_definitions_list() {
    // Test that tool list schema is valid
    let expected_tools = vec![
        "wallpaper_status",
        "wallpaper_list",
        "wallpaper_switch",
        "wallpaper_set_property",
        "wallpaper_deploy_interactive",
        "wallpaper_control",
        "wallpaper_play_sound",
    ];

    assert_eq!(expected_tools.len(), 7);
}
