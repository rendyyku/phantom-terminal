/**
 * 🦅 PHANTOM TERMINAL - LUXALGO SMC & VOLUME PROFILE CANVAS ENGINE
 * High-Performance institutional chart rendering:
 * - LuxAlgo Smart Money Concepts (BOS, CHoCH, Order Blocks, FVGs, EQH/EQL, Premium/Discount)
 * - LonesomeTheBlue Volume Profile (POC Line, 70% Value Area VAH/VAL, Up/Down Volume Histogram)
 * - Infinite Historical Scroll & Smooth Drag/Pan/Zoom
 */

class CandleChartEngine {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    if (!this.canvas) return;
    this.ctx = this.canvas.getContext('2d');

    this.candles = [];
    this.smc = null;
    this.volumeProfile = null;

    // Layout & Viewport
    this.paddingRight = 85;
    this.paddingBottom = 26;
    this.visibleCount = 65;
    this.scrollOffset = 0; // 0 = live edge, > 0 = panned left into history

    // Drag / Pan State
    this.isDragging = false;
    this.dragStartX = 0;
    this.dragStartOffset = 0;

    // Crosshair state
    this.mouse = { x: -1, y: -1, active: false };

    // Infinite scroll & Viewport callback
    this.onViewportChange = null;
    this.onReachHistoryEdge = null;
    this.isLoadingHistory = false;
    this.hasMoreHistory = true;

    // Overlay Toggles (Default OFF / 100% Clean Chart)
    this.showSMC = false;
    this.showVolumeProfile = false;
    this.showZones = false;

