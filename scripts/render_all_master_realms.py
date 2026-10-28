#!/usr/bin/env python3
"""
Aegis Sovereign Deterministic Motion Engine - Master Suite Renderer (All 11 Realms)
===================================================================================
Unified Master Pipeline & Single Source of Truth for Aegis Live Wallpapers.

Mathematical Invariants & Architectural Rules:
1. Exact Dual-Phase Windowing:
   `frame = f1 * w_blend + f2 * (1.0 - w_blend)` where `w_blend = sin^2(t1 * pi)`.
   Guarantees 0% weight on `f1` at `t1 = 0` (reset) and 0% weight on `f2` at `t1 = 0.5` (reset).
2. Strict Integer Harmonics:
   All `sin(k * phase)` terms use integer `k in {1, 2, 3}` (eliminating half-integer `1.5`/`2.5` loop snaps).
3. Zero-Teleport Particle Envelopes:
   Every particle (snow, embers, leaves, meteors, bubbles, stardust) uses a periodic
   `sin^1.5(prog * pi)` alpha lifecycle so particles never jump at the loop boundary.
4. Surgical Feature Gating:
   100% rock-solid architecture, bridges, ships, cliffs, trees, and statues (zero rubber mesh warping).
5. Hardware NVENC Zero-B-Frame Loop Encoding:
   `2560x1440 @ 30fps`, `h264_nvenc -preset p5 -cq 15 -bf 0 -g 30` for stutter-free WebView2 `<video loop>`.

CLI Usage:
  python render_all_master_realms.py --all             # Render all 11 realms
  python render_all_master_realms.py --realm 5        # Render only Realm 05 (Sky Citadel)
  python render_all_master_realms.py --realm 1,3,9    # Render a subset of realms
  python render_all_master_realms.py --list           # List all realms & parameter profiles
  python render_all_master_realms.py --no-sync        # Skip syncing to external folders
"""

import os
import sys
import time
import shutil
import argparse
import subprocess
import cv2
import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

REPO_INTERACTIVE = r"E:\GitHub\aegis-wallpaper\assets\interactive"
COLLECTION_DIR = r"C:\Users\agung\Pictures\Wallpapers\Fantasy_RPG_Collection"
SRC_DIR = COLLECTION_DIR if os.path.exists(COLLECTION_DIR) else REPO_INTERACTIVE
OUT_DIR = COLLECTION_DIR if os.path.exists(COLLECTION_DIR) else REPO_INTERACTIVE

DESTINATIONS = [
    r"E:\GitHub\aegis-wallpaper\assets\interactive",
    r"C:\Users\agung\Pictures\Wallpapers\Interactive_Fantasy_Suite",
    r"C:\Users\agung\AppData\Local\Lively Wallpaper\Library\wallpapers\aegis_interactive",
    r"C:\Users\agung\AppData\Local\Lively Wallpaper\Library\SaveData\wptmp\lrosxyrt.a4j",
]

W, H = 2560, 1440
FPS = 30
DURATION = 8.0
NUM_FRAMES = int(FPS * DURATION)  # 240 frames (8.0s @ 30fps)

Y_GRID, X_GRID = np.mgrid[0:H, 0:W].astype(np.float32)
NY = Y_GRID / float(H)
NX = X_GRID / float(W)


def open_nvenc(out_path, cq=15):
    cmd = [
        "ffmpeg", "-y",
        "-loglevel", "error",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", f"{W}x{H}",
        "-pix_fmt", "bgr24",
        "-r", str(FPS),
        "-i", "-",
        "-c:v", "h264_nvenc",
        "-preset", "p5",
        "-cq", str(cq),
        "-bf", "0",
        "-g", str(FPS),
        "-pix_fmt", "yuv420p",
        out_path,
    ]
    return subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def finish_nvenc(proc, name, t0, out_path):
    proc.stdin.close()
    proc.wait()
    if proc.returncode != 0:
        raise RuntimeError(f"FFmpeg failed on {name} with code {proc.returncode}")
    mb = os.path.getsize(out_path) / (1024 * 1024)
    print(f"  [OK] {name} rendered in {time.time() - t0:.1f}s ({mb:.2f} MB)", flush=True)


def load_master(filename):
    p = os.path.join(SRC_DIR, filename)
    if not os.path.exists(p):
        p = os.path.join(REPO_INTERACTIVE, filename)
    raw = cv2.imread(p)
    if raw is None:
        raise FileNotFoundError(p)
    return cv2.resize(raw, (W, H), interpolation=cv2.INTER_LANCZOS4)


def make_glow_bgr(mask, b_scale, g_scale, r_scale):
    return np.stack([mask * b_scale, mask * g_scale, mask * r_scale], axis=2).astype(np.float32)


def draw_soft_particles(frame_u8, xs, ys, radii, bgr_color, alphas):
    """Ultra-fast local-patch particle renderer using additive glow + core blending."""
    for x, y, r, a in zip(xs, ys, radii, alphas):
        if a <= 0.02:
            continue
        ix, iy = int(round(x)), int(round(y))
        ir = max(1, int(round(r)))
        rad_pad = ir + 2
        if not (rad_pad <= ix < W - rad_pad and rad_pad <= iy < H - rad_pad):
            continue
        fa = float(a)
        outer_col = (int(bgr_color[0] * fa * 0.55), int(bgr_color[1] * fa * 0.55), int(bgr_color[2] * fa * 0.55))
        core_col = (int(min(255, bgr_color[0] * 1.15) * fa), int(min(255, bgr_color[1] * 1.15) * fa), int(min(255, bgr_color[2] * 1.15) * fa))

        x1, y1 = ix - rad_pad, iy - rad_pad
        x2, y2 = ix + rad_pad + 1, iy + rad_pad + 1
        roi = frame_u8[y1:y2, x1:x2]
        patch = np.zeros_like(roi)
        cv2.circle(patch, (rad_pad, rad_pad), ir + 1, outer_col, -1, lineType=cv2.LINE_AA)
        cv2.circle(patch, (rad_pad, rad_pad), max(1, int(round(r * 0.6))), core_col, -1, lineType=cv2.LINE_AA)
        cv2.add(roi, patch, dst=roi)


# ==============================================================================
# REALM 01: Valerius Citadel Twilight (Winding River + Sunset Godrays + Motes)
# ==============================================================================
def render_01_citadel(cq=15):
    print("\n[01/11] Rendering Realm 01: Valerius Citadel Twilight...", flush=True)
    t0 = time.time()
    img = load_master("01_citadel_twilight_4k.jpg")
    out_path = os.path.join(OUT_DIR, "01_citadel_twilight_live.mp4")
    img_f = img.astype(np.float32)
    b, g, r = cv2.split(img_f)
    lum = (b + g + r) / 3.0

    in_valley = (NY >= 0.50) & (NY <= 0.98) & (NX >= 0.42) & (NX <= 0.62)
    is_bridge_or_tree = (r > b * 1.08) | (g > b * 1.08) | (lum < 70)
    is_river = in_valley & (~is_bridge_or_tree) & (b > 80)
    river_u8 = cv2.morphologyEx(is_river.astype(np.uint8) * 255, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)))
    river_u8 = cv2.morphologyEx(river_u8, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
    river_mask = cv2.GaussianBlur(river_u8.astype(np.float32) / 255.0, (9, 9), 0)

    in_rays = (NY <= 0.45) & (NX >= 0.35) & (NX <= 0.92) & (r > 130) & (g > 95) & (r > b * 1.2)
    ray_mask = cv2.GaussianBlur(in_rays.astype(np.float32), (31, 31), 0)
    ray_glow = make_glow_bgr(ray_mask, 2.0, 9.0, 13.5)

    in_windows = (NX <= 0.35) & (NY >= 0.15) & (NY <= 0.58) & (r > 180) & (g > 110) & (b < 90)
    win_mask = cv2.GaussianBlur(in_windows.astype(np.float32), (7, 7), 0)
    win_glow = make_glow_bgr(win_mask, 2.0, 12.5, 21.0)

    ry0 = int(0.48 * H)
    rx0, rx1 = int(0.40 * W), int(0.64 * W)
    r_crop = img[ry0:, rx0:rx1]
    rm_crop = river_mask[ry0:, rx0:rx1]
    xg_crop, yg_crop = np.meshgrid(np.arange(rx1 - rx0, dtype=np.float32), np.arange(H - ry0, dtype=np.float32))
    ny_crop = NY[ry0:, rx0:rx1]

    np.random.seed(101)
    n_motes = 55
    mx0 = np.random.uniform(0.10, 0.90, n_motes) * W
    my0 = np.random.uniform(0.45, 0.92, n_motes) * H
    m_rise = np.random.uniform(55.0, 110.0, n_motes)
    m_sway = np.random.uniform(12.0, 24.0, n_motes)
    m_off = np.random.uniform(0.0, 1.0, n_motes)
    m_rad = np.random.uniform(1.4, 2.6, n_motes)
    m_alpha = np.random.uniform(0.45, 0.85, n_motes)

    proc = open_nvenc(out_path, cq=cq)
    num_cycles = 6
    cycle_d = 13.0

    for i in range(NUM_FRAMES):
        prog = i / float(NUM_FRAMES)
        phase = 2.0 * np.pi * prog
        t1 = (prog * num_cycles) % 1.0
        t2 = (t1 + 0.5) % 1.0
        w_blend = float(np.sin(t1 * np.pi) ** 2.0)

        ray_p = float(np.sin(phase) * 0.5 + 0.5)
        win_p = float(np.sin(phase * 2.0) * 0.5 + 0.5)
        frame = img_f + ray_p * ray_glow + win_p * win_glow

        dy1 = (t1 - 0.5) * cycle_d * rm_crop
        dy2 = (t2 - 0.5) * cycle_d * rm_crop
        f1 = cv2.remap(r_crop, xg_crop - dy1 * 0.35, yg_crop - dy1, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT).astype(np.float32)
        f2 = cv2.remap(r_crop, xg_crop - dy2 * 0.35, yg_crop - dy2, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT).astype(np.float32)
        river_frame = f1 * w_blend + f2 * (1.0 - w_blend)
        gleam = ((np.sin(ny_crop * 36.0 - phase * 2.0) * 0.5 + 0.5) ** 1.5) * rm_crop * 14.0
        river_frame += gleam[:, :, np.newaxis]
        frame[ry0:, rx0:rx1] = river_frame

        frame_u8 = np.clip(frame, 0, 255).astype(np.uint8)
        p_prog = (prog + m_off) % 1.0
        p_a = (np.sin(p_prog * np.pi) ** 1.5) * m_alpha
        draw_soft_particles(frame_u8, mx0 + np.sin(p_prog * 2.0 * np.pi) * m_sway, my0 - p_prog * m_rise, m_rad, (110, 215, 255), p_a)
        proc.stdin.write(frame_u8.tobytes())

    finish_nvenc(proc, "Realm 01", t0, out_path)
    return out_path


# ==============================================================================
# REALM 02: Eldertree Mystical Shrine (Arcane Runes + Canopy Rays + Forest Wisps)
# ==============================================================================
def render_02_shrine(cq=15):
    print("\n[02/11] Rendering Realm 02: Eldertree Mystical Shrine...", flush=True)
    t0 = time.time()
    img = load_master("02_mystical_forest_shrine_4k.jpg")
    out_path = os.path.join(OUT_DIR, "02_mystical_forest_shrine_live.mp4")
    img_f = img.astype(np.float32)
    b, g, r = cv2.split(img_f)

    is_cyan_rune = (b > 135) & (g > 125) & (b > r * 1.30) & (NY >= 0.30)
    rune_mask = cv2.GaussianBlur(is_cyan_rune.astype(np.float32), (11, 11), 0)
    altar_mask = np.exp(-(((NX - 0.50) / 0.09) ** 2 + ((NY - 0.56) / 0.08) ** 2)).astype(np.float32)
    in_sunbeams = (NX >= 0.48) & (NX <= 0.88) & (NY <= 0.58) & (r > 110) & (g > 110) & (r > b * 1.05)
    beam_mask = cv2.GaussianBlur(in_sunbeams.astype(np.float32), (31, 31), 0)

    glow_rune = make_glow_bgr(rune_mask, 28.0, 24.0, 5.0)
    glow_altar = make_glow_bgr(altar_mask, 21.0, 16.0, 3.5) + make_glow_bgr(beam_mask, 2.5, 11.0, 13.5)

    np.random.seed(202)
    n_wisps = 64
    wx0 = np.random.uniform(0.12, 0.88, n_wisps) * W
    wy0 = np.random.uniform(0.30, 0.92, n_wisps) * H
    w_rise = np.random.uniform(60.0, 130.0, n_wisps)
    w_sway = np.random.uniform(14.0, 30.0, n_wisps)
    w_off = np.random.uniform(0.0, 1.0, n_wisps)
    w_rad = np.random.uniform(1.5, 2.8, n_wisps)
    w_alpha = np.random.uniform(0.48, 0.88, n_wisps)

    proc = open_nvenc(out_path, cq=cq)
    for i in range(NUM_FRAMES):
        prog = i / float(NUM_FRAMES)
        phase = 2.0 * np.pi * prog
        p1 = float(np.sin(phase) * 0.5 + 0.5)
        p2 = float(np.sin(phase * 2.0) * 0.5 + 0.5)
        frame_u8 = np.clip(img_f + p1 * glow_altar + p2 * glow_rune, 0, 255).astype(np.uint8)

        p_prog = (prog + w_off) % 1.0
        p_a = (np.sin(p_prog * np.pi) ** 1.5) * w_alpha
        px = wx0 + np.sin(p_prog * 2.0 * np.pi) * w_sway
        py = wy0 - p_prog * w_rise
        draw_soft_particles(frame_u8, px[:34], py[:34], w_rad[:34], (235, 255, 130), p_a[:34])
        draw_soft_particles(frame_u8, px[34:], py[34:], w_rad[34:], (130, 235, 255), p_a[34:])
        proc.stdin.write(frame_u8.tobytes())

    finish_nvenc(proc, "Realm 02", t0, out_path)
    return out_path


# ==============================================================================
# REALM 03: Mountain Aurora Fortress (Northern Lights + Zero-Seam Snowfall)
# ==============================================================================
def render_03_aurora(cq=15):
    print("\n[03/11] Rendering Realm 03: Frostpeak Aurora Fortress...", flush=True)
    t0 = time.time()
    img = load_master("03_mountain_aurora_fortress_4k.jpg")
    out_path = os.path.join(OUT_DIR, "03_mountain_aurora_snow_live.mp4")
    img_f = img.astype(np.float32)
    b, g, r = cv2.split(img_f)

    sky_h = int(0.48 * H)
    is_aurora_sky = (NY[:sky_h, :] <= 0.46) & ((g[:sky_h, :] > 75) | (b[:sky_h, :] > 80)) & (
        ~((r[:sky_h, :] > g[:sky_h, :] * 0.92) & (NY[:sky_h, :] > 0.14) & (NX[:sky_h, :] > 0.42) & (NX[:sky_h, :] < 0.78))
    )
    aurora_mask = cv2.GaussianBlur(is_aurora_sky.astype(np.float32), (31, 31), 0)
    aur_spatial_1 = NX[:sky_h, :] * 5.0 + NY[:sky_h, :] * 3.0
    aur_spatial_2 = NX[:sky_h, :] * 7.0 - NY[:sky_h, :] * 4.0

    is_torch = (NY >= 0.25) & (NY <= 0.88) & (r > 155) & (g > 95) & (b < 90) & (r > b * 1.6)
    torch_mask = cv2.GaussianBlur(is_torch.astype(np.float32), (7, 7), 0)
    torch_glow = make_glow_bgr(torch_mask, 1.5, 11.0, 19.0)

    np.random.seed(303)
    n_snow = 280
    sx0 = np.random.uniform(0.0, W, n_snow)
    sy0 = np.random.uniform(0.0, H, n_snow)
    s_fall = np.random.uniform(140.0, 260.0, n_snow)
    s_drift = np.random.uniform(20.0, 48.0, n_snow)
    s_sway = np.random.uniform(10.0, 20.0, n_snow)
    s_off = np.random.uniform(0.0, 1.0, n_snow)
    s_rad = np.random.choice([1.2, 1.8, 2.4], size=n_snow, p=[0.55, 0.35, 0.10])
    s_alpha = np.random.uniform(0.40, 0.85, n_snow)

    proc = open_nvenc(out_path, cq=cq)
    for i in range(NUM_FRAMES):
        prog = i / float(NUM_FRAMES)
        phase = 2.0 * np.pi * prog
        tp = float(np.sin(phase * 2.0) * 0.5 + 0.5)
        frame = img_f + tp * torch_glow

        w1 = (np.sin(aur_spatial_1 + phase) * 0.5 + 0.5) * aurora_mask * 17.5
        w2 = (np.sin(aur_spatial_2 - phase * 2.0) * 0.5 + 0.5) * aurora_mask * 12.0
        frame[:sky_h, :, 0] += w2 * 1.30
        frame[:sky_h, :, 1] += w1 * 1.55
        frame[:sky_h, :, 2] += w2 * 0.70

        frame_u8 = np.clip(frame, 0, 255).astype(np.uint8)
        p_prog = (prog + s_off) % 1.0
        p_a = (np.sin(p_prog * np.pi) ** 1.4) * s_alpha
        px = (sx0 + p_prog * s_drift + np.sin(p_prog * 2.0 * np.pi) * s_sway) % W
        py = (sy0 + p_prog * s_fall) % H
        draw_soft_particles(frame_u8, px, py, s_rad, (255, 248, 240), p_a)
        proc.stdin.write(frame_u8.tobytes())

    finish_nvenc(proc, "Realm 03", t0, out_path)
    return out_path


# ==============================================================================
# REALM 04: Celestial Dunes Oasis (2560x1440 Oasis Pool + Obelisk Glyphs + Stars)
# ==============================================================================
def render_04_dunes(cq=15):
    print("\n[04/11] Rendering Realm 04: Celestial Dunes Oasis...", flush=True)
    t0 = time.time()
    img = load_master("04_celestial_dunes_oasis_4k.jpg")
    out_path = os.path.join(OUT_DIR, "04_celestial_dunes_oasis_live.mp4")
    img_f = img.astype(np.float32)
    b, g, r = cv2.split(img_f)

    in_pool_box = (NY >= 0.57) & (NY <= 0.87) & (NX >= 0.24) & (NX <= 0.70)
    is_pool_water = in_pool_box & (b > r * 1.05) & (g > r * 0.95) & (b > 55)
    pool_u8 = cv2.morphologyEx(is_pool_water.astype(np.uint8) * 255, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7)))
    pool_mask = cv2.GaussianBlur(pool_u8.astype(np.float32) / 255.0, (15, 15), 0)

    is_glyph = (NY >= 0.16) & (NY <= 0.62) & (r > 165) & (g > 105) & (b < 95) & (r > b * 1.8)
    glyph_mask = cv2.GaussianBlur(is_glyph.astype(np.float32), (7, 7), 0)
    glyph_glow = make_glow_bgr(glyph_mask, 2.0, 15.0, 24.0)

    is_moon_sky = (NY <= 0.42) & (NX >= 0.18) & (NX <= 0.82) & ((b > 110) | (r > 130))
    sky_mask = cv2.GaussianBlur(is_moon_sky.astype(np.float32), (25, 25), 0)
    sky_glow = make_glow_bgr(sky_mask, 9.0, 4.0, 7.0)

    py0, py1 = int(0.55 * H), int(0.89 * H)
    px0, px1 = int(0.22 * W), int(0.72 * W)
    p_crop = img[py0:py1, px0:px1]
    pm_crop = pool_mask[py0:py1, px0:px1]
    xg_crop, yg_crop = np.meshgrid(np.arange(px1 - px0, dtype=np.float32), np.arange(py1 - py0, dtype=np.float32))
    nx_crop = NX[py0:py1, px0:px1]
    ny_crop = NY[py0:py1, px0:px1]

    np.random.seed(404)
    n_motes = 58
    mx0 = np.random.uniform(0.12, 0.88, n_motes) * W
    my0 = np.random.uniform(0.32, 0.88, n_motes) * H
    m_rise = np.random.uniform(45.0, 95.0, n_motes)
    m_sway = np.random.uniform(10.0, 22.0, n_motes)
    m_off = np.random.uniform(0.0, 1.0, n_motes)
    m_rad = np.random.uniform(1.3, 2.4, n_motes)
    m_alpha = np.random.uniform(0.48, 0.86, n_motes)

    proc = open_nvenc(out_path, cq=cq)
    num_cycles = 6
    cycle_w = 9.0

    for i in range(NUM_FRAMES):
        prog = i / float(NUM_FRAMES)
        phase = 2.0 * np.pi * prog
        t1 = (prog * num_cycles) % 1.0
        t2 = (t1 + 0.5) % 1.0
        w_blend = float(np.sin(t1 * np.pi) ** 2.0)

        gp = float(np.sin(phase * 2.0) * 0.5 + 0.5)
        sp = float(np.sin(phase) * 0.5 + 0.5)
        frame = img_f + gp * glyph_glow + sp * sky_glow

        dx1 = (t1 - 0.5) * cycle_w * pm_crop
        dx2 = (t2 - 0.5) * cycle_w * pm_crop
        f1 = cv2.remap(p_crop, xg_crop - dx1, yg_crop, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT).astype(np.float32)
        f2 = cv2.remap(p_crop, xg_crop - dx2, yg_crop, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT).astype(np.float32)
        pool_frame = f1 * w_blend + f2 * (1.0 - w_blend)
        caust = (np.sin(nx_crop * 28.0 + ny_crop * 18.0 - phase * 2.0) * 0.5 + 0.5) * pm_crop * 14.0
        pool_frame[:, :, 0] += caust * 1.20
        pool_frame[:, :, 1] += caust * 1.10
        frame[py0:py1, px0:px1] = pool_frame

        frame_u8 = np.clip(frame, 0, 255).astype(np.uint8)
        p_prog = (prog + m_off) % 1.0
        p_a = (np.sin(p_prog * np.pi) ** 1.5) * m_alpha
        px = mx0 + np.sin(p_prog * 2.0 * np.pi) * m_sway
        py = my0 - p_prog * m_rise
        draw_soft_particles(frame_u8, px[:30], py[:30], m_rad[:30], (110, 215, 255), p_a[:30])
        draw_soft_particles(frame_u8, px[30:], py[30:], m_rad[30:], (255, 230, 120), p_a[30:])
        proc.stdin.write(frame_u8.tobytes())

    finish_nvenc(proc, "Realm 04", t0, out_path)
    return out_path


