/**
 * 🦅 PHANTOM TERMINAL - CUMULATIVE VOLUME DELTA (CVD) SUB-CHART
 * Synchronized with Main Chart for Pan, Drag, and Zoom viewport exploration.
 */

class CVDChartEngine {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    if (!this.canvas) return;
    this.ctx = this.canvas.getContext('2d');
    this.cvdData = [];
    this.paddingRight = 75;
    this.visibleCount = 60;
    this.scrollOffset = 0;

    this.resize();
    window.addEventListener('resize', () => this.resize());
    if (window.ResizeObserver && this.canvas.parentElement) {
      try {
        const ro = new ResizeObserver(() => this.resize());
        ro.observe(this.canvas.parentElement);
      } catch (e) {}
    }
  }

  resize() {
    if (!this.canvas) return;
    const parent = this.canvas.parentElement;
    if (!parent) return;
    const rect = parent.getBoundingClientRect();
    const w = rect.width || parent.clientWidth || 800;
    const h = rect.height || parent.clientHeight || 110;
    if (w > 0 && h > 0) {
      this.canvas.width = Math.floor(w);
      this.canvas.height = Math.floor(h);
      this.render();
    }
  }

  setData(cvdSeries) {
    this.cvdData = cvdSeries || [];
    this.resize();
    this.render();
  }

  setViewport(scrollOffset, visibleCount) {
    this.scrollOffset = scrollOffset;
    this.visibleCount = visibleCount;
    this.render();
  }

  updateLatestCVD(item) {
    if (this.cvdData.length > 0 && item) {
      this.cvdData[this.cvdData.length - 1] = item;
      this.render();
    }
  }

  render() {
    if (!this.ctx || !this.canvas) return;

    const w = this.canvas.width;
    const h = this.canvas.height;
    if (w <= 0 || h <= 0) return;

    this.ctx.clearRect(0, 0, w, h);

    if (this.cvdData.length === 0) {
      this.ctx.fillStyle = '#475569';
      this.ctx.font = '10px JetBrains Mono, monospace';
      this.ctx.textAlign = 'center';
      this.ctx.fillText('[Awaiting MT5 Tick Volume for CVD calculation...]', w / 2, h / 2 + 3);
      this.ctx.textAlign = 'left';
      return;
    }

    const plotW = w - this.paddingRight;

    // Viewport slice matching main chart pan/scroll
    const total = this.cvdData.length;
    const endIdx = Math.max(1, total - this.scrollOffset);
    const startIdx = Math.max(0, endIdx - this.visibleCount);
    const visible = this.cvdData.slice(startIdx, endIdx);

    if (visible.length === 0) return;

    // Find min and max CVD
    let minCVD = Infinity;
    let maxCVD = -Infinity;
    for (const d of visible) {
      if (d.cvd < minCVD) minCVD = d.cvd;
      if (d.cvd > maxCVD) maxCVD = d.cvd;
    }

    const range = Math.max(1, maxCVD - minCVD);
    const getY = (val) => h - ((val - minCVD) / range) * (h - 14) - 7;

    // Grid baseline zero or midpoint
    this.ctx.strokeStyle = 'rgba(38, 56, 89, 0.4)';
    this.ctx.lineWidth = 1;
    const midY = h / 2;
    this.ctx.beginPath();
    this.ctx.moveTo(0, midY);
    this.ctx.lineTo(plotW, midY);
    this.ctx.stroke();

    // Draw Delta Bars
    const step = plotW / visible.length;
    for (let i = 0; i < visible.length; i++) {
      const d = visible[i];
      const x = i * step + step / 2;
      const isPositive = d.delta >= 0;

      const barHeight = Math.min(h / 2.5, Math.abs(d.delta) / 10);
      this.ctx.fillStyle = isPositive ? 'rgba(0, 255, 136, 0.4)' : 'rgba(255, 51, 102, 0.4)';
      
      if (isPositive) {
        this.ctx.fillRect(x - step * 0.3, midY - barHeight, step * 0.6, barHeight);
      } else {
        this.ctx.fillRect(x - step * 0.3, midY, step * 0.6, barHeight);
      }
    }

    // Draw CVD Cumulative Line
    this.ctx.strokeStyle = '#00f0ff';
    this.ctx.lineWidth = 2;
    this.ctx.beginPath();

    for (let i = 0; i < visible.length; i++) {
      const x = i * step + step / 2;
      const y = getY(visible[i].cvd);
      if (i === 0) this.ctx.moveTo(x, y);
      else this.ctx.lineTo(x, y);
    }
    this.ctx.stroke();

    // Latest value label
    const latest = visible[visible.length - 1];
    this.ctx.font = 'bold 10px JetBrains Mono, monospace';
    this.ctx.fillStyle = latest.cvd >= 0 ? '#00ff88' : '#ff3366';
    this.ctx.fillText(`CVD: ${latest.cvd > 0 ? '+' : ''}${latest.cvd}`, plotW + 6, h / 2 + 3);
  }
}
