use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::collections::HashMap;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LivelyInfo {
    #[serde(rename = "AppVersion", default)]
    pub app_version: Option<String>,
    #[serde(rename = "Title", default)]
    pub title: Option<String>,
    #[serde(rename = "Thumbnail", default)]
    pub thumbnail: Option<String>,
    #[serde(rename = "Preview", default)]
    pub preview: Option<String>,
    #[serde(rename = "Desc", default)]
    pub desc: Option<String>,
    #[serde(rename = "Author", default)]
    pub author: Option<String>,
    #[serde(rename = "License", default)]
    pub license: Option<String>,
    #[serde(rename = "Contact", default)]
    pub contact: Option<String>,
    #[serde(rename = "Type")]
    pub wallpaper_type: i32,
    #[serde(rename = "FileName")]
    pub file_name: String,
    #[serde(rename = "Arguments", default)]
    pub arguments: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WallpaperLayoutEntry {
    #[serde(rename = "LivelyScreen")]
    pub lively_screen: Value,
    #[serde(rename = "LivelyInfoPath")]
    pub lively_info_path: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WallpaperSummary {
    pub id: String,
    pub title: String,
    pub wallpaper_type: String,
    pub author: String,
    pub description: String,
    pub folder_path: String,
    pub is_active: bool,
}

pub type LivelyPropertiesMap = HashMap<String, Value>;