# ==============================================================================
# REALM 05: Floating Sky Citadel of Aetheria (Pure Waterfalls + Drifting Mist)
# ==============================================================================
def render_05_sky_citadel(cq=15):
    print("\n[05/11] Rendering Realm 05: Floating Sky Citadel (Lively Falls + Mist)...", flush=True)
    t0 = time.time()
    img = load_master("05_floating_sky_citadel_4k.jpg")
    out_path = os.path.join(OUT_DIR, "05_floating_sky_citadel_live.mp4")
    img_f = img.astype(np.float32)
    b, g, r = cv2.split(img_f)

    def add_vertical_fall(x1, x2, y1, y2, fade_len=55, top_fade=15):
        f = np.zeros((H, W), dtype=np.float32)
        cx = (x1 + x2) / 2.0
        hw = (x2 - x1) / 2.0
        xs = np.arange(W, dtype=np.float32)
        h_prof = np.clip(1.0 - ((xs - cx) / hw) ** 2, 0.0, 1.0) ** 1.5
        ys = np.arange(H, dtype=np.float32)
        v_prof = np.zeros(H, dtype=np.float32)
        tf_idx = (ys >= y1) & (ys < y1 + top_fade)
        v_prof[tf_idx] = (ys[tf_idx] - y1) / max(1.0, top_fade)
        mb_idx = (ys >= y1 + top_fade) & (ys <= y2 - fade_len)
        v_prof[mb_idx] = 1.0
        bf_idx = (ys > y2 - fade_len) & (ys <= y2)
        v_prof[bf_idx] = (y2 - ys[bf_idx]) / max(1.0, fade_len)
        return np.outer(v_prof, h_prof)

    is_cliff = (r > 1.08 * b) | (g > 1.18 * b)
    is_water_chroma = (b > 115) & (b >= 0.85 * r) & (~is_cliff)

    m1_upper = add_vertical_fall(1445, 1575, 675, 860, fade_len=30, top_fade=12)
    m1_lower = add_vertical_fall(1445, 1535, 840, 1360, fade_len=110, top_fade=25)
    m1_arch = add_vertical_fall(1392, 1422, 685, 1060, fade_len=70, top_fade=12)
    m_palace_r = add_vertical_fall(1670, 1712, 715, 1040, fade_len=55, top_fade=12)
    m_left_l = add_vertical_fall(740, 775, 835, 1090, fade_len=70, top_fade=12)
    m_left_r = add_vertical_fall(1082, 1135, 845, 1310, fade_len=95, top_fade=15)
    m_spire = add_vertical_fall(1968, 1995, 380, 640, fade_len=40, top_fade=12)

    corridors = np.maximum.reduce([m1_upper, m1_lower, m1_arch, m_palace_r, m_left_l, m_left_r, m_spire])
    water_mask = cv2.GaussianBlur(corridors * is_water_chroma.astype(np.float32), (7, 13), 0)

    rainbow_dist = ((NX - 0.60) ** 2) / (0.09 ** 2) + ((NY - 0.82) ** 2) / (0.14 ** 2)
    rainbow_mask = np.clip(np.exp(-((rainbow_dist - 0.60) ** 2) / 0.08), 0.0, 1.0).astype(np.float32)
    godray_mask = ((np.clip(1.0 - (NX / 0.48), 0.0, 1.0) * np.clip(1.0 - (NY / 0.52), 0.0, 1.0)) ** 1.8).astype(np.float32)
    atmo_glow = make_glow_bgr(rainbow_mask, 10.0, 11.0, 7.5) + make_glow_bgr(godray_mask, 1.5, 6.5, 9.0)

    wy0, wy1 = 370, 1375
    wx0, wx1 = 725, 2010
    w_crop = img[wy0:wy1, wx0:wx1]
    wm_crop = water_mask[wy0:wy1, wx0:wx1]
    xg_crop, yg_crop = np.meshgrid(np.arange(wx1 - wx0, dtype=np.float32), np.arange(wy1 - wy0, dtype=np.float32))
    ny_crop = NY[wy0:wy1, wx0:wx1]

    np.random.seed(505)
    n_mist = 48
    mx0 = np.random.uniform(0.28, 0.78, n_mist) * W
    my0 = np.random.uniform(0.48, 0.92, n_mist) * H
    m_drift = np.random.uniform(25.0, 50.0, n_mist)
    m_rise = np.random.uniform(10.0, 25.0, n_mist)
    m_sway = np.random.uniform(8.0, 18.0, n_mist)
    m_off = np.random.uniform(0.0, 1.0, n_mist)
    m_rad = np.random.uniform(1.4, 2.5, n_mist)
    m_alpha = np.random.uniform(0.40, 0.75, n_mist)

    proc = open_nvenc(out_path, cq=cq)
    num_cycles = 7
    cycle_h = 22.0

    for i in range(NUM_FRAMES):
        prog = i / float(NUM_FRAMES)
        phase = 2.0 * np.pi * prog
        t1 = (prog * num_cycles) % 1.0
        t2 = (t1 + 0.5) % 1.0
        w_blend = float(np.sin(t1 * np.pi) ** 2.0)
        atmo_p = float(np.sin(phase) * 0.5 + 0.5)

        frame = img_f.copy()
        dy1 = (t1 - 0.5) * cycle_h * wm_crop
        dy2 = (t2 - 0.5) * cycle_h * wm_crop
        f1 = cv2.remap(w_crop, xg_crop, yg_crop - dy1, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT).astype(np.float32)
        f2 = cv2.remap(w_crop, xg_crop, yg_crop - dy2, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT).astype(np.float32)
        wf_frame = f1 * w_blend + f2 * (1.0 - w_blend)

        gleam = ((np.sin(ny_crop * 32.0 - phase * 2.0) * 0.5 + 0.5) ** 1.5) * wm_crop * 16.0
        wf_frame += gleam[:, :, np.newaxis]
        frame[wy0:wy1, wx0:wx1] = wf_frame
        frame += atmo_p * atmo_glow

        frame_u8 = np.clip(frame, 0, 255).astype(np.uint8)
        p_prog = (prog + m_off) % 1.0
        p_a = (np.sin(p_prog * np.pi) ** 1.5) * m_alpha
        px = mx0 + p_prog * m_drift + np.sin(p_prog * 2.0 * np.pi) * m_sway
        py = my0 - p_prog * m_rise
        draw_soft_particles(frame_u8, px[:24], py[:24], m_rad[:24], (255, 240, 210), p_a[:24])
        draw_soft_particles(frame_u8, px[24:], py[24:], m_rad[24:], (210, 245, 255), p_a[24:])
        proc.stdin.write(frame_u8.tobytes())

    finish_nvenc(proc, "Realm 05", t0, out_path)
    return out_path


