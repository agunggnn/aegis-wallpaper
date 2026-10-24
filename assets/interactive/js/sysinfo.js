// Sovereign System Hardware Telemetry Controller (CPU, GPU, MEM, DISK I/O)
(function() {
    let currentStats = {
        cpu: 16,
        cpuLabel: "AMD Ryzen 7 5700X",
        gpu: 10,
        gpuLabel: "NVIDIA GeForce RTX 4070",
        memUsed: 19.8,
        memTotal: 40.0,
        memPct: 50,
        diskReadMBs: 0.0,
        diskWriteMBs: 0.0,
        diskIoPct: 0,
        diskLabel: "R: 0.0 MB/s • W: 0.0 MB/s",
        diskStorage: "C: 191.8 / 198.5 GB"
    };

    const cpuBar = document.getElementById('cpuBar');
    const cpuPct = document.getElementById('cpuPct');
    const cpuLabel = document.getElementById('cpuLabel');

    const gpuBar = document.getElementById('gpuBar');
    const gpuPct = document.getElementById('gpuPct');
    const gpuLabel = document.getElementById('gpuLabel');

    const memBar = document.getElementById('memBar');
    const memPct = document.getElementById('memPct');
    const memLabel = document.getElementById('memLabel');

    const diskBar = document.getElementById('diskBar');
    const diskPct = document.getElementById('diskPct');
    const diskLabel = document.getElementById('diskLabel');

    const monitorStatus = document.getElementById('monitorStatus');

    function formatSpeed(mbs) {
        if (mbs >= 1.0) {
            return mbs.toFixed(1) + ' MB/s';
        } else if (mbs > 0.01) {
            return Math.round(mbs * 1024) + ' KB/s';
        }
        return '0.0 MB/s';
    }

    function updateDOM() {
        if (cpuBar) cpuBar.style.width = Math.min(100, Math.max(0, currentStats.cpu)) + '%';
        if (cpuPct) cpuPct.textContent = Math.round(currentStats.cpu) + '%';
        if (cpuLabel && currentStats.cpuLabel) cpuLabel.textContent = currentStats.cpuLabel;

        if (gpuBar) gpuBar.style.width = Math.min(100, Math.max(0, currentStats.gpu)) + '%';
        if (gpuPct) gpuPct.textContent = Math.round(currentStats.gpu) + '%';
        if (gpuLabel && currentStats.gpuLabel) gpuLabel.textContent = currentStats.gpuLabel;

        if (memBar) memBar.style.width = Math.min(100, Math.max(0, currentStats.memPct)) + '%';
        if (memPct) memPct.textContent = Math.round(currentStats.memPct) + '%';
        if (memLabel) memLabel.textContent = `${currentStats.memUsed} / ${currentStats.memTotal} GB`;

        if (diskBar) {
            // Visual I/O bar: combination of active IO percentage and throughput scaling
            const totalThroughput = currentStats.diskReadMBs + currentStats.diskWriteMBs;
            const throughputPct = Math.min(100, (totalThroughput / 50.0) * 100);
            const displayPct = Math.max(currentStats.diskIoPct, Math.round(throughputPct));
            diskBar.style.width = Math.min(100, Math.max(displayPct > 0 ? 3 : 0, displayPct)) + '%';
        }
        if (diskPct) {
            const totalSpeed = currentStats.diskReadMBs + currentStats.diskWriteMBs;
            if (totalSpeed >= 1.0) {
                diskPct.textContent = totalSpeed.toFixed(1) + 'M';
            } else if (totalSpeed > 0.01) {
                diskPct.textContent = Math.round(totalSpeed * 1024) + 'K';
            } else {
                diskPct.textContent = 'IDLE';
            }
        }
        if (diskLabel && currentStats.diskLabel) diskLabel.textContent = currentStats.diskLabel;
    }

    // 1. Native Lively Wallpaper Integration Hook (CPU, GPU, RAM)
    window.livelySystemInformation = function(data) {
        try {
            const info = typeof data === 'string' ? JSON.parse(data) : data;
            if (!info) return;

            if (monitorStatus && monitorStatus.textContent !== 'TELEMETRY') {
                monitorStatus.textContent = 'LIVE';
            }

            if (typeof info.CurrentCpu === 'number') {
                currentStats.cpu = info.CurrentCpu;
            }
            if (info.NameCpu) {
                currentStats.cpuLabel = info.NameCpu.replace(/(\d+-Core Processor|Processor|with Radeon Graphics)/gi, '').trim();
            }

            if (typeof info.CurrentGpu3D === 'number') {
                currentStats.gpu = info.CurrentGpu3D;
            }
            if (info.NameGpu) {
                currentStats.gpuLabel = info.NameGpu.replace(/Corporation/gi, '').trim();
            }

            if (typeof info.TotalRam === 'number' && typeof info.CurrentRamAvail === 'number') {
                const totalGB = (info.TotalRam / (1024 * 1024 * 1024)).toFixed(1);
                const usedBytes = info.TotalRam - info.CurrentRamAvail;
                const usedGB = (usedBytes / (1024 * 1024 * 1024)).toFixed(1);
                currentStats.memTotal = parseFloat(totalGB);
                currentStats.memUsed = parseFloat(usedGB);
                currentStats.memPct = Math.min(100, Math.max(0, Math.round((usedBytes / info.TotalRam) * 100)));
            }

            updateDOM();
        } catch (e) {
            console.error("Error processing livelySystemInformation:", e);
        }
    };

    // 2. Loopback Telemetry Poller (Queries Aegis Rust PDH Disk I/O Bridge)
    async function pollLoopbackTelemetry() {
        try {
            const res = await fetch('http://127.0.0.1:48123/stats', { cache: 'no-store' });
            if (res.ok) {
                const data = await res.json();
                if (monitorStatus) monitorStatus.textContent = 'TELEMETRY';

                if (typeof data.cpu_percent === 'number') {
                    currentStats.cpu = data.cpu_percent;
                }
                if (typeof data.mem_percent === 'number') {
                    currentStats.memPct = data.mem_percent;
                    currentStats.memUsed = data.mem_used_gb;
                    currentStats.memTotal = data.mem_total_gb;
                }
                if (typeof data.disk_read_mbs === 'number' && typeof data.disk_write_mbs === 'number') {
                    currentStats.diskReadMBs = data.disk_read_mbs;
                    currentStats.diskWriteMBs = data.disk_write_mbs;
                    currentStats.diskIoPct = data.disk_io_percent || 0;
                    currentStats.diskLabel = `R: ${formatSpeed(data.disk_read_mbs)} • W: ${formatSpeed(data.disk_write_mbs)}`;
                }
                updateDOM();
            }
        } catch (_) {
            // Loopback bridge offline; fallback to smooth idle simulation
        }
    }

    setInterval(pollLoopbackTelemetry, 1000);
    pollLoopbackTelemetry();

    // Pulse animation trigger on desktop interaction
    window.pulseResourceMonitor = function() {
        const card = document.getElementById('resourceMonitor');
        if (card) {
            card.classList.add('pulse');
            setTimeout(() => card.classList.remove('pulse'), 200);
        }
    };

    updateDOM();
})();
