use anyhow::Result;
use serde::Serialize;
use std::sync::{Arc, Mutex};
use tokio::io::{AsyncReadExt, AsyncWriteExt};
use tokio::net::TcpListener;
use windows::core::PCWSTR;
use windows::Win32::Foundation::FILETIME;
use windows::Win32::Storage::FileSystem::GetDiskFreeSpaceExW;
use windows::Win32::System::SystemInformation::{GlobalMemoryStatusEx, MEMORYSTATUSEX};
use windows::Win32::System::Threading::GetSystemTimes;

#[repr(C)]
struct PdhFmtCountervalueUnion {
    double_value: f64,
}

#[repr(C)]
struct PdhFmtCountervalue {
    c_status: u32,
    data: PdhFmtCountervalueUnion,
}

const PDH_FMT_DOUBLE: u32 = 0x00000200;

#[link(name = "pdh")]
extern "system" {
    fn PdhOpenQueryW(szDataSource: *const u16, dwUserData: usize, phQuery: *mut isize) -> i32;
    fn PdhAddEnglishCounterW(
        hQuery: isize,
        szFullCounterPath: *const u16,
        dwUserData: usize,
        phCounter: *mut isize,
    ) -> i32;
    fn PdhCollectQueryData(hQuery: isize) -> i32;
    fn PdhGetFormattedCounterValue(
        hCounter: isize,
        dwFormat: u32,
        lpdwType: *mut u32,
        pValue: *mut PdhFmtCountervalue,
    ) -> i32;
    fn PdhCloseQuery(hQuery: isize) -> i32;
}

#[link(name = "user32")]
extern "system" {
    fn OpenClipboard(hWndNewOwner: *mut std::ffi::c_void) -> i32;
    fn CloseClipboard() -> i32;
    fn GetClipboardData(uFormat: u32) -> *mut std::ffi::c_void;
}

#[link(name = "kernel32")]
extern "system" {
    fn GlobalLock(hMem: *mut std::ffi::c_void) -> *mut std::ffi::c_void;
    fn GlobalUnlock(hMem: *mut std::ffi::c_void) -> i32;
}

pub fn get_system_clipboard_text() -> Option<String> {
    unsafe {
        if OpenClipboard(std::ptr::null_mut()) == 0 {
            return None;
        }

        const CF_UNICODETEXT: u32 = 13;
        let handle = GetClipboardData(CF_UNICODETEXT);
        if handle.is_null() {
            let _ = CloseClipboard();
            return None;
        }

        let ptr = GlobalLock(handle);
        if ptr.is_null() {
            let _ = CloseClipboard();
            return None;
        }

        let u16_ptr = ptr as *const u16;
        let mut len = 0;
        while *u16_ptr.add(len) != 0 && len < 16384 {
            len += 1;
        }

        let slice = std::slice::from_raw_parts(u16_ptr, len);
        let text = String::from_utf16_lossy(slice);

        let _ = GlobalUnlock(handle);
        let _ = CloseClipboard();

        Some(text)
    }
}

pub fn spawn_native_input_box(prompt_msg: &str, title: &str, default_val: &str) -> Option<String> {
    let script = format!(
        "[void][System.Reflection.Assembly]::LoadWithPartialName('Microsoft.VisualBasic'); [Microsoft.VisualBasic.Interaction]::InputBox('{}', '{}', '{}')",
        prompt_msg.replace('\'', "''"),
        title.replace('\'', "''"),
        default_val.replace('\'', "''")
    );
    let output = std::process::Command::new("powershell.exe")
        .args(&["-NoProfile", "-WindowStyle", "Hidden", "-Command", &script])
        .output()
        .ok()?;
    if output.status.success() {
        let text = String::from_utf8_lossy(&output.stdout).trim().to_string();
        if !text.is_empty() {
            return Some(text);
        }
    }
    None
}

#[derive(Serialize, Clone, Debug)]
pub struct SystemTelemetrySnapshot {
    pub cpu_percent: f32,
    pub mem_total_gb: f32,
    pub mem_used_gb: f32,
    pub mem_percent: u32,
    pub disk_read_mbs: f32,
    pub disk_write_mbs: f32,
    pub disk_io_percent: u32,
    pub disk_name: String,
    pub disk_total_gb: f32,
    pub disk_used_gb: f32,
    pub timestamp_ms: u64,
}

#[derive(Serialize, Clone, Debug)]
pub struct ResolvedTarget {
    pub status: String,
    pub target_type: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub video_id: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub playlist_id: Option<String>,
    pub title: String,
}