# ==============================================================================
# REALM 06: Volcanic Obsidian Forge (Zero-Seam Magma Cataracts + Rising Embers)
# ==============================================================================
def render_06_forge(cq=14):
    print("\n[06/11] Rendering Realm 06: Volcanic Obsidian Forge...", flush=True)
    t0 = time.time()
    img = load_master("06_volcanic_obsidian_forge_4k.jpg")
    out_path = os.path.join(OUT_DIR, "06_volcanic_obsidian_forge_live.mp4")
    img_f = img.astype(np.float32)
    b, g, r = cv2.split(img_f)

    is_lava_color = (r > 120) & (r > 1.38 * b) & (g > 45) & (r > 0.95 * g)
    is_bright_lava = (r > 160) & (g > 85) & (b < 150)
    is_landscape = (NY >= 0.38) | ((NX <= 0.36) & (NY >= 0.22)) | ((NX >= 0.78) & (NY >= 0.08))
    lava_raw = ((is_lava_color | is_bright_lava) & is_landscape).astype(np.uint8) * 255
    lava_clean = cv2.morphologyEx(lava_raw, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)))
    lava_clean = cv2.morphologyEx(lava_clean, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
    lava_mask = cv2.GaussianBlur(lava_clean.astype(np.float32) / 255.0, (7, 7), 0)

    is_vertical_fall = (
        ((NX >= 0.48) & (NX <= 0.62) & (NY >= 0.50) & (NY <= 0.88))
        | ((NX >= 0.24) & (NX <= 0.30) & (NY >= 0.42) & (NY <= 0.72))
        | ((NX >= 0.04) & (NX <= 0.22) & (NY >= 0.40) & (NY <= 0.88))
        | ((NX >= 0.71) & (NX <= 0.76) & (NY >= 0.54) & (NY <= 0.78))
        | ((NX >= 0.88) & (NX <= 0.98) & (NY >= 0.50) & (NY <= 0.75))
    )
    cataract_mask = lava_mask * is_vertical_fall.astype(np.float32)
    pool_mask = lava_mask * (~is_vertical_fall).astype(np.float32)

    is_runes = (r > 140) & (g > 70) & (b < 60) & (NY >= 0.28) & (NY <= 0.55) & (NX >= 0.38) & (NX <= 0.76)
    runes_mask = cv2.GaussianBlur(is_runes.astype(np.float32), (5, 5), 0)

    magma_glow = make_glow_bgr(lava_mask, 0.5, 12.0, 18.0)
    rune_glow = make_glow_bgr(runes_mask, 0.5, 14.0, 22.0)

    np.random.seed(606)
    n_embers = 85
    ex0 = np.random.uniform(0.12, 0.88, n_embers) * W
    ey0 = np.random.uniform(0.42, 0.96, n_embers) * H
    e_rise = np.random.uniform(110.0, 220.0, n_embers)
    e_sway = np.random.uniform(12.0, 26.0, n_embers)
    e_off = np.random.uniform(0.0, 1.0, n_embers)
    e_rad = np.random.choice([1.4, 2.0, 2.6], size=n_embers, p=[0.5, 0.35, 0.15])
    e_alpha = np.random.uniform(0.55, 0.95, n_embers)

    proc = open_nvenc(out_path, cq=cq)
    num_cycles = 6
    cycle_h = 18.0

    for i in range(NUM_FRAMES):
        prog = i / float(NUM_FRAMES)
        phase = 2.0 * np.pi * prog
        t1 = (prog * num_cycles) % 1.0
        t2 = (t1 + 0.5) % 1.0
        w_blend = float(np.sin(t1 * np.pi) ** 2.0)

        dy1 = (t1 - 0.5) * cycle_h * cataract_mask
        dy2 = (t2 - 0.5) * cycle_h * cataract_mask
        dx_pool = np.sin(NY * 8.0 + phase) * 1.4 * pool_mask

        f1 = cv2.remap(img, X_GRID + dx_pool, Y_GRID - dy1, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT).astype(np.float32)
        f2 = cv2.remap(img, X_GRID + dx_pool, Y_GRID - dy2, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT).astype(np.float32)
        frame = f1 * w_blend + f2 * (1.0 - w_blend)

        p1 = float(np.sin(phase) * 0.5 + 0.5)
        p2 = float(np.sin(phase * 2.0) * 0.5 + 0.5)
        frame += p1 * magma_glow + p2 * rune_glow

        frame_u8 = np.clip(frame, 0, 255).astype(np.uint8)
        p_prog = (prog + e_off) % 1.0
        p_a = (np.sin(p_prog * np.pi) ** 1.5) * e_alpha
        draw_soft_particles(frame_u8, ex0 + np.sin(p_prog * 2.0 * np.pi) * e_sway, ey0 - p_prog * e_rise, e_rad, (40, 175, 255), p_a)
        proc.stdin.write(frame_u8.tobytes())

    finish_nvenc(proc, "Realm 06", t0, out_path)
    return out_path


# ==============================================================================
# REALM 07: Sunken Coral Atlantis (2560x1440 Abyssal Currents + Caustics + Bubbles)
# ==============================================================================
def render_07_atlantis(cq=15):
    print("\n[07/11] Rendering Realm 07: Sunken Coral Atlantis...", flush=True)
    t0 = time.time()
    img = load_master("07_sunken_coral_atlantis_4k.jpg")
    out_path = os.path.join(OUT_DIR, "07_sunken_coral_atlantis_live.mp4")
    img_f = img.astype(np.float32)
    b, g, r = cv2.split(img_f)

    in_shafts = (NY <= 0.62) & (NX >= 0.25) & (NX <= 0.68) & (b > 130) & (g > 110)
    shaft_mask = cv2.GaussianBlur(in_shafts.astype(np.float32), (31, 31), 0)
    shaft_glow = make_glow_bgr(shaft_mask, 14.0, 12.5, 2.0)

    is_biolum = ((b > 165) & (g > 140) & (b > r * 1.35)) | ((r > 140) & (b > 160) & (NY >= 0.55))
    biolum_mask = cv2.GaussianBlur(is_biolum.astype(np.float32), (9, 9), 0)
    biolum_glow = make_glow_bgr(biolum_mask, 22.0, 18.0, 5.0)

    # Subtle open water gentle advection
    water_flow_mask = cv2.GaussianBlur((in_shafts | is_biolum).astype(np.float32), (25, 25), 0)

    np.random.seed(707)
    n_bub = 85
    bx0 = np.random.uniform(0.06, 0.94, n_bub) * W
    by0 = np.random.uniform(0.18, 0.96, n_bub) * H
    b_rise = np.random.uniform(85.0, 180.0, n_bub)
    b_sway = np.random.uniform(10.0, 24.0, n_bub)
    b_off = np.random.uniform(0.0, 1.0, n_bub)
    b_rad = np.random.uniform(1.5, 3.4, n_bub)
    b_alpha = np.random.uniform(0.42, 0.82, n_bub)

    proc = open_nvenc(out_path, cq=cq)
    num_cycles = 4
    cycle_w = 8.0

    for i in range(NUM_FRAMES):
        prog = i / float(NUM_FRAMES)
        phase = 2.0 * np.pi * prog
        t1 = (prog * num_cycles) % 1.0
        t2 = (t1 + 0.5) % 1.0
        w_blend = float(np.sin(t1 * np.pi) ** 2.0)

        sp = float(np.sin(phase) * 0.5 + 0.5)
        bp = float(np.sin(phase * 2.0) * 0.5 + 0.5)

        dx1 = (t1 - 0.5) * cycle_w * water_flow_mask
        dx2 = (t2 - 0.5) * cycle_w * water_flow_mask
        f1 = cv2.remap(img, X_GRID + dx1, Y_GRID, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT).astype(np.float32)
        f2 = cv2.remap(img, X_GRID + dx2, Y_GRID, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT).astype(np.float32)
        frame = f1 * w_blend + f2 * (1.0 - w_blend)
        frame += sp * shaft_glow + bp * biolum_glow

        frame_u8 = np.clip(frame, 0, 255).astype(np.uint8)
        p_prog = (prog + b_off) % 1.0
        p_a = (np.sin(p_prog * np.pi) ** 1.5) * b_alpha
        draw_soft_particles(frame_u8, bx0 + np.sin(p_prog * 2.0 * np.pi) * b_sway, by0 - p_prog * b_rise, b_rad, (255, 240, 170), p_a)
        proc.stdin.write(frame_u8.tobytes())

    finish_nvenc(proc, "Realm 07", t0, out_path)
    return out_path


# ==============================================================================
# REALM 08: Cyber-Aegis Megacity (Zero-Seam Shield, Wet Neon & Rain Streaks)
# ==============================================================================
def render_08_cyber(cq=15):
    print("\n[08/11] Rendering Realm 08: Cyber-Aegis Neo-Tokyo Bastion...", flush=True)
    t0 = time.time()
    img = load_master("08_cyber_aegis_megacity_4k.jpg")
    out_path = os.path.join(OUT_DIR, "08_cyber_aegis_megacity_live.mp4")
    img_f = img.astype(np.float32)
    b, g, r = cv2.split(img_f)

    is_shield = (NY <= 0.52) & ((b > 135) | (r > 135))
    shield_mask = cv2.GaussianBlur(is_shield.astype(np.float32), (19, 19), 0)
    shield_glow = make_glow_bgr(shield_mask, 22.0, 5.0, 15.0)

    is_wet_road = (NY >= 0.68) & ((b > 95) | (r > 95))
    road_mask = cv2.GaussianBlur(is_wet_road.astype(np.float32), (15, 15), 0)
    road_glow = make_glow_bgr(road_mask, 18.0, 13.0, 10.0)

    is_neon = (NY >= 0.25) & (NY <= 0.78) & ((b > 200) | (r > 200)) & (np.abs(b - r) > 50)
    neon_mask = cv2.GaussianBlur(is_neon.astype(np.float32), (9, 9), 0)
    neon_glow = make_glow_bgr(neon_mask, 18.0, 4.0, 18.0)

    np.random.seed(808)
    n_rain = 135
    rx0 = np.random.uniform(0.02, 0.98, n_rain) * W
    ry0 = np.random.uniform(0.0, 0.82, n_rain) * H
    r_fall = np.random.uniform(180.0, 320.0, n_rain)
    r_len = np.random.uniform(18.0, 36.0, n_rain)
    r_off = np.random.uniform(0.0, 1.0, n_rain)
    r_alpha = np.random.uniform(0.32, 0.65, n_rain)

    proc = open_nvenc(out_path, cq=cq)
    for i in range(NUM_FRAMES):
        prog = i / float(NUM_FRAMES)
        phase = 2.0 * np.pi * prog
        p1 = float(np.sin(phase) * 0.5 + 0.5)
        p2 = float(np.sin(phase * 2.0) * 0.5 + 0.5)
        p3 = float(np.sin(phase * 3.0) * 0.5 + 0.5)
        frame_u8 = np.clip(img_f + p1 * road_glow + p2 * shield_glow + p3 * neon_glow, 0, 255).astype(np.uint8)

        rain_layer = np.zeros_like(frame_u8)
        for k in range(n_rain):
            p_k = (prog + r_off[k]) % 1.0
            a_k = float(np.sin(p_k * np.pi) ** 1.6) * r_alpha[k]
            if a_k < 0.04:
                continue
            y1 = int(ry0[k] + p_k * r_fall[k])
            x1 = int(rx0[k] + p_k * r_fall[k] * 0.16)
            y2 = int(y1 + r_len[k])
            x2 = int(x1 + r_len[k] * 0.16)
            if 0 <= y1 < H and 0 <= x1 < W:
                col = (int(255 * a_k), int(225 * a_k), int(120 * a_k)) if k % 3 != 0 else (int(235 * a_k), int(110 * a_k), int(255 * a_k))
                cv2.line(rain_layer, (x1, y1), (x2, y2), col, 1, lineType=cv2.LINE_AA)

        cv2.add(frame_u8, rain_layer, dst=frame_u8)
        proc.stdin.write(frame_u8.tobytes())

    finish_nvenc(proc, "Realm 08", t0, out_path)
    return out_path


# ==============================================================================
# REALM 09: Autumn Dragon Valley (Clean Inpaint + Rushing Falls + Maple Swirl)
# ==============================================================================
def render_09_valley(cq=15):
    print("\n[09/16] Rendering Realm 09: Autumn Dragon Valley (Accurate Waterfall & Lake Flow)...", flush=True)
    t0 = time.time()
    img = load_master("09_autumn_dragon_valley_4k.jpg")
    out_path = os.path.join(OUT_DIR, "09_autumn_dragon_valley_v2_live.mp4")
    img_f = img.astype(np.float32)
    b_chan, g_chan, r_chan = cv2.split(img_f)

    # 1. Cascading Waterfalls & Stream
    is_upper_fall = (NX >= 0.35) & (NX <= 0.44) & (NY >= 0.32) & (NY <= 0.52) & (b_chan > 115) & (b_chan > 0.80 * r_chan)
    is_lower_fall = (NX >= 0.38) & (NX <= 0.50) & (NY >= 0.52) & (NY <= 0.74) & (b_chan > 115) & (b_chan > 0.80 * r_chan)
    is_stream = (NX >= 0.51) & (NX <= 0.64) & (NY >= 0.56) & (NY <= 0.75) & (b_chan > 110) & (b_chan > 0.78 * r_chan)
    falls_raw = (is_upper_fall | is_lower_fall | is_stream).astype(np.uint8) * 255
    falls_clean = cv2.morphologyEx(falls_raw, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 7)))
    falls_mask = cv2.GaussianBlur(falls_clean.astype(np.float32) / 255.0, (7, 11), 0)

    # 2. Emerald Lake Pool (Bottom Center)
    is_lake = (NY >= 0.68) & (NX >= 0.15) & (NX <= 0.68) & (g_chan > 55) & (b_chan > 50) & (g_chan >= r_chan * 0.90) & (r_chan < 115)
    lake_raw = is_lake.astype(np.uint8) * 255
    lake_clean = cv2.morphologyEx(lake_raw, cv2.MORPH_CLOSE, lake_kernel := cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7)))
    lake_mask = cv2.GaussianBlur(lake_clean.astype(np.float32) / 255.0, (15, 15), 0)

    # 3. Plunge Pool Rising Mist
    plunge_dist_sq = ((NX - 0.45) ** 2) / (0.09 ** 2) + ((NY - 0.71) ** 2) / (0.045 ** 2)
    mist_mask = np.clip(np.exp(-plunge_dist_sq).astype(np.float32), 0.0, 1.0)

    # 4. Valley Sunbeam Godrays
    godray_dist_sq = ((NX - 0.80) ** 2) / (0.18 ** 2) + ((NY - 0.22) ** 2) / (0.15 ** 2)
    godray_mask = np.clip(np.exp(-godray_dist_sq).astype(np.float32), 0.0, 1.0)

    # 5. Lantern Lights
    lantern_mask = np.zeros((H, W), dtype=np.float32)
    for lx, ly, rad in [(int(0.730 * W), int(0.628 * H), 32), (int(0.853 * W), int(0.625 * H), 32), (int(0.796 * W), int(0.780 * H), 26)]:
        l_dist_sq = ((X_GRID - lx) ** 2 + (Y_GRID - ly) ** 2) / (rad ** 2)
        lantern_mask += np.clip(np.exp(-l_dist_sq), 0.0, 1.0)
    lantern_mask = np.clip(lantern_mask, 0.0, 1.0)

    glow_mist = make_glow_bgr(mist_mask, 7.0, 8.0, 8.0)
    glow_godray = make_glow_bgr(godray_mask, 2.0, 6.0, 9.0)
    glow_lantern = make_glow_bgr(lantern_mask, 3.0, 10.0, 16.0)

    # 6. Serene Momiji Leaves (16 drifting leaves)
    np.random.seed(909)
    leaf_sprites = []
    for s in [14, 16, 18, 20]:
        l_img = np.zeros((s, s), dtype=np.uint8)
        pts = np.array([
            [s * 0.50, s * 0.05], [s * 0.42, s * 0.25], [s * 0.20, s * 0.15],
            [s * 0.28, s * 0.40], [s * 0.08, s * 0.48], [s * 0.35, s * 0.65],
            [s * 0.48, s * 0.90], [s * 0.52, s * 0.90], [s * 0.65, s * 0.65],
            [s * 0.92, s * 0.48], [s * 0.72, s * 0.40], [s * 0.80, s * 0.15],
            [s * 0.58, s * 0.25]
        ], np.int32)
        cv2.fillPoly(l_img, [pts], 255)
        leaf_sprites.append(cv2.GaussianBlur(l_img, (3, 3), 0).astype(np.float32) / 255.0)

    leaf_colors = [(25, 40, 215), (20, 130, 245), (30, 85, 220), (15, 110, 235)]
    leaves = []
    for k in range(16):
        leaves.append({
            "x_start": np.random.uniform(0.12, 0.84) * W,
            "y_start": np.random.uniform(0.15, 0.72) * H,
            "fall_dist": np.random.uniform(32.0, 50.0),
            "sway_amp": np.random.uniform(14.0, 24.0),
            "phase_offset": np.random.uniform(0.0, 1.0),
            "base_angle": np.random.uniform(0.0, 360.0),
            "rot_amp": np.random.uniform(15.0, 30.0),
            "color": leaf_colors[k % len(leaf_colors)],
            "sprite": leaf_sprites[k % len(leaf_sprites)],
            "max_alpha": np.random.uniform(0.70, 0.88),
        })

    proc = open_nvenc(out_path, cq=cq)

    for i in range(NUM_FRAMES):
        prog = i / float(NUM_FRAMES)
        phase = 2.0 * np.pi * prog

        p_mist = float(np.sin(phase) * 0.5 + 0.5)
        p_godray = float(np.sin(phase) * 0.5 + 0.5)
        p_lantern = float(np.sin(phase * 2.0) * 0.5 + 0.5)
        base_lit = img_f + p_mist * glow_mist + p_godray * glow_godray + p_lantern * glow_lantern

        # Accurate Water Motion:
        fall_disp_y = np.sin(NY * 24.0 - phase * 3.0) * 1.5 * falls_mask
        lake_disp_x = np.cos(NX * 8.0 + phase) * 0.5 * lake_mask
        lake_disp_y = np.sin(NY * 6.0 + phase) * 0.4 * lake_mask

        remap_x = np.clip(X_GRID + lake_disp_x, 0, W - 1).astype(np.float32)
        remap_y = np.clip(Y_GRID + fall_disp_y + lake_disp_y, 0, H - 1).astype(np.float32)
        frame = cv2.remap(base_lit, remap_x, remap_y, interpolation=cv2.INTER_LINEAR).astype(np.float32)

        # Waterfall crystalline sparkle
        fall_sparkle = ((np.sin(NY * 28.0 - phase * 3.0) * 0.5 + 0.5) ** 1.5) * falls_mask * 14.0
        frame[:, :, 0] += fall_sparkle * 1.20
        frame[:, :, 1] += fall_sparkle * 1.10
        frame[:, :, 2] += fall_sparkle * 0.90

        # Emerald Lake sheen & caustics
        lake_sheen = ((np.sin(NX * 12.0 + NY * 8.0 + phase * 2.0) * 0.5 + 0.5) * lake_mask * 8.0)
        frame[:, :, 0] += lake_sheen * 0.8
        frame[:, :, 1] += lake_sheen * 1.2
        frame[:, :, 2] += lake_sheen * 0.6

        frame_u8 = np.clip(frame, 0, 255).astype(np.uint8)

        for leaf in leaves:
            l_prog = (prog + leaf["phase_offset"]) % 1.0
            alpha = float(np.sin(l_prog * np.pi) ** 2.0) * leaf["max_alpha"]
            if alpha < 0.01:
                continue
            cur_y = leaf["y_start"] + l_prog * leaf["fall_dist"]
            cur_x = leaf["x_start"] + np.sin(l_prog * 2.0 * np.pi) * leaf["sway_amp"]
            cur_angle = leaf["base_angle"] + np.cos(l_prog * 2.0 * np.pi) * leaf["rot_amp"]
            sprite = leaf["sprite"]
            sh, sw = sprite.shape
            M = cv2.getRotationMatrix2D((sw / 2, sh / 2), cur_angle, 1.0)
            rot_mask = cv2.warpAffine(sprite, M, (sw, sh), flags=cv2.INTER_LINEAR)
            ix, iy = int(round(cur_x)), int(round(cur_y))
            x1, y1 = max(0, ix - sw // 2), max(0, iy - sh // 2)
            x2, y2 = min(W, x1 + sw), min(H, y1 + sh)
            sx1, sy1 = x1 - (ix - sw // 2), y1 - (iy - sh // 2)
            sx2, sy2 = sx1 + (x2 - x1), sy1 + (y2 - y1)
            if x2 > x1 and y2 > y1 and sx2 > sx1 and sy2 > sy1:
                sub_mask = rot_mask[sy1:sy2, sx1:sx2] * alpha
                roi = frame_u8[y1:y2, x1:x2].astype(np.float32)
                color = np.array(leaf["color"], dtype=np.float32)
                for c in range(3):
                    roi[:, :, c] = roi[:, :, c] * (1.0 - sub_mask) + color[c] * sub_mask
                frame_u8[y1:y2, x1:x2] = np.clip(roi, 0, 255).astype(np.uint8)

        proc.stdin.write(frame_u8.tobytes())

    finish_nvenc(proc, "Realm 09", t0, out_path)
    return out_path


# ==============================================================================
def render_10_starfall(cq=15):
    print("\n[10/11] Rendering Realm 10: Celestial Starfall Observatory...", flush=True)
    t0 = time.time()
    img = load_master("10_celestial_starfall_spire_4k.jpg")
    out_path = os.path.join(OUT_DIR, "10_celestial_starfall_spire_live.mp4")
    img_f = img.astype(np.float32)

    in_mountain_or_spire = (
        (NY >= 0.46)
        | ((NX <= 0.16) & (NY >= 0.32))
        | ((NX >= 0.38) & (NX <= 0.78) & (NY >= 0.25))
    )
    sky_safe_mask = cv2.GaussianBlur((~in_mountain_or_spire).astype(np.float32), (25, 25), 0)

    gy1 = int(0.47 * H)
    gx1 = int(0.50 * W)
    g_crop = img[:gy1, :gx1]
    gal_cx, gal_cy = W * 0.295, H * 0.235
    dx_gal = X_GRID[:gy1, :gx1] - gal_cx
    dy_gal = Y_GRID[:gy1, :gx1] - gal_cy
    r_gal = np.sqrt(dx_gal ** 2 + dy_gal ** 2)
    angle_gal = np.arctan2(dy_gal, dx_gal)
    gal_norm = np.clip(r_gal / (W * 0.19), 0.0, 1.0)
    swirl_weight = (((1.0 - gal_norm) ** 2.2) * sky_safe_mask[:gy1, :gx1]).astype(np.float32)

    gal_glow_full = (np.exp(-(((X_GRID - gal_cx) ** 2 + (Y_GRID - gal_cy) ** 2) / ((W * 0.15) ** 2))) * sky_safe_mask).astype(np.float32)
    r_arm = np.sqrt((X_GRID - W * 0.658) ** 2 + (Y_GRID - H * 0.183) ** 2)
    sun_core_mask = np.exp(-((r_arm / (W * 0.045)) ** 2)).astype(np.float32)

    b, g, r = cv2.split(img_f)
    is_obs_win = (NY >= 0.42) & (NY <= 0.88) & (NX >= 0.36) & (NX <= 0.65) & (r > 165) & (g > 100) & (b < 90)
    obs_win_mask = cv2.GaussianBlur(is_obs_win.astype(np.float32), (7, 7), 0)

    glow_1x = make_glow_bgr(gal_glow_full, 18.0, 5.0, 13.0)
    glow_2x = make_glow_bgr(sun_core_mask, 3.0, 19.5, 27.0) + make_glow_bgr(obs_win_mask, 2.0, 12.5, 19.5)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    angle_rad = np.radians(140.0)
    dir_x, dir_y = float(np.cos(angle_rad)), float(np.sin(angle_rad))
    k_len = 25
    k_streak = np.zeros((k_len, k_len), dtype=np.float32)
    for ki in range(k_len):
        kj = int((k_len - 1 - ki) * 0.84)
        if 0 <= kj < k_len:
            k_streak[ki, kj] = 1.0
    k_streak /= np.sum(k_streak)
    streak_filtered = cv2.filter2D(gray, cv2.CV_32F, k_streak)
    bg_blur = cv2.blur(gray, (21, 21)).astype(np.float32)
    raw_streak_mask = np.clip((streak_filtered - bg_blur) / 22.0, 0.0, 1.0)
    sky_only_streaks = np.clip((0.46 - NY) / 0.05, 0.0, 1.0)
    streak_mask = (raw_streak_mask * sky_only_streaks).astype(np.float32)

    _, streak_thresh = cv2.threshold((streak_mask * 255).astype(np.uint8), 75, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(streak_thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    anchored = []
    for c in contours:
        if cv2.contourArea(c) > 20:
            (rcx, rcy), (d1, d2), _ = cv2.minAreaRect(c)
            length, width = max(d1, d2), min(d1, d2)
            if length > 28 and (length / (width + 1e-3)) > 2.2:
                anchored.append((rcx, rcy, length))
    anchored.sort(key=lambda s: s[2], reverse=True)

    bolides = []
    n_bolides = min(10, len(anchored))
    for idx, (scx, scy, slen) in enumerate(anchored[:n_bolides]):
        bolides.append({
            "start_t": idx / float(n_bolides),
            "life_dur": 0.25,
            "anchor_x": scx,
            "anchor_y": scy,
            "trail_len": max(slen * 1.35, 115.0),
            "color": (255, 248, 230) if idx % 2 == 0 else (255, 235, 255),
            "bloom_color": (255, 190, 100) if idx % 2 == 0 else (210, 140, 255),
        })

    # Ambient stardust around observatory spire
    np.random.seed(1010)
    n_dust = 45
    dx0 = np.random.uniform(0.35, 0.70, n_dust) * W
    dy0 = np.random.uniform(0.25, 0.65, n_dust) * H
    d_rise = np.random.uniform(35.0, 75.0, n_dust)
    d_sway = np.random.uniform(8.0, 18.0, n_dust)
    d_off = np.random.uniform(0.0, 1.0, n_dust)
    d_rad = np.random.uniform(1.2, 2.2, n_dust)
    d_alpha = np.random.uniform(0.40, 0.80, n_dust)

    proc = open_nvenc(out_path, cq=cq)
    for i in range(NUM_FRAMES):
        prog = i / float(NUM_FRAMES)
        phase = 2.0 * np.pi * prog
        sin_p = float(np.sin(phase))
        p1 = sin_p * 0.5 + 0.5
        p2 = float(np.sin(phase * 2.0) * 0.5 + 0.5)

        frame = img_f.copy()
        swirl_angle = 0.032 * sin_p * swirl_weight
        new_angle = angle_gal + swirl_angle
        map_x = (gal_cx + r_gal * np.cos(new_angle)).astype(np.float32)
        map_y = (gal_cy + r_gal * np.sin(new_angle)).astype(np.float32)
        frame[:gy1, :gx1] = cv2.remap(g_crop, map_x, map_y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT).astype(np.float32)

        frame += p1 * glow_1x + p2 * glow_2x
        frame_u8 = np.clip(frame, 0, 255).astype(np.uint8)

        # Draw ambient spire stardust
        p_prog = (prog + d_off) % 1.0
        p_a = (np.sin(p_prog * np.pi) ** 1.5) * d_alpha
        draw_soft_particles(frame_u8, dx0 + np.sin(p_prog * 2.0 * np.pi) * d_sway, dy0 - p_prog * d_rise, d_rad, (240, 220, 255), p_a)

        # Draw dynamic bolides
        bloom_layer = np.zeros_like(frame_u8)
        for bol in bolides:
            t_rel = (prog - bol["start_t"]) % 1.0
            if t_rel < bol["life_dur"]:
                b_prog = t_rel / bol["life_dur"]
                dist = (b_prog - 0.5) * (bol["trail_len"] * 1.8)
                hx = int(bol["anchor_x"] + dir_x * dist)
                hy = int(bol["anchor_y"] + dir_y * dist)
                cur_trail = bol["trail_len"] * np.sin(b_prog * np.pi)
                tx = int(hx - dir_x * cur_trail)
                ty = int(hy - dir_y * cur_trail)
                alpha = float(np.sin(b_prog * np.pi) ** 1.5)
                b_val = int(165 * alpha)
                b_col = tuple(int(c * (b_val / 255.0)) for c in bol["bloom_color"])
                cv2.line(bloom_layer, (tx, ty), (hx, hy), b_col, 3, lineType=cv2.LINE_AA)
                cv2.circle(bloom_layer, (hx, hy), 3, b_col, -1, lineType=cv2.LINE_AA)
                c_val = int(245 * alpha)
                c_col = tuple(int(c * (c_val / 255.0)) for c in bol["color"])
                cv2.line(frame_u8, (tx, ty), (hx, hy), c_col, 2, lineType=cv2.LINE_AA)
                cv2.circle(frame_u8, (hx, hy), 2, (c_val, c_val, c_val), -1, lineType=cv2.LINE_AA)

        cv2.add(frame_u8, bloom_layer, dst=frame_u8)
        proc.stdin.write(frame_u8.tobytes())

    finish_nvenc(proc, "Realm 10", t0, out_path)
    return out_path


# ==============================================================================
# REALM 11: Ethereal Dreamscript Nexus (Zero Bridge Warp + Rolling Cloud Ocean)
# ==============================================================================
def render_11_dreamscript(cq=14):
    print("\n[11/11] Rendering Realm 11: Ethereal Dreamscript Nexus...", flush=True)
    t0 = time.time()
    img = load_master("11_ethereal_dreamscript_4k.jpg")
    out_path = os.path.join(OUT_DIR, "11_ethereal_dreamscript_live.mp4")
    img_f = img.astype(np.float32)
    b, g, r = cv2.split(img_f)
    lum = (b + g + r) / 3.0

    is_cyan_crystal = (b > 140) & (g > 140) & (b > r * 1.1) & (lum > 130)
    is_violet_crystal = (b > 120) & (r > 120) & (b > g * 1.15) & (r > g * 1.1)
    cyan_mask = cv2.GaussianBlur(is_cyan_crystal.astype(np.float32), (9, 9), 0)
    violet_mask = cv2.GaussianBlur(is_violet_crystal.astype(np.float32), (9, 9), 0)

    in_zodiac = (NX >= 0.18) & (NX <= 0.72) & (NY >= 0.03) & (NY <= 0.42)
    is_gold = (r > 115) & (g > 95) & (r > b * 1.20) & in_zodiac
    zodiac_mask = cv2.GaussianBlur(is_gold.astype(np.float32), (11, 11), 0)

    in_ribbon = (NY >= 0.02) & (NY <= 0.46) & (lum > 80) & (b > 105)
    ribbon_mask = cv2.GaussianBlur(in_ribbon.astype(np.float32), (21, 21), 0)

    glow_cyan = make_glow_bgr(cyan_mask, 19.0, 16.0, 3.0) + make_glow_bgr(ribbon_mask, 11.0, 3.5, 7.5)
    glow_violet = make_glow_bgr(violet_mask, 15.0, 3.0, 17.0)
    glow_zodiac = make_glow_bgr(zodiac_mask, 3.0, 13.0, 19.0)

    cy0 = int(0.52 * H)
    in_left_clouds = (NX[cy0:, :] >= 0.09) & (NX[cy0:, :] <= 0.34) & (NY[cy0:, :] >= 0.54) & (NY[cy0:, :] <= 0.78) & (NY[cy0:, :] < (0.92 - NX[cy0:, :] * 0.65))
    in_lower_clouds = (NX[cy0:, :] >= 0.46) & (NX[cy0:, :] <= 0.68) & (NY[cy0:, :] >= 0.80) & (NY[cy0:, :] <= 0.96)
    cm_crop = cv2.GaussianBlur((in_left_clouds | in_lower_clouds).astype(np.float32), (35, 35), 0)
    c_crop = img[cy0:, :]
    xg_crop, yg_crop = np.meshgrid(np.arange(W, dtype=np.float32), np.arange(H - cy0, dtype=np.float32))

    np.random.seed(1111)
    n_dust = 70
    dx0 = np.random.uniform(0.08, 0.92, n_dust) * W
    dy0 = np.random.uniform(0.22, 0.94, n_dust) * H
    d_rise = np.random.uniform(60.0, 130.0, n_dust)
    d_sway = np.random.uniform(12.0, 25.0, n_dust)
    d_off = np.random.uniform(0.0, 1.0, n_dust)
    d_rad = np.random.uniform(1.3, 2.5, n_dust)
    d_alpha = np.random.uniform(0.48, 0.88, n_dust)

    proc = open_nvenc(out_path, cq=cq)
    num_cycles = 6
    cycle_w = 16.0

    for i in range(NUM_FRAMES):
        prog = i / float(NUM_FRAMES)
        phase = 2.0 * np.pi * prog
        t1 = (prog * num_cycles) % 1.0
        t2 = (t1 + 0.5) % 1.0
        w_blend = float(np.sin(t1 * np.pi) ** 2.0)

        p_cyan = float(np.sin(phase) * 0.5 + 0.5)
        p_viol = float(np.cos(phase) * 0.5 + 0.5)
        p_zod = float(np.sin(phase * 2.0) * 0.5 + 0.5)

        frame = img_f.copy()
        dx1 = (t1 - 0.5) * cycle_w * cm_crop
        dx2 = (t2 - 0.5) * cycle_w * cm_crop
        f1 = cv2.remap(c_crop, xg_crop - dx1, yg_crop, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT).astype(np.float32)
        f2 = cv2.remap(c_crop, xg_crop - dx2, yg_crop, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT).astype(np.float32)
        frame[cy0:, :] = f1 * w_blend + f2 * (1.0 - w_blend)
        frame += p_cyan * glow_cyan + p_viol * glow_violet + p_zod * glow_zodiac

        frame_u8 = np.clip(frame, 0, 255).astype(np.uint8)
        p_prog = (prog + d_off) % 1.0
        p_a = (np.sin(p_prog * np.pi) ** 1.5) * d_alpha
        px = dx0 + np.sin(p_prog * 2.0 * np.pi) * d_sway
        py = dy0 - p_prog * d_rise
        draw_soft_particles(frame_u8, px[:35], py[:35], d_rad[:35], (255, 225, 130), p_a[:35])
        draw_soft_particles(frame_u8, px[35:], py[35:], d_rad[35:], (250, 175, 225), p_a[35:])
        proc.stdin.write(frame_u8.tobytes())

    finish_nvenc(proc, "Realm 11", t0, out_path)
    return out_path



# ==============================================================================
# REALM 12: Celestial Titan Dunes (Forgotten Colossus & Glowing Oasis)
# ==============================================================================
def render_12_titan_dunes(cq=15):
    print("\n[12/16] Rendering Realm 12: Celestial Titan Dunes...", flush=True)
    t0 = time.time()
    img = load_master("12_celestial_dunes_titan_4k.jpg")
    out_path = os.path.join(OUT_DIR, "12_celestial_dunes_titan_live.mp4")
    img_f = img.astype(np.float32)
    b, g, r = cv2.split(img_f)

    # 1. Turquoise Oasis Pool
    in_pool_box = (NY >= 0.55) & (NY <= 0.88) & (NX >= 0.20) & (NX <= 0.80)
    is_pool = in_pool_box & (b > 60) & (g > r * 0.95) & (b > r * 1.05)
    pool_u8 = cv2.morphologyEx(is_pool.astype(np.uint8) * 255, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7)))
    pool_mask = cv2.GaussianBlur(pool_u8.astype(np.float32) / 255.0, (15, 15), 0)

    # 2. Glowing Titan Runes (Hieroglyphics on stone colossus & obelisks)
    is_runes = (r > 150) & (g > 130) & (b < 100) & (NY >= 0.15) & (NY <= 0.65)
    rune_mask = cv2.GaussianBlur(is_runes.astype(np.float32), (7, 7), 0)
    rune_glow = make_glow_bgr(rune_mask, 3.0, 16.0, 24.0)

    # 3. Celestial Aurora & Twin Moons Sky
    is_sky = (NY <= 0.40) & ((b > 90) | (r > 120))
    sky_mask = cv2.GaussianBlur(is_sky.astype(np.float32), (31, 31), 0)
    sky_glow = make_glow_bgr(sky_mask, 8.0, 4.0, 7.0)

    # 4. Floating Stardust Particles
    np.random.seed(1212)
    n_dust = 60
    dx0 = np.random.uniform(0.15, 0.85, n_dust) * W
    dy0 = np.random.uniform(0.35, 0.88, n_dust) * H
    d_rise = np.random.uniform(40.0, 85.0, n_dust)
    d_sway = np.random.uniform(10.0, 22.0, n_dust)
    d_off = np.random.uniform(0.0, 1.0, n_dust)
    d_rad = np.random.uniform(1.3, 2.4, n_dust)
    d_alpha = np.random.uniform(0.45, 0.85, n_dust)

    proc = open_nvenc(out_path, cq=cq)

    for i in range(NUM_FRAMES):
        prog = i / float(NUM_FRAMES)
        phase = 2.0 * np.pi * prog

        p_rune = float(np.sin(phase * 2.0) * 0.5 + 0.5)
        p_sky = float(np.sin(phase) * 0.5 + 0.5)
        base_frame = img_f + p_rune * rune_glow + p_sky * sky_glow

        lake_disp_x = np.sin(NX * 12.0 + phase * 2.0) * 0.5 * pool_mask
        lake_disp_y = np.cos(NY * 8.0 + phase * 2.0) * 0.4 * pool_mask
        remap_x = np.clip(X_GRID + lake_disp_x, 0, W - 1).astype(np.float32)
        remap_y = np.clip(Y_GRID + lake_disp_y, 0, H - 1).astype(np.float32)
        frame = cv2.remap(base_frame, remap_x, remap_y, interpolation=cv2.INTER_LINEAR).astype(np.float32)

        caust = ((np.sin(NX * 18.0 + NY * 12.0 - phase * 2.0) * 0.5 + 0.5) * pool_mask * 12.0)
        frame[:, :, 0] += caust * 1.25
        frame[:, :, 1] += caust * 1.15
        frame[:, :, 2] += caust * 0.70

        frame_u8 = np.clip(frame, 0, 255).astype(np.uint8)

        p_prog = (prog + d_off) % 1.0
        p_a = (np.sin(p_prog * np.pi) ** 1.5) * d_alpha
        px = dx0 + np.sin(p_prog * 2.0 * np.pi) * d_sway
        py = dy0 - p_prog * d_rise
        draw_soft_particles(frame_u8, px[:30], py[:30], d_rad[:30], (100, 220, 255), p_a[:30])
        draw_soft_particles(frame_u8, px[30:], py[30:], d_rad[30:], (255, 220, 130), p_a[30:])

        proc.stdin.write(frame_u8.tobytes())

    finish_nvenc(proc, "Realm 12", t0, out_path)
    return out_path


# ==============================================================================
# REALM 13: Octopath Traveler HD-2D Coastal Citadel
# ==============================================================================
def render_13_octopath(cq=15):
    print("\n[13/16] Rendering Realm 13: Octopath HD-2D Harbor Citadel...", flush=True)
    t0 = time.time()
    img = load_master("13_octopath_hd2d_coastal_citadel_4k.jpg")
    out_path = os.path.join(OUT_DIR, "13_octopath_hd2d_coastal_citadel_live.mp4")
    img_f = img.astype(np.float32)
    b, g, r = cv2.split(img_f)

    # 1. Sapphire Harbor Ocean Waves
    is_sea = (NY >= 0.65) & (b > 65) & (b > r * 1.08)
    sea_u8 = cv2.morphologyEx(is_sea.astype(np.uint8) * 255, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7)))
    sea_mask = cv2.GaussianBlur(sea_u8.astype(np.float32) / 255.0, (15, 15), 0)

    # 2. Amber Gas Lamps & Paper Lanterns
    is_lamps = (r > 175) & (g > 125) & (b < 95)
    lamp_mask = cv2.GaussianBlur(is_lamps.astype(np.float32), (9, 9), 0)
    lamp_glow = make_glow_bgr(lamp_mask, 3.0, 14.0, 20.0)

    # 3. Stained Glass Windows & Library Glow
    is_windows = (r > 140) & (g > 110) & (b < 90) & (NY >= 0.25) & (NY <= 0.55) & (NX >= 0.35) & (NX <= 0.65)
    win_mask = cv2.GaussianBlur(is_windows.astype(np.float32), (13, 13), 0)
    win_glow = make_glow_bgr(win_mask, 2.0, 9.0, 15.0)

    # 4. HD-2D Floating Luminous Motes (Golden essence)
    np.random.seed(1313)
    n_motes = 50
    mx0 = np.random.uniform(0.10, 0.90, n_motes) * W
    my0 = np.random.uniform(0.25, 0.85, n_motes) * H
    m_rise = np.random.uniform(35.0, 75.0, n_motes)
    m_sway = np.random.uniform(12.0, 25.0, n_motes)
    m_off = np.random.uniform(0.0, 1.0, n_motes)
    m_rad = np.random.uniform(1.2, 2.3, n_motes)
    m_alpha = np.random.uniform(0.40, 0.85, n_motes)

    proc = open_nvenc(out_path, cq=cq)

    for i in range(NUM_FRAMES):
        prog = i / float(NUM_FRAMES)
        phase = 2.0 * np.pi * prog

        p_lamp = float((np.sin(phase * 3.0) * 0.3 + np.sin(phase * 4.0) * 0.2 + 0.5))
        p_win = float(np.sin(phase * 2.0) * 0.5 + 0.5)
        base_frame = img_f + p_lamp * lamp_glow + p_win * win_glow

        sea_disp_x = np.sin(NX * 8.0 - phase * 2.0) * 0.7 * sea_mask
        sea_disp_y = np.cos(NY * 10.0 + phase) * 0.5 * sea_mask
        remap_x = np.clip(X_GRID + sea_disp_x, 0, W - 1).astype(np.float32)
        remap_y = np.clip(Y_GRID + sea_disp_y, 0, H - 1).astype(np.float32)
        frame = cv2.remap(base_frame, remap_x, remap_y, interpolation=cv2.INTER_LINEAR).astype(np.float32)

        caust = ((np.sin(NX * 14.0 - phase * 2.0 + NY * 8.0) * 0.5 + 0.5) * sea_mask * 10.0)
        frame[:, :, 0] += caust * 1.30
        frame[:, :, 1] += caust * 1.10
        frame[:, :, 2] += caust * 0.75

        frame_u8 = np.clip(frame, 0, 255).astype(np.uint8)

        p_prog = (prog + m_off) % 1.0
        p_a = (np.sin(p_prog * np.pi) ** 1.5) * m_alpha
        px = mx0 + np.sin(p_prog * 2.0 * np.pi) * m_sway
        py = my0 - p_prog * m_rise
        draw_soft_particles(frame_u8, px, py, m_rad, (255, 215, 120), p_a)

        proc.stdin.write(frame_u8.tobytes())

    finish_nvenc(proc, "Realm 13", t0, out_path)
    return out_path


