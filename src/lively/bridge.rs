use anyhow::{anyhow, Context, Result};
use serde_json::Value;
use std::fs;
use std::path::{Path, PathBuf};
use walkdir::WalkDir;

use super::models::{LivelyInfo, LivelyPropertiesMap, WallpaperLayoutEntry, WallpaperSummary};

pub struct LivelyBridge {
    pub base_dir: PathBuf,
}

impl LivelyBridge {
    pub fn new() -> Result<Self> {
        let local_appdata = std::env::var("LOCALAPPDATA")
            .unwrap_or_else(|_| "C:\\Users\\agung\\AppData\\Local".to_string());
        
        let standard_dir = PathBuf::from(&local_appdata).join("Lively Wallpaper");
        let store_dir = PathBuf::from(&local_appdata)
            .join("Packages\\12030rocksdanister.LivelyWallpaper_97hta09mmv6hy\\LocalCache\\Local\\Lively Wallpaper");

        let base_dir = if standard_dir.exists() {
            standard_dir
        } else if store_dir.exists() {
            store_dir
        } else {
            standard_dir
        };

        Ok(Self { base_dir })
    }

    pub fn get_layout_file(&self) -> PathBuf {
        self.base_dir.join("WallpaperLayout.json")
    }

    pub fn get_settings_file(&self) -> PathBuf {
        self.base_dir.join("Settings.json")
    }

    #[allow(dead_code)]
    pub fn get_library_dir(&self) -> PathBuf {
        self.base_dir.join("Library")
    }

    pub fn get_active_info_path(&self) -> Result<Option<PathBuf>> {
        let layout_file = self.get_layout_file();
        if !layout_file.exists() {
            return Ok(None);
        }

        let content = fs::read_to_string(&layout_file)
            .context("Failed to read WallpaperLayout.json")?;
        let entries: Vec<WallpaperLayoutEntry> = serde_json::from_str(&content)
            .context("Failed to parse WallpaperLayout.json")?;

        if let Some(first) = entries.first() {
            Ok(Some(PathBuf::from(&first.lively_info_path)))
        } else {
            Ok(None)
        }
    }

    pub fn get_active_wallpaper(&self) -> Result<Option<WallpaperSummary>> {
        let active_path = match self.get_active_info_path()? {
            Some(p) => p,
            None => return Ok(None),
        };

        let info_file = active_path.join("LivelyInfo.json");
        if !info_file.exists() {
            return Ok(None);
        }

        let content = fs::read_to_string(&info_file)
            .context("Failed to read active LivelyInfo.json")?;
        let info: LivelyInfo = serde_json::from_str(&content)?;

        let id = active_path
            .file_name()
            .map(|s| s.to_string_lossy().to_string())
            .unwrap_or_else(|| "active".to_string());

        let wp_type = match info.wallpaper_type {
            0 => "Video (Native)",
            1 => "Web / HTML5 (Interactive)",
            2 => "GIF / Animated Image",
            3 => "Unity / Engine",
            7 => "Video (MPV Hardware Accelerated)",
            _ => "Custom Live Wallpaper",
        };

        Ok(Some(WallpaperSummary {
            id,
            title: info.title.unwrap_or_else(|| info.file_name.clone()),
            wallpaper_type: wp_type.to_string(),
            author: info.author.unwrap_or_else(|| "User".to_string()),
            description: info.desc.unwrap_or_default(),
            folder_path: active_path.to_string_lossy().to_string(),
            is_active: true,
        }))
    }

