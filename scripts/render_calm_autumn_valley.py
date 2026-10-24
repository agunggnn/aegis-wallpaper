import os
import cv2
import numpy as np
import subprocess
import time
import shutil

BASE_DIR = r"C:\Users\agung\Pictures\Wallpapers\Fantasy_RPG_Collection"
SRC_IMG = os.path.join(BASE_DIR, "09_autumn_dragon_valley_4k.jpg")
DST_VID = os.path.join(BASE_DIR, "09_autumn_dragon_valley_live.mp4")

TARGET_W = 2560
TARGET_H = 1440
FPS = 30
DURATION = 12.0  # 12-second ultra-calm meditative seamless loop
NUM_FRAMES = int(FPS * DURATION)  # 360 frames

def make_maple_leaf_sprite(size=24):
    """Generate high-quality 5-lobe Japanese momiji maple leaf alpha mask."""
    leaf = np.zeros((size, size), dtype=np.uint8)
    pts = np.array([
        [size * 0.50, size * 0.05],  # tip central
        [size * 0.42, size * 0.25],
        [size * 0.20, size * 0.15],  # tip upper-left
        [size * 0.28, size * 0.40],
        [size * 0.08, size * 0.48],  # tip mid-left
        [size * 0.35, size * 0.65],
        [size * 0.48, size * 0.90],  # stem base
        [size * 0.52, size * 0.90],
        [size * 0.65, size * 0.65],
        [size * 0.92, size * 0.48],  # tip mid-right
        [size * 0.72, size * 0.40],
        [size * 0.80, size * 0.15],  # tip upper-right
        [size * 0.58, size * 0.25]
    ], np.int32)
    cv2.fillPoly(leaf, [pts], 255)
    leaf = cv2.GaussianBlur(leaf, (3, 3), 0)
    return leaf.astype(np.float32) / 255.0

