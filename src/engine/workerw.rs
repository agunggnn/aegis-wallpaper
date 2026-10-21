#![allow(dead_code)]

use anyhow::{anyhow, Result};
use std::sync::atomic::{AtomicUsize, Ordering};
use windows::core::PCWSTR;
use windows::Win32::Foundation::{BOOL, HWND, LPARAM};
use windows::Win32::UI::WindowsAndMessaging::{
    EnumWindows, FindWindowExW, FindWindowW, SendMessageTimeoutW,
    SMTO_NORMAL,
};

static WORKERW_HWND: AtomicUsize = AtomicUsize::new(0);

unsafe extern "system" fn enum_windows_callback(hwnd: HWND, _lparam: LPARAM) -> BOOL {
    let defview_name: Vec<u16> = "SHELLDLL_DefView\0".encode_utf16().collect();
    let defview = FindWindowExW(
        hwnd,
        HWND(std::ptr::null_mut()),
        PCWSTR::from_raw(defview_name.as_ptr()),
        PCWSTR::null(),
    );

    if defview.is_ok() && !defview.unwrap().0.is_null() {
        let workerw_name: Vec<u16> = "WorkerW\0".encode_utf16().collect();
        let next_worker = FindWindowExW(
            HWND(std::ptr::null_mut()),
            hwnd,
            PCWSTR::from_raw(workerw_name.as_ptr()),
            PCWSTR::null(),
        );

        if let Ok(w) = next_worker {
            if !w.0.is_null() {
                WORKERW_HWND.store(w.0 as usize, Ordering::SeqCst);
                return BOOL(0); // Stop enumeration
            }
        }
    }

    BOOL(1) // Continue
}

pub struct Win32DesktopHook;

impl Win32DesktopHook {
    pub fn locate_or_spawn_workerw() -> Result<HWND> {
        // Run in dedicated thread to ensure SetThreadDesktop succeeds without ERROR_BUSY
        let raw_handle = std::thread::spawn(|| -> Result<usize> {
            unsafe {
                let default_name: Vec<u16> = "Default\0".encode_utf16().collect();
                if let Ok(hdesk) = windows::Win32::System::StationsAndDesktops::OpenDesktopW(
                    PCWSTR::from_raw(default_name.as_ptr()),
                    windows::Win32::System::StationsAndDesktops::DESKTOP_CONTROL_FLAGS(0),
                    false,
                    0x01FF,
                ) {
                    let _ = windows::Win32::System::StationsAndDesktops::SetThreadDesktop(hdesk);
                }

                let progman_name: Vec<u16> = "Progman\0".encode_utf16().collect();
                let progman = FindWindowW(PCWSTR::from_raw(progman_name.as_ptr()), PCWSTR::null())
                    .map_err(|e| anyhow!("Could not find Progman window: {:?}", e))?;

                if progman.0.is_null() {
                    return Err(anyhow!("Progman window handle is null"));
                }

                // Send 0x052C to Progman to spawn the WorkerW behind desktop icons
                let mut result: usize = 0;
                let _ = SendMessageTimeoutW(
                    progman,
                    0x052C,
                    windows::Win32::Foundation::WPARAM(0x0000000D),
                    LPARAM(0),
                    SMTO_NORMAL,
                    1000,
                    Some(&mut result as *mut usize),
                );

                // Enumerate windows to locate the spawned WorkerW
                WORKERW_HWND.store(0, Ordering::SeqCst);
                let _ = EnumWindows(Some(enum_windows_callback), LPARAM(0));

                let handle = WORKERW_HWND.load(Ordering::SeqCst);
                if handle != 0 {
                    Ok(handle)
                } else {
                    // Fallback to progman
                    Ok(progman.0 as usize)
                }
            }
        })
        .join()
        .map_err(|_| anyhow!("Thread panicked while locating WorkerW"))??;

        Ok(HWND(raw_handle as *mut std::ffi::c_void))
    }
}