# ==============================================================================
# REALM 14: Final Fantasy VII Rebirth Cosmo Canyon & Mako Veil
# ==============================================================================
def render_14_ffvii_cosmo(cq=15):
    print("\n[14/16] Rendering Realm 14: FFVII Rebirth Cosmo Canyon...", flush=True)
    t0 = time.time()
    img = load_master("14_ffvii_rebirth_cosmo_canyon_mako_4k.jpg")
    out_path = os.path.join(OUT_DIR, "14_ffvii_rebirth_cosmo_canyon_mako_live.mp4")
    img_f = img.astype(np.float32)
    b, g, r = cv2.split(img_f)

    # 1. Emerald Mako / Lifestream Veil Mask
    is_mako = (g > 105) & (g > r * 1.12) & (g > b * 0.92)
    mako_u8 = cv2.morphologyEx(is_mako.astype(np.uint8) * 255, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
    mako_mask = cv2.GaussianBlur(mako_u8.astype(np.float32) / 255.0, (13, 13), 0)
    mako_glow = make_glow_bgr(mako_mask, 16.0, 26.0, 4.0)

    # 2. Ritual Torches & Braziers
    is_torches = (r > 185) & (g > 95) & (b < 80)
    torch_mask = cv2.GaussianBlur(is_torches.astype(np.float32), (9, 9), 0)
    torch_glow = make_glow_bgr(torch_mask, 2.0, 12.0, 24.0)

    # 3. Rising Fiery Embers & Mako Wisps
    np.random.seed(1414)
    n_embers = 65
    ex0 = np.random.uniform(0.15, 0.85, n_embers) * W
    ey0 = np.random.uniform(0.40, 0.92, n_embers) * H
    e_rise = np.random.uniform(60.0, 140.0, n_embers)
    e_sway = np.random.uniform(14.0, 28.0, n_embers)
    e_off = np.random.uniform(0.0, 1.0, n_embers)
    e_rad = np.random.uniform(1.2, 2.2, n_embers)
    e_alpha = np.random.uniform(0.50, 0.90, n_embers)

    proc = open_nvenc(out_path, cq=cq)

    for i in range(NUM_FRAMES):
        prog = i / float(NUM_FRAMES)
        phase = 2.0 * np.pi * prog

        p_mako = float(np.sin(phase * 2.0) * 0.5 + 0.5)
        p_torch = float(np.sin(phase * 4.0) * 0.3 + np.cos(phase * 2.0) * 0.2 + 0.5)
        base_frame = img_f + p_mako * mako_glow + p_torch * torch_glow

        mako_disp_y = -np.sin(NY * 16.0 + phase * 3.0) * 1.2 * mako_mask
        mako_disp_x = np.cos(NX * 10.0 + phase * 2.0) * 0.6 * mako_mask
        remap_x = np.clip(X_GRID + mako_disp_x, 0, W - 1).astype(np.float32)
        remap_y = np.clip(Y_GRID + mako_disp_y, 0, H - 1).astype(np.float32)
        frame = cv2.remap(base_frame, remap_x, remap_y, interpolation=cv2.INTER_LINEAR).astype(np.float32)

        mako_shimmer = ((np.sin(NY * 24.0 + phase * 3.0) * 0.5 + 0.5) * mako_mask * 15.0)
        frame[:, :, 0] += mako_shimmer * 0.9
        frame[:, :, 1] += mako_shimmer * 1.4
        frame[:, :, 2] += mako_shimmer * 0.2

        frame_u8 = np.clip(frame, 0, 255).astype(np.uint8)

        p_prog = (prog + e_off) % 1.0
        p_a = (np.sin(p_prog * np.pi) ** 1.5) * e_alpha
        px = ex0 + np.sin(p_prog * 2.0 * np.pi) * e_sway
        py = ey0 - p_prog * e_rise
        draw_soft_particles(frame_u8, px[:35], py[:35], e_rad[:35], (40, 160, 255), p_a[:35])
        draw_soft_particles(frame_u8, px[35:], py[35:], e_rad[35:], (120, 255, 140), p_a[35:])

        proc.stdin.write(frame_u8.tobytes())

    finish_nvenc(proc, "Realm 14", t0, out_path)
    return out_path


# ==============================================================================
# REALM 15: Studio Ghibli Overgrown Watermill Sanctuary
# ==============================================================================
def render_15_ghibli_watermill(cq=15):
    print("\n[15/16] Rendering Realm 15: Ghibli Watermill Sanctuary...", flush=True)
    t0 = time.time()
    img = load_master("15_ghibli_overgrown_sanctuary_4k.jpg")
    out_path = os.path.join(OUT_DIR, "15_ghibli_overgrown_sanctuary_live.mp4")
    img_f = img.astype(np.float32)
    b, g, r = cv2.split(img_f)

    # 1. Winding Brook Stream Mask
    is_stream = (NY >= 0.52) & (b > 70) & (b >= r * 0.92) & (g >= r * 0.92) & (NX >= 0.20) & (NX <= 0.85)
    stream_u8 = cv2.morphologyEx(is_stream.astype(np.uint8) * 255, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7)))
    stream_mask = cv2.GaussianBlur(stream_u8.astype(np.float32) / 255.0, (11, 11), 0)

    # 2. Meadow & Wildflower Grass
    is_meadow = (NY >= 0.48) & (g > r * 1.1) & (g > b * 1.1) & (~is_stream)
    meadow_mask = cv2.GaussianBlur(is_meadow.astype(np.float32), (21, 21), 0)

    # 3. Summer Godrays through Tree
    is_rays = (NY <= 0.45) & (NX <= 0.55) & (r > 160) & (g > 160)
    ray_mask = cv2.GaussianBlur(is_rays.astype(np.float32), (31, 31), 0)
    ray_glow = make_glow_bgr(ray_mask, 3.0, 9.0, 14.0)

    # 4. Floating Dandelion Fluff & Pollen
    np.random.seed(1515)
    n_seeds = 45
    sx0 = np.random.uniform(0.10, 0.90, n_seeds) * W
    sy0 = np.random.uniform(0.20, 0.85, n_seeds) * H
    s_drift = np.random.uniform(30.0, 70.0, n_seeds)
    s_sway = np.random.uniform(15.0, 30.0, n_seeds)
    s_off = np.random.uniform(0.0, 1.0, n_seeds)
    s_rad = np.random.uniform(1.2, 2.0, n_seeds)
    s_alpha = np.random.uniform(0.40, 0.80, n_seeds)

    proc = open_nvenc(out_path, cq=cq)

    for i in range(NUM_FRAMES):
        prog = i / float(NUM_FRAMES)
        phase = 2.0 * np.pi * prog

        p_ray = float(np.sin(phase) * 0.5 + 0.5)
        base_frame = img_f + p_ray * ray_glow

        stream_disp_y = np.sin(NY * 18.0 - phase * 3.0) * 1.2 * stream_mask
        stream_disp_x = np.cos(NX * 12.0 + phase * 2.0) * 0.6 * stream_mask
        meadow_disp_x = np.sin(NX * 8.0 + phase * 2.0) * 0.5 * meadow_mask

        remap_x = np.clip(X_GRID + stream_disp_x + meadow_disp_x, 0, W - 1).astype(np.float32)
        remap_y = np.clip(Y_GRID + stream_disp_y, 0, H - 1).astype(np.float32)
        frame = cv2.remap(base_frame, remap_x, remap_y, interpolation=cv2.INTER_LINEAR).astype(np.float32)

        stream_glint = ((np.sin(NY * 22.0 - phase * 3.0) * 0.5 + 0.5) * stream_mask * 11.0)
        frame[:, :, 0] += stream_glint * 1.25
        frame[:, :, 1] += stream_glint * 1.15
        frame[:, :, 2] += stream_glint * 0.85

        frame_u8 = np.clip(frame, 0, 255).astype(np.uint8)

        p_prog = (prog + s_off) % 1.0
        p_a = (np.sin(p_prog * np.pi) ** 1.5) * s_alpha
        px = sx0 + np.sin(p_prog * 2.0 * np.pi) * s_sway + p_prog * 25.0
        py = sy0 - p_prog * s_drift
        draw_soft_particles(frame_u8, px, py, s_rad, (240, 250, 255), p_a)

        proc.stdin.write(frame_u8.tobytes())

    finish_nvenc(proc, "Realm 15", t0, out_path)
    return out_path