    pub fn list_wallpapers(&self) -> Result<Vec<WallpaperSummary>> {
        let active_path = self.get_active_info_path()?.unwrap_or_default();
        let active_norm = active_path.canonicalize().unwrap_or(active_path.clone());

        let mut list = Vec::new();
        let search_roots = vec![
            self.base_dir.join("Library\\wallpapers"),
            self.base_dir.join("Library\\SaveData\\wptmp"),
        ];

        for root in search_roots {
            if !root.exists() {
                continue;
            }

            for entry in WalkDir::new(&root).max_depth(4).into_iter().filter_map(|e| e.ok()) {
                if entry.file_name() == "LivelyInfo.json" {
                    let folder = entry.path().parent().unwrap_or_else(|| Path::new(""));
                    if let Ok(content) = fs::read_to_string(entry.path()) {
                        if let Ok(info) = serde_json::from_str::<LivelyInfo>(&content) {
                            let folder_norm = folder.canonicalize().unwrap_or_else(|_| folder.to_path_buf());
                            let is_active = folder_norm == active_norm;

                            let id = folder
                                .file_name()
                                .map(|s| s.to_string_lossy().to_string())
                                .unwrap_or_else(|| "item".to_string());

                            let wp_type = match info.wallpaper_type {
                                0 => "Video (Native)",
                                1 => "Web / HTML5 (Interactive)",
                                2 => "GIF / Animated Image",
                                3 => "Unity / Engine",
                                7 => "Video (MPV Hardware Accelerated)",
                                _ => "Custom Live Wallpaper",
                            };

                            list.push(WallpaperSummary {
                                id,
                                title: info.title.unwrap_or_else(|| info.file_name.clone()),
                                wallpaper_type: wp_type.to_string(),
                                author: info.author.unwrap_or_else(|| "User".to_string()),
                                description: info.desc.unwrap_or_default(),
                                folder_path: folder.to_string_lossy().to_string(),
                                is_active,
                            });
                        }
                    }
                }
            }
        }

        Ok(list)
    }

    pub fn find_wallpaper_folder(&self, identifier: &str) -> Result<PathBuf> {
        let direct_path = PathBuf::from(identifier);
        if direct_path.exists() && direct_path.join("LivelyInfo.json").exists() {
            return Ok(direct_path);
        }

        let all = self.list_wallpapers()?;
        for wp in all {
            if wp.id.eq_ignore_ascii_case(identifier)
                || wp.title.eq_ignore_ascii_case(identifier)
                || wp.folder_path.ends_with(identifier)
            {
                return Ok(PathBuf::from(wp.folder_path));
            }
        }

        Err(anyhow!("Wallpaper not found matching identifier: {}", identifier))
    }

    pub fn switch_wallpaper(&self, identifier: &str) -> Result<WallpaperSummary> {
        let folder = self.find_wallpaper_folder(identifier)?;
        let layout_file = self.get_layout_file();

        let mut entries: Vec<WallpaperLayoutEntry> = if layout_file.exists() {
            let content = fs::read_to_string(&layout_file)?;
            serde_json::from_str(&content).unwrap_or_default()
        } else {
            Vec::new()
        };

        let target_path_str = folder.to_string_lossy().to_string();

        if entries.is_empty() {
            let default_screen = serde_json::json!({
                "Bounds": "0, 0, 2560, 1440",
                "DeviceName": "\\\\.\\DISPLAY1",
                "DisplayName": "Primary Display",
                "Index": 1,
                "IsPrimary": true,
                "WorkingArea": "0, 0, 2560, 1400"
            });
            entries.push(WallpaperLayoutEntry {
                lively_screen: default_screen,
                lively_info_path: target_path_str,
            });
        } else {
            for entry in entries.iter_mut() {
                entry.lively_info_path = target_path_str.clone();
            }
        }

        let new_content = serde_json::to_string_pretty(&entries)?;
        fs::write(&layout_file, new_content)?;

        // Read and return the switched wallpaper summary
        let info_file = folder.join("LivelyInfo.json");
        let content = fs::read_to_string(info_file)?;
        let info: LivelyInfo = serde_json::from_str(&content)?;

        Ok(WallpaperSummary {
            id: folder.file_name().map(|s| s.to_string_lossy().to_string()).unwrap_or_default(),
            title: info.title.unwrap_or_else(|| info.file_name.clone()),
            wallpaper_type: if info.wallpaper_type == 1 { "Web / HTML5".into() } else { "Video / Native".into() },
            author: info.author.unwrap_or_else(|| "User".to_string()),
            description: info.desc.unwrap_or_default(),
            folder_path: folder.to_string_lossy().to_string(),
            is_active: true,
        })
    }