fn filetime_to_u64(ft: FILETIME) -> u64 {
    ((ft.dwHighDateTime as u64) << 32) | (ft.dwLowDateTime as u64)
}

struct HardwareSampler {
    last_idle: u64,
    last_kernel: u64,
    last_user: u64,
    pdh_query: isize,
    counter_read: isize,
    counter_write: isize,
    counter_time: isize,
    pdh_initialized: bool,
}

impl HardwareSampler {
    fn new() -> Self {
        let mut s = Self {
            last_idle: 0,
            last_kernel: 0,
            last_user: 0,
            pdh_query: 0,
            counter_read: 0,
            counter_write: 0,
            counter_time: 0,
            pdh_initialized: false,
        };
        s.init_pdh();
        s.sample_cpu();
        s
    }

    fn init_pdh(&mut self) {
        unsafe {
            let mut q: isize = 0;
            if PdhOpenQueryW(std::ptr::null(), 0, &mut q) != 0 {
                return;
            }
            self.pdh_query = q;

            let path_read: Vec<u16> = "\\PhysicalDisk(_Total)\\Disk Read Bytes/sec\0"
                .encode_utf16()
                .collect();
            let path_write: Vec<u16> = "\\PhysicalDisk(_Total)\\Disk Write Bytes/sec\0"
                .encode_utf16()
                .collect();
            let path_time: Vec<u16> = "\\PhysicalDisk(_Total)\\% Disk Time\0"
                .encode_utf16()
                .collect();

            let mut c_read: isize = 0;
            let mut c_write: isize = 0;
            let mut c_time: isize = 0;

            let r1 = PdhAddEnglishCounterW(q, path_read.as_ptr(), 0, &mut c_read);
            let r2 = PdhAddEnglishCounterW(q, path_write.as_ptr(), 0, &mut c_write);
            let r3 = PdhAddEnglishCounterW(q, path_time.as_ptr(), 0, &mut c_time);

            if r1 == 0 && r2 == 0 && r3 == 0 {
                self.counter_read = c_read;
                self.counter_write = c_write;
                self.counter_time = c_time;
                let _ = PdhCollectQueryData(q);
                self.pdh_initialized = true;
            }
        }
    }

    fn sample_cpu(&mut self) -> f32 {
        unsafe {
            let mut idle = FILETIME::default();
            let mut kernel = FILETIME::default();
            let mut user = FILETIME::default();

            if GetSystemTimes(Some(&mut idle), Some(&mut kernel), Some(&mut user)).is_ok() {
                let idle_u64 = filetime_to_u64(idle);
                let kernel_u64 = filetime_to_u64(kernel);
                let user_u64 = filetime_to_u64(user);

                let d_idle = idle_u64.saturating_sub(self.last_idle);
                let d_kernel = kernel_u64.saturating_sub(self.last_kernel);
                let d_user = user_u64.saturating_sub(self.last_user);

                self.last_idle = idle_u64;
                self.last_kernel = kernel_u64;
                self.last_user = user_u64;

                let sys = d_kernel + d_user;
                if sys > 0 && sys >= d_idle {
                    let busy = sys - d_idle;
                    return ((busy as f64 / sys as f64) * 100.0) as f32;
                }
            }
            0.0
        }
    }

    fn sample_memory() -> (f32, f32, u32) {
        unsafe {
            let mut state = MEMORYSTATUSEX::default();
            state.dwLength = std::mem::size_of::<MEMORYSTATUSEX>() as u32;
            if GlobalMemoryStatusEx(&mut state).is_ok() {
                let total_gb = state.ullTotalPhys as f32 / (1024.0 * 1024.0 * 1024.0);
                let avail_gb = state.ullAvailPhys as f32 / (1024.0 * 1024.0 * 1024.0);
                let used_gb = total_gb - avail_gb;
                (total_gb, used_gb, state.dwMemoryLoad)
            } else {
                (40.0, 20.0, 50)
            }
        }
    }

    fn sample_disk_storage(drive_letter: &str) -> (f32, f32) {
        unsafe {
            let path_str = format!("{}:\\", drive_letter);
            let mut utf16: Vec<u16> = path_str.encode_utf16().collect();
            utf16.push(0);

            let mut free_avail = 0u64;
            let mut total = 0u64;
            let mut total_free = 0u64;

            if GetDiskFreeSpaceExW(
                PCWSTR::from_raw(utf16.as_ptr()),
                Some(&mut free_avail),
                Some(&mut total),
                Some(&mut total_free),
            )
            .is_ok()
                && total > 0
            {
                let total_gb = total as f32 / (1024.0 * 1024.0 * 1024.0);
                let free_gb = total_free as f32 / (1024.0 * 1024.0 * 1024.0);
                let used_gb = total_gb - free_gb;
                (total_gb, used_gb)
            } else {
                (198.5, 191.8)
            }
        }
    }