# ==============================================================================
# REALM 16: The Sleeping Titan (Fallen Gundam Relic Overgrown by Nature)
# ==============================================================================
def render_16_gundam_relic(cq=15):
    print("\n[16/16] Rendering Realm 16: The Sleeping Titan Gundam Relic...", flush=True)
    t0 = time.time()
    img = load_master("16_gundam_relic_overgrown_meadow_4k.jpg")
    out_path = os.path.join(OUT_DIR, "16_gundam_relic_overgrown_meadow_live.mp4")
    img_f = img.astype(np.float32)
    b, g, r = cv2.split(img_f)

    # 1. Cliffside Waterfall Cascade (Behind Gundam's shoulder)
    is_waterfall = (NX <= 0.42) & (NY >= 0.20) & (NY <= 0.80) & (b > 85) & (b >= r * 0.88)
    wf_u8 = cv2.morphologyEx(is_waterfall.astype(np.uint8) * 255, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 7)))
    wf_mask = cv2.GaussianBlur(wf_u8.astype(np.float32) / 255.0, (7, 11), 0)

    # 2. Reflective Lily Pond (Base)
    is_pool = (NY >= 0.70) & (NX <= 0.55) & (b > 65) & (g > 65)
    pool_u8 = cv2.morphologyEx(is_pool.astype(np.uint8) * 255, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7)))
    pool_mask = cv2.GaussianBlur(pool_u8.astype(np.float32) / 255.0, (15, 15), 0)

    # 3. Morning Sunbeams / Crepuscular Godrays
    is_rays = (NY <= 0.50) & (r > 150) & (g > 150)
    ray_mask = cv2.GaussianBlur(is_rays.astype(np.float32), (31, 31), 0)
    ray_glow = make_glow_bgr(ray_mask, 3.0, 9.0, 15.0)

    # 4. Valley Floating Pollen / Dandelion Motes
    np.random.seed(1616)
    n_motes = 50
    mx0 = np.random.uniform(0.10, 0.90, n_motes) * W
    my0 = np.random.uniform(0.20, 0.88, n_motes) * H
    m_drift = np.random.uniform(35.0, 80.0, n_motes)
    m_sway = np.random.uniform(12.0, 24.0, n_motes)
    m_off = np.random.uniform(0.0, 1.0, n_motes)
    m_rad = np.random.uniform(1.2, 2.2, n_motes)
    m_alpha = np.random.uniform(0.40, 0.85, n_motes)

    proc = open_nvenc(out_path, cq=cq)

    for i in range(NUM_FRAMES):
        prog = i / float(NUM_FRAMES)
        phase = 2.0 * np.pi * prog

        p_ray = float(np.sin(phase) * 0.5 + 0.5)
        base_frame = img_f + p_ray * ray_glow

        wf_disp_y = np.sin(NY * 24.0 - phase * 3.0) * 1.5 * wf_mask
        pool_disp_x = np.sin(NX * 10.0 + phase) * 0.5 * pool_mask
        pool_disp_y = np.cos(NY * 8.0 + phase) * 0.4 * pool_mask

        remap_x = np.clip(X_GRID + pool_disp_x, 0, W - 1).astype(np.float32)
        remap_y = np.clip(Y_GRID + wf_disp_y + pool_disp_y, 0, H - 1).astype(np.float32)
        frame = cv2.remap(base_frame, remap_x, remap_y, interpolation=cv2.INTER_LINEAR).astype(np.float32)

        wf_sparkle = ((np.sin(NY * 28.0 - phase * 3.0) * 0.5 + 0.5) ** 1.5) * wf_mask * 13.0
        frame[:, :, 0] += wf_sparkle * 1.25
        frame[:, :, 1] += wf_sparkle * 1.15
        frame[:, :, 2] += wf_sparkle * 0.90

        pool_sheen = ((np.sin(NX * 12.0 + phase * 2.0) * 0.5 + 0.5) * pool_mask * 8.0)
        frame[:, :, 0] += pool_sheen * 0.9
        frame[:, :, 1] += pool_sheen * 1.2
        frame[:, :, 2] += pool_sheen * 0.7

        frame_u8 = np.clip(frame, 0, 255).astype(np.uint8)

        p_prog = (prog + m_off) % 1.0
        p_a = (np.sin(p_prog * np.pi) ** 1.5) * m_alpha
        px = mx0 + np.sin(p_prog * 2.0 * np.pi) * m_sway
        py = my0 - p_prog * m_drift
        draw_soft_particles(frame_u8, px, py, m_rad, (220, 245, 255), p_a)

        proc.stdin.write(frame_u8.tobytes())

    finish_nvenc(proc, "Realm 16", t0, out_path)
    return out_path



