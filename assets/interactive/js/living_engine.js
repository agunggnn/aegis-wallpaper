/**
 * =============================================================================
 * Aegis Sovereign WebGL Living Shader Engine
 * =============================================================================
 * Transforms static 4K master UHD artworks into living, breathing worlds:
 *  - Cosmic Galaxy Vortex Swirl (Realm 10 & 4)
 *  - 2-Phase Seamless Water & Waterfall Flow (Realm 0, 8, 3)
 *  - Boiling Incandescent Molten Magma Churn (Realm 5)
 *  - Wind Foliage & Maple Tree Sway (Realm 1, 8)
 *  - Atmospheric Cloud Fall & Deep-Sea Refractions (Realm 4, 6)
 *  - 2.5D Parallax Depth Shifting with Mouse & Ambient Lissajous Motion
 * 
 * Hardware-accelerated via WebGL (DirectX/Vulkan/GPU). 60FPS with ~0% CPU.
 * =============================================================================
 */

class LivingShaderEngine {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        if (!this.canvas) {
            console.warn('[LivingEngine] Canvas not found:', canvasId);
            return;
        }

        this.gl = this.canvas.getContext('webgl', { 
            alpha: false, 
            antialias: true, 
            depth: false, 
            stencil: false,
            preserveDrawingBuffer: false,
            powerPreference: 'high-performance'
        }) || this.canvas.getContext('experimental-webgl');

        if (!this.gl) {
            console.error('[LivingEngine] WebGL not supported, falling back to static 4K layer.');
            return;
        }

        this.program = null;
        this.texture = null;
        this.currentImageSrc = '';
        this.currentRealm = 9; // Default: Starfall Observatory
        this.parallaxStrength = 1.0;
        this.flowSpeed = 1.0;
        this.motionEnabled = true;
        this.mouse = { x: 0.5, y: 0.5, targetX: 0.5, targetY: 0.5 };
        this.startTime = performance.now();
        this.isLoaded = false;
        this.textureWidth = 3840;
        this.textureHeight = 2160;