    fn sample_disk_io(&mut self) -> (f32, f32, u32) {
        if !self.pdh_initialized || self.pdh_query == 0 {
            return (0.0, 0.0, 0);
        }

        unsafe {
            if PdhCollectQueryData(self.pdh_query) != 0 {
                return (0.0, 0.0, 0);
            }

            let mut t: u32 = 0;
            let mut val_read = PdhFmtCountervalue {
                c_status: 0,
                data: PdhFmtCountervalueUnion { double_value: 0.0 },
            };
            let mut val_write = PdhFmtCountervalue {
                c_status: 0,
                data: PdhFmtCountervalueUnion { double_value: 0.0 },
            };
            let mut val_time = PdhFmtCountervalue {
                c_status: 0,
                data: PdhFmtCountervalueUnion { double_value: 0.0 },
            };

            let _ = PdhGetFormattedCounterValue(
                self.counter_read,
                PDH_FMT_DOUBLE,
                &mut t,
                &mut val_read,
            );
            let _ = PdhGetFormattedCounterValue(
                self.counter_write,
                PDH_FMT_DOUBLE,
                &mut t,
                &mut val_write,
            );
            let _ = PdhGetFormattedCounterValue(
                self.counter_time,
                PDH_FMT_DOUBLE,
                &mut t,
                &mut val_time,
            );

            let read_mbs = (val_read.data.double_value / (1024.0 * 1024.0)).max(0.0) as f32;
            let write_mbs = (val_write.data.double_value / (1024.0 * 1024.0)).max(0.0) as f32;
            let io_pct = val_time.data.double_value.clamp(0.0, 100.0).round() as u32;

            (read_mbs, write_mbs, io_pct)
        }
    }

    pub fn snapshot(&mut self) -> SystemTelemetrySnapshot {
        let cpu = self.sample_cpu();
        let (mem_total, mem_used, mem_pct) = Self::sample_memory();
        let (disk_total, disk_used) = Self::sample_disk_storage("C");
        let (disk_read_mbs, disk_write_mbs, disk_io_pct) = self.sample_disk_io();

        let now = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap_or_default()
            .as_millis() as u64;

        SystemTelemetrySnapshot {
            cpu_percent: (cpu * 10.0).round() / 10.0,
            mem_total_gb: (mem_total * 10.0).round() / 10.0,
            mem_used_gb: (mem_used * 10.0).round() / 10.0,
            mem_percent: mem_pct,
            disk_read_mbs: (disk_read_mbs * 100.0).round() / 100.0,
            disk_write_mbs: (disk_write_mbs * 100.0).round() / 100.0,
            disk_io_percent: disk_io_pct,
            disk_name: "C: NVMe System".to_string(),
            disk_total_gb: (disk_total * 10.0).round() / 10.0,
            disk_used_gb: (disk_used * 10.0).round() / 10.0,
            timestamp_ms: now,
        }
    }
}

impl Drop for HardwareSampler {
    fn drop(&mut self) {
        if self.pdh_query != 0 {
            unsafe {
                let _ = PdhCloseQuery(self.pdh_query);
            }
        }
    }
}

fn url_decode(s: &str) -> String {
    let mut res = String::new();
    let bytes = s.as_bytes();
    let mut i = 0;
    while i < bytes.len() {
        if bytes[i] == b'%' && i + 2 < bytes.len() {
            if let Ok(byte_val) = u8::from_str_radix(std::str::from_utf8(&bytes[i + 1..i + 3]).unwrap_or(""), 16) {
                res.push(byte_val as char);
                i += 3;
                continue;
            }
        } else if bytes[i] == b'+' {
            res.push(' ');
            i += 1;
            continue;
        }
        res.push(bytes[i] as char);
        i += 1;
    }
    res
}

fn extract_video_id_from_html(html: &str) -> Option<String> {
    let needle = "\"videoId\":\"";
    if let Some(pos) = html.find(needle) {
        let after = &html[pos + needle.len()..];
        let vid: String = after.chars().take(11).collect();
        if vid.len() == 11 && vid.chars().all(|c| c.is_ascii_alphanumeric() || c == '_' || c == '-') {
            return Some(vid);
        }
    }
    None
}