def render_17_wanzer_relic(cq=15):
    print("\n[17/18] Rendering Realm 17: Front Mission 5: Wanzer Battle Relic...", flush=True)
    t0 = time.time()
    img = load_master("17_front_mission_wanzer_relic_4k.jpg")
    out_path = os.path.join(OUT_DIR, "17_front_mission_wanzer_relic_live.mp4")
    img_f = img.astype(np.float32)
    b, g, r = cv2.split(img_f)

    # 1. Cockpit HUD screen & interior blue ambient glow
    is_cockpit = (NX >= 0.25) & (NX <= 0.58) & (NY >= 0.18) & (NY <= 0.48) & (b > 130) & (b > r * 1.25)
    cockpit_mask = cv2.GaussianBlur(is_cockpit.astype(np.float32), (15, 15), 0)
    glow_cockpit = make_glow_bgr(cockpit_mask, 28.0, 18.0, 4.0)

    # 2. Joint Short Circuit Sparks & Electric Arcs
    is_sparks = (NX >= 0.28) & (NX <= 0.60) & (NY >= 0.28) & (NY <= 0.50) & (((r > 180) & (g > 130) & (b < 140)) | ((b > 220) & (g > 210)))
    sparks_mask = cv2.GaussianBlur(is_sparks.astype(np.float32), (7, 7), 0)
    glow_sparks = make_glow_bgr(sparks_mask, 35.0, 30.0, 24.0)
    glow_sparks_ambient = make_glow_bgr(cv2.GaussianBlur(sparks_mask, (25, 25), 0), 12.0, 10.0, 6.0)

    # 3. Ground Puddles (Remapping & Specular Gleam)
    is_puddle = (NY >= 0.66) & (NX >= 0.10) & (NX <= 0.90) & (b > 45) & (b >= r * 0.9)
    puddle_mask = cv2.GaussianBlur(is_puddle.astype(np.float32), (21, 21), 0)

    # 4. Drifting Heat / Electrical Sparks Motes
    np.random.seed(1717)
    n_sparks = 36
    sx0 = np.random.uniform(0.30, 0.58, n_sparks) * W
    sy0 = np.random.uniform(0.30, 0.50, n_sparks) * H
    s_drift = np.random.uniform(30.0, 65.0, n_sparks)
    s_sway = np.random.uniform(10.0, 25.0, n_sparks)
    s_off = np.random.uniform(0.0, 1.0, n_sparks)
    s_rad = np.random.uniform(1.0, 2.2, n_sparks)
    s_alpha = np.random.uniform(0.50, 0.95, n_sparks)

    proc = open_nvenc(out_path, cq=cq)

    for i in range(NUM_FRAMES):
        prog = i / float(NUM_FRAMES)
        phase = 2.0 * np.pi * prog

        p_cockpit = float(np.sin(phase * 4.0) * 0.15 + np.sin(phase * 8.0) * 0.05 + 1.0)

        # Stochastic harmonic spark bursts
        spark_spike1 = float(max(0.0, np.sin(phase * 4.0)) ** 12.0) * 1.6
        spark_spike2 = float(max(0.0, np.sin(phase * 6.0 + 1.5)) ** 14.0) * 1.3
        spark_spike3 = float(max(0.0, np.cos(phase * 8.0 + 3.0)) ** 16.0) * 2.0
        spark_intensity = spark_spike1 + spark_spike2 + spark_spike3

        base_frame = img_f + (p_cockpit * glow_cockpit) + (spark_intensity * (glow_sparks + glow_sparks_ambient))

        puddle_disp_x = np.sin(NX * 16.0 + phase * 2.0) * 0.4 * puddle_mask
        puddle_disp_y = np.cos(NY * 12.0 + phase * 2.0) * 0.3 * puddle_mask

        remap_x = np.clip(X_GRID + puddle_disp_x, 0, W - 1).astype(np.float32)
        remap_y = np.clip(Y_GRID + puddle_disp_y, 0, H - 1).astype(np.float32)
        frame = cv2.remap(base_frame, remap_x, remap_y, interpolation=cv2.INTER_LINEAR).astype(np.float32)

        puddle_gleam = ((np.sin(NX * 20.0 + NY * 14.0 + phase * 2.0) * 0.5 + 0.5) * puddle_mask * 7.0)
        frame[:, :, 0] += puddle_gleam * 1.1
        frame[:, :, 1] += puddle_gleam * 0.9
        frame[:, :, 2] += puddle_gleam * 0.6

        frame_u8 = np.clip(frame, 0, 255).astype(np.uint8)

        p_prog = (prog + s_off) % 1.0
        p_a = (np.sin(p_prog * np.pi) ** 1.5) * s_alpha
        px = sx0 + np.sin(p_prog * 2.0 * np.pi) * s_sway
        py = sy0 - p_prog * s_drift
        draw_soft_particles(frame_u8, px, py, s_rad, (160, 230, 255), p_a)

        proc.stdin.write(frame_u8.tobytes())

    finish_nvenc(proc, "Realm 17", t0, out_path)
    return out_path


def render_18_ff_resonance(cq=15):
    print("\n[18/18] Rendering Realm 18: Final Fantasy Resonance Crystal Citadel...", flush=True)
    t0 = time.time()
    img = load_master("18_ff_resonance_crystal_citadel_4k.jpg")
    out_path = os.path.join(OUT_DIR, "18_ff_resonance_crystal_citadel_live.mp4")
    img_f = img.astype(np.float32)
    b, g, r = cv2.split(img_f)

    # 1. Colossal Resonance Mothercrystal
    is_crystal = (NX >= 0.38) & (NX <= 0.62) & (NY >= 0.12) & (NY <= 0.72) & (b > 160) & (b > r * 1.15)
    crystal_u8 = cv2.morphologyEx(is_crystal.astype(np.uint8) * 255, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7)))
    crystal_mask = cv2.GaussianBlur(crystal_u8.astype(np.float32) / 255.0, (15, 15), 0)
    glow_crystal = make_glow_bgr(crystal_mask, 24.0, 16.0, 6.0)

    # 2. Citadel Street Lanterns / Torches
    is_lantern = (r > 190) & (g > 130) & (b < 110) & (NY >= 0.50)
    lantern_mask = cv2.GaussianBlur(is_lantern.astype(np.float32), (9, 9), 0)
    glow_lantern = make_glow_bgr(lantern_mask, 4.0, 12.0, 20.0)

    # 3. Airship Engine & Sky
    is_airship = (NX >= 0.80) & (NY >= 0.18) & (NY <= 0.32) & (r > 140)
    airship_mask = cv2.GaussianBlur(is_airship.astype(np.float32), (11, 11), 0)
    glow_airship = make_glow_bgr(airship_mask, 3.0, 10.0, 16.0)

    # 4. Cobblestone Plaza Mana Ripples (Bottom)
    is_plaza_refl = (NY >= 0.68) & (NX >= 0.20) & (NX <= 0.80) & (b > 70)
    plaza_mask = cv2.GaussianBlur(is_plaza_refl.astype(np.float32), (21, 21), 0)

    # 5. Rising Lapis Mana Motes & Vision Sparkles
    np.random.seed(1818)
    n_mana = 45
    mx0 = np.random.uniform(0.35, 0.65, n_mana) * W
    my0 = np.random.uniform(0.30, 0.78, n_mana) * H
    m_drift = np.random.uniform(35.0, 80.0, n_mana)
    m_sway = np.random.uniform(12.0, 26.0, n_mana)
    m_off = np.random.uniform(0.0, 1.0, n_mana)
    m_rad = np.random.uniform(1.2, 2.5, n_mana)
    m_alpha = np.random.uniform(0.40, 0.90, n_mana)

    proc = open_nvenc(out_path, cq=cq)

    for i in range(NUM_FRAMES):
        prog = i / float(NUM_FRAMES)
        phase = 2.0 * np.pi * prog

        p_crystal = float((np.sin(phase * 2.0) * 0.5 + 0.5) * 1.1 + 0.3)
        p_lantern = float(np.sin(phase * 4.0) * 0.08 + np.cos(phase * 9.0) * 0.05 + 1.0)
        p_airship = float(np.sin(phase * 3.0) * 0.2 + 1.0)

        base_frame = img_f + (p_crystal * glow_crystal) + (p_lantern * glow_lantern) + (p_airship * glow_airship)

        plaza_disp_x = np.sin(NX * 12.0 + phase) * 0.4 * plaza_mask
        plaza_disp_y = np.cos(NY * 10.0 + phase) * 0.3 * plaza_mask

        remap_x = np.clip(X_GRID + plaza_disp_x, 0, W - 1).astype(np.float32)
        remap_y = np.clip(Y_GRID + plaza_disp_y, 0, H - 1).astype(np.float32)
        frame = cv2.remap(base_frame, remap_x, remap_y, interpolation=cv2.INTER_LINEAR).astype(np.float32)

        cryst_shimmer = ((np.sin(NX * 28.0 + NY * 16.0 + phase * 3.0) * 0.5 + 0.5) ** 1.8) * crystal_mask * 14.0
        frame[:, :, 0] += cryst_shimmer * 1.2
        frame[:, :, 1] += cryst_shimmer * 1.0
        frame[:, :, 2] += cryst_shimmer * 0.4

        plaza_gleam = ((np.sin(NX * 18.0 + NY * 12.0 + phase * 2.0) * 0.5 + 0.5) * plaza_mask * 7.0)
        frame[:, :, 0] += plaza_gleam * 1.1
        frame[:, :, 1] += plaza_gleam * 0.8
        frame[:, :, 2] += plaza_gleam * 0.5

        frame_u8 = np.clip(frame, 0, 255).astype(np.uint8)

        p_prog = (prog + m_off) % 1.0
        p_a = (np.sin(p_prog * np.pi) ** 1.5) * m_alpha
        px = mx0 + np.sin(p_prog * 2.0 * np.pi) * m_sway
        py = my0 - p_prog * m_drift
        draw_soft_particles(frame_u8, px, py, m_rad, (255, 220, 130), p_a)

        proc.stdin.write(frame_u8.tobytes())

    finish_nvenc(proc, "Realm 18", t0, out_path)
    return out_path


