import cv2
import numpy as np
import subprocess
import os
import time

def render_starfall_soft_master():
    src_path = r"C:\Users\agung\Pictures\Wallpapers\Fantasy_RPG_Collection\10_celestial_starfall_spire_4k.jpg"
    out_file = r"C:\Users\agung\Pictures\Wallpapers\Fantasy_RPG_Collection\10_celestial_starfall_spire_live.mp4"
    print(f"Loading master source image: {src_path}...")
    base_img = cv2.imread(src_path)
    if base_img is None:
        raise FileNotFoundError(f"Cannot load image: {src_path}")

    # 2560x1440 @ 30 FPS, 8.0 seconds for an ultra-soft, relaxed loop (240 frames)
    target_w, target_h = 2560, 1440
    fps = 30
    duration = 8.0
    num_frames = int(duration * fps) # 240 frames

    print(f"Resizing master image to {target_w}x{target_h} via Lanczos-4...")
    img = cv2.resize(base_img, (target_w, target_h), interpolation=cv2.INTER_LANCZOS4)

    y_coords, x_coords = np.mgrid[0:target_h, 0:target_w].astype(np.float32)

    # 1. Galaxy Vortex at (0.301 * W, 0.240 * H)
    gal_cx = target_w * 0.301
    gal_cy = target_h * 0.240
    dx_gal = x_coords - gal_cx
    dy_gal = y_coords - gal_cy
    r_gal = np.sqrt(dx_gal**2 + dy_gal**2)
    angle_gal = np.arctan2(dy_gal, dx_gal)
    max_gal_r = target_w * 0.26
    gal_norm = np.clip(r_gal / max_gal_r, 0.0, 1.0)
    swirl_weight = ((1.0 - gal_norm) ** 2.2).astype(np.float32)
    gal_glow_mask = np.exp(-((r_gal / (target_w * 0.17))**2)).astype(np.float32)

    # 2. Armillary Sphere & Radiant Miniature Sun Core at (0.658 * W, 0.183 * H)
    arm_cx = target_w * 0.658
    arm_cy = target_h * 0.183
    dx_arm = x_coords - arm_cx
    dy_arm = y_coords - arm_cy
    r_arm = np.sqrt(dx_arm**2 + dy_arm**2)
    sun_core_mask = np.exp(-((r_arm / (target_w * 0.038))**2)).astype(np.float32)

    # 3. Cloud Ocean Mask (Left ocean below observatory: y in 0.55-0.85, x < 0.50)
    cloud_mask = np.exp(-((y_coords / target_h - 0.70)**2) / 0.016) * np.clip((0.52 * target_w - x_coords) / (0.15 * target_w), 0.0, 1.0)
    cloud_mask = cloud_mask.astype(np.float32)

    # 4. Extract Painted Streaks Mask from Source Image
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    angle_rad = np.radians(140.0) # Angle of painted streaks in artwork (~140 deg)
    dir_x = float(np.cos(angle_rad)) # -0.766
    dir_y = float(np.sin(angle_rad)) # +0.642

    k_len = 25
    k_streak = np.zeros((k_len, k_len), dtype=np.float32)
    for ki in range(k_len):
        kj = int((k_len - 1 - ki) * 0.84)
        if 0 <= kj < k_len:
            k_streak[ki, kj] = 1.0
    k_streak /= np.sum(k_streak)

    streak_filtered = cv2.filter2D(gray, cv2.CV_32F, k_streak)
    bg_blur = cv2.blur(gray, (21, 21)).astype(np.float32)
    raw_streak_mask = np.clip((streak_filtered - bg_blur) / 20.0, 0.0, 1.0)
    sky_cutoff = np.clip((0.56 * target_h - y_coords) / (0.06 * target_h), 0.0, 1.0)
    streak_mask = (raw_streak_mask * sky_cutoff).astype(np.float32)
    proj_coords = (x_coords * dir_x + y_coords * dir_y).astype(np.float32)

    # 5. Extract top painted streak positions for gentle celestial bolides
    _, streak_thresh = cv2.threshold((streak_mask * 255).astype(np.uint8), 75, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(streak_thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    anchored_streaks = []
    for c in contours:
        if cv2.contourArea(c) > 20:
            rect = cv2.minAreaRect(c)
            (rcx, rcy), (dim1, dim2), _ = rect
            length = max(dim1, dim2)
            width = min(dim1, dim2)
            if length > 28 and (length / (width + 1e-3)) > 2.2:
                anchored_streaks.append((rcx, rcy, length))

    anchored_streaks.sort(key=lambda s: s[2], reverse=True)
    top_streaks = anchored_streaks[:6] # 6 major streaks for tranquil, uncluttered sky

    bolides = []
    for idx, (scx, scy, slen) in enumerate(top_streaks):
        bolides.append({
            'start_t': (idx / float(len(top_streaks))),
            'life_dur': 0.28, # Soft, longer duration for serene glide
            'anchor_x': scx,
            'anchor_y': scy,
            'trail_len': max(slen * 1.4, 110.0),
            'color': (255, 248, 230) if idx % 2 == 0 else (255, 235, 255),
            'bloom_color': (255, 190, 100) if idx % 2 == 0 else (210, 140, 255)
        })

    # 6. Cosmic Background Stars
    np.random.seed(555)
    num_stars = 65
    star_x = np.random.uniform(20, target_w - 20, num_stars)
    star_y = np.random.uniform(20, target_h * 0.52, num_stars)
    star_freq = np.random.choice([1, 2], size=num_stars)
    star_phase_offset = np.random.uniform(0, 2 * np.pi, num_stars)
    star_alpha = np.random.uniform(0.25, 0.65, num_stars)

    print(f"Encoding master soft video via FFmpeg NVENC to {out_file}...")

    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", f"{target_w}x{target_h}",
        "-pix_fmt", "bgr24",
        "-r", str(fps),
        "-i", "-",
        "-c:v", "h264_nvenc",
        "-preset", "p5",
        "-cq", "18",
        "-pix_fmt", "yuv420p",
        out_file
    ]

    proc = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)

    for i in range(num_frames):
        t_norm = i / float(num_frames)
        phase = 2.0 * np.pi * t_norm
        cos_p = np.cos(phase)
        sin_p = np.sin(phase)

        # -------------------------------------------------------------
        # A. Gentle, Soft Galaxy Swirl (Relaxed Pacing)
        # -------------------------------------------------------------
        swirl_angle = 0.024 * sin_p * swirl_weight
        new_angle = angle_gal + swirl_angle
        r_pulse = r_gal * (1.0 + 0.005 * np.sin(phase * 2.0) * swirl_weight)

        map_x = (gal_cx + r_pulse * np.cos(new_angle)).astype(np.float32)
        map_y = (gal_cy + r_pulse * np.sin(new_angle)).astype(np.float32)

        # Soft cloud drift
        cloud_drift = 5.0 * np.sin(phase + y_coords / 45.0) * cloud_mask
        map_x += cloud_drift

        # -------------------------------------------------------------
        # B. Gentle Traveling Luminescence along Painted Streaks
        # -------------------------------------------------------------
        w1 = np.maximum(0.0, np.sin((proj_coords / 240.0) - phase * 2.0)) ** 7.0
        w2 = np.maximum(0.0, np.sin((proj_coords / 320.0) - phase * 2.5 - 1.5)) ** 8.0
        streak_surge = ((w1 * 0.9 + w2 * 1.0) * streak_mask).astype(np.float32)

        # Subtle micro-displacement
        map_x += dir_x * (streak_surge * 3.2)
        map_y += dir_y * (streak_surge * 3.2)

        frame = cv2.remap(img, map_x, map_y, interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        frame = frame.astype(np.float32)

        # -------------------------------------------------------------
        # C. Soft, Calm Lighting
        # -------------------------------------------------------------
        # Galaxy breath
        gal_pulse = (sin_p * 0.5 + 0.5) * 16.0
        frame[:, :, 0] += gal_pulse * gal_glow_mask * 1.1 # Blue
        frame[:, :, 2] += gal_pulse * gal_glow_mask * 0.8 # Magenta

        # Miniature Sun starlight
        sun_pulse = (np.sin(phase * 2.0) * 0.5 + 0.5) * 32.0
        frame[:, :, 1] += sun_pulse * sun_core_mask * 0.7 # Green
        frame[:, :, 2] += sun_pulse * sun_core_mask * 1.0 # Amber

        # Painted streak soft flare
        frame[:, :, 0] += streak_surge * 50.0
        frame[:, :, 1] += streak_surge * 58.0
        frame[:, :, 2] += streak_surge * 72.0

        frame_u8 = np.clip(frame, 0, 255).astype(np.uint8)

        # Twinkling stars
        for s in range(num_stars):
            twinkle = np.sin(phase * star_freq[s] + star_phase_offset[s]) * 0.5 + 0.5
            val = int(255 * star_alpha[s] * (0.4 + 0.6 * twinkle))
            cv2.circle(frame_u8, (int(star_x[s]), int(star_y[s])), 1, (val, val, val), -1, lineType=cv2.LINE_AA)

        # E. Soft, Serene Bolides
        bloom_layer = np.zeros_like(frame_u8)

        for b in bolides:
            t_rel = (t_norm - b['start_t']) % 1.0
            if t_rel < b['life_dur']:
                prog = t_rel / b['life_dur']

                dist = (prog - 0.5) * (b['trail_len'] * 2.0)
                hx = int(b['anchor_x'] + dir_x * dist)
                hy = int(b['anchor_y'] + dir_y * dist)

                cur_trail = b['trail_len'] * np.sin(prog * np.pi)
                tx = int(hx - dir_x * cur_trail)
                ty = int(hy - dir_y * cur_trail)

                alpha = np.sin(prog * np.pi) ** 1.5

                b_val = int(170 * alpha)
                b_col = tuple(int(c * (b_val / 255.0)) for c in b['bloom_color'])
                cv2.line(bloom_layer, (tx, ty), (hx, hy), b_col, 3, lineType=cv2.LINE_AA)
                cv2.circle(bloom_layer, (hx, hy), 3, b_col, -1, lineType=cv2.LINE_AA)

                c_val = int(240 * alpha)
                c_col = tuple(int(c * (c_val / 255.0)) for c in b['color'])
                cv2.line(frame_u8, (tx, ty), (hx, hy), c_col, 2, lineType=cv2.LINE_AA)
                cv2.circle(frame_u8, (hx, hy), 2, (c_val, c_val, c_val), -1, lineType=cv2.LINE_AA)

        frame_u8 = cv2.add(frame_u8, bloom_layer)
        proc.stdin.write(frame_u8.tobytes())

        if i % 40 == 0:
            print(f"Rendering frame {i}/{num_frames} ({(i/num_frames)*100:.1f}%)", flush=True)

    proc.stdin.close()
    proc.wait()
    file_size_mb = os.path.getsize(out_file) / (1024 * 1024)
    print(f"\nMaster Soft Starfall Video generated successfully: {out_file} ({file_size_mb:.2f} MB)", flush=True)

if __name__ == "__main__":
    t0 = time.time()
    render_starfall_soft_master()
    print(f"Total render time: {time.time()-t0:.2f}s")