fn extract_title_from_html(html: &str) -> Option<String> {
    if let Some(start) = html.find("<title>") {
        if let Some(end) = html[start..].find("</title>") {
            let t = &html[start + 7..start + end];
            let clean = t.trim().trim_end_matches(" - YouTube").trim();
            return Some(clean.to_string());
        }
    }
    None
}

fn resolve_target(raw: &str) -> ResolvedTarget {
    let mut target = raw.trim().to_string();
    if target.is_empty() || target == "clipboard" {
        if let Some(clip) = get_system_clipboard_text() {
            target = clip.trim().to_string();
        }
    }

    if target.is_empty() {
        return ResolvedTarget {
            status: "error".to_string(),
            target_type: "unknown".to_string(),
            video_id: None,
            playlist_id: None,
            title: "Empty Input".to_string(),
        };
    }

    // 1. Raw 11-char ID
    if target.len() == 11 && target.chars().all(|c| c.is_ascii_alphanumeric() || c == '_' || c == '-') {
        return ResolvedTarget {
            status: "ok".to_string(),
            target_type: "video".to_string(),
            video_id: Some(target),
            playlist_id: None,
            title: "YouTube Video".to_string(),
        };
    }

    // 2. Playlist URL
    if let Some(pos) = target.find("list=") {
        let after = &target[pos + 5..];
        let pl_id: String = after.chars().take_while(|c| c.is_ascii_alphanumeric() || *c == '_' || *c == '-').collect();
        if !pl_id.is_empty() {
            return ResolvedTarget {
                status: "ok".to_string(),
                target_type: "playlist".to_string(),
                video_id: None,
                playlist_id: Some(pl_id),
                title: "YouTube Playlist".to_string(),
            };
        }
    }

    // 3. Direct watch URL or shortlink
    if let Some(pos) = target.find("v=") {
        let after = &target[pos + 2..];
        let vid: String = after.chars().take_while(|c| c.is_ascii_alphanumeric() || *c == '_' || *c == '-').collect();
        if vid.len() == 11 {
            return ResolvedTarget {
                status: "ok".to_string(),
                target_type: "video".to_string(),
                video_id: Some(vid),
                playlist_id: None,
                title: "YouTube Video".to_string(),
            };
        }
    }
    if target.contains("youtu.be/") {
        if let Some(pos) = target.find("youtu.be/") {
            let after = &target[pos + 9..];
            let vid: String = after.chars().take_while(|c| c.is_ascii_alphanumeric() || *c == '_' || *c == '-').collect();
            if vid.len() == 11 {
                return ResolvedTarget {
                    status: "ok".to_string(),
                    target_type: "video".to_string(),
                    video_id: Some(vid),
                    playlist_id: None,
                    title: "YouTube Video".to_string(),
                };
            }
        }
    }

    // 4. Channel URL, @Handle, or Search query
    let mut fetch_url = target.clone();
    if !fetch_url.starts_with("http://") && !fetch_url.starts_with("https://") {
        if fetch_url.starts_with('@') {
            fetch_url = format!("https://www.youtube.com/{}", fetch_url);
        } else {
            let encoded_query = target.replace(' ', "+");
            fetch_url = format!("https://www.youtube.com/results?search_query={}", encoded_query);
        }
    }

    let live_candidate = if (fetch_url.contains("/@") || fetch_url.contains("/channel/") || fetch_url.contains("/c/"))
        && !fetch_url.ends_with("/live")
    {
        format!("{}/live", fetch_url.trim_end_matches('/'))
    } else {
        fetch_url.clone()
    };

    // Attempt 1: Fetch live stream endpoint
    if let Ok(output) = std::process::Command::new("curl.exe")
        .args(&["-s", "-L", &live_candidate, "-H", "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)"])
        .output()
    {
        if let Ok(html) = String::from_utf8(output.stdout) {
            if let Some(vid) = extract_video_id_from_html(&html) {
                let title = extract_title_from_html(&html).unwrap_or_else(|| "YouTube Stream".to_string());
                return ResolvedTarget {
                    status: "ok".to_string(),
                    target_type: "video".to_string(),
                    video_id: Some(vid),
                    playlist_id: None,
                    title,
                };
            }
        }
    }

    // Attempt 2: Fetch base channel URL
    if live_candidate != fetch_url {
        if let Ok(output) = std::process::Command::new("curl.exe")
            .args(&["-s", "-L", &fetch_url, "-H", "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)"])
            .output()
        {
            if let Ok(html) = String::from_utf8(output.stdout) {
                if let Some(vid) = extract_video_id_from_html(&html) {
                    let title = extract_title_from_html(&html).unwrap_or_else(|| "YouTube Stream".to_string());
                    return ResolvedTarget {
                        status: "ok".to_string(),
                        target_type: "video".to_string(),
                        video_id: Some(vid),
                        playlist_id: None,
                        title,
                    };
                }
            }
        }
    }

    ResolvedTarget {
        status: "error".to_string(),
        target_type: "unresolved".to_string(),
        video_id: None,
        playlist_id: None,
        title: "Could not resolve channel or video".to_string(),
    }
}

