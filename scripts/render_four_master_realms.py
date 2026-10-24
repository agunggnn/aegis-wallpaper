import os
import sys
import time
import cv2
import numpy as np
import subprocess
import shutil

BASE_DIR = r"C:\Users\agung\Pictures\Wallpapers\Fantasy_RPG_Collection"
TARGET_W = 2560
TARGET_H = 1440
FPS = 30
DURATION = 12.0  # 12.0-second ultra-calm meditative seamless loop
NUM_FRAMES = int(FPS * DURATION)  # 360 frames

Y_GRID, X_GRID = np.mgrid[0:TARGET_H, 0:TARGET_W].astype(np.float32)
NY = Y_GRID / TARGET_H
NX = X_GRID / TARGET_W

def make_ffmpeg_process(out_path, cq=16):
    cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", f"{TARGET_W}x{TARGET_H}",
        "-pix_fmt", "bgr24",
        "-r", str(FPS),
        "-i", "-",
        "-c:v", "h264_nvenc",
        "-preset", "p6",
        "-cq", str(cq),
        "-pix_fmt", "yuv420p",
        out_path
    ]
    return subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# ==============================================================================
# 1. REALM 09: Autumn Dragon Valley (Inpainted Clean Base + Dynamic Cascades)
# ==============================================================================
def render_realm_09_autumn_valley():
    src = os.path.join(BASE_DIR, "09_autumn_dragon_valley_4k.jpg")
    dst = os.path.join(BASE_DIR, "09_autumn_dragon_valley_live.mp4")
    print(f"\n[1/4] Rendering Realm 09: Autumn Dragon Valley -> {dst}", flush=True)

    img_raw = cv2.imread(src)
    img = cv2.resize(img_raw, (TARGET_W, TARGET_H), interpolation=cv2.INTER_LANCZOS4)

    # 1. Inpaint all frozen mid-air painted leaves so they never break focus!
    leaves_to_inpaint = [
        (int(TARGET_W * 0.306), int(TARGET_H * 0.108), 35),  # sky leaf
        (int(TARGET_W * 0.354), int(TARGET_H * 0.258), 30),  # cliff leaf
        (755, 1156, 55),                                      # big golden leaf over lake
        (int(TARGET_W * 0.503), int(TARGET_H * 0.680), 25),  # fall leaf
        (int(TARGET_W * 0.620), int(TARGET_H * 0.320), 28),  # gorge leaf 1
        (int(TARGET_W * 0.665), int(TARGET_H * 0.375), 25),  # gorge leaf 2
        (int(TARGET_W * 0.621), int(TARGET_H * 0.428), 28),  # gorge leaf 3
        (int(TARGET_W * 0.605), int(TARGET_H * 0.722), 25),  # gorge leaf 4
        (int(TARGET_W * 0.623), int(TARGET_H * 0.762), 28),  # gorge leaf 5
        (int(TARGET_W * 0.697), int(TARGET_H * 0.648), 22),  # torii leaf
        (int(TARGET_W * 0.800), int(TARGET_H * 0.356), 22),  # mountain leaf
        (int(TARGET_W * 0.210), int(TARGET_H * 0.495), 22),  # bridge leaf
        (int(TARGET_W * 0.098), int(TARGET_H * 0.642), 28),  # left branch leaf
        (int(TARGET_W * 0.315), int(TARGET_H * 0.745), 22),  # lower cliff leaf
        (int(TARGET_W * 0.370), int(TARGET_H * 0.840), 22),  # lake shore leaf
    ]

    inpaint_mask = np.zeros((TARGET_H, TARGET_W), dtype=np.uint8)
    b_c, g_c, r_c = cv2.split(img.astype(np.float32))

    for cx, cy, rad in leaves_to_inpaint:
        y1, y2 = max(0, cy - rad), min(TARGET_H, cy + rad)
        x1, x2 = max(0, cx - rad), min(TARGET_W, cx + rad)
        crop_r = r_c[y1:y2, x1:x2]
        crop_b = b_c[y1:y2, x1:x2]
        is_l = (crop_r > crop_b * 1.15) & (crop_r > 65)
        yy, xx = np.mgrid[y1:y2, x1:x2]
        inpaint_mask[y1:y2, x1:x2][((xx - cx)**2 + (yy - cy)**2 <= rad**2) & is_l] = 255

    # Precise patch on foreground big leaf
    leaf_crop = img[1115:1195, 715:795].astype(np.float32)
    b_lc, g_lc, r_lc = cv2.split(leaf_crop)
    inpaint_mask[1115:1195, 715:795][(r_lc > 130) & (g_lc > 80) & (b_lc < 100)] = 255

    inpaint_mask = cv2.dilate(inpaint_mask, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
    base_img = cv2.inpaint(img, inpaint_mask, 5, cv2.INPAINT_TELEA)

    # 2. Waterfalls & River Flow Masks
    b_chan, g_chan, r_chan = cv2.split(base_img.astype(np.float32))

    # Emerald Lake Pool (glassy, calm)
    is_lake = (NY >= 0.70) & (NX >= 0.16) & (NX <= 0.66) & (g_chan > 60) & (g_chan >= r_chan * 0.92) & (b_chan > 50) & (r_chan < 110)
    lake_clean = cv2.morphologyEx(is_lake.astype(np.uint8) * 255, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7)))
    lake_mask = cv2.GaussianBlur(lake_clean.astype(np.float32) / 255.0, (15, 15), 0)

    # Waterfalls & Gorge River (visible cascading flow)
    is_upper_fall = (NX >= 0.34) & (NX <= 0.45) & (NY >= 0.32) & (NY <= 0.52) & (b_chan > 115) & (b_chan > 0.80 * r_chan)
    is_lower_fall = (NX >= 0.37) & (NX <= 0.51) & (NY >= 0.52) & (NY <= 0.74) & (b_chan > 115) & (b_chan > 0.80 * r_chan)
    is_stream = (NX >= 0.51) & (NX <= 0.64) & (NY >= 0.56) & (NY <= 0.75) & (b_chan > 110) & (b_chan > 0.78 * r_chan)

    falls_raw = (is_upper_fall | is_lower_fall | is_stream).astype(np.uint8) * 255
    falls_clean = cv2.morphologyEx(falls_raw, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 7)))
    falls_mask = cv2.GaussianBlur(falls_clean.astype(np.float32) / 255.0, (7, 11), 0)

    # Plunge pool mist
    plunge_dist_sq = ((NX - 0.45)**2) / (0.09**2) + ((NY - 0.71)**2) / (0.045**2)
    mist_mask = np.clip(np.exp(-plunge_dist_sq).astype(np.float32), 0.0, 1.0)

    # Godrays & Lanterns
    godray_dist_sq = ((NX - 0.80)**2) / (0.18**2) + ((NY - 0.22)**2) / (0.15**2)
    godray_mask = np.clip(np.exp(-godray_dist_sq).astype(np.float32), 0.0, 1.0)

    lantern_mask = np.zeros((TARGET_H, TARGET_W), dtype=np.float32)
    lantern_coords = [
        (int(0.730 * TARGET_W), int(0.628 * TARGET_H), 32),
        (int(0.853 * TARGET_W), int(0.625 * TARGET_H), 32),
        (int(0.796 * TARGET_W), int(0.780 * TARGET_H), 26),
    ]
    for lx, ly, rad in lantern_coords:
        l_dist_sq = ((X_GRID - lx)**2 + (Y_GRID - ly)**2) / (rad**2)
        lantern_mask += np.clip(np.exp(-l_dist_sq), 0.0, 1.0)
    lantern_mask = np.clip(lantern_mask, 0.0, 1.0)

    # 3. Dynamic Serene Japanese Momiji Leaves
    np.random.seed(101)
    num_leaves = 14
    leaf_sprites = []
    for s in [14, 16, 18, 20]:
        l_img = np.zeros((s, s), dtype=np.uint8)
        pts = np.array([
            [s*0.50, s*0.05], [s*0.42, s*0.25], [s*0.20, s*0.15],
            [s*0.28, s*0.40], [s*0.08, s*0.48], [s*0.35, s*0.65],
            [s*0.48, s*0.90], [s*0.52, s*0.90], [s*0.65, s*0.65],
            [s*0.92, s*0.48], [s*0.72, s*0.40], [s*0.80, s*0.15],
            [s*0.58, s*0.25]
        ], np.int32)
        cv2.fillPoly(l_img, [pts], 255)
        leaf_sprites.append(cv2.GaussianBlur(l_img, (3, 3), 0).astype(np.float32) / 255.0)

    leaf_colors = [(25, 40, 215), (20, 130, 245), (30, 85, 220), (15, 110, 235)]
    leaves = []
    for k in range(num_leaves):
        leaves.append({
            'x_start': np.random.uniform(0.12, 0.82) * TARGET_W,
            'y_start': np.random.uniform(0.18, 0.72) * TARGET_H,
            'fall_dist': np.random.uniform(28.0, 42.0),
            'sway_amp': np.random.uniform(16.0, 26.0),
            'phase_offset': np.random.uniform(0.0, 1.0),
            'base_angle': np.random.uniform(0.0, 360.0),
            'rot_amp': np.random.uniform(15.0, 30.0),
            'color': leaf_colors[k % len(leaf_colors)],
            'sprite': leaf_sprites[k % len(leaf_sprites)],
            'max_alpha': np.random.uniform(0.70, 0.88),
        })

    cycle_h = 16.0  # Dual-phase advection cycle height
    proc = make_ffmpeg_process(dst, cq=16)
    t0 = time.time()

    for i in range(NUM_FRAMES):
        phase = (2.0 * np.pi * i) / NUM_FRAMES
        t1 = (i / NUM_FRAMES) % 1.0
        t2 = (t1 + 0.5) % 1.0
        w_blend = np.sin(t1 * np.pi) ** 2.0

        # Continuous downward waterfall and river advection
        dy1 = (t1 - 0.5) * cycle_h * falls_mask
        dy2 = (t2 - 0.5) * cycle_h * falls_mask
        lake_disp = np.sin(NX * 6.0 + phase) * 0.4 * lake_mask

        remap_y1 = np.clip(Y_GRID - dy1 + lake_disp, 0, TARGET_H - 1).astype(np.float32)
        remap_y2 = np.clip(Y_GRID - dy2 + lake_disp, 0, TARGET_H - 1).astype(np.float32)

        f1 = cv2.remap(base_img, X_GRID, remap_y1, interpolation=cv2.INTER_LINEAR).astype(np.float32)
        f2 = cv2.remap(base_img, X_GRID, remap_y2, interpolation=cv2.INTER_LINEAR).astype(np.float32)
        frame = f1 * (1.0 - w_blend) + f2 * w_blend

        # Waterfall froth sparkle
        fall_sparkle = (np.sin(NY * 30.0 - phase * 3.0) * 0.5 + 0.5) ** 1.5 * falls_mask * 14.0
        frame[:, :, 0] += fall_sparkle * 1.15
        frame[:, :, 1] += fall_sparkle * 1.05
        frame[:, :, 2] += fall_sparkle * 0.90

        # Lake sunlight sheen
        lake_sheen = (np.sin(NX * 4.0 + NY * 2.0 + phase) * 0.5 + 0.5) * lake_mask * 6.0
        frame[:, :, 0] += lake_sheen * 0.7
        frame[:, :, 1] += lake_sheen * 1.1
        frame[:, :, 2] += lake_sheen * 0.6

        # Mist pulse
        mist_pulse = (np.sin(phase) * 0.5 + 0.5) * mist_mask * 8.0
        frame[:, :, 0] += mist_pulse * 1.05
        frame[:, :, 1] += mist_pulse * 0.95
        frame[:, :, 2] += mist_pulse * 0.85

        # Lantern breathing
        lantern_breathe = (np.sin(phase * 1.5) * 0.5 + 0.5) * lantern_mask * 14.0
        frame[:, :, 0] += lantern_breathe * 0.25
        frame[:, :, 1] += lantern_breathe * 0.70
        frame[:, :, 2] += lantern_breathe * 1.00

        # Godray shimmer
        godray_shimmer = (np.sin(phase) * 0.5 + 0.5) * godray_mask * 5.0
        frame[:, :, 0] += godray_shimmer * 0.4
        frame[:, :, 1] += godray_shimmer * 0.8
        frame[:, :, 2] += godray_shimmer * 1.0

        frame_u8 = np.clip(frame, 0, 255).astype(np.uint8)

        # Draw serene drifting leaves
        for leaf in leaves:
            prog = (i / NUM_FRAMES + leaf['phase_offset']) % 1.0
            alpha = (np.sin(prog * np.pi) ** 2.0) * leaf['max_alpha']
            if alpha < 0.01:
                continue

            cur_y = leaf['y_start'] + prog * leaf['fall_dist']
            cur_x = leaf['x_start'] + np.sin(prog * 2.0 * np.pi) * leaf['sway_amp']
            cur_angle = leaf['base_angle'] + np.cos(prog * 2.0 * np.pi) * leaf['rot_amp']

            sprite = leaf['sprite']
            sh, sw = sprite.shape
            M = cv2.getRotationMatrix2D((sw / 2, sh / 2), cur_angle, 1.0)
            rot_mask = cv2.warpAffine(sprite, M, (sw, sh), flags=cv2.INTER_LINEAR)

            ix, iy = int(round(cur_x)), int(round(cur_y))
            x1, y1 = max(0, ix - sw // 2), max(0, iy - sh // 2)
            x2, y2 = min(TARGET_W, x1 + sw), min(TARGET_H, y1 + sh)
            sx1, sy1 = x1 - (ix - sw // 2), y1 - (iy - sh // 2)
            sx2, sy2 = sx1 + (x2 - x1), sy1 + (y2 - y1)

            if x2 > x1 and y2 > y1 and sx2 > sx1 and sy2 > sy1:
                sub_mask = rot_mask[sy1:sy2, sx1:sx2] * alpha
                roi = frame_u8[y1:y2, x1:x2].astype(np.float32)
                color = np.array(leaf['color'], dtype=np.float32)
                for c in range(3):
                    roi[:, :, c] = roi[:, :, c] * (1.0 - sub_mask) + color[c] * sub_mask
                frame_u8[y1:y2, x1:x2] = np.clip(roi, 0, 255).astype(np.uint8)

        proc.stdin.write(frame_u8.tobytes())
        if (i + 1) % 90 == 0:
            print(f"  Realm 09: Frame {i+1}/{NUM_FRAMES} ({(i+1)/NUM_FRAMES*100:.1f}%) rendered...", flush=True)

    proc.stdin.close()
    proc.wait()
    print(f"Realm 09 completed in {time.time() - t0:.1f}s!", flush=True)

# ==============================================================================
# 2. REALM 03: Mountain Aurora Fortress (Calm, Slow Gentle Snowfall)
# ==============================================================================
def render_realm_03_mountain_aurora():
    src = os.path.join(BASE_DIR, "03_mountain_aurora_fortress_4k.jpg")
    dst = os.path.join(BASE_DIR, "03_mountain_aurora_snow_live.mp4")
    print(f"\n[2/4] Rendering Realm 03: Mountain Aurora Fortress -> {dst}", flush=True)

    img_raw = cv2.imread(src)
    img = cv2.resize(img_raw, (TARGET_W, TARGET_H), interpolation=cv2.INTER_LANCZOS4)

    # Aurora sky mask (upper 55%)
    sky_mask = np.clip(1.0 - (NY / 0.55), 0.0, 1.0).astype(np.float32)

    # Slow, peaceful multi-depth snowflakes (280 flakes)
    np.random.seed(77)
    num_flakes = 280
    flake_x0 = np.random.uniform(0, TARGET_W, num_flakes)
    flake_y0 = np.random.uniform(0, TARGET_H, num_flakes)
    # Total descent over 12s is only 280-420px (~25-35 px/sec instead of 240 px/sec!)
    flake_speed = np.random.uniform(260.0, 420.0, num_flakes)
    flake_rad = np.random.choice([1, 2, 3], size=num_flakes, p=[0.60, 0.32, 0.08])
    flake_alpha = np.random.uniform(0.35, 0.80, num_flakes)
    flake_sway_amp = np.random.uniform(12.0, 30.0, num_flakes)
    flake_phase_off = np.random.uniform(0.0, 2.0 * np.pi, num_flakes)

    proc = make_ffmpeg_process(dst, cq=16)
    t0 = time.time()

    for i in range(NUM_FRAMES):
        phase = (2.0 * np.pi * i) / NUM_FRAMES
        prog = i / NUM_FRAMES

        frame = img.copy().astype(np.float32)

        # A. Undulating Northern Lights (Green & Violet Aurora)
        aurora_wave1 = (np.sin(NX * 4.0 + phase * 1.5) * 0.5 + 0.5) * sky_mask * 18.0
        aurora_wave2 = (np.sin(NX * 6.0 - phase * 1.0) * 0.5 + 0.5) * sky_mask * 12.0
        frame[:, :, 0] += aurora_wave2 * 1.2  # Violet Blue
        frame[:, :, 1] += aurora_wave1 * 1.4  # Emerald Green
        frame[:, :, 2] += aurora_wave2 * 0.8  # Magenta Red

        frame_u8 = np.clip(frame, 0, 255).astype(np.uint8)

        # B. Ultra-Calm, Slow Gentle Snowflakes
        for k in range(num_flakes):
            cy = int((flake_y0[k] + prog * flake_speed[k]) % TARGET_H)
            cx = int((flake_x0[k] + np.sin(phase + flake_phase_off[k]) * flake_sway_amp[k]) % TARGET_W)
            r = flake_rad[k]
            a = flake_alpha[k]

            # Soft white/cyan snowflake dot
            cv2.circle(frame_u8, (cx, cy), r, (int(255 * a), int(250 * a), int(245 * a)), -1)

        proc.stdin.write(frame_u8.tobytes())
        if (i + 1) % 90 == 0:
            print(f"  Realm 03: Frame {i+1}/{NUM_FRAMES} ({(i+1)/NUM_FRAMES*100:.1f}%) rendered...", flush=True)

    proc.stdin.close()
    proc.wait()
    print(f"Realm 03 completed in {time.time() - t0:.1f}s!", flush=True)

# ==============================================================================
# 3. REALM 05: Floating Sky Citadel (Aligned Waterfalls + Prismatic Rainbow)
# ==============================================================================
def render_realm_05_sky_citadel():
    src = os.path.join(BASE_DIR, "05_floating_sky_citadel_4k.jpg")
    dst = os.path.join(BASE_DIR, "05_floating_sky_citadel_live.mp4")
    print(f"\n[3/4] Rendering Realm 05: Floating Sky Citadel -> {dst}", flush=True)

    img_raw = cv2.imread(src)
    img = cv2.resize(img_raw, (TARGET_W, TARGET_H), interpolation=cv2.INTER_LANCZOS4)
    b_chan, g_chan, r_chan = cv2.split(img.astype(np.float32))

    # Clean separation: exclude brown cliffs and green lawns
    is_solid = (r_chan > 1.10 * b_chan) | (g_chan > 1.25 * b_chan)
    is_water_color = (b_chan > 108) & (b_chan >= 0.82 * r_chan) & (~is_solid)

    # 1. Main Palace Waterfall (continuous from terrace pool down into clouds)
    is_main_col = (NX >= 0.535) & (NX <= 0.645) & (NY >= 0.43) & (NY <= 0.985) & is_water_color

    # 2. Left Terraced Island (terrace stream + 2 cliff falls)
    is_left_stream = (NX >= 0.36) & (NX <= 0.44) & (NY >= 0.53) & (NY <= 0.58) & is_water_color
    is_left_fall1 = (NX >= 0.278) & (NX <= 0.315) & (NY >= 0.56) & (NY <= 0.88) & is_water_color
    is_left_fall2 = (NX >= 0.415) & (NX <= 0.455) & (NY >= 0.57) & (NY <= 0.88) & is_water_color

    # 3. Palace secondary right fall & Spire fall
    is_palace_right = (NX >= 0.645) & (NX <= 0.680) & (NY >= 0.53) & (NY <= 0.82) & is_water_color
    is_spire_fall = (NX >= 0.768) & (NX <= 0.796) & (NY >= 0.26) & (NY <= 0.43) & is_water_color

    sky_water = is_main_col | is_left_stream | is_left_fall1 | is_left_fall2 | is_palace_right | is_spire_fall
    raw = sky_water.astype(np.uint8) * 255
    clean = cv2.morphologyEx(raw, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 5)))
    clean = cv2.morphologyEx(clean, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 7)))
    smooth_mask = cv2.GaussianBlur(clean.astype(np.float32) / 255.0, (7, 13), 0)

    # Gentle bottom fade at lowest edge
    smooth_mask *= np.clip((1.0 - NY) / 0.03, 0.0, 1.0)

    # Prismatic rainbow mask (curving across the base of the main waterfall)
    # nx: 0.54 to 0.68, ny: 0.65 to 0.95
    rainbow_dist = ((NX - 0.61)**2) / (0.10**2) + ((NY - 0.80)**2) / (0.16**2)
    rainbow_mask = np.clip(np.exp(-((rainbow_dist - 0.65)**2) / 0.08), 0.0, 1.0).astype(np.float32)

    # Flying Sail Ship & Rocket Flyer masks
    ship_mask = np.clip(np.exp(-(((NX - 0.865) / 0.058)**2 + ((NY - 0.345) / 0.088)**2) * 1.5), 0.0, 1.0).astype(np.float32)
    rkt_mask = np.clip(np.exp(-(((NX - 0.412) / 0.048)**2 + ((NY - 0.328) / 0.042)**2) * 2.0), 0.0, 1.0).astype(np.float32)

    cycle_h = 16.0
    proc = make_ffmpeg_process(dst, cq=16)
    t0 = time.time()

    for i in range(NUM_FRAMES):
        phase = (2.0 * np.pi * i) / NUM_FRAMES
        t1 = (i / NUM_FRAMES) % 1.0
        t2 = (t1 + 0.5) % 1.0
        w_blend = np.sin(t1 * np.pi) ** 2.0

        # Continuous downward waterfall advection
        dy1 = (t1 - 0.5) * cycle_h * smooth_mask
        dy2 = (t2 - 0.5) * cycle_h * smooth_mask

        # Gentle floating celestial boats sway
        ship_disp_y = np.sin(phase) * 3.5 * ship_mask
        rkt_disp_x = np.cos(phase) * 6.0 * rkt_mask
        rkt_disp_y = np.sin(phase * 1.5) * 2.5 * rkt_mask

        remap_y1 = np.clip(Y_GRID - dy1 + ship_disp_y + rkt_disp_y, 0, TARGET_H - 1).astype(np.float32)
        remap_y2 = np.clip(Y_GRID - dy2 + ship_disp_y + rkt_disp_y, 0, TARGET_H - 1).astype(np.float32)
        remap_x = np.clip(X_GRID + rkt_disp_x, 0, TARGET_W - 1).astype(np.float32)

        f1 = cv2.remap(img, remap_x, remap_y1, interpolation=cv2.INTER_LINEAR).astype(np.float32)
        f2 = cv2.remap(img, remap_x, remap_y2, interpolation=cv2.INTER_LINEAR).astype(np.float32)
        frame = f1 * (1.0 - w_blend) + f2 * w_blend

        # Waterfall crystalline foam sparkle
        water_gleam = (np.sin(NY * 32.0 - phase * 3.0) * 0.5 + 0.5) ** 1.5 * smooth_mask * 14.0
        frame[:, :, 0] += water_gleam * 1.2
        frame[:, :, 1] += water_gleam * 1.1
        frame[:, :, 2] += water_gleam * 0.9

        # Prismatic Rainbow shimmer
        rb_shimmer = (np.sin(phase * 1.5) * 0.5 + 0.5) * rainbow_mask * 10.0
        frame[:, :, 0] += rb_shimmer * 1.1  # Cyan
        frame[:, :, 1] += rb_shimmer * 1.2  # Green
        frame[:, :, 2] += rb_shimmer * 0.8  # Red/Gold

        # Rocket cyan thruster glow
        rkt_glow = (np.sin(phase * 3.0) * 0.5 + 0.5) * rkt_mask * 16.0
        frame[:, :, 0] += rkt_glow * 1.2
        frame[:, :, 1] += rkt_glow * 0.8

        frame_u8 = np.clip(frame, 0, 255).astype(np.uint8)
        proc.stdin.write(frame_u8.tobytes())
        if (i + 1) % 90 == 0:
            print(f"  Realm 05: Frame {i+1}/{NUM_FRAMES} ({(i+1)/NUM_FRAMES*100:.1f}%) rendered...", flush=True)

    proc.stdin.close()
    proc.wait()
    print(f"Realm 05 completed in {time.time() - t0:.1f}s!", flush=True)

