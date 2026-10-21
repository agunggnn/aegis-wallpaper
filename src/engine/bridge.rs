use anyhow::{anyhow, Result};
use std::sync::atomic::{AtomicIsize, Ordering};
use windows::core::PCWSTR;
use windows::Win32::Foundation::{HWND, LPARAM, LRESULT, WPARAM};
use windows::Win32::Media::Audio::{PlaySoundW, SND_ASYNC, SND_FILENAME};
use windows::Win32::UI::WindowsAndMessaging::{
    CallNextHookEx, DispatchMessageW, GetClassNameW, GetMessageW, GetWindow,
    PostMessageW, SetWindowsHookExW, TranslateMessage, UnhookWindowsHookEx,
    WindowFromPoint, HHOOK, MSLLHOOKSTRUCT, WH_MOUSE_LL, WM_LBUTTONDOWN,
    WM_LBUTTONUP, WM_MOUSEMOVE,
};

static RENDER_HWND: AtomicIsize = AtomicIsize::new(0);
static SOUND_FILE_UTF16: std::sync::Mutex<Option<Vec<u16>>> = std::sync::Mutex::new(None);
static HOOK_HANDLE: AtomicIsize = AtomicIsize::new(0);

unsafe fn find_recursive(parent: HWND) -> HWND {
    let mut child = match GetWindow(parent, windows::Win32::UI::WindowsAndMessaging::GW_CHILD) {
        Ok(h) => h,
        Err(_) => return HWND(std::ptr::null_mut()),
    };

    while !child.0.is_null() {
        let mut class_buf = [0u16; 256];
        let len = GetClassNameW(child, &mut class_buf);
        if len > 0 {
            let class_name = String::from_utf16_lossy(&class_buf[..len as usize]);
            if class_name == "Chrome_RenderWidgetHostHWND" {
                return child;
            }
        }

        let sub = find_recursive(child);
        if !sub.0.is_null() {
            return sub;
        }

        child = match GetWindow(child, windows::Win32::UI::WindowsAndMessaging::GW_HWNDNEXT) {
            Ok(h) => h,
            Err(_) => break,
        };
    }

    HWND(std::ptr::null_mut())
}

pub fn locate_render_hwnd(workerw: HWND) -> Result<HWND> {
    unsafe {
        let hwnd = find_recursive(workerw);
        if hwnd.0.is_null() {
            Err(anyhow!("Chrome_RenderWidgetHostHWND not found under WorkerW"))
        } else {
            Ok(hwnd)
        }
    }
}

unsafe extern "system" fn mouse_hook_proc(code: i32, wparam: WPARAM, lparam: LPARAM) -> LRESULT {
    if code >= 0 && wparam.0 == WM_LBUTTONDOWN as usize {
        let hook_struct = *(lparam.0 as *const MSLLHOOKSTRUCT);
        let pt = hook_struct.pt;
        let clicked = WindowFromPoint(pt);

        if !clicked.0.is_null() {
            let mut class_buf = [0u16; 256];
            let len = GetClassNameW(clicked, &mut class_buf);
            if len > 0 {
                let cls = String::from_utf16_lossy(&class_buf[..len as usize]);
                if cls == "SysListView32"
                    || cls == "SHELLDLL_DefView"
                    || cls == "WorkerW"
                    || cls == "Progman"
                {
                    let render = RENDER_HWND.load(Ordering::SeqCst);
                    if render != 0 {
                        let target = HWND(render as *mut std::ffi::c_void);
                        let lparam_pos = LPARAM(((pt.y << 16) | (pt.x & 0xFFFF)) as isize);

                        let _ = PostMessageW(target, WM_MOUSEMOVE, WPARAM(0), lparam_pos);
                        let _ = PostMessageW(target, WM_LBUTTONDOWN, WPARAM(1), lparam_pos);
                        let _ = PostMessageW(target, WM_LBUTTONUP, WPARAM(0), lparam_pos);
                    }

                    if let Ok(guard) = SOUND_FILE_UTF16.lock() {
                        if let Some(ref sound_vec) = *guard {
                            let _ = PlaySoundW(
                                PCWSTR::from_raw(sound_vec.as_ptr()),
                                None,
                                SND_FILENAME | SND_ASYNC,
                            );
                        }
                    }
                }
            }
        }
    }

    let hhook = HOOK_HANDLE.load(Ordering::SeqCst);
    CallNextHookEx(HHOOK(hhook as *mut std::ffi::c_void), code, wparam, lparam)
}

pub struct DesktopInputBridge;

impl DesktopInputBridge {
    pub fn run(workerw: HWND, sound_path: Option<&str>) -> Result<()> {
        let sound_path_owned = sound_path.map(|s| s.to_string());
        let workerw_raw = workerw.0 as usize;

        let handle = std::thread::spawn(move || -> Result<()> {
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

                let render_hwnd = locate_render_hwnd(HWND(workerw_raw as *mut std::ffi::c_void))?;
                RENDER_HWND.store(render_hwnd.0 as isize, Ordering::SeqCst);

                if let Some(ref path) = sound_path_owned {
                    let mut utf16: Vec<u16> = path.encode_utf16().collect();
                    utf16.push(0);
                    if let Ok(mut guard) = SOUND_FILE_UTF16.lock() {
                        *guard = Some(utf16);
                    }
                }

                let hook = SetWindowsHookExW(
                    WH_MOUSE_LL,
                    Some(mouse_hook_proc),
                    windows::Win32::Foundation::HINSTANCE(std::ptr::null_mut()),
                    0,
                )
                .map_err(|e| anyhow!("Failed to install WH_MOUSE_LL hook: {:?}", e))?;

                HOOK_HANDLE.store(hook.0 as isize, Ordering::SeqCst);
                println!("✅ Desktop Input Bridge active. Listening for desktop clicks...");

                let mut msg = windows::Win32::UI::WindowsAndMessaging::MSG::default();
                while GetMessageW(&mut msg, HWND(std::ptr::null_mut()), 0, 0).as_bool() {
                    let _ = TranslateMessage(&msg);
                    DispatchMessageW(&msg);
                }

                let _ = UnhookWindowsHookEx(hook);
            }
            Ok(())
        });

        handle
            .join()
            .map_err(|_| anyhow!("Bridge thread panicked"))??;

        Ok(())
    }
}