        this.initGL();
        this.setupEventListeners();
    }

    initGL() {
        const gl = this.gl;

        const vsSource = `
            attribute vec2 a_position;
            varying vec2 v_uv;
            void main() {
                v_uv = (a_position + 1.0) * 0.5;
                v_uv.y = 1.0 - v_uv.y; // Flip Y for WebGL texture sampling
                gl_Position = vec4(a_position, 0.0, 1.0);
            }
        `;

        const fsSource = `
            precision highp float;
            varying vec2 v_uv;

            uniform sampler2D u_image;
            uniform float u_time;
            uniform vec2 u_resolution;
            uniform vec2 u_mouse;
            uniform int u_realm;
            uniform float u_parallax;
            uniform float u_flowSpeed;
            uniform float u_motionEnabled;

            // Pseudo-random noise
            float hash(vec2 p) {
                p = fract(p * vec2(123.34, 456.21));
                p += dot(p, p + 45.32);
                return fract(p.x * p.y);
            }

            void main() {
                vec2 uv = v_uv;
                float aspect = u_resolution.x / u_resolution.y;

                // -------------------------------------------------------------
                // 1. 2.5D Parallax Depth Estimation & Shift
                // -------------------------------------------------------------
                // Ambient Lissajous drift when mouse is stationary
                vec2 ambientDrift = vec2(
                    sin(u_time * 0.35) * 0.06,
                    cos(u_time * 0.28) * 0.04
                );
                vec2 mouseDelta = (u_mouse - vec2(0.5, 0.5)) * 2.0 + ambientDrift;

                // Depth profile approximation:
                // Upper region (sky/galaxy/mountains) has low depth -> moves with background.
                // Lower/Mid region (spire dome, trees, foreground fortress) has high depth -> shifts more.
                float depth = smoothstep(0.15, 0.95, uv.y);
                if (u_realm == 9) {
                    // Starfall: Foreground observatory dome starts at y > 0.48
                    depth = smoothstep(0.40, 0.85, uv.y);
                } else if (u_realm == 8) {
                    // Autumn valley: Rocks and trees in foreground
                    depth = smoothstep(0.35, 0.90, uv.y);
                } else if (u_realm == 0) {
                    // Citadel: Bridge & water in foreground
                    depth = smoothstep(0.50, 0.95, uv.y);
                }

                vec2 parallaxOffset = mouseDelta * 0.012 * u_parallax * (depth - 0.5);
                uv += parallaxOffset;

                // If motion disabled, sample image directly with parallax
                if (u_motionEnabled < 0.5) {
                    gl_FragColor = texture2D(u_image, uv);
                    return;
                }

                // -------------------------------------------------------------
                // 2. Realm-Specific Object Motion Shaders
                // -------------------------------------------------------------
                vec4 finalColor = vec4(0.0);

                if (u_realm == 9) {
                    // =========================================================
                    // REALM 10: Celestial Starfall Spire
                    // COSMIC GALAXY VORTEX SWIRL + ACCRETION SPIRAL TWIST
                    // =========================================================
                    vec2 galCenter = vec2(0.50, 0.245);
                    vec2 toGal = (uv - galCenter);
                    toGal.x *= aspect; // Equal aspect circle
                    float dist = length(toGal);
                    float galRadius = 0.46;

                    if (dist < galRadius) {
                        float normDist = dist / galRadius;
                        // Logarithmic vortex angular swirl strength
                        float swirlFactor = pow(1.0 - normDist, 2.0);
                        float angle = u_time * 0.075 * u_flowSpeed * swirlFactor;
                        
                        // Rotate coordinates around galaxy center
                        float cosA = cos(angle);
                        float sinA = sin(angle);
                        vec2 rotated = vec2(
                            toGal.x * cosA - toGal.y * sinA,
                            toGal.x * sinA + toGal.y * cosA
                        );

                        // Subtle breathing accretion suction
                        float pulse = sin(u_time * 0.8 + normDist * 18.0) * 0.0025 * swirlFactor;
                        rotated += normalize(rotated) * pulse;

                        rotated.x /= aspect;
                        uv = galCenter + rotated;
                    }

                    vec4 col = texture2D(u_image, uv);

                    // Soft luminous breathing glow at the galactic accretion core
                    if (dist < 0.28) {
                        float coreGlow = pow(1.0 - dist / 0.28, 2.5) * (0.08 + 0.04 * sin(u_time * 1.2));
                        col.rgb += vec3(0.5, 0.25, 0.9) * coreGlow;
                    }

                    finalColor = col;

                } else if (u_realm == 0) {
                    // =========================================================
                    // REALM 01: Valerius Citadel Twilight
                    // SEAMLESS RIVER FLOW & WATER SURFACE RIPPLES
                    // =========================================================
                    // River occupies lower central portion (uv.y > 0.65)
                    if (uv.y > 0.60 && abs(uv.x - 0.5) < 0.40) {
                        float waterFactor = smoothstep(0.60, 0.75, uv.y) * smoothstep(0.40, 0.20, abs(uv.x - 0.5));
                        float speed = 0.14 * u_flowSpeed;
                        
                        // 2-Phase Cycle UV Blend
                        float t1 = fract(u_time * speed);
                        float t2 = fract(u_time * speed + 0.5);
                        float blend = abs(2.0 * t1 - 1.0);

                        vec2 flowDir = vec2(sin(uv.y * 12.0) * 0.003, 0.035 * (1.0 + (uv.y - 0.6) * 1.5));
                        vec4 c1 = texture2D(u_image, uv + flowDir * t1);
                        vec4 c2 = texture2D(u_image, uv + flowDir * t2);
                        vec4 waterCol = mix(c1, c2, blend);

                        // Shimmering river caustics
                        float shimmer = sin(uv.x * 45.0 + uv.y * 30.0 + u_time * 2.5) * 0.03 * waterFactor;
                        waterCol.rgb += vec3(shimmer * 0.5, shimmer * 0.8, shimmer);

                        vec4 baseCol = texture2D(u_image, uv);
                        finalColor = mix(baseCol, waterCol, waterFactor);
                    } else {
                        finalColor = texture2D(u_image, uv);
                    }

                } else if (u_realm == 5) {
                    // =========================================================
                    // REALM 06: Volcanic Obsidian Forge
                    // MOLTEN BOILING MAGMA CHURN & HEAT DISTORTION
                    // =========================================================
                    if (uv.y > 0.54) {
                        float magmaFactor = smoothstep(0.54, 0.68, uv.y);
                        // Multi-octave wave displacement
                        vec2 wave = vec2(
                            sin(uv.y * 24.0 + u_time * 1.6 * u_flowSpeed) * 0.006,
                            cos(uv.x * 20.0 - u_time * 1.3 * u_flowSpeed) * 0.005
                        );
                        vec4 magmaCol = texture2D(u_image, uv + wave * magmaFactor);

                        // Incandescent heat breathing
                        float heat = (sin(u_time * 2.2 + uv.x * 12.0) * 0.5 + 0.5) * 0.14 * magmaFactor;
                        magmaCol.rgb += vec3(heat * 1.2, heat * 0.4, 0.0);

                        vec4 baseCol = texture2D(u_image, uv);
                        finalColor = mix(baseCol, magmaCol, magmaFactor);
                    } else {
                        // Subtle heat haze shimmering above forge
                        float haze = sin(uv.y * 50.0 + u_time * 4.0) * 0.002 * (1.0 - uv.y);
                        uv.x += haze;
                        finalColor = texture2D(u_image, uv);
                    }

                } else if (u_realm == 8) {
                    // =========================================================
                    // REALM 09: Autumn Dragon Valley
                    // WATERFALL FLOW CASCADE & MAPLE FOLIAGE WIND SWAY (ULTRA-CALM & SERENE)
                    // =========================================================
                    // 1. Waterfalls (around x: 0.35-0.65, y: 0.32-0.75)
                    if (uv.x > 0.35 && uv.x < 0.65 && uv.y > 0.32 && uv.y < 0.78) {
                        float wf = smoothstep(0.35, 0.42, uv.x) * smoothstep(0.65, 0.58, uv.x) *
                                  smoothstep(0.32, 0.40, uv.y) * smoothstep(0.78, 0.70, uv.y);
                        
                        // Ultra-calm, slow cascade speed (0.06 instead of 0.28)
                        float speed = 0.06 * u_flowSpeed;
                        float t1 = fract(u_time * speed);
                        float t2 = fract(u_time * speed + 0.5);
                        float blend = abs(2.0 * t1 - 1.0);

                        // Subtle displacement (0.012 instead of 0.05)
                        vec2 flowDir = vec2(0.0, 0.012);
                        vec4 c1 = texture2D(u_image, uv + flowDir * t1);
                        vec4 c2 = texture2D(u_image, uv + flowDir * t2);
                        vec4 waterCol = mix(c1, c2, blend);

                        vec4 baseCol = texture2D(u_image, uv);
                        finalColor = mix(baseCol, waterCol, wf);
                    } else {
                        // 2. Wind Foliage Sway on Maple Canopy (upper & left foliage) - Gentle Autumn Breeze
                        if (uv.y < 0.50 || uv.x < 0.35) {
                            float swayStrength = smoothstep(0.1, 0.5, uv.y) * 0.0012 * u_flowSpeed;
                            float sway = sin(u_time * 0.6 + uv.y * 8.0 + uv.x * 4.0) * swayStrength;
                            uv.x += sway;
                        }
                        finalColor = texture2D(u_image, uv);
                    }

                } else if (u_realm == 1) {
                    // =========================================================
                    // REALM 02: Eldertree Forest Shrine
                    // FOLIAGE SWAY & ARCANE RUNES PULSATION
                    // =========================================================
                    float foliageSway = sin(u_time * 1.4 + uv.y * 10.0) * 0.003 * u_flowSpeed;
                    if (uv.y < 0.55) uv.x += foliageSway;

                    vec4 col = texture2D(u_image, uv);
                    
                    // Arcane mana rune pulsation in central shrine stone
                    if (uv.y > 0.45 && uv.y < 0.78 && abs(uv.x - 0.5) < 0.25) {
                        float runePulse = sin(u_time * 2.0) * 0.5 + 0.5;
                        col.rgb += vec3(0.05, 0.18, 0.14) * runePulse * 0.25;
                    }
                    finalColor = col;

                } else if (u_realm == 4) {
                    // =========================================================
                    // REALM 05: Floating Sky Citadel of Aetheria
                    // HORIZONTAL CLOUD DRIFT & VERTICAL CLOUDFALLS
                    // =========================================================
                    // Gentle cloud drift in upper sky
                    if (uv.y < 0.40) {
                        float cloudSpeed = u_time * 0.003 * u_flowSpeed;
                        vec2 cloudUV = uv;
                        cloudUV.x = fract(cloudUV.x - cloudSpeed);
                        vec4 skyCol = texture2D(u_image, cloudUV);
                        vec4 baseCol = texture2D(u_image, uv);
                        finalColor = mix(baseCol, skyCol, 0.35);
                    } else if (uv.y > 0.50 && abs(uv.x - 0.5) < 0.35) {
                        // Cloudfall cascade
                        float t1 = fract(u_time * 0.15 * u_flowSpeed);
                        float t2 = fract(u_time * 0.15 * u_flowSpeed + 0.5);
                        float blend = abs(2.0 * t1 - 1.0);
                        vec4 c1 = texture2D(u_image, uv + vec2(0.0, 0.03 * t1));
                        vec4 c2 = texture2D(u_image, uv + vec2(0.0, 0.03 * t2));
                        finalColor = mix(c1, c2, blend);
                    } else {
                        finalColor = texture2D(u_image, uv);
                    }

                } else if (u_realm == 6) {
                    // =========================================================
                    // REALM 07: Sunken Coral Atlantis
                    // UNDERWATER OPTICAL CAUSTICS & CURRENT REFRACTION
                    // =========================================================
                    vec2 causticUV = uv * 6.0;
                    float c1 = sin(causticUV.x + u_time * 1.5 * u_flowSpeed + sin(causticUV.y * 1.2));
                    float c2 = cos(causticUV.y + u_time * 1.2 * u_flowSpeed + cos(causticUV.x * 1.4));
                    vec2 ripple = vec2(c1, c2) * 0.004;

                    vec4 col = texture2D(u_image, uv + ripple);
                    float lightBand = (c1 * c2) * 0.06;
                    col.rgb += vec3(0.0, lightBand * 0.8, lightBand);
                    finalColor = col;

                } else if (u_realm == 2) {
                    // =========================================================
                    // REALM 03: Mountain Aurora Fortress
                    // NORTHERN LIGHTS UNDULATION & EMERALD RADIANCE
                    // =========================================================
                    if (uv.y < 0.42) {
                        float wave = sin(uv.x * 8.0 + u_time * 1.2 * u_flowSpeed) * 0.006;
                        uv.y += wave;
                        vec4 col = texture2D(u_image, uv);
                        float auroraBreath = (sin(u_time * 0.8 + uv.x * 4.0) * 0.5 + 0.5) * 0.12;
                        col.rgb += vec3(0.02, 0.15, 0.08) * auroraBreath * (1.0 - uv.y / 0.42);
                        finalColor = col;
                    } else {
                        finalColor = texture2D(u_image, uv);
                    }

                } else if (u_realm == 3) {
                    // =========================================================
                    // REALM 04: Celestial Dunes Oasis
                    // OASIS WATER REFLECTIONS & HEAT HAZE MIRAGE
                    // =========================================================
                    if (uv.y > 0.62 && abs(uv.x - 0.5) < 0.38) {
                        vec2 ripple = vec2(
                            sin(uv.y * 30.0 + u_time * 2.0 * u_flowSpeed) * 0.004,
                            cos(uv.x * 25.0 + u_time * 1.8 * u_flowSpeed) * 0.003
                        );
                        finalColor = texture2D(u_image, uv + ripple);
                    } else {
                        finalColor = texture2D(u_image, uv);
                    }

                } else if (u_realm == 7) {
                    // =========================================================
                    // REALM 08: Cyber-Aegis Bastion Neo-Tokyo
                    // HOLOGRAPHIC SHIELD SCANLINES & WET PAVEMENT REFLECTION
                    // =========================================================
                    vec4 col = texture2D(u_image, uv);
                    // Scanline barrier
                    float scanline = sin(uv.y * 300.0 - u_time * 8.0) * 0.02;
                    col.rgb += vec3(0.0, scanline * 0.6, scanline);
                    finalColor = col;

                } else {
                    finalColor = texture2D(u_image, uv);
                }

                gl_FragColor = finalColor;
            }
        `;

        this.program = this.createProgram(gl, vsSource, fsSource);
        if (!this.program) {
            console.error('[LivingEngine] Failed to compile shaders.');
            return;
        }

        // Fullscreen quad buffer
        const positionBuffer = gl.createBuffer();
        gl.bindBuffer(gl.ARRAY_BUFFER, positionBuffer);
        gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([
            -1.0, -1.0,
             1.0, -1.0,
            -1.0,  1.0,
            -1.0,  1.0,
             1.0, -1.0,
             1.0,  1.0
        ]), gl.STATIC_DRAW);

        this.positionLocation = gl.getAttribLocation(this.program, 'a_position');
        gl.enableVertexAttribArray(this.positionLocation);
        gl.vertexAttribPointer(this.positionLocation, 2, gl.FLOAT, false, 0, 0);

        // Uniform locations
        this.uniforms = {
            image: gl.getUniformLocation(this.program, 'u_image'),
            time: gl.getUniformLocation(this.program, 'u_time'),
            resolution: gl.getUniformLocation(this.program, 'u_resolution'),
            mouse: gl.getUniformLocation(this.program, 'u_mouse'),
            realm: gl.getUniformLocation(this.program, 'u_realm'),
            parallax: gl.getUniformLocation(this.program, 'u_parallax'),
            flowSpeed: gl.getUniformLocation(this.program, 'u_flowSpeed'),
            motionEnabled: gl.getUniformLocation(this.program, 'u_motionEnabled')
        };

        // Create 4K Texture
        this.texture = gl.createTexture();
        gl.bindTexture(gl.TEXTURE_2D, this.texture);
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
        gl.TEXTURE_WRAP_T = 0x2803;
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);

        // Initial placeholder 1x1 black pixel
        gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, 1, 1, 0, gl.RGBA, gl.UNSIGNED_BYTE, new Uint8Array([10, 15, 30, 255]));

        this.resize();
    }

    createProgram(gl, vsSource, fsSource) {
        const vs = this.compileShader(gl, vsSource, gl.VERTEX_SHADER);
        const fs = this.compileShader(gl, fsSource, gl.FRAGMENT_SHADER);
        if (!vs || !fs) return null;

        const program = gl.createProgram();
        gl.attachShader(program, vs);
        gl.attachShader(program, fs);
        gl.linkProgram(program);

        if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
            console.error('[LivingEngine] Program link error:', gl.getProgramInfoLog(program));
            return null;
        }
        return program;
    }

    compileShader(gl, source, type) {
        const shader = gl.createShader(type);
        gl.shaderSource(shader, source);
        gl.compileShader(shader);

        if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
            console.error('[LivingEngine] Shader compile error:', gl.getShaderInfoLog(shader));
            gl.deleteShader(shader);
            return null;
        }
        return shader;
    }

    loadTexture(imageSrc) {
        if (this.currentImageSrc === imageSrc && this.isLoaded) return;
        this.currentImageSrc = imageSrc;
        this.isLoaded = false;

        const img = new Image();
        img.crossOrigin = 'anonymous';
        img.onload = () => {
            const gl = this.gl;
            if (!gl) return;

            gl.bindTexture(gl.TEXTURE_2D, this.texture);
            gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, false);
            gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, img);
            this.textureWidth = img.width;
            this.textureHeight = img.height;
            this.isLoaded = true;

            // Notify UI
            const bgImg = document.getElementById('bgImage');
            if (bgImg) bgImg.style.opacity = '0'; // Hide static image smoothly as WebGL living engine takes over
        };
        img.onerror = (e) => {
            console.error('[LivingEngine] Failed to load image texture:', imageSrc, e);
        };
        img.src = imageSrc;
    }

    setRealm(realmIndex, imageSrc) {
        this.currentRealm = realmIndex;
        if (imageSrc) {
            this.loadTexture(imageSrc);
        }
    }

    setupEventListeners() {
        window.addEventListener('resize', () => this.resize());

        window.addEventListener('mousemove', (e) => {
            this.mouse.targetX = e.clientX / window.innerWidth;
            this.mouse.targetY = e.clientY / window.innerHeight;
        });
    }

    resize() {
        if (!this.canvas || !this.gl) return;
        const dpr = Math.min(window.devicePixelRatio || 1, 1.5); // Cap at 1.5x DPR for silky 60FPS on 4K displays
        this.canvas.width = window.innerWidth * dpr;
        this.canvas.height = window.innerHeight * dpr;
        this.gl.viewport(0, 0, this.canvas.width, this.canvas.height);
    }

    render() {
        if (!this.gl || !this.program) return;
        const gl = this.gl;

        // Smooth mouse lerping
        this.mouse.x += (this.mouse.targetX - this.mouse.x) * 0.05;
        this.mouse.y += (this.mouse.targetY - this.mouse.y) * 0.05;

        const currentTime = (performance.now() - this.startTime) / 1000.0;

        gl.useProgram(this.program);

        gl.uniform1i(this.uniforms.image, 0);
        gl.uniform1f(this.uniforms.time, currentTime);
        gl.uniform2f(this.uniforms.resolution, this.canvas.width, this.canvas.height);
        gl.uniform2f(this.uniforms.mouse, this.mouse.x, this.mouse.y);
        gl.uniform1i(this.uniforms.realm, this.currentRealm);
        gl.uniform1f(this.uniforms.parallax, this.parallaxStrength);
        gl.uniform1f(this.uniforms.flowSpeed, this.flowSpeed);
        gl.uniform1f(this.uniforms.motionEnabled, this.motionEnabled ? 1.0 : 0.0);

        gl.activeTexture(gl.TEXTURE0);
        gl.bindTexture(gl.TEXTURE_2D, this.texture);

        gl.drawArrays(gl.TRIANGLES, 0, 6);
    }
}

window.LivingShaderEngine = LivingShaderEngine;