    pub fn get_properties(&self, identifier: Option<&str>) -> Result<LivelyPropertiesMap> {
        let folder = match identifier {
            Some(id) => self.find_wallpaper_folder(id)?,
            None => match self.get_active_info_path()? {
                Some(p) => p,
                None => return Err(anyhow!("No active wallpaper found")),
            },
        };

        let prop_file = folder.join("LivelyProperties.json");
        if !prop_file.exists() {
            return Ok(LivelyPropertiesMap::new());
        }

        let content = fs::read_to_string(prop_file)?;
        let props: LivelyPropertiesMap = serde_json::from_str(&content)?;
        Ok(props)
    }

    pub fn set_property(&self, identifier: Option<&str>, key: &str, val: Value) -> Result<Value> {
        let folder = match identifier {
            Some(id) => self.find_wallpaper_folder(id)?,
            None => match self.get_active_info_path()? {
                Some(p) => p,
                None => return Err(anyhow!("No active wallpaper found")),
            },
        };

        let prop_file = folder.join("LivelyProperties.json");
        let mut props: LivelyPropertiesMap = if prop_file.exists() {
            let content = fs::read_to_string(&prop_file)?;
            serde_json::from_str(&content).unwrap_or_default()
        } else {
            LivelyPropertiesMap::new()
        };

        // If key exists as an object with "value", update the "value" field; else set directly
        if let Some(entry) = props.get_mut(key) {
            if let Some(obj) = entry.as_object_mut() {
                if obj.contains_key("value") {
                    obj.insert("value".into(), val.clone());
                } else {
                    *entry = val.clone();
                }
            } else {
                *entry = val.clone();
            }
        } else {
            props.insert(key.into(), serde_json::json!({ "value": val }));
        }

        let formatted = serde_json::to_string_pretty(&props)?;
        fs::write(&prop_file, &formatted)?;

        if let Some(folder_name) = folder.file_name() {
            let wpdata_file = self.base_dir
                .join("Library")
                .join("SaveData")
                .join("wpdata")
                .join(folder_name)
                .join("1")
                .join("LivelyProperties.json");
            if wpdata_file.exists() {
                let _ = fs::write(&wpdata_file, &formatted);
            }
        }

        Ok(val)
    }

    pub fn set_realm(&self, realm_num: u32) -> Result<u32> {
        let idx = (realm_num.saturating_sub(1)).min(21);
        self.set_property(None, "activeScene", serde_json::json!(idx))?;
        Ok(idx + 1)
    }

    pub fn next_realm(&self) -> Result<u32> {
        let props = self.get_properties(None)?;
        let cur = props.get("activeScene")
            .and_then(|v| v.get("value"))
            .and_then(|v| v.as_u64())
            .unwrap_or(0);
        let next = (cur + 1) % 22;
        self.set_property(None, "activeScene", serde_json::json!(next))?;
        Ok((next as u32) + 1)
    }

    pub fn get_global_volume(&self) -> Result<u32> {
        let settings_file = self.get_settings_file();
        if !settings_file.exists() {
            return Ok(75);
        }

        let content = fs::read_to_string(settings_file)?;
        let val: Value = serde_json::from_str(&content)?;
        let vol = val.get("AudioVolumeGlobal").and_then(|v| v.as_u64()).unwrap_or(75);
        Ok(vol as u32)
    }

    pub fn set_global_volume(&self, volume: u32) -> Result<u32> {
        let bounded = volume.min(100);
        let settings_file = self.get_settings_file();
        if settings_file.exists() {
            let content = fs::read_to_string(&settings_file)?;
            let mut val: Value = serde_json::from_str(&content)?;
            if let Some(obj) = val.as_object_mut() {
                obj.insert("AudioVolumeGlobal".into(), serde_json::json!(bounded));
                let formatted = serde_json::to_string_pretty(&obj)?;
                fs::write(&settings_file, formatted)?;
            }
        }
        Ok(bounded)
    }
}