# ==============================================================================
# REALM 19: Front Mission 5: Scars of the War - Strike Wanzer Vanguard
# ==============================================================================
def render_19_fm5_vanguard(cq=15):
    print("\n[19/22] Rendering Realm 19: Front Mission 5: Wanzer Vanguard...", flush=True)
    t0 = time.time()
    img = load_master("19_front_mission_5_wanzer_vanguard_4k.jpg")
    out_path = os.path.join(OUT_DIR, "19_front_mission_5_wanzer_vanguard_live.mp4")
    img_f = img.astype(np.float32)
    b, g, r = cv2.split(img_f)

    # 1. Visor & Tactical HUD Sensor
    is_visor = (NX >= 0.35) & (NX <= 0.65) & (NY >= 0.15) & (NY <= 0.45) & (b > 130) & (b > r * 1.15)
    visor_mask = cv2.GaussianBlur(is_visor.astype(np.float32), (11, 11), 0)
    glow_visor = make_glow_bgr(visor_mask, 28.0, 16.0, 4.0)

    # 2. Searchlights & Volumetric Floodlight Haze
    is_light = (NY <= 0.35) & (r > 150) & (g > 140)
    light_mask = cv2.GaussianBlur(is_light.astype(np.float32), (25, 25), 0)
    glow_light = make_glow_bgr(light_mask, 16.0, 14.0, 10.0)

    # 3. Rain Puddles & Wet Tarmac Specular Gleam
    is_puddle = (NY >= 0.70) & (b > 50) & (b >= r * 0.9)
    puddle_mask = cv2.GaussianBlur(is_puddle.astype(np.float32), (19, 19), 0)

    # 4. Heavy Rain Particle Streaks
    np.random.seed(1919)
    n_rain = 160
    rx0 = np.random.uniform(0.05, 0.95, n_rain) * W
    ry0 = np.random.uniform(0.0, 0.90, n_rain) * H
    r_fall = np.random.uniform(320.0, 480.0, n_rain)
    r_drift = np.random.uniform(20.0, 45.0, n_rain)
    r_off = np.random.uniform(0.0, 1.0, n_rain)
    r_rad = np.random.uniform(0.8, 1.6, n_rain)
    r_alpha = np.random.uniform(0.35, 0.75, n_rain)

    proc = open_nvenc(out_path, cq=cq)

    for i in range(NUM_FRAMES):
        prog = i / float(NUM_FRAMES)
        phase = 2.0 * np.pi * prog

        p_visor = float(np.sin(phase * 4.0) * 0.12 + np.cos(phase * 8.0) * 0.06 + 1.0)
        p_light = float(np.sin(phase * 2.0) * 0.15 + 1.0)

        base_frame = img_f + (p_visor * glow_visor) + (p_light * glow_light)

        puddle_disp_x = np.sin(NX * 16.0 + phase * 2.0) * 0.35 * puddle_mask
        puddle_disp_y = np.cos(NY * 12.0 + phase * 2.0) * 0.25 * puddle_mask

        remap_x = np.clip(X_GRID + puddle_disp_x, 0, W - 1).astype(np.float32)
        remap_y = np.clip(Y_GRID + puddle_disp_y, 0, H - 1).astype(np.float32)
        frame = cv2.remap(base_frame, remap_x, remap_y, interpolation=cv2.INTER_LINEAR).astype(np.float32)

        puddle_gleam = ((np.sin(NX * 22.0 + NY * 14.0 + phase * 3.0) * 0.5 + 0.5) * puddle_mask * 8.0)
        frame[:, :, 0] += puddle_gleam * 1.1
        frame[:, :, 1] += puddle_gleam * 0.9
        frame[:, :, 2] += puddle_gleam * 0.6

        frame_u8 = np.clip(frame, 0, 255).astype(np.uint8)

        # Draw fast rain streaks
        p_prog = (prog + r_off) % 1.0
        p_a = (np.sin(p_prog * np.pi) ** 1.5) * r_alpha
        px = rx0 + p_prog * r_drift
        py = ry0 + p_prog * r_fall
        draw_soft_particles(frame_u8, px % W, py % H, r_rad, (220, 235, 255), p_a)

        proc.stdin.write(frame_u8.tobytes())

    finish_nvenc(proc, "Realm 19", t0, out_path)
    return out_path


# ==============================================================================
# REALM 20: Front Mission 3: Remaster - Zenith Rev & Kirishima Type 97
# ==============================================================================
def render_20_fm3_remaster(cq=15):
    print("\n[20/22] Rendering Realm 20: Front Mission 3: Zenith Remaster...", flush=True)
    t0 = time.time()
    img = load_master("20_front_mission_3_wanzer_zenith_4k.jpg")
    out_path = os.path.join(OUT_DIR, "20_front_mission_3_wanzer_zenith_live.mp4")
    img_f = img.astype(np.float32)
    b, g, r = cv2.split(img_f)

    # 1. Heat Exhaust Vents & Missile Launcher Heat
    is_exhaust = (r > 160) & (g > 110) & (b < 100) & (NY <= 0.55)
    exhaust_mask = cv2.GaussianBlur(is_exhaust.astype(np.float32), (13, 13), 0)
    glow_exhaust = make_glow_bgr(exhaust_mask, 4.0, 14.0, 26.0)

    # 2. Port Harbor Sodium Floodlights
    is_port_light = (NY <= 0.40) & (r > 180) & (g > 160)
    port_mask = cv2.GaussianBlur(is_port_light.astype(np.float32), (21, 21), 0)
    glow_port = make_glow_bgr(port_mask, 12.0, 18.0, 24.0)

    # 3. Dockside Wet Container & Harbor Water Remap
    is_water = (NY >= 0.72) & (b > 45)
    water_mask = cv2.GaussianBlur(is_water.astype(np.float32), (17, 17), 0)

    # 4. Atmospheric Drizzle Motes
    np.random.seed(2020)
    n_drizzle = 70
    dx0 = np.random.uniform(0.10, 0.90, n_drizzle) * W
    dy0 = np.random.uniform(0.10, 0.85, n_drizzle) * H
    d_drift = np.random.uniform(40.0, 90.0, n_drizzle)
    d_sway = np.random.uniform(10.0, 24.0, n_drizzle)
    d_off = np.random.uniform(0.0, 1.0, n_drizzle)
    d_rad = np.random.uniform(1.0, 2.0, n_drizzle)
    d_alpha = np.random.uniform(0.35, 0.80, n_drizzle)

    proc = open_nvenc(out_path, cq=cq)

    for i in range(NUM_FRAMES):
        prog = i / float(NUM_FRAMES)
        phase = 2.0 * np.pi * prog

        p_exhaust = float((np.sin(phase * 3.0) * 0.5 + 0.5) * 0.8 + 0.6)
        p_port = float(np.sin(phase * 2.0) * 0.10 + 1.0)

        base_frame = img_f + (p_exhaust * glow_exhaust) + (p_port * glow_port)

        water_disp_x = np.sin(NX * 14.0 + phase * 2.0) * 0.4 * water_mask
        water_disp_y = np.cos(NY * 10.0 + phase * 2.0) * 0.3 * water_mask

        remap_x = np.clip(X_GRID + water_disp_x, 0, W - 1).astype(np.float32)
        remap_y = np.clip(Y_GRID + water_disp_y, 0, H - 1).astype(np.float32)
        frame = cv2.remap(base_frame, remap_x, remap_y, interpolation=cv2.INTER_LINEAR).astype(np.float32)

        water_gleam = ((np.sin(NX * 18.0 + NY * 12.0 + phase * 2.0) * 0.5 + 0.5) * water_mask * 7.0)
        frame[:, :, 0] += water_gleam * 1.0
        frame[:, :, 1] += water_gleam * 0.8
        frame[:, :, 2] += water_gleam * 0.6

        frame_u8 = np.clip(frame, 0, 255).astype(np.uint8)

        p_prog = (prog + d_off) % 1.0
        p_a = (np.sin(p_prog * np.pi) ** 1.5) * d_alpha
        px = dx0 + np.sin(p_prog * 2.0 * np.pi) * d_sway
        py = dy0 - p_prog * d_drift
        draw_soft_particles(frame_u8, px % W, py % H, d_rad, (180, 220, 255), p_a)

        proc.stdin.write(frame_u8.tobytes())

    finish_nvenc(proc, "Realm 20", t0, out_path)
    return out_path


# ==============================================================================
# REALM 21: Mobile Suit Gundam: UC - RX-93 Nu Gundam Psycho-Frame Resonance
# ==============================================================================
def render_21_gundam_nu(cq=15):
    print("\n[21/22] Rendering Realm 21: RX-93 Nu Gundam Psycho-Frame Resonance...", flush=True)
    t0 = time.time()
    img = load_master("21_gundam_nu_psychoframe_resonance_4k.jpg")
    out_path = os.path.join(OUT_DIR, "21_gundam_nu_psychoframe_resonance_live.mp4")
    img_f = img.astype(np.float32)
    b, g, r = cv2.split(img_f)

    # 1. Emerald Psycho-Frame Resonance Aura & Optical Sensor Eyes
    is_psycho = (g > 130) & (g > r * 1.15) & (g > b * 0.95)
    psycho_mask = cv2.GaussianBlur(is_psycho.astype(np.float32), (13, 13), 0)
    glow_psycho = make_glow_bgr(psycho_mask, 16.0, 32.0, 6.0)

    # 2. Rocket Thruster Vernier Plumes
    is_thruster = ((b > 170) & (g > 130) & (r < 120)) | ((r > 180) & (g > 130) & (b < 100))
    thruster_mask = cv2.GaussianBlur(is_thruster.astype(np.float32), (11, 11), 0)
    glow_thruster = make_glow_bgr(thruster_mask, 24.0, 18.0, 10.0)

    # 3. Earth Horizon Dawn Glow
    is_earth_dawn = (NY >= 0.58) & (b > 90) & (b > r * 1.1)
    dawn_mask = cv2.GaussianBlur(is_earth_dawn.astype(np.float32), (25, 25), 0)
    glow_dawn = make_glow_bgr(dawn_mask, 18.0, 12.0, 4.0)

    # 4. Drifting Psycho-Frame Resonance Stardust
    np.random.seed(2121)
    n_psy_motes = 75
    px0 = np.random.uniform(0.15, 0.85, n_psy_motes) * W
    py0 = np.random.uniform(0.10, 0.80, n_psy_motes) * H
    p_drift = np.random.uniform(30.0, 75.0, n_psy_motes)
    p_sway = np.random.uniform(14.0, 30.0, n_psy_motes)
    p_off = np.random.uniform(0.0, 1.0, n_psy_motes)
    p_rad = np.random.uniform(1.2, 2.4, n_psy_motes)
    p_alpha = np.random.uniform(0.45, 0.90, n_psy_motes)

    proc = open_nvenc(out_path, cq=cq)

    for i in range(NUM_FRAMES):
        prog = i / float(NUM_FRAMES)
        phase = 2.0 * np.pi * prog

        p_psycho = float((np.sin(phase * 2.0) * 0.5 + 0.5) * 1.2 + 0.4)
        p_thruster = float(np.sin(phase * 5.0) * 0.15 + np.cos(phase * 9.0) * 0.08 + 1.0)
        p_dawn = float(np.sin(phase * 1.0) * 0.15 + 1.0)

        base_frame = img_f + (p_psycho * glow_psycho) + (p_thruster * glow_thruster) + (p_dawn * glow_dawn)

        frame_u8 = np.clip(base_frame, 0, 255).astype(np.uint8)

        p_prog = (prog + p_off) % 1.0
        p_a = (np.sin(p_prog * np.pi) ** 1.5) * p_alpha
        px = px0 + np.sin(p_prog * 2.0 * np.pi) * p_sway
        py = py0 - p_prog * p_drift
        draw_soft_particles(frame_u8, px % W, py % H, p_rad, (120, 255, 140), p_a)

        proc.stdin.write(frame_u8.tobytes())

    finish_nvenc(proc, "Realm 21", t0, out_path)
    return out_path


# ==============================================================================
# REALM 22: Super Robot Taisen: OG - Alteisen Revolver Stake Assault
# ==============================================================================
def render_22_srw_alteisen(cq=15):
    print("\n[22/22] Rendering Realm 22: SRW OG Alteisen Revolver Stake...", flush=True)
    t0 = time.time()
    img = load_master("22_srw_og_alteisen_revolver_stake_4k.jpg")
    out_path = os.path.join(OUT_DIR, "22_srw_og_alteisen_revolver_stake_live.mp4")
    img_f = img.astype(np.float32)
    b, g, r = cv2.split(img_f)

    # 1. Revolver Stake Superheated Kinetic Spike (Incandescent Red/Gold)
    is_stake = (NX >= 0.48) & (r > 170) & (r > b * 1.3)
    stake_mask = cv2.GaussianBlur(is_stake.astype(np.float32), (13, 13), 0)
    glow_stake = make_glow_bgr(stake_mask, 4.0, 18.0, 34.0)

    # 2. Camera Optical Sensor Eye (Crimson Glint)
    is_sensor = (NX >= 0.40) & (NX <= 0.60) & (NY >= 0.18) & (NY <= 0.38) & (r > 180) & (g < 100) & (b < 100)
    sensor_mask = cv2.GaussianBlur(is_sensor.astype(np.float32), (9, 9), 0)
    glow_sensor = make_glow_bgr(sensor_mask, 2.0, 6.0, 28.0)

    # 3. Subterranean Hangar Steam & Hazard Lights
    is_hangar_light = (r > 180) & (g > 150) & (b < 110)
    hangar_mask = cv2.GaussianBlur(is_hangar_light.astype(np.float32), (21, 21), 0)
    glow_hangar = make_glow_bgr(hangar_mask, 6.0, 16.0, 24.0)

    # 4. Industrial Welding Sparks / Hot Embers
    np.random.seed(2222)
    n_sparks = 55
    sx0 = np.random.uniform(0.20, 0.80, n_sparks) * W
    sy0 = np.random.uniform(0.35, 0.85, n_sparks) * H
    s_drift = np.random.uniform(40.0, 85.0, n_sparks)
    s_sway = np.random.uniform(12.0, 28.0, n_sparks)
    s_off = np.random.uniform(0.0, 1.0, n_sparks)
    s_rad = np.random.uniform(1.2, 2.3, n_sparks)
    s_alpha = np.random.uniform(0.50, 0.95, n_sparks)

    proc = open_nvenc(out_path, cq=cq)

    for i in range(NUM_FRAMES):
        prog = i / float(NUM_FRAMES)
        phase = 2.0 * np.pi * prog

        p_stake = float((np.sin(phase * 2.0) * 0.5 + 0.5) * 1.3 + 0.5)
        p_sensor = float(np.sin(phase * 4.0) * 0.15 + np.cos(phase * 7.0) * 0.08 + 1.0)
        p_hangar = float(np.sin(phase * 2.0) * 0.12 + 1.0)

        base_frame = img_f + (p_stake * glow_stake) + (p_sensor * glow_sensor) + (p_hangar * glow_hangar)

        frame_u8 = np.clip(base_frame, 0, 255).astype(np.uint8)

        p_prog = (prog + s_off) % 1.0
        p_a = (np.sin(p_prog * np.pi) ** 1.5) * s_alpha
        px = sx0 + np.sin(p_prog * 2.0 * np.pi) * s_sway
        py = sy0 - p_prog * s_drift
        draw_soft_particles(frame_u8, px % W, py % H, s_rad, (120, 210, 255), p_a)

        proc.stdin.write(frame_u8.tobytes())

    finish_nvenc(proc, "Realm 22", t0, out_path)
    return out_path