pub struct TelemetryServer;

impl TelemetryServer {
    pub fn spawn_loopback_service(port: u16) -> Result<()> {
        let sampler = Arc::new(Mutex::new(HardwareSampler::new()));

        tokio::spawn(async move {
            let addr = format!("127.0.0.1:{}", port);
            let listener = match TcpListener::bind(&addr).await {
                Ok(l) => {
                    log::info!("Telemetry HTTP service listening on http://{}", addr);
                    l
                }
                Err(e) => {
                    log::warn!("Could not bind telemetry server on {}: {}", addr, e);
                    return;
                }
            };

            loop {
                let (mut socket, _) = match listener.accept().await {
                    Ok(res) => res,
                    Err(_) => continue,
                };

                let sampler_clone = Arc::clone(&sampler);
                tokio::spawn(async move {
                    let mut buf = [0u8; 2048];
                    let n = socket.read(&mut buf).await.unwrap_or(0);
                    let req_str = String::from_utf8_lossy(&buf[..n]);

                    let (status_line, body) = if req_str.starts_with("GET /clipboard") {
                        let text = get_system_clipboard_text().unwrap_or_default();
                        let json = serde_json::json!({
                            "status": "ok",
                            "text": text
                        }).to_string();
                        ("HTTP/1.1 200 OK", json)
                    } else if req_str.starts_with("GET /prompt") {
                        let default_val = if let Some(d_pos) = req_str.find("?default=") {
                            let end_pos = req_str[d_pos + 9..].find(' ').unwrap_or(req_str.len() - d_pos - 9);
                            url_decode(&req_str[d_pos + 9..d_pos + 9 + end_pos])
                        } else {
                            get_system_clipboard_text().unwrap_or_default()
                        };
                        let text = tokio::task::spawn_blocking(move || {
                            spawn_native_input_box(
                                "Enter YouTube URL, Video ID, Playlist, or Search Keyword:",
                                "Aegis Live Wallpaper - YouTube Audio Lounge",
                                &default_val,
                            )
                        }).await.unwrap_or(None);

                        let json = serde_json::json!({
                            "status": if text.is_some() { "ok" } else { "cancelled" },
                            "text": text.unwrap_or_default()
                        }).to_string();
                        ("HTTP/1.1 200 OK", json)
                    } else if req_str.starts_with("GET /resolve") {
                        // Extract query parameter ?q= or ?url=
                        let target = if let Some(q_pos) = req_str.find("?q=") {
                            let end_pos = req_str[q_pos + 3..].find(' ').unwrap_or(req_str.len() - q_pos - 3);
                            url_decode(&req_str[q_pos + 3..q_pos + 3 + end_pos])
                        } else if let Some(u_pos) = req_str.find("?url=") {
                            let end_pos = req_str[u_pos + 5..].find(' ').unwrap_or(req_str.len() - u_pos - 5);
                            url_decode(&req_str[u_pos + 5..u_pos + 5 + end_pos])
                        } else {
                            String::new()
                        };

                        let resolved = resolve_target(&target);
                        let json = serde_json::to_string(&resolved).unwrap_or_default();
                        ("HTTP/1.1 200 OK", json)
                    } else {
                        // Default to /stats
                        let snapshot = {
                            let mut guard = sampler_clone.lock().unwrap();
                            guard.snapshot()
                        };
                        let json = serde_json::to_string(&snapshot).unwrap_or_default();
                        ("HTTP/1.1 200 OK", json)
                    };

                    let response = format!(
                        "{}\r\n\
                         Access-Control-Allow-Origin: *\r\n\
                         Content-Type: application/json\r\n\
                         Content-Length: {}\r\n\
                         Connection: close\r\n\r\n\
                         {}",
                        status_line,
                        body.len(),
                        body
                    );

                    let _ = socket.write_all(response.as_bytes()).await;
                    let _ = socket.flush().await;
                });
            }
        });

        Ok(())
    }
}