def render_calm_autumn_valley():
    print(f"Loading master artwork: {SRC_IMG}")
    img_raw = cv2.imread(SRC_IMG)
    if img_raw is None:
        raise FileNotFoundError(f"Cannot load image: {SRC_IMG}")
    
    img = cv2.resize(img_raw, (TARGET_W, TARGET_H), interpolation=cv2.INTER_LANCZOS4)
    b_chan, g_chan, r_chan = cv2.split(img.astype(np.float32))

    y_grid, x_grid = np.mgrid[0:TARGET_H, 0:TARGET_W].astype(np.float32)
    ny = y_grid / TARGET_H
    nx = x_grid / TARGET_W

    print("Computing precision masks for waterfalls, lake pool, mist, and lanterns...")
    # 1. Emerald Lake Pool Mask
    is_lake = (ny >= 0.70) & (nx >= 0.16) & (nx <= 0.66) & (g_chan > 60) & (g_chan >= r_chan * 0.92) & (b_chan > 50) & (r_chan < 110)
    lake_raw = (is_lake.astype(np.uint8)) * 255
    lake_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    lake_clean = cv2.morphologyEx(lake_raw, cv2.MORPH_CLOSE, lake_kernel)
    lake_mask = cv2.GaussianBlur(lake_clean.astype(np.float32) / 255.0, (15, 15), 0)

    # 2. Waterfalls & Stream Cascades Mask (Frozen cliffs, rocks, and temples)
    is_upper_fall = (nx >= 0.35) & (nx <= 0.44) & (ny >= 0.32) & (ny <= 0.52) & (b_chan > 120) & (b_chan > 0.82 * r_chan)
    is_lower_fall = (nx >= 0.38) & (nx <= 0.50) & (ny >= 0.52) & (ny <= 0.73) & (b_chan > 120) & (b_chan > 0.82 * r_chan)
    is_stream = (nx >= 0.52) & (nx <= 0.63) & (ny >= 0.58) & (ny <= 0.74) & (b_chan > 115) & (b_chan > 0.80 * r_chan)

    is_falls = is_upper_fall | is_lower_fall | is_stream
    falls_raw = (is_falls.astype(np.uint8)) * 255
    falls_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 7))
    falls_clean = cv2.morphologyEx(falls_raw, cv2.MORPH_CLOSE, falls_kernel)
    falls_mask = cv2.GaussianBlur(falls_clean.astype(np.float32) / 255.0, (7, 11), 0)

    # 3. Plunge pool rising mist
    plunge_dist_sq = ((nx - 0.45)**2) / (0.09**2) + ((ny - 0.71)**2) / (0.045**2)
    mist_mask = np.clip(np.exp(-plunge_dist_sq).astype(np.float32), 0.0, 1.0)

    # 4. Sunbeam godrays in upper right valley gorge
    godray_dist_sq = ((nx - 0.80)**2) / (0.18**2) + ((ny - 0.22)**2) / (0.15**2)
    godray_mask = np.clip(np.exp(-godray_dist_sq).astype(np.float32), 0.0, 1.0)

    # 5. Lantern light radial masks
    lantern_mask = np.zeros((TARGET_H, TARGET_W), dtype=np.float32)
    lantern_coords = [
        (int(0.730 * TARGET_W), int(0.628 * TARGET_H), 32),  # Torii left lantern
        (int(0.853 * TARGET_W), int(0.625 * TARGET_H), 32),  # Torii right lantern
        (int(0.796 * TARGET_W), int(0.780 * TARGET_H), 26),  # Traveler lantern
    ]
    for lx, ly, rad in lantern_coords:
        l_dist_sq = ((x_grid - lx)**2 + (y_grid - ly)**2) / (rad**2)
        lantern_mask += np.clip(np.exp(-l_dist_sq), 0.0, 1.0)
    lantern_mask = np.clip(lantern_mask, 0.0, 1.0)

    # 6. Maple leaf configuration (14 serene leaves)
    np.random.seed(42)
    num_leaves = 14
    leaf_sprites = [make_maple_leaf_sprite(s) for s in [14, 16, 18, 20]]
    leaves = []
    
    # Pre-select serene leaf properties
    leaf_colors = [
        (25, 40, 210),   # Crimson
        (20, 130, 245),  # Golden Amber
        (30, 85, 220),   # Warm Scarlet
        (15, 110, 235),  # Honey Orange
    ]

    for k in range(num_leaves):
        leaves.append({
            'x_start': np.random.uniform(0.12, 0.82) * TARGET_W,
            'y_start': np.random.uniform(0.18, 0.72) * TARGET_H,
            'fall_dist': np.random.uniform(28.0, 42.0),       # Ultra-slow descent (~3px / sec)
            'sway_amp': np.random.uniform(16.0, 26.0),        # Gentle pendulum sway
            'phase_offset': np.random.uniform(0.0, 1.0),      # Staggered lifecycle
            'base_angle': np.random.uniform(0.0, 360.0),
            'rot_amp': np.random.uniform(15.0, 30.0),
            'color': leaf_colors[k % len(leaf_colors)],
            'sprite': leaf_sprites[k % len(leaf_sprites)],
            'max_alpha': np.random.uniform(0.70, 0.88),
        })

    print(f"Starting NVENC render to {DST_VID} ({NUM_FRAMES} frames @ {FPS} FPS)...")
    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", f"{TARGET_W}x{TARGET_H}",
        "-pix_fmt", "bgr24",
        "-r", str(FPS),
        "-i", "-",
        "-c:v", "h264_nvenc",
        "-preset", "p5",
        "-cq", "18",
        "-pix_fmt", "yuv420p",
        DST_VID
    ]

    proc = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    t0 = time.time()

    for i in range(NUM_FRAMES):
        phase = (2.0 * np.pi * i) / NUM_FRAMES

        # A. Water Cascade Flow (Ultra-smooth 2-cycle wave over 12s, max 1.5px displacement)
        fall_disp = np.sin(ny * 22.0 - phase * 2.0) * 1.5 * falls_mask
        
        # B. Emerald Lake Breathing (Tranquil, glassy 1-cycle wave over 12s, max 0.4px displacement)
        lake_disp = np.sin(nx * 6.0 + phase) * 0.4 * lake_mask

        # Remap Y
        remap_y = np.clip(y_grid + fall_disp + lake_disp, 0, TARGET_H - 1).astype(np.float32)
        frame = cv2.remap(img, x_grid, remap_y, interpolation=cv2.INTER_LINEAR).astype(np.float32)

        # C. Waterfall crystalline sparkle (Gentle luminance gleam, period 6s)
        fall_sparkle = (np.sin(ny * 26.0 - phase * 2.0) * 0.5 + 0.5) ** 1.5 * falls_mask * 12.0
        frame[:, :, 0] += fall_sparkle * 1.15  # Blue
        frame[:, :, 1] += fall_sparkle * 1.05  # Green
        frame[:, :, 2] += fall_sparkle * 0.90  # Red

        # D. Emerald Lake gentle sunlight caress (Slow, wide sheen)
        lake_sheen = (np.sin(nx * 4.0 + ny * 2.0 + phase) * 0.5 + 0.5) * lake_mask * 6.0
        frame[:, :, 0] += lake_sheen * 0.7
        frame[:, :, 1] += lake_sheen * 1.1
        frame[:, :, 2] += lake_sheen * 0.6

        # E. Plunge pool gentle mist pulse
        mist_pulse = (np.sin(phase) * 0.5 + 0.5) * mist_mask * 8.0
        frame[:, :, 0] += mist_pulse * 1.05
        frame[:, :, 1] += mist_pulse * 0.95
        frame[:, :, 2] += mist_pulse * 0.85

        # F. Torii & Traveler lanterns warm golden breathing (Slow, peaceful candlelight)
        lantern_breathe = (np.sin(phase * 1.5) * 0.5 + 0.5) * lantern_mask * 14.0
        frame[:, :, 0] += lantern_breathe * 0.25  # Amber gold (low blue)
        frame[:, :, 1] += lantern_breathe * 0.70  # Warm amber (medium green)
        frame[:, :, 2] += lantern_breathe * 1.00  # Radiant gold (high red)

        # G. Valley Sunbeams gentle golden godray shimmer
        godray_shimmer = (np.sin(phase) * 0.5 + 0.5) * godray_mask * 5.0
        frame[:, :, 0] += godray_shimmer * 0.4
        frame[:, :, 1] += godray_shimmer * 0.8
        frame[:, :, 2] += godray_shimmer * 1.0

        # Clip frame to valid uint8 range
        frame_u8 = np.clip(frame, 0, 255).astype(np.uint8)

        # H. Serene Drifting Japanese Maple Leaves (Momiji)
        for leaf in leaves:
            prog = (i / NUM_FRAMES + leaf['phase_offset']) % 1.0
            
            # Smooth bell-curve alpha fade (0 at birth, 1 at midpoint, 0 at fade-out) -> 100% seamless loop!
            alpha = (np.sin(prog * np.pi) ** 2.0) * leaf['max_alpha']
            if alpha < 0.01:
                continue

            # Position
            cur_y = leaf['y_start'] + prog * leaf['fall_dist']
            cur_x = leaf['x_start'] + np.sin(prog * 2.0 * np.pi) * leaf['sway_amp']
            
            # Rotation
            cur_angle = leaf['base_angle'] + np.cos(prog * 2.0 * np.pi) * leaf['rot_amp']

            # Rotate leaf sprite
            sprite = leaf['sprite']
            sh, sw = sprite.shape
            M = cv2.getRotationMatrix2D((sw / 2, sh / 2), cur_angle, 1.0)
            rot_mask = cv2.warpAffine(sprite, M, (sw, sh), flags=cv2.INTER_LINEAR)

            # Sub-pixel blit
            ix, iy = int(round(cur_x)), int(round(cur_y))
            x1 = max(0, ix - sw // 2)
            y1 = max(0, iy - sh // 2)
            x2 = min(TARGET_W, x1 + sw)
            y2 = min(TARGET_H, y1 + sh)

            sx1 = x1 - (ix - sw // 2)
            sy1 = y1 - (iy - sh // 2)
            sx2 = sx1 + (x2 - x1)
            sy2 = sy1 + (y2 - y1)

            if x2 > x1 and y2 > y1 and sx2 > sx1 and sy2 > sy1:
                sub_mask = rot_mask[sy1:sy2, sx1:sx2] * alpha
                roi = frame_u8[y1:y2, x1:x2].astype(np.float32)
                color = np.array(leaf['color'], dtype=np.float32)

                for c in range(3):
                    roi[:, :, c] = roi[:, :, c] * (1.0 - sub_mask) + color[c] * sub_mask

                frame_u8[y1:y2, x1:x2] = np.clip(roi, 0, 255).astype(np.uint8)

        proc.stdin.write(frame_u8.tobytes())

        if (i + 1) % 60 == 0 or i == NUM_FRAMES - 1:
            print(f"  Frame {i+1}/{NUM_FRAMES} ({(i+1)/NUM_FRAMES*100:.1f}%) rendered...")

    proc.stdin.close()
    proc.wait()
    dt = time.time() - t0
    size_mb = os.path.getsize(DST_VID) / (1024 * 1024)
    print(f"\nRender complete in {dt:.1f}s! File size: {size_mb:.2f} MB")

if __name__ == "__main__":
    render_calm_autumn_valley()