# ==============================================================================
# RENDER REGISTRY & SYNC DISPATCHER
# ==============================================================================
REALM_RENDERERS = {
    1: ("Valerius Citadel Twilight", "01_citadel_twilight_live.mp4", render_01_citadel),
    2: ("Eldertree Mystical Shrine", "02_mystical_forest_shrine_live.mp4", render_02_shrine),
    3: ("Frostpeak Aurora Fortress", "03_mountain_aurora_snow_live.mp4", render_03_aurora),
    4: ("Celestial Dunes Oasis", "04_celestial_dunes_oasis_live.mp4", render_04_dunes),
    5: ("Floating Sky Citadel", "05_floating_sky_citadel_live.mp4", render_05_sky_citadel),
    6: ("Volcanic Obsidian Forge", "06_volcanic_obsidian_forge_live.mp4", render_06_forge),
    7: ("Sunken Coral Atlantis", "07_sunken_coral_atlantis_live.mp4", render_07_atlantis),
    8: ("Cyber-Aegis Megacity", "08_cyber_aegis_megacity_live.mp4", render_08_cyber),
    9: ("Autumn Dragon Valley", "09_autumn_dragon_valley_v2_live.mp4", render_09_valley),
    10: ("Celestial Starfall Observatory", "10_celestial_starfall_spire_live.mp4", render_10_starfall),
    11: ("Ethereal Dreamscript Nexus", "11_ethereal_dreamscript_live.mp4", render_11_dreamscript),
    12: ("Celestial Titan Dunes", "12_celestial_dunes_titan_live.mp4", render_12_titan_dunes),
    13: ("Octopath HD-2D Harbor Citadel", "13_octopath_hd2d_coastal_citadel_live.mp4", render_13_octopath),
    14: ("FFVII Rebirth Cosmo Canyon", "14_ffvii_rebirth_cosmo_canyon_mako_live.mp4", render_14_ffvii_cosmo),
    15: ("Ghibli Watermill Sanctuary", "15_ghibli_overgrown_sanctuary_live.mp4", render_15_ghibli_watermill),
    16: ("The Sleeping Titan Gundam Relic", "16_gundam_relic_overgrown_meadow_live.mp4", render_16_gundam_relic),
    17: ("Front Mission 5: Wanzer Relic", "17_front_mission_wanzer_relic_live.mp4", render_17_wanzer_relic),
    18: ("Final Fantasy Resonance Citadel", "18_ff_resonance_crystal_citadel_live.mp4", render_18_ff_resonance),
    19: ("Front Mission 5: Wanzer Vanguard", "19_front_mission_5_wanzer_vanguard_live.mp4", render_19_fm5_vanguard),
    20: ("Front Mission 3: Zenith Remaster", "20_front_mission_3_wanzer_zenith_live.mp4", render_20_fm3_remaster),
    21: ("RX-93 Nu Gundam Psycho-Frame", "21_gundam_nu_psychoframe_resonance_live.mp4", render_21_gundam_nu),
    22: ("SRW OG: Alteisen Revolver Stake", "22_srw_og_alteisen_revolver_stake_live.mp4", render_22_srw_alteisen),
}


def sync_suites(selected_indices=None):
    web_files = [
        "index.html",
        "style.css",
        "LivelyProperties.json",
        os.path.join("js", "main.js"),
        os.path.join("js", "realm_fx.js"),
        os.path.join("js", "particles.js"),
    ]

    target_indices = selected_indices if selected_indices else list(REALM_RENDERERS.keys())
    mp4_files = [REALM_RENDERERS[idx][1] for idx in target_indices]

    print(f"\nSyncing {len(mp4_files)} master MP4 video(s) and interactive web suite to deployment targets...", flush=True)
    for dst in DESTINATIONS:
        if not os.path.exists(dst):
            continue
        for f in mp4_files:
            src_f = os.path.join(OUT_DIR, f)
            dst_f = os.path.join(dst, f)
            if os.path.exists(src_f) and os.path.abspath(src_f) != os.path.abspath(dst_f):
                shutil.copy2(src_f, dst_f)
        for wf in web_files:
            src_wf = os.path.join(REPO_INTERACTIVE, wf)
            dst_wf = os.path.join(dst, wf)
            if os.path.exists(src_wf) and os.path.abspath(src_wf) != os.path.abspath(dst_wf):
                os.makedirs(os.path.dirname(dst_wf), exist_ok=True)
                shutil.copy2(src_wf, dst_wf)
        print(f"  [SYNCED] -> {dst}", flush=True)


def list_realms():
    print("\n🌌 Aegis Sovereign Master Realm Registry (11 Realms):")
    print("-" * 75)
    print(f"{'#':<4} {'Realm Name':<35} {'Output Video File':<35}")
    print("-" * 75)
    for idx, (name, fname, _) in REALM_RENDERERS.items():
        print(f"{idx:<4} {name:<35} {fname:<35}")
    print("-" * 75)


def clamp(v, a, b):
    return min(b, max(a, v))


def render_dreamscript_realm(job_id_or_path, cq=15):
    """
    Renders a live seamless wallpaper loop directly from a Dreamscript Realm Builder job JSON.
    Auto-binds motion parameters from structured element definitions (flow, drift, glow, rise, fall, still).
    """
    import json
    job_file = job_id_or_path
    if not os.path.exists(job_file):
        job_file = os.path.join(r"E:\GitHub\Ethereal Dreamscript Dashboard\production\realms", f"{job_id_or_path}.job.json")
    if not os.path.exists(job_file):
        raise FileNotFoundError(f"Dreamscript realm job not found: {job_id_or_path}")

    with open(job_file, "r", encoding="utf-8") as f:
        job = json.load(f)

    realm_id = job.get("id", os.path.splitext(os.path.basename(job_file))[0].replace(".job", ""))
    realm_name = job.get("name", realm_id)
    print(f"\n[Dreamscript] Rendering Realm: {realm_name} ({realm_id})...", flush=True)

    img_path = os.path.join(r"E:\GitHub\Ethereal Dreamscript Dashboard\production\realms", f"{realm_id}.jpg")
    if not os.path.exists(img_path):
        img_path = os.path.join(r"E:\GitHub\Ethereal Dreamscript Dashboard\assets\bg", f"{realm_id}.jpg")
    if not os.path.exists(img_path):
        img_path = os.path.join(r"E:\GitHub\Ethereal Dreamscript Dashboard\assets\bg", "ui_realm.jpg")
    if not os.path.exists(img_path):
        raise FileNotFoundError(f"Source image plate not found for {realm_id}")

    t0 = time.time()
    raw = cv2.imread(img_path)
    img = cv2.resize(raw, (W, H), interpolation=cv2.INTER_LANCZOS4)

    elements = job.get("elements", [])
    flow_mask = np.zeros((H, W), dtype=np.float32)
    drift_mask = np.zeros((H, W), dtype=np.float32)
    glow_mask = np.zeros((H, W), dtype=np.float32)
    still_mask = np.zeros((H, W), dtype=np.float32)
    particle_specs = []

    for el in elements:
        box = el.get("box", [0, 0, 1, 1])
        x1 = int(clamp(box[0], 0, 1) * W)
        y1 = int(clamp(box[1], 0, 1) * H)
        x2 = int(clamp(box[0] + box[2], 0, 1) * W)
        y2 = int(clamp(box[1] + box[3], 0, 1) * H)
        motion = el.get("motion", "still")

        if motion == "flow":
            flow_mask[y1:y2, x1:x2] = 1.0
        elif motion == "drift":
            drift_mask[y1:y2, x1:x2] = 1.0
        elif motion in ("glow", "flicker"):
            glow_mask[y1:y2, x1:x2] = 1.0
        elif motion in ("still", "lock"):
            still_mask[y1:y2, x1:x2] = 1.0
        elif motion in ("rise", "fall"):
            particle_specs.append({
                "x_range": (x1, x2),
                "y_range": (y1, y2),
                "motion": motion,
                "count": 45
            })

    if np.max(flow_mask) > 0:
        flow_mask = cv2.GaussianBlur(flow_mask, (21, 21), 0)
        flow_mask = np.clip(flow_mask - still_mask, 0.0, 1.0)
    if np.max(drift_mask) > 0:
        drift_mask = cv2.GaussianBlur(drift_mask, (35, 35), 0)
        drift_mask = np.clip(drift_mask - still_mask, 0.0, 1.0)
    if np.max(glow_mask) > 0:
        glow_mask = cv2.GaussianBlur(glow_mask, (15, 15), 0)

    particles = []
    np.random.seed(42)
    for ps in particle_specs:
        x_min, x_max = ps["x_range"]
        y_min, y_max = ps["y_range"]
        cnt = ps["count"]
        direction = -1.0 if ps["motion"] == "rise" else 1.0
        for _ in range(cnt):
            particles.append({
                "x0": np.random.uniform(x_min, x_max),
                "y0": np.random.uniform(y_min, y_max),
                "speed": np.random.uniform(40.0, 95.0) * direction,
                "sway": np.random.uniform(10.0, 22.0),
                "off": np.random.uniform(0.0, 1.0),
                "rad": np.random.uniform(1.3, 2.4),
                "alpha": np.random.uniform(0.45, 0.85),
                "color": (255, 230, 140)
            })

    out_name = f"{realm_id}_live.mp4"
    out_path = os.path.join(OUT_DIR, out_name)
    proc = open_nvenc(out_path, cq=cq)

    num_cycles = 6
    cycle_d = 14.0
    cycle_drift = 16.0
    glow_bgr = make_glow_bgr(glow_mask, 3.0, 12.0, 18.0)

    for i in range(NUM_FRAMES):
        prog = i / float(NUM_FRAMES)
        phase = 2.0 * np.pi * prog
        t1 = (prog * num_cycles) % 1.0
        t2 = (t1 + 0.5) % 1.0
        w_blend = float(np.sin(t1 * np.pi) ** 2.0)

        dy1 = (t1 - 0.5) * cycle_d * flow_mask
        dy2 = (t2 - 0.5) * cycle_d * flow_mask
        dx1 = (t1 - 0.5) * cycle_drift * drift_mask
        dx2 = (t2 - 0.5) * cycle_drift * drift_mask

        f1 = cv2.remap(img, X_GRID - dx1, Y_GRID - dy1, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT).astype(np.float32)
        f2 = cv2.remap(img, X_GRID - dx2, Y_GRID - dy2, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT).astype(np.float32)
        frame = f1 * w_blend + f2 * (1.0 - w_blend)

        if np.max(glow_mask) > 0:
            gp = float(np.sin(phase * 2.0) * 0.5 + 0.5)
            frame += gp * glow_bgr

        frame_u8 = np.clip(frame, 0, 255).astype(np.uint8)

        if particles:
            p_xs = [p["x0"] + np.sin(((prog + p["off"]) % 1.0) * 2.0 * np.pi) * p["sway"] for p in particles]
            p_ys = [p["y0"] + ((prog + p["off"]) % 1.0) * p["speed"] for p in particles]
            p_rads = [p["rad"] for p in particles]
            p_alphas = [(np.sin(((prog + p["off"]) % 1.0) * np.pi) ** 1.5) * p["alpha"] for p in particles]
            draw_soft_particles(frame_u8, p_xs, p_ys, p_rads, (255, 230, 140), p_alphas)

        proc.stdin.write(frame_u8.tobytes())

    finish_nvenc(proc, f"Dreamscript Realm [{realm_name}]", t0, out_path)

    ds_realms_dir = r"E:\GitHub\Ethereal Dreamscript Dashboard\production\realms"
    ds_aegis_dir = r"E:\GitHub\Ethereal Dreamscript Dashboard\aegis"
    for d in (ds_realms_dir, ds_aegis_dir):
        if os.path.exists(d):
            shutil.copy2(out_path, os.path.join(d, out_name))
            print(f"  [SYNCED] -> {d}\\{out_name}", flush=True)

    job["status"] = "done"
    job["video"] = f"production/realms/{out_name}"
    job["renderedAt"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    with open(job_file, "w", encoding="utf-8") as f:
        json.dump(job, f, indent=2)

    return out_path


def parse_realm_indices(realm_arg):
    if realm_arg.lower() == "all":
        return list(REALM_RENDERERS.keys())
    indices = []
    for part in realm_arg.split(","):
        part = part.strip()
        if part.isdigit():
            idx = int(part)
            if idx in REALM_RENDERERS:
                indices.append(idx)
        else:
            # Match by name fragment
            part_lower = part.lower()
            for idx, (name, fname, _) in REALM_RENDERERS.items():
                if part_lower in name.lower() or part_lower in fname.lower():
                    indices.append(idx)
    return sorted(list(set(indices)))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Aegis Sovereign Deterministic Motion Engine")
    parser.add_argument("--realm", "-r", type=str, default="", help="Realm number (1-11), name, or 'all'")
    parser.add_argument("--job", "-j", type=str, default="", help="Dreamscript realm job ID or path to render directly from Realm Builder")
    parser.add_argument("--list", "-l", action="store_true", help="List all available realms and exit")
    parser.add_argument("--no-sync", action="store_true", help="Skip syncing output files to external directories")
    parser.add_argument("--cq", type=int, default=15, help="NVENC Constant Quality level (14-18, default 15)")
    args = parser.parse_args()

    if args.list:
        list_realms()
        sys.exit(0)

    if args.job:
        t_total = time.time()
        out_f = render_dreamscript_realm(args.job, cq=args.cq)
        if not args.no_sync:
            destinations = DESTINATIONS
            for dst in destinations:
                if os.path.exists(dst):
                    dst_f = os.path.join(dst, os.path.basename(out_f))
                    if os.path.abspath(out_f) != os.path.abspath(dst_f):
                        shutil.copy2(out_f, dst_f)
                        print(f"  [SYNCED] -> {dst_f}", flush=True)
        print(f"\n[DONE] Dreamscript Realm rendered in {time.time() - t_total:.1f}s!", flush=True)
        sys.exit(0)

    realm_to_render = args.realm if args.realm else "all"
    target_realms = parse_realm_indices(realm_to_render)
    if not target_realms:
        print(f"Error: No matching realms found for '{realm_to_render}'. Use --list to view valid realms.")
        sys.exit(1)

    t_total = time.time()
    rendered_files = []
    print(f"Starting deterministic rendering for {len(target_realms)} realm(s)...")

    for idx in target_realms:
        name, _, fn = REALM_RENDERERS[idx]
        out_f = fn(cq=args.cq)
        rendered_files.append(out_f)

    if not args.no_sync:
        sync_suites(selected_indices=target_realms)

    print(f"\n[DONE] {len(target_realms)} Realm(s) rendered in {time.time() - t_total:.1f}s!", flush=True)