    this.initEvents();
    this.resize();
  }

  resize() {
    if (!this.canvas) return;
    const parent = this.canvas.parentElement;
    if (!parent) return;
    const rect = parent.getBoundingClientRect();
    const w = rect.width || parent.clientWidth || 800;
    const h = rect.height || parent.clientHeight || 400;
    if (w > 0 && h > 0) {
      this.canvas.width = Math.floor(w);
      this.canvas.height = Math.floor(h);
      this.render();
    }
  }

  initEvents() {
    window.addEventListener('resize', () => this.resize());

    if (window.ResizeObserver && this.canvas.parentElement) {
      try {
        const ro = new ResizeObserver(() => this.resize());
        ro.observe(this.canvas.parentElement);
      } catch (e) {}
    }

    // --- MOUSE PANNING & DRAG EVENTS ---
    this.canvas.addEventListener('mousedown', (e) => {
      if (e.button === 0) { // Left click
        this.isDragging = true;
        this.dragStartX = e.clientX;
        this.dragStartOffset = this.scrollOffset;
        this.canvas.style.cursor = 'grabbing';
      }
    });

    window.addEventListener('mouseup', () => {
      if (this.isDragging) {
        this.isDragging = false;
        if (this.canvas) this.canvas.style.cursor = 'crosshair';
      }
    });

    this.canvas.addEventListener('mousemove', (e) => {
      const rect = this.canvas.getBoundingClientRect();
      this.mouse.x = e.clientX - rect.left;
      this.mouse.y = e.clientY - rect.top;
      this.mouse.active = true;

      if (this.isDragging) {
        const dx = e.clientX - this.dragStartX;
        const plotW = this.canvas.width - this.paddingRight;
        const step = plotW / this.visibleCount;
        const deltaCandles = Math.round(dx / step);

        const maxOffset = Math.max(0, this.candles.length - this.visibleCount);
        this.scrollOffset = Math.max(0, Math.min(maxOffset, this.dragStartOffset + deltaCandles));

        // Trigger Infinite Scroll near left edge
        const total = this.candles.length;
        const endIdx = Math.max(1, total - this.scrollOffset);
        const startIdx = Math.max(0, endIdx - this.visibleCount);

        if (startIdx <= 15 && !this.isLoadingHistory && this.hasMoreHistory && this.onReachHistoryEdge) {
          this.isLoadingHistory = true;
          const oldestTime = this.candles[0] ? this.candles[0].time : null;
          this.onReachHistoryEdge(oldestTime, this.candles.length);
        }

        this.render();
        if (this.onViewportChange) {
          this.onViewportChange(this.scrollOffset, this.visibleCount);
        }
      } else {
        this.render();
      }
    });

    this.canvas.addEventListener('mouseleave', () => {
      this.mouse.active = false;
      this.render();
    });

    // --- MOUSE WHEEL ZOOM ---
    this.canvas.addEventListener('wheel', (e) => {
      e.preventDefault();
      const zoomStep = e.deltaY < 0 ? -4 : 4;
      const minCandles = 15;
      const maxCandles = Math.max(minCandles, Math.min(400, this.candles.length || 100));

      this.visibleCount = Math.max(minCandles, Math.min(maxCandles, this.visibleCount + zoomStep));
      const maxOffset = Math.max(0, this.candles.length - this.visibleCount);
      this.scrollOffset = Math.min(this.scrollOffset, maxOffset);

      this.render();
      if (this.onViewportChange) {
        this.onViewportChange(this.scrollOffset, this.visibleCount);
      }
    }, { passive: false });

    // --- DOUBLE CLICK TO SNAP TO LIVE ---
    this.canvas.addEventListener('dblclick', () => {
      this.scrollOffset = 0;
      this.visibleCount = 65;
      this.render();
      if (this.onViewportChange) {
        this.onViewportChange(this.scrollOffset, this.visibleCount);
      }
    });
  }

  setData(data) {
    this.candles = data.candles || [];
    this.smc = data.smc || null;
    this.volumeProfile = data.volume_profile || null;
    this.hasMoreHistory = true;
    this.isLoadingHistory = false;
    this.resize();
    this.render();
  }

  prependHistoricalCandles(olderCandles) {
    if (!olderCandles || olderCandles.length === 0) {
      this.hasMoreHistory = false;
      this.isLoadingHistory = false;
      this.render();
      return;
    }

    const existingTimes = new Set(this.candles.map((c) => c.time));
    const fresh = olderCandles.filter((c) => !existingTimes.has(c.time));

    if (fresh.length > 0) {
      fresh.sort((a, b) => a.time - b.time);
      this.candles = [...fresh, ...this.candles];
      this.scrollOffset += fresh.length;
    } else {
      this.hasMoreHistory = false;
    }

    this.isLoadingHistory = false;
    this.render();
  }

  updateLatestCandle(candle) {
    if (this.candles.length > 0) {
      this.candles[this.candles.length - 1] = candle;
      this.render();
    }
  }

  render() {
    if (!this.ctx || !this.canvas) return;

    const w = this.canvas.width;
    const h = this.canvas.height;
    if (w <= 0 || h <= 0) return;

    this.ctx.clearRect(0, 0, w, h);

    if (this.candles.length === 0) {
      // Offline / Empty State
      this.ctx.fillStyle = 'rgba(148, 163, 184, 0.4)';
      this.ctx.font = '14px Outfit, sans-serif';
      this.ctx.textAlign = 'center';
      this.ctx.fillText('⚡ METATRADER 5 OFFLINE (NO CANDLE DATA)', w / 2, h / 2 - 10);
      
      this.ctx.font = '11px JetBrains Mono, monospace';
      this.ctx.fillStyle = '#64748b';
      this.ctx.fillText('Buka aplikasi MetaTrader 5 di PC untuk mengalirkan data pasar live.', w / 2, h / 2 + 15);
      this.ctx.textAlign = 'left';
      return;
    }

    const plotW = w - this.paddingRight;
    const plotH = h - this.paddingBottom;

    // Viewport Slicing
    const total = this.candles.length;
    const endIdx = Math.max(1, total - this.scrollOffset);
    const startIdx = Math.max(0, endIdx - this.visibleCount);
    const visibleCandles = this.candles.slice(startIdx, endIdx);

    if (visibleCandles.length === 0) return;

    // Price scaling
    let minPrice = Infinity;
    let maxPrice = -Infinity;
    for (const c of visibleCandles) {
      if (c.low < minPrice) minPrice = c.low;
      if (c.high > maxPrice) maxPrice = c.high;
    }

    const range = Math.max(0.0001, maxPrice - minPrice);
    minPrice -= range * 0.08;
    maxPrice += range * 0.08;
    const totalRange = maxPrice - minPrice;

    const getY = (price) => plotH - ((price - minPrice) / totalRange) * plotH;
    const getPrice = (y) => maxPrice - (y / plotH) * totalRange;

    // 1. Draw Grid Lines
    this.drawGrid(plotW, plotH, minPrice, maxPrice, totalRange, visibleCandles);

    // 2. Draw Premium / Discount / Equilibrium Zones
    if (this.showZones && this.smc && this.smc.zones) {
      this.drawPremiumDiscountZones(this.smc.zones, plotW, getY);
    }

    // 3. Draw Volume Profile (LonesomeTheBlue VP Fixed Range)
    if (this.showVolumeProfile && this.volumeProfile && this.volumeProfile.rows) {
      this.drawVolumeProfile(this.volumeProfile, plotW, plotH, getY);
    }

    // 4. Draw LuxAlgo Order Blocks (OB)
    if (this.showSMC && this.smc && this.smc.order_blocks) {
      this.drawOrderBlocks(this.smc.order_blocks, startIdx, endIdx, plotW, getY);
    }

    // 5. Draw LuxAlgo Fair Value Gaps (FVG)
    if (this.showSMC && this.smc && this.smc.fvgs) {
      this.drawFVGs(this.smc.fvgs, startIdx, endIdx, plotW, getY);
    }

    // 6. Draw LuxAlgo Structure (BOS / CHoCH)
    if (this.showSMC && this.smc && this.smc.swing_structures) {
      this.drawBreakoutStructures(this.smc.swing_structures, startIdx, endIdx, plotW, getY);
    }

    // 7. Draw Equal Highs / Lows (EQH / EQL)
    if (this.showSMC && this.smc && this.smc.equal_high_lows) {
      this.drawEqualHighLows(this.smc.equal_high_lows, startIdx, endIdx, plotW, getY);
    }

    // 8. Draw Strong / Weak Highs and Lows
    if (this.showSMC && this.smc && this.smc.strong_weak) {
      this.drawStrongWeak(this.smc.strong_weak, plotW, getY);
    }

    // 9. Draw Candlesticks (60 FPS Native Renderer)
    const step = plotW / visibleCandles.length;
    for (let i = 0; i < visibleCandles.length; i++) {
      const c = visibleCandles[i];
      const x = i * step + step / 2;
      const isBull = c.close >= c.open;

      const yOpen = getY(c.open);
      const yClose = getY(c.close);
      const yHigh = getY(c.high);
      const yLow = getY(c.low);

      const color = isBull ? '#089981' : '#f23645';
      const wickColor = isBull ? 'rgba(8, 153, 129, 0.75)' : 'rgba(242, 54, 69, 0.75)';

      // Wick
      this.ctx.strokeStyle = wickColor;
      this.ctx.lineWidth = 1.2;
      this.ctx.beginPath();
      this.ctx.moveTo(x, yHigh);
      this.ctx.lineTo(x, yLow);
      this.ctx.stroke();

      // Body
      const bodyTop = Math.min(yOpen, yClose);
      const bodyHeight = Math.max(2, Math.abs(yOpen - yClose));
      const cWidth = Math.max(3, step * 0.65);

      this.ctx.fillStyle = color;
      this.ctx.fillRect(x - cWidth / 2, bodyTop, cWidth, bodyHeight);
    }

    // 10. Historical Pan Indicator
    if (this.scrollOffset > 0) {
      this.ctx.fillStyle = 'rgba(245, 158, 11, 0.9)';
      this.ctx.font = 'bold 10px JetBrains Mono, monospace';
      this.ctx.fillText(`⏮ HISTORICAL VIEW (+${this.scrollOffset} bars) | Double-click to Snap Live`, 14, 22);
    }

    // 11. Crosshair & Tooltip
    if (this.mouse.active && this.mouse.x <= plotW && this.mouse.y <= plotH) {
      this.drawCrosshair(plotW, plotH, w, getPrice, visibleCandles, step);
    }
  }

  drawGrid(plotW, plotH, minPrice, maxPrice, totalRange, visibleCandles) {
    this.ctx.strokeStyle = 'rgba(38, 56, 89, 0.25)';
    this.ctx.lineWidth = 1;
    this.ctx.font = '10px JetBrains Mono, monospace';
    this.ctx.fillStyle = '#64748b';

    const steps = 6;
    for (let i = 0; i <= steps; i++) {
      const y = (plotH / steps) * i;
      const p = maxPrice - (i / steps) * totalRange;

      this.ctx.beginPath();
      this.ctx.moveTo(0, y);
      this.ctx.lineTo(plotW, y);
      this.ctx.stroke();

      this.ctx.fillText(p.toFixed(p > 100 ? 2 : 5), plotW + 6, y + 3);
    }

    const timeStep = Math.max(1, Math.floor(visibleCandles.length / 5));
    const stepX = plotW / visibleCandles.length;
    for (let i = 0; i < visibleCandles.length; i += timeStep) {
      const c = visibleCandles[i];
      if (c && c.time) {
        const x = i * stepX + stepX / 2;
        const d = new Date(c.time * 1000);
        const timeStr = d.toTimeString().split(' ')[0];
        this.ctx.fillText(timeStr, x - 18, plotH + 16);
      }
    }
  }

  // --- VOLUME PROFILE (LonesomeTheBlue) ---
  drawVolumeProfile(vp, plotW, plotH, getY) {
    const rows = vp.rows || [];
    if (rows.length === 0) return;

    let maxVol = 0;
    for (const r of rows) {
      if (r.total_volume > maxVol) maxVol = r.total_volume;
    }
    if (maxVol <= 0) return;

    const maxBarW = Math.min(180, plotW * 0.22);
    const startX = plotW - maxBarW - 10;

    for (const r of rows) {
      const yTop = getY(r.price_high);
      const yBot = getY(r.price_low);
      const rowHeight = Math.max(1.5, Math.abs(yBot - yTop));
      const rowY = Math.min(yTop, yBot);

      const upW = (r.up_volume / maxVol) * maxBarW;
      const downW = (r.down_volume / maxVol) * maxBarW;

      // Up Volume Bar (Blue / Cyan)
      this.ctx.fillStyle = r.in_value_area ? 'rgba(33, 87, 243, 0.45)' : 'rgba(33, 87, 243, 0.18)';
      this.ctx.fillRect(plotW - (upW + downW), rowY, upW, rowHeight);

      // Down Volume Bar (Orange / Red)
      this.ctx.fillStyle = r.in_value_area ? 'rgba(245, 158, 11, 0.45)' : 'rgba(245, 158, 11, 0.18)';
      this.ctx.fillRect(plotW - downW, rowY, downW, rowHeight);
    }

    // Draw POC Line (Red)
    if (vp.poc) {
      const pocY = getY(vp.poc);
      this.ctx.strokeStyle = '#ff0033';
      this.ctx.lineWidth = 1.8;
      this.ctx.setLineDash([]);
      this.ctx.beginPath();
      this.ctx.moveTo(startX - 20, pocY);
      this.ctx.lineTo(plotW, pocY);
      this.ctx.stroke();

      // POC Label
      this.ctx.fillStyle = '#ff0033';
      this.ctx.font = 'bold 9px JetBrains Mono, monospace';
      this.ctx.fillText(`POC: ${vp.poc}`, startX - 85, pocY + 3);
    }

    // Draw VAH / VAL Lines (Value Area 70%)
    if (vp.vah && vp.val) {
      this.ctx.strokeStyle = 'rgba(0, 240, 255, 0.45)';
      this.ctx.setLineDash([3, 3]);

      const vahY = getY(vp.vah);
      this.ctx.beginPath();
      this.ctx.moveTo(startX, vahY);
      this.ctx.lineTo(plotW, vahY);
      this.ctx.stroke();
      this.ctx.fillStyle = '#00f0ff';
      this.ctx.font = '9px JetBrains Mono, monospace';
      this.ctx.fillText(`VAH: ${vp.vah}`, startX - 65, vahY + 3);

      const valY = getY(vp.val);
      this.ctx.beginPath();
      this.ctx.moveTo(startX, valY);
      this.ctx.lineTo(plotW, valY);
      this.ctx.stroke();
      this.ctx.fillText(`VAL: ${vp.val}`, startX - 65, valY + 3);

      this.ctx.setLineDash([]);
    }
  }

  // --- LUXALGO ORDER BLOCKS (OB) ---
  drawOrderBlocks(obs, startIdx, endIdx, plotW, getY) {
    const step = plotW / (endIdx - startIdx);

    for (const ob of obs) {
      if (ob.index > endIdx) continue;
      const relIdx = Math.max(0, ob.index - startIdx);
      const startX = relIdx * step;
      
      const relEnd = ob.mitigated_index ? Math.min(endIdx - startIdx, ob.mitigated_index - startIdx) : (endIdx - startIdx);
      const endX = Math.max(startX + 20, relEnd * step);

      const yTop = getY(ob.top);
      const yBot = getY(ob.bottom);
      const h = Math.max(3, Math.abs(yBot - yTop));
      const y = Math.min(yTop, yBot);

      if (ob.type === 'BULLISH_OB') {
        this.ctx.fillStyle = 'rgba(49, 121, 245, 0.2)';
        this.ctx.strokeStyle = '#3179f5';
      } else {
        this.ctx.fillStyle = 'rgba(247, 124, 128, 0.2)';
        this.ctx.strokeStyle = '#f77c80';
      }

      this.ctx.lineWidth = 1;
      this.ctx.fillRect(startX, y, endX - startX, h);
      this.ctx.strokeRect(startX, y, endX - startX, h);

      // Label
      this.ctx.font = 'bold 9px JetBrains Mono, monospace';
      this.ctx.fillStyle = (ob.type === 'BULLISH_OB') ? '#3179f5' : '#f77c80';
      this.ctx.fillText(ob.type === 'BULLISH_OB' ? '+OB' : '-OB', startX + 4, y + 10);
    }
  }

  // --- LUXALGO FAIR VALUE GAPS (FVG) ---
  drawFVGs(fvgs, startIdx, endIdx, plotW, getY) {
    const step = plotW / (endIdx - startIdx);

    for (const fvg of fvgs) {
      if (fvg.index > endIdx || fvg.mitigated) continue;
      const relIdx = Math.max(0, fvg.index - startIdx);
      const startX = relIdx * step;
      const endX = Math.min(plotW, (relIdx + 8) * step);

      const yTop = getY(fvg.top);
      const yBot = getY(fvg.bottom);
      const h = Math.max(2, Math.abs(yBot - yTop));
      const y = Math.min(yTop, yBot);

      if (fvg.type === 'BULLISH_FVG') {
        this.ctx.fillStyle = 'rgba(0, 255, 104, 0.15)';
        this.ctx.strokeStyle = 'rgba(0, 255, 104, 0.5)';
      } else {
        this.ctx.fillStyle = 'rgba(255, 0, 8, 0.15)';
        this.ctx.strokeStyle = 'rgba(255, 0, 8, 0.5)';
      }

      this.ctx.lineWidth = 1;
      this.ctx.fillRect(startX, y, endX - startX, h);
      this.ctx.strokeRect(startX, y, endX - startX, h);

      this.ctx.font = '8px JetBrains Mono, monospace';
      this.ctx.fillStyle = (fvg.type === 'BULLISH_FVG') ? '#00ff68' : '#ff0008';
      this.ctx.fillText('FVG', startX + 3, y + h / 2 + 3);
    }
  }

  // --- LUXALGO BREAKOUT STRUCTURES (BOS & CHoCH) ---
  drawBreakoutStructures(structures, startIdx, endIdx, plotW, getY) {
    const step = plotW / (endIdx - startIdx);

    for (const s of structures) {
      if (s.end_index < startIdx || s.start_index > endIdx) continue;

      const x1 = Math.max(0, (s.start_index - startIdx) * step);
      const x2 = Math.min(plotW, (s.end_index - startIdx) * step);
      const y = getY(s.price);

      const isBull = s.type === 'BULLISH';
      const color = isBull ? '#089981' : '#f23645';

      this.ctx.strokeStyle = color;
      this.ctx.lineWidth = 1.2;
      this.ctx.setLineDash(s.tag === 'CHoCH' ? [3, 3] : [5, 2]);

      this.ctx.beginPath();
      this.ctx.moveTo(x1, y);
      this.ctx.lineTo(x2, y);
      this.ctx.stroke();

      // Tag Label (BOS / CHoCH)
      const midX = (x1 + x2) / 2;
      this.ctx.font = 'bold 9px JetBrains Mono, monospace';
      this.ctx.fillStyle = color;
      this.ctx.fillText(s.tag, midX - 10, isBull ? y - 4 : y + 10);
    }
    this.ctx.setLineDash([]);
  }

  // --- LUXALGO EQUAL HIGHS / LOWS (EQH / EQL) ---
  drawEqualHighLows(eqs, startIdx, endIdx, plotW, getY) {
    const step = plotW / (endIdx - startIdx);

    for (const eq of eqs) {
      if (eq.end_index < startIdx || eq.start_index > endIdx) continue;

      const x1 = Math.max(0, (eq.start_index - startIdx) * step);
      const x2 = Math.min(plotW, (eq.end_index - startIdx) * step);
      const y = getY(eq.price);

      const isHigh = eq.type === 'EQH';
      const color = isHigh ? '#f23645' : '#089981';

      this.ctx.strokeStyle = color;
      this.ctx.lineWidth = 1;
      this.ctx.setLineDash([2, 2]);

      this.ctx.beginPath();
      this.ctx.moveTo(x1, y);
      this.ctx.lineTo(x2 + 30, y);
      this.ctx.stroke();

      this.ctx.font = 'bold 9px JetBrains Mono, monospace';
      this.ctx.fillStyle = color;
      this.ctx.fillText(eq.label, x2 + 6, isHigh ? y - 3 : y + 9);
    }
    this.ctx.setLineDash([]);
  }

  // --- LUXALGO PREMIUM, DISCOUNT & EQUILIBRIUM ZONES ---
  drawPremiumDiscountZones(zones, plotW, getY) {
    if (!zones.premium || !zones.discount) return;

    // Premium Zone (Top 5% Red)
    const yP1 = getY(zones.premium.top);
    const yP2 = getY(zones.premium.bottom);
    this.ctx.fillStyle = 'rgba(242, 54, 69, 0.06)';
    this.ctx.fillRect(0, yP1, plotW, Math.abs(yP2 - yP1));
    this.ctx.fillStyle = 'rgba(242, 54, 69, 0.6)';
    this.ctx.font = '9px Outfit, sans-serif';
    this.ctx.fillText('PREMIUM ZONE', 10, yP2 - 3);

    // Equilibrium Line (50% Gray)
    const yEq = getY(zones.equilibrium.mid);
    this.ctx.strokeStyle = 'rgba(135, 139, 148, 0.35)';
    this.ctx.setLineDash([4, 4]);
    this.ctx.beginPath();
    this.ctx.moveTo(0, yEq);
    this.ctx.lineTo(plotW, yEq);
    this.ctx.stroke();
    this.ctx.fillStyle = '#878b94';
    this.ctx.fillText('EQUILIBRIUM (50%)', 10, yEq - 3);

    // Discount Zone (Bottom 5% Green)
    const yD1 = getY(zones.discount.top);
    const yD2 = getY(zones.discount.bottom);
    this.ctx.fillStyle = 'rgba(8, 153, 129, 0.06)';
    this.ctx.fillRect(0, yD1, plotW, Math.abs(yD2 - yD1));
    this.ctx.fillStyle = 'rgba(8, 153, 129, 0.6)';
    this.ctx.fillText('DISCOUNT ZONE', 10, yD2 + 10);

    this.ctx.setLineDash([]);
  }

  // --- STRONG / WEAK HIGHS & LOWS ---
  drawStrongWeak(sw, plotW, getY) {
    this.ctx.font = '9px JetBrains Mono, monospace';

    if (sw.high_price) {
      const yH = getY(sw.high_price);
      this.ctx.fillStyle = '#f23645';
      this.ctx.fillText(`▲ ${sw.high_type}`, plotW - 120, yH - 3);
    }

    if (sw.low_price) {
      const yL = getY(sw.low_price);
      this.ctx.fillStyle = '#089981';
      this.ctx.fillText(`▼ ${sw.low_type}`, plotW - 120, yL + 11);
    }
  }

  drawCrosshair(plotW, plotH, w, getPrice, visibleCandles, step) {
    this.ctx.strokeStyle = 'rgba(255, 255, 255, 0.35)';
    this.ctx.setLineDash([2, 2]);

    this.ctx.beginPath();
    this.ctx.moveTo(this.mouse.x, 0);
    this.ctx.lineTo(this.mouse.x, plotH);
    this.ctx.stroke();

    this.ctx.beginPath();
    this.ctx.moveTo(0, this.mouse.y);
    this.ctx.lineTo(plotW, this.mouse.y);
    this.ctx.stroke();

    this.ctx.setLineDash([]);

    // Price badge on Y-Axis
    const priceVal = getPrice(this.mouse.y);
    this.ctx.fillStyle = '#00f0ff';
    this.ctx.fillRect(plotW + 2, this.mouse.y - 9, this.paddingRight - 4, 18);
    this.ctx.fillStyle = '#07090e';
    this.ctx.font = 'bold 10px JetBrains Mono, monospace';
    this.ctx.fillText(priceVal.toFixed(priceVal > 100 ? 2 : 5), plotW + 4, this.mouse.y + 4);

    // Candle Info Tooltip on hover
    const candleIdx = Math.min(visibleCandles.length - 1, Math.max(0, Math.floor(this.mouse.x / step)));
    const c = visibleCandles[candleIdx];
    if (c) {
      const isBull = c.close >= c.open;
      this.ctx.fillStyle = 'rgba(10, 14, 23, 0.85)';
      this.ctx.fillRect(10, 10, 280, 22);
      this.ctx.strokeStyle = isBull ? 'rgba(8, 153, 129, 0.5)' : 'rgba(242, 54, 69, 0.5)';
      this.ctx.strokeRect(10, 10, 280, 22);

      this.ctx.font = '10px JetBrains Mono, monospace';
      this.ctx.fillStyle = '#94a3b8';
      this.ctx.fillText(`O:`, 16, 25);
      this.ctx.fillStyle = '#ffffff';
      this.ctx.fillText(`${c.open}`, 30, 25);

      this.ctx.fillStyle = '#94a3b8';
      this.ctx.fillText(`H:`, 85, 25);
      this.ctx.fillStyle = '#089981';
      this.ctx.fillText(`${c.high}`, 98, 25);

      this.ctx.fillStyle = '#94a3b8';
      this.ctx.fillText(`L:`, 150, 25);
      this.ctx.fillStyle = '#f23645';
      this.ctx.fillText(`${c.low}`, 163, 25);

      this.ctx.fillStyle = '#94a3b8';
      this.ctx.fillText(`C:`, 215, 25);
      this.ctx.fillStyle = isBull ? '#089981' : '#f23645';
      this.ctx.fillText(`${c.close}`, 228, 25);
    }
  }
}