# ==============================================================================
# 4. REALM 06: Volcanic Obsidian Forge (High-Res CQ 14 + ALL Lava Motion)
# ==============================================================================
def render_realm_06_obsidian_forge():
    src = os.path.join(BASE_DIR, "06_volcanic_obsidian_forge_4k.jpg")
    dst = os.path.join(BASE_DIR, "06_volcanic_obsidian_forge_live.mp4")
    print(f"\n[4/4] Rendering Realm 06: Volcanic Obsidian Forge -> {dst}", flush=True)

    img_raw = cv2.imread(src)
    # High-Resolution Lanczos-4 QHD 2560x1440
    img = cv2.resize(img_raw, (TARGET_W, TARGET_H), interpolation=cv2.INTER_LANCZOS4)
    b_chan, g_chan, r_chan = cv2.split(img.astype(np.float32))

    # Comprehensive Lava Detection across ALL regions
    # Exclude dark basalt stone and grey fortress walls
    is_lava_color = (r_chan > 115) & (r_chan > 1.35 * b_chan) & (g_chan > 45) & (r_chan > 0.95 * g_chan)
    is_bright_lava = (r_chan > 155) & (g_chan > 80) & (b_chan < 160)
    all_lava_raw = is_lava_color | is_bright_lava

    # Lava is strictly on landscape/volcanoes: exclude upper atmospheric sky
    is_landscape = (NY >= 0.38) | ((NX <= 0.36) & (NY >= 0.22)) | ((NX >= 0.78) & (NY >= 0.08))
    lava_masked = all_lava_raw & is_landscape

    raw_mask = lava_masked.astype(np.uint8) * 255
    clean = cv2.morphologyEx(raw_mask, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)))
    clean = cv2.morphologyEx(clean, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
    lava_mask = cv2.GaussianBlur(clean.astype(np.float32) / 255.0, (5, 5), 0)

    # Separate vertical lava cataracts (central fall, gorge falls) from horizontal molten pools
    is_vertical_fall = ((NX >= 0.48) & (NX <= 0.62) & (NY >= 0.50) & (NY <= 0.88)) | \
                       ((NX >= 0.24) & (NX <= 0.30) & (NY >= 0.42) & (NY <= 0.72)) | \
                       ((NX >= 0.04) & (NX <= 0.22) & (NY >= 0.40) & (NY <= 0.88)) | \
                       ((NX >= 0.71) & (NX <= 0.76) & (NY >= 0.54) & (NY <= 0.78)) | \
                       ((NX >= 0.88) & (NX <= 0.98) & (NY >= 0.50) & (NY <= 0.75))
    
    cataract_mask = lava_mask * is_vertical_fall.astype(np.float32)
    pool_mask = lava_mask * (~is_vertical_fall).astype(np.float32)

    # Fortress windows and glowing dwarven runes mask
    is_runes = (r_chan > 140) & (g_chan > 70) & (b_chan < 60) & (NY >= 0.28) & (NY <= 0.55) & (NX >= 0.38) & (NX <= 0.76)
    runes_mask = cv2.GaussianBlur(is_runes.astype(np.uint8).astype(np.float32), (5, 5), 0)

    # 40 rising embers
    np.random.seed(55)
    num_embers = 45
    ex0 = np.random.uniform(0.15, 0.75, num_embers) * TARGET_W
    ey0 = np.random.uniform(0.40, 0.95, num_embers) * TARGET_H
    espeed = np.random.uniform(180.0, 320.0, num_embers)
    esway = np.random.uniform(10.0, 25.0, num_embers)
    eradius = np.random.choice([1, 2], size=num_embers, p=[0.7, 0.3])

    # High Bitrate CQ 14 for maximum high-resolution crispness
    proc = make_ffmpeg_process(dst, cq=14)
    t0 = time.time()
    cycle_h = 14.0  # Slow, thick viscous displacement

    for i in range(NUM_FRAMES):
        phase = (2.0 * np.pi * i) / NUM_FRAMES
        prog = i / NUM_FRAMES
        t1 = prog % 1.0
        t2 = (t1 + 0.5) % 1.0
        w_blend = np.sin(t1 * np.pi) ** 2.0

        # Slow, viscous downward magma advection on falls
        dy1 = (t1 - 0.5) * cycle_h * cataract_mask
        dy2 = (t2 - 0.5) * cycle_h * cataract_mask

        # Calm, hypnotic molten lake churning surface crawl
        dx_pool = np.sin(NY * 8.0 + phase) * 1.2 * pool_mask
        dy_pool = np.cos(NX * 6.0 + phase) * 0.8 * pool_mask

        remap_y1 = np.clip(Y_GRID - dy1 + dy_pool, 0, TARGET_H - 1).astype(np.float32)
        remap_y2 = np.clip(Y_GRID - dy2 + dy_pool, 0, TARGET_H - 1).astype(np.float32)
        remap_x = np.clip(X_GRID + dx_pool, 0, TARGET_W - 1).astype(np.float32)

        f1 = cv2.remap(img, remap_x, remap_y1, interpolation=cv2.INTER_LINEAR).astype(np.float32)
        f2 = cv2.remap(img, remap_x, remap_y2, interpolation=cv2.INTER_LINEAR).astype(np.float32)
        frame = f1 * (1.0 - w_blend) + f2 * w_blend

        # Incandescent molten glow pulse (rhythmic, slow 12s breathing)
        magma_pulse = (np.sin(phase) * 0.5 + 0.5) * lava_mask * 14.0
        frame[:, :, 1] += magma_pulse * 0.7  # Gold / Yellow
        frame[:, :, 2] += magma_pulse * 1.0  # Fiery Red

        # Fortress dwarven rune breathing
        rune_pulse = (np.sin(phase * 2.0) * 0.5 + 0.5) * runes_mask * 18.0
        frame[:, :, 1] += rune_pulse * 0.6
        frame[:, :, 2] += rune_pulse * 1.0

        frame_u8 = np.clip(frame, 0, 255).astype(np.uint8)

        # Draw rising glowing embers
        for k in range(num_embers):
            ey = int((ey0[k] - prog * espeed[k]) % TARGET_H)
            ex = int((ex0[k] + np.sin(phase * 1.5 + k) * esway[k]) % TARGET_W)
            r = eradius[k]
            cv2.circle(frame_u8, (ex, ey), r, (30, 160, 255), -1)

        proc.stdin.write(frame_u8.tobytes())
        if (i + 1) % 90 == 0:
            print(f"  Realm 06: Frame {i+1}/{NUM_FRAMES} ({(i+1)/NUM_FRAMES*100:.1f}%) rendered...", flush=True)

    proc.stdin.close()
    proc.wait()
    print(f"Realm 06 completed in {time.time() - t0:.1f}s!", flush=True)

if __name__ == "__main__":
    t_start = time.time()
    render_realm_09_autumn_valley()
    render_realm_03_mountain_aurora()
    render_realm_05_sky_citadel()
    render_realm_06_obsidian_forge()
    print(f"\nAll 4 Master Realms rendered in {time.time() - t_start:.1f}s!", flush=True)
