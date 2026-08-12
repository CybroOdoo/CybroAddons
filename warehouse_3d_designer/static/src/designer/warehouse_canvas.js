/** @odoo-module **/

/**
 * Warehouse Canvas — 2D HTML5 Canvas renderer for the warehouse layout
 * designer. Handles grid drawing, location rendering, drag-and-drop,
 * resizing, heatmap visualization, and product tooltips.
 */

import { Component, onMounted, onPatched, onWillUnmount, useRef } from "@odoo/owl";

export class WarehouseCanvas extends Component {
    static template = "warehouse_3d_designer.WarehouseCanvas";
    static props = {
        locations: { type: Array },
        layoutData: { type: Object },
        mapObjects: { type: Array },
        gridEnabled: { type: Boolean },
        heatmapEnabled: { type: Boolean },
        heatmapData: { type: Object },
        zoomLevel: { type: Number },
        selectedLocationId: { type: [Number, { value: null }], optional: true },
        highlightedLocationId: { type: [Number, { value: null }], optional: true },
        isAdmin: { type: Boolean },
        measurementUnit: { type: String },
        cellSizeCm: { type: Number },
        productSearchResults: { type: Array },
        onLocationSelected: { type: Function },
        onLocationMoved: { type: Function },
        onLocationResized: { type: Function },
        onLocationDropped: { type: Function },
        onMapObjectDropped: { type: Function, optional: true },
        selectedMapObjectId: { type: [Number, { value: null }], optional: true },
        onMapObjectSelected: { type: Function, optional: true },
        onMapObjectMoved: { type: Function, optional: true },
        onMapObjectResized: { type: Function, optional: true },
        onChildMoved: { type: Function },
        onChildResized: { type: Function },
    };

    // Max products shown inline on the tile before switching to badge-only mode
    static MAX_INLINE_PRODUCTS = 2;

    setup() {
        this.canvasRef = useRef("canvas");
        this.ctx = null;

        // Parent drag/resize state
        this._isDragging = false;
        this._isResizing = false;
        this._isPanning = false;
        this._dragLocId = null;
        this._dragOffsetX = 0;
        this._dragOffsetY = 0;
        this._resizeLocId = null;
        this._panStartX = 0;
        this._panStartY = 0;
        this._panOffsetX = 0;
        this._panOffsetY = 0;
        this._resizeStartW = 0;
        this._resizeStartH = 0;
        this._resizeStartMX = 0;
        this._resizeStartMY = 0;

        // Child drag/resize state
        this._isDraggingChild = false;
        this._isResizingChild = false;
        this._selectedChildId = null;
        this._dragChildId = null;
        this._dragChildParentId = null;
        this._dragChildOffsetX = 0;
        this._dragChildOffsetY = 0;
        this._resizeChildId = null;
        this._resizeChildParentId = null;

        // Map object drag/resize state
        this._isDraggingMapObj = false;
        this._isResizingMapObj = false;
        this._dragMapObjId = null;
        this._resizeMapObjId = null;

        // Animation
        this._highlightAnim = 0;
        this._needsRedraw = false;

        // Tooltip
        this._tooltipEl = null;
        this._tooltipLocId = null;
        this._tooltipHideTimer = null;

        this._onMouseDown = this._onMouseDown.bind(this);
        this._onMouseMove = this._onMouseMove.bind(this);
        this._onMouseUp = this._onMouseUp.bind(this);
        this._onMouseLeaveCanvas = this._onMouseLeaveCanvas.bind(this);
        this._onWheel = this._onWheel.bind(this);
        this._onDragOver = this._onDragOver.bind(this);
        this._onDrop = this._onDrop.bind(this);

        onMounted(() => {
            const el = this.canvasRef.el;
            if (!el) return;
            this.ctx = el.getContext("2d");
            el.addEventListener("mousedown", this._onMouseDown);
            el.addEventListener("mousemove", this._onMouseMove);
            el.addEventListener("mouseup", this._onMouseUp);
            el.addEventListener("mouseleave", this._onMouseLeaveCanvas);
            el.addEventListener("wheel", this._onWheel, { passive: false });
            el.addEventListener("dragover", this._onDragOver);
            el.addEventListener("drop", this._onDrop);
            // Auto-redraw on container resize
            this._resizeObserver = new ResizeObserver(() => {
                this._needsRedraw = true;
            });
            this._resizeObserver.observe(el.parentElement);
            this._startAnimLoop();
            this._needsRedraw = true;
            requestAnimationFrame(() => this._draw());
        });

        onPatched(() => {
            this._needsRedraw = true;
        });

        onWillUnmount(() => {
            this._stopAnimLoop();
            if (this._resizeObserver) {
                this._resizeObserver.disconnect();
                this._resizeObserver = null;
            }
            this._hideProductTooltip();
            const el = this.canvasRef.el;
            if (!el) return;
            el.removeEventListener("mousedown", this._onMouseDown);
            el.removeEventListener("mousemove", this._onMouseMove);
            el.removeEventListener("mouseup", this._onMouseUp);
            el.removeEventListener("mouseleave", this._onMouseLeaveCanvas);
            el.removeEventListener("wheel", this._onWheel);
            el.removeEventListener("dragover", this._onDragOver);
            el.removeEventListener("drop", this._onDrop);
        });
    }

    // ========================================================================
    // Unit conversion
    // ========================================================================

    _convertSize(gridCells) {
        const cm = gridCells * this.props.cellSizeCm;
        switch (this.props.measurementUnit) {
            case 'cm': return { value: cm, label: `${cm}cm` };
            case 'inch': return { value: +(cm / 2.54).toFixed(1), label: `${(cm / 2.54).toFixed(1)}″` };
            default: return { value: +(cm / 100).toFixed(2), label: `${(cm / 100).toFixed(2)}m` };
        }
    }

    _formatDimension(w, h) {
        const wc = this._convertSize(w);
        const hc = this._convertSize(h);
        return `${wc.label} × ${hc.label}`;
    }

    _formatArea(w, h) {
        const wc = this._convertSize(w);
        const hc = this._convertSize(h);
        const unit = this.props.measurementUnit === 'inch' ? 'sq.in' :
            this.props.measurementUnit === 'cm' ? 'cm²' : 'm²';
        return `${(wc.value * hc.value).toFixed(1)} ${unit}`;
    }

    // ========================================================================
    // Animation loop (for highlight pulse + smooth rendering)
    // ========================================================================

    _startAnimLoop() {
        this._animRunning = true;
        const loop = () => {
            if (!this._animRunning) return;
            // Only advance highlight animation when actually highlighting
            const hasHighlight = this.props.highlightedLocationId ||
                (this.props.productSearchResults && this.props.productSearchResults.length > 0);
            if (hasHighlight) {
                this._highlightAnim += 0.05;
                this._needsRedraw = true;
            }
            if (this._needsRedraw) {
                this._needsRedraw = false;
                this._draw();
            }
            requestAnimationFrame(loop);
        };
        requestAnimationFrame(loop);
    }

    _stopAnimLoop() {
        this._animRunning = false;
    }

    // ========================================================================
    // Drawing
    // ========================================================================

    /**
     * Compute effective grid dimensions — fixed to the configured canvas size.
     */
    _getEffectiveGrid() {
        const layout = this.props.layoutData;
        const gridSize = layout.grid_size || 1;
        const cw = layout.canvas_width || 40;
        const ch = layout.canvas_height || 30;
        return { gridSize, cw, ch };
    }

    /**
     * Clamp pan offsets so the user cannot scroll endlessly.
     * Allows 50px of overscroll beyond the grid frame.
     */
    _clampPan(viewW, viewH, totalW, totalH, zoom) {
        const pad = 50;
        const scaledW = totalW * zoom;
        const scaledH = totalH * zoom;
        // Allow scrolling so the grid can be panned left/right and up/down,
        // but never more than 50px beyond the edge.
        this._panOffsetX = Math.min(pad, Math.max(-(scaledW - viewW + pad), this._panOffsetX));
        this._panOffsetY = Math.min(pad, Math.max(-(scaledH - viewH + pad), this._panOffsetY));
    }

    _draw() {
        const canvas = this.canvasRef.el;
        const ctx = this.ctx;
        if (!canvas || !ctx) return;

        const { gridSize, cw, ch } = this._getEffectiveGrid();
        const zoom = this.props.zoomLevel;
        const totalW = cw * gridSize;
        const totalH = ch * gridSize;

        // High DPI fix
        const dpr = window.devicePixelRatio || 1;
        const rect = canvas.parentElement.getBoundingClientRect();
        const viewW = rect.width;
        const viewH = rect.height;

        canvas.width = viewW * dpr;
        canvas.height = viewH * dpr;
        canvas.style.width = `${viewW}px`;
        canvas.style.height = `${viewH}px`;

        // Clamp pan so scroll ends 50px past grid
        this._clampPan(viewW, viewH, totalW, totalH, zoom);

        // Clear entire canvas with outer background FIRST
        ctx.save();
        ctx.scale(dpr, dpr);
        ctx.fillStyle = "#e2e8f0";
        ctx.fillRect(0, 0, viewW, viewH);

        ctx.translate(this._panOffsetX, this._panOffsetY);
        ctx.scale(zoom, zoom);

        // Grid area background (white)
        ctx.fillStyle = "#f8f9fa";
        ctx.fillRect(0, 0, totalW, totalH);

        // Grid lines — batched into a single path for performance
        if (this.props.gridEnabled) {
            ctx.strokeStyle = "#e0e0e0";
            ctx.lineWidth = 0.5;
            ctx.beginPath();
            for (let x = 0; x <= cw; x++) {
                ctx.moveTo(x * gridSize, 0);
                ctx.lineTo(x * gridSize, totalH);
            }
            for (let y = 0; y <= ch; y++) {
                ctx.moveTo(0, y * gridSize);
                ctx.lineTo(totalW, y * gridSize);
            }
            ctx.stroke();
        }

        // Map objects
        for (const obj of this.props.mapObjects) {
            this._drawMapObject(ctx, obj, gridSize);
        }

        // Locations — draw zone/floor first (background), then others on top
        const searchLocIds = new Set();
        for (const r of this.props.productSearchResults) {
            searchLocIds.add(r.location_id);
        }
        const zoneFloorTypes = new Set(['zone', 'floor']);
        const zones = [];
        const others = [];
        for (const loc of this.props.locations) {
            if (zoneFloorTypes.has(loc.location_shape)) {
                zones.push(loc);
            } else {
                others.push(loc);
            }
        }
        for (const loc of zones) {
            this._drawLocation(ctx, loc, gridSize, searchLocIds);
        }
        for (const loc of others) {
            this._drawLocation(ctx, loc, gridSize, searchLocIds);
        }

        // ── Heatmap Legend (drawn in screen space, after grid transform) ──
        if (this.props.heatmapEnabled) {
            ctx.restore();
            ctx.save();
            ctx.scale(dpr, dpr);
            this._drawHeatmapLegend(ctx, viewW, viewH);
            ctx.restore();
        } else {
            ctx.restore();
        }
    }

    _drawMapObject(ctx, obj, gridSize) {
        const x = obj.pos_x * gridSize;
        const y = obj.pos_y * gridSize;
        const w = (obj.size_x || 1) * gridSize;
        const h = (obj.size_y || 1) * gridSize;

        const isSelected = obj.id === this.props.selectedMapObjectId;
        const isWall = obj.object_type === 'wall';

        if (isWall) {
            ctx.fillStyle = obj.color || "#555555";
            const flipped = !!obj.is_flipped;

            // Replicate 3D thickness proportionally
            const thickness = Math.max(3, gridSize * 0.15);

            if (obj.size_x <= obj.size_y) {
                // Vertical wall — default: left edge; flipped: right edge
                const wx = flipped ? (x + w - thickness) : x;
                ctx.fillRect(wx, y, thickness, h);
            } else {
                // Horizontal wall — default: top edge; flipped: bottom edge
                const wy = flipped ? (y + h - thickness) : y;
                ctx.fillRect(x, wy, w, thickness);
            }
        } else if (obj.object_type === 'room') {
            // Room: thick border walls with transparent interior + door icon
            ctx.fillStyle = "rgba(255,255,255,0.1)";
            ctx.fillRect(x + 2, y + 2, w - 4, h - 4);
            ctx.strokeStyle = obj.color || "#7F8C8D";
            ctx.lineWidth = 4;
            ctx.strokeRect(x + 2, y + 2, w - 4, h - 4);

            // Door icon
            ctx.font = `${Math.min(16, gridSize * 0.35)}px sans-serif`;
            ctx.textAlign = "left";
            ctx.fillStyle = "rgba(255,255,255,0.7)";
            ctx.fillText("🚪", x + 6, y + 18);

            // Name label
            ctx.fillStyle = "white";
            ctx.font = `bold ${Math.min(12, gridSize * 0.3)}px sans-serif`;
            ctx.textAlign = "center";
            ctx.textBaseline = "middle";
            ctx.fillText(obj.name || "Room", x + w / 2, y + h / 2);
            ctx.textAlign = "center";
        } else {
            // Standard map object Background with padding
            ctx.fillStyle = obj.color || "#95A5A6";
            ctx.globalAlpha = 0.35;
            ctx.fillRect(x + 1, y + 1, w - 2, h - 2);
            ctx.globalAlpha = 1.0;

            // Border dashed
            ctx.strokeStyle = isSelected ? '#1a73e8' : (obj.color || "#95A5A6");
            ctx.lineWidth = isSelected ? 2 : 1;
            ctx.setLineDash(isSelected ? [] : [4, 3]);
            ctx.strokeRect(x + 1, y + 1, w - 2, h - 2);
            ctx.setLineDash([]);
        }

        if (isSelected) {
            // Selection highlight
            ctx.strokeStyle = "rgba(26,115,232,0.5)";
            ctx.lineWidth = 3;
            if (isWall) {
                ctx.strokeRect(x, y, w, h);
            } else {
                ctx.strokeRect(x - 1, y - 1, w + 2, h + 2);
            }
        }

        if (!isWall) {
            // Icon
            const iconSize = Math.min(gridSize * 0.6, 24);
            ctx.font = `${iconSize}px sans-serif`;
            ctx.textAlign = "center";
            ctx.textBaseline = "middle";
            ctx.fillStyle = "#333";
            ctx.fillText(obj.icon || "📌", x + w / 2, y + h / 2 - 2);

            // Name
            ctx.font = `bold ${Math.max(8, gridSize * 0.22)}px Inter, system-ui, sans-serif`;
            ctx.fillStyle = "#555";
            ctx.fillText(obj.name || "", x + w / 2, y + h - gridSize * 0.18);
        }

        // Resize handle for admin
        if (this.props.isAdmin && isSelected) {
            ctx.strokeStyle = "rgba(0,0,0,0.5)";
            ctx.lineWidth = 1;
            for (let i = 0; i < 3; i++) {
                const offset = 4 + i * 3;
                ctx.beginPath();
                ctx.moveTo(x + w - offset, y + h - 2);
                ctx.lineTo(x + w - 2, y + h - offset);
                ctx.stroke();
            }

            // Flip hint for selected walls
            if (isWall) {
                const hintText = "Press F to flip";
                const hintFs = Math.max(8, gridSize * 0.22);
                ctx.font = `${hintFs}px Inter, system-ui, sans-serif`;
                const tw = ctx.measureText(hintText).width + 10;
                const tx = x + w / 2 - tw / 2;
                const ty = y + h + 4;

                ctx.fillStyle = "rgba(0,0,0,0.75)";
                ctx.beginPath();
                ctx.roundRect(tx, ty, tw, hintFs + 6, 4);
                ctx.fill();

                ctx.fillStyle = "#fff";
                ctx.textAlign = "center";
                ctx.textBaseline = "middle";
                ctx.fillText(hintText, x + w / 2, ty + (hintFs + 6) / 2);
            }
        }
    }

    _drawLocation(ctx, loc, gridSize, searchLocIds) {
        const x = loc.pos_x * gridSize;
        const y = loc.pos_y * gridSize;
        const w = (loc.size_x || 2) * gridSize;
        const h = (loc.size_y || 1) * gridSize;

        const isSelected = loc.id === this.props.selectedLocationId;
        const isHighlighted = loc.id === this.props.highlightedLocationId;
        const isSearchHit = searchLocIds.has(loc.id);
        const isZoneFloor = loc.location_shape === 'zone' || loc.location_shape === 'floor';
        const r = Math.min(6, gridSize * 0.15); // corner radius

        // Color
        let color = loc.location_color || "#4A90D9";
        if (this.props.heatmapEnabled) {
            const hd = this.props.heatmapData[loc.id];
            if (hd) color = this._getHeatmapColor(hd.fill_pct);
        }

        // ── Drop shadow ──
        if (!isZoneFloor) {
            ctx.save();
            ctx.shadowColor = "rgba(0,0,0,0.12)";
            ctx.shadowBlur = 6;
            ctx.shadowOffsetX = 1;
            ctx.shadowOffsetY = 2;
            ctx.fillStyle = color;
            ctx.beginPath();
            ctx.roundRect(x + 1, y + 1, w - 2, h - 2, r);
            ctx.fill();
            ctx.restore();
        }

        // ── Gradient fill ──
        ctx.globalAlpha = isZoneFloor ? 0.3 : 0.9;
        const grad = ctx.createLinearGradient(x, y, x, y + h);
        grad.addColorStop(0, this._lightenColor(color, 0.18));
        grad.addColorStop(1, color);
        ctx.fillStyle = grad;
        ctx.beginPath();
        ctx.roundRect(x + 1, y + 1, w - 2, h - 2, r);
        ctx.fill();
        ctx.globalAlpha = 1.0;

        // ── Inner top highlight (gloss) ──
        if (!isZoneFloor) {
            const gloss = ctx.createLinearGradient(x, y + 1, x, y + h * 0.35);
            gloss.addColorStop(0, "rgba(255,255,255,0.15)");
            gloss.addColorStop(1, "rgba(255,255,255,0)");
            ctx.fillStyle = gloss;
            ctx.beginPath();
            ctx.roundRect(x + 1, y + 1, w - 2, h * 0.35, [r, r, 0, 0]);
            ctx.fill();
        }

        // Shape-specific details
        this._drawShapeDetails(ctx, loc, x, y, w, h, gridSize, color);

        // ── Border ──
        if (isSelected) {
            // Outer glow
            ctx.strokeStyle = "rgba(26,115,232,0.3)";
            ctx.lineWidth = 5;
            ctx.beginPath();
            ctx.roundRect(x - 1, y - 1, w + 2, h + 2, r + 1);
            ctx.stroke();
            // Inner border
            ctx.strokeStyle = "#1a73e8";
            ctx.lineWidth = 2;
        } else if (isHighlighted || isSearchHit) {
            ctx.strokeStyle = "#F59E0B";
            ctx.lineWidth = 2.5;
        } else {
            ctx.strokeStyle = isZoneFloor ? "rgba(0,0,0,0.2)" : "rgba(0,0,0,0.15)";
            ctx.lineWidth = 1;
        }
        ctx.beginPath();
        ctx.roundRect(x + 1, y + 1, w - 2, h - 2, r);
        ctx.stroke();

        // Highlight pulse for search results
        if (isHighlighted || isSearchHit) {
            const pulse = Math.sin(this._highlightAnim * 3) * 0.2 + 0.2;
            ctx.fillStyle = `rgba(245, 158, 11, ${pulse})`;
            ctx.beginPath();
            ctx.roundRect(x + 1, y + 1, w - 2, h - 2, r);
            ctx.fill();
        }

        // ── Label (auto-fit to available width) ──
        const fontSize = Math.max(9, Math.min(gridSize * 0.35, 14));
        ctx.font = `600 ${fontSize}px Inter, system-ui, sans-serif`;
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillStyle = isZoneFloor ? "rgba(30,41,59,0.85)" : "#fff";
        ctx.shadowColor = isZoneFloor ? "rgba(255,255,255,0.6)" : "rgba(0,0,0,0.4)";
        ctx.shadowBlur = isZoneFloor ? 0 : 3;
        let label = loc.name || "Location";
        const maxLabelW = w - 8; // padding inside the box
        if (ctx.measureText(label).width > maxLabelW) {
            // Truncate until it fits
            while (label.length > 1 && ctx.measureText(label + "…").width > maxLabelW) {
                label = label.slice(0, -1);
            }
            label += "…";
        }
        ctx.fillText(label, x + w / 2, y + h / 2 - fontSize * 0.5);
        ctx.shadowBlur = 0;

        // Dimension text below name
        const dimText = this._formatDimension(loc.size_x || 2, loc.size_y || 1);
        const dimFontSize = Math.max(7, fontSize * 0.7);
        ctx.font = `${dimFontSize}px Inter, system-ui, sans-serif`;
        ctx.fillStyle = isZoneFloor ? "rgba(30,41,59,0.5)" : "rgba(255,255,255,0.7)";
        ctx.fillText(dimText, x + w / 2, y + h / 2 + fontSize * 0.4);

        // Area for zone/floor
        if (isZoneFloor) {
            const areaText = this._formatArea(loc.size_x || 2, loc.size_y || 1);
            ctx.font = `italic ${dimFontSize}px Inter, system-ui, sans-serif`;
            ctx.fillStyle = "rgba(60,60,60,0.7)";
            ctx.fillText(areaText, x + w / 2, y + h / 2 + fontSize * 1.2);
        }

        // Product search quantity badge
        if (isSearchHit) {
            const result = this.props.productSearchResults.find(r => r.location_id === loc.id);
            if (result) {
                const badgeText = `${result.qty} ${result.uom || ''}`.trim();
                ctx.font = `bold 10px Inter, system-ui, sans-serif`;
                const badgeW = ctx.measureText(badgeText).width + 12;
                ctx.fillStyle = "#EF4444";
                ctx.beginPath();
                const bx = x + w - badgeW - 3;
                const by = y + 3;
                ctx.roundRect(bx, by, badgeW, 16, 6);
                ctx.fill();
                ctx.fillStyle = "#fff";
                ctx.textAlign = "center";
                ctx.fillText(badgeText, bx + badgeW / 2, by + 9);
            }
        }

        // ── Product summary badge on tile ──
        const summary = loc.product_summary || [];
        if (summary.length > 0) {
            const productCount = summary.length;
            const totalQty = summary.reduce((s, p) => s + (p.qty || 0), 0);

            if (productCount <= WarehouseCanvas.MAX_INLINE_PRODUCTS) {
                // Show inline, one thin line per product, truncated
                const pf = Math.max(6, Math.min(gridSize * 0.18, 9));
                ctx.font = `${pf}px Inter, system-ui, sans-serif`;
                ctx.textAlign = 'center';
                ctx.textBaseline = 'bottom';
                const lineH = pf + 2;
                const startY = y + h - 4 - (productCount - 1) * lineH;
                for (let pi = 0; pi < productCount; pi++) {
                    const p = summary[pi];
                    const maxPW = w - 10;
                    let pLabel = `${p.product_name || p.name || '?'}: ${p.qty}${p.uom ? ' ' + p.uom : ''}`;
                    while (pLabel.length > 3 && ctx.measureText(pLabel).width > maxPW) {
                        pLabel = pLabel.slice(0, -1);
                    }
                    if (ctx.measureText(pLabel).width > maxPW) pLabel = pLabel.slice(0, -1) + '…';
                    const alpha = isZoneFloor ? 0.7 : 0.85;
                    ctx.fillStyle = isZoneFloor ? `rgba(30,41,59,${alpha})` : `rgba(255,255,255,${alpha})`;
                    ctx.fillText(pLabel, x + w / 2, startY + pi * lineH + lineH);
                }
            } else {
                // Badge-only: show 📦 count + total qty
                const badgeText = `📦 ${productCount} products`;
                const pf = Math.max(7, Math.min(gridSize * 0.2, 10));
                ctx.font = `bold ${pf}px Inter, system-ui, sans-serif`;
                const bW = ctx.measureText(badgeText).width + 10;
                const bH = pf + 6;
                const bx = x + w / 2 - bW / 2;
                const by2 = y + h - bH - 3;
                // Badge background
                ctx.fillStyle = isZoneFloor ? 'rgba(30,41,59,0.65)' : 'rgba(0,0,0,0.55)';
                ctx.beginPath();
                ctx.roundRect(bx, by2, bW, bH, 4);
                ctx.fill();
                // Badge text
                ctx.fillStyle = '#FFD700';
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';
                ctx.fillText(badgeText, x + w / 2, by2 + bH / 2);
                ctx.textBaseline = 'middle';
            }
        }

        // ── Resize handle (admin) — grip lines ──
        if (this.props.isAdmin) {
            ctx.strokeStyle = "rgba(0,0,0,0.25)";
            ctx.lineWidth = 1;
            for (let i = 0; i < 3; i++) {
                const offset = 4 + i * 3;
                ctx.beginPath();
                ctx.moveTo(x + w - offset, y + h - 2);
                ctx.lineTo(x + w - 2, y + h - offset);
                ctx.stroke();
            }
        }

        // LIVE measurement tooltip during resize
        if (this._isResizing && this._resizeLocId === loc.id) {
            const liveW = loc.size_x || 2;
            const liveH = loc.size_y || 1;
            const tipText = this._formatDimension(liveW, liveH);
            const tipFontSize = 12;
            ctx.font = `bold ${tipFontSize}px Inter, system-ui, sans-serif`;
            const tw = ctx.measureText(tipText).width + 14;
            const tx = x + w + 5;
            const ty = y + h - 10;

            ctx.fillStyle = "rgba(0,0,0,0.85)";
            ctx.beginPath();
            ctx.roundRect(tx, ty, tw, 22, 6);
            ctx.fill();

            ctx.fillStyle = "#FFD700";
            ctx.textAlign = "left";
            ctx.textBaseline = "middle";
            ctx.fillText(tipText, tx + 7, ty + 11);
            ctx.textAlign = "center";
        }

        // ── Draw children inside parent ──
        const children = loc.children || [];
        if (children.length > 0) {
            for (const child of children) {
                this._drawChildLocation(ctx, child, loc, gridSize, searchLocIds);
            }
        }
    }

    _drawChildLocation(ctx, child, parent, gridSize, searchLocIds) {
        const parentX = parent.pos_x * gridSize;
        const parentY = parent.pos_y * gridSize;

        // Child position is relative to parent
        const cx = parentX + child.pos_x * gridSize;
        const cy = parentY + child.pos_y * gridSize;
        const cw = (child.size_x || 1) * gridSize;
        const ch = (child.size_y || 1) * gridSize;

        const isSelectedChild = (this._selectedChildId === child.id);

        // Child background — use heatmap color when enabled
        let childColor = child.location_color || '#6BB5E0';
        if (this.props.heatmapEnabled && child.id) {
            const hd = this.props.heatmapData[child.id];
            if (hd) childColor = this._getHeatmapColor(hd.fill_pct);
        }
        ctx.fillStyle = childColor;
        ctx.globalAlpha = 0.75;
        ctx.fillRect(cx + 2, cy + 2, cw - 4, ch - 4);
        ctx.globalAlpha = 1.0;

        // Child border
        ctx.strokeStyle = isSelectedChild ? '#1a73e8' : 'rgba(255,255,255,0.6)';
        ctx.lineWidth = isSelectedChild ? 2 : 1;
        ctx.strokeRect(cx + 2, cy + 2, cw - 4, ch - 4);

        // Shape icon (small)
        const icon = WarehouseCanvas.SHAPE_ICONS[child.location_shape] || '📦';
        const iconSize = Math.min(12, gridSize * 0.3);
        ctx.font = `${iconSize}px sans-serif`;
        ctx.textAlign = 'left';
        ctx.fillStyle = 'rgba(255,255,255,0.7)';
        ctx.fillText(icon, cx + 4, cy + iconSize + 2);

        // Child name (auto-fit)
        const lf = Math.max(6, Math.min(gridSize * 0.25, 11));
        ctx.font = `bold ${lf}px Inter, system-ui, sans-serif`;
        ctx.fillStyle = '#fff';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.shadowColor = 'rgba(0,0,0,0.5)';
        ctx.shadowBlur = 1;
        let childName = child.name || '';
        const maxChildW = cw - 8;
        if (ctx.measureText(childName).width > maxChildW) {
            while (childName.length > 1 && ctx.measureText(childName + '…').width > maxChildW) {
                childName = childName.slice(0, -1);
            }
            childName += '…';
        }
        ctx.fillText(childName, cx + cw / 2, cy + ch / 2);
        ctx.shadowBlur = 0;

        // Resize handle for admin
        if (this.props.isAdmin) {
            const hSize = 6;
            ctx.fillStyle = '#999';
            ctx.beginPath();
            ctx.moveTo(cx + cw - 2, cy + ch - 2);
            ctx.lineTo(cx + cw - hSize - 2, cy + ch - 2);
            ctx.lineTo(cx + cw - 2, cy + ch - hSize - 2);
            ctx.closePath();
            ctx.fill();
        }
    }

    // ========================================================================
    // Product Tooltip (HTML overlay)
    // ========================================================================

    _showProductTooltip(loc, screenX, screenY) {
        const summary = loc.product_summary || [];
        if (summary.length === 0) return;
        // If same loc already shown, just reposition
        if (this._tooltipLocId === loc.id && this._tooltipEl) {
            this._repositionTooltip(screenX, screenY);
            return;
        }
        this._hideProductTooltip();
        this._tooltipLocId = loc.id;

        const el = document.createElement('div');
        el.className = 'o_wh_product_tooltip';
        el.style.cssText = [
            'position:fixed',
            'z-index:9999',
            'background:linear-gradient(135deg,#1e293b,#0f172a)',
            'color:#f1f5f9',
            'border-radius:12px',
            'box-shadow:0 8px 32px rgba(0,0,0,0.55)',
            'min-width:220px',
            'max-width:320px',
            'padding:0',
            'font-family:Inter,system-ui,sans-serif',
            'font-size:12px',
            'pointer-events:auto',
            'border:1px solid rgba(255,255,255,0.1)',
            'overflow:hidden',
            'transition:opacity 0.15s ease',
            'opacity:0',
        ].join(';');

        // Header
        const header = document.createElement('div');
        header.style.cssText = 'padding:10px 14px 8px;border-bottom:1px solid rgba(255,255,255,0.1);background:rgba(255,255,255,0.05);';
        header.innerHTML = `
            <div style="display:flex;align-items:center;gap:6px;">
                <span style="font-size:15px;">📦</span>
                <div>
                    <div style="font-weight:700;font-size:12px;color:#f8fafc;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:240px;">${loc.name || 'Location'}</div>
                    <div style="font-size:10px;color:#94a3b8;margin-top:1px;">${summary.length} product${summary.length !== 1 ? 's' : ''} stored</div>
                </div>
            </div>`;
        el.appendChild(header);

        // Scrollable body
        const body = document.createElement('div');
        body.style.cssText = 'max-height:200px;overflow-y:auto;padding:6px 0;scrollbar-width:thin;scrollbar-color:#334155 transparent;';

        // Custom scrollbar for webkit
        const style = document.createElement('style');
        style.textContent = `.o_wh_product_tooltip div::-webkit-scrollbar{width:4px;}.o_wh_product_tooltip div::-webkit-scrollbar-track{background:transparent;}.o_wh_product_tooltip div::-webkit-scrollbar-thumb{background:#334155;border-radius:2px;}`;
        document.head.appendChild(style);
        this._tooltipStyle = style;

        const totalQty = summary.reduce((s, p) => s + (parseFloat(p.qty !== undefined ? p.qty : p.quantity) || 0), 0);

        summary.forEach((p, idx) => {
            const row = document.createElement('div');
            row.style.cssText = [
                'display:flex',
                'align-items:center',
                'justify-content:space-between',
                'padding:5px 14px',
                idx % 2 === 0 ? 'background:rgba(255,255,255,0.03)' : 'background:transparent',
                'gap:8px',
            ].join(';');

            const nameSpan = document.createElement('span');
            nameSpan.style.cssText = 'flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:#cbd5e1;font-size:11px;';
            nameSpan.textContent = p.product_name || p.name || 'Unknown Product';
            nameSpan.title = p.product_name || p.name || '';

            const qtyBadge = document.createElement('span');
            qtyBadge.style.cssText = 'background:rgba(99,102,241,0.3);color:#a5b4fc;border-radius:20px;padding:1px 8px;font-size:10px;font-weight:700;white-space:nowrap;flex-shrink:0;border:1px solid rgba(99,102,241,0.4);';
            const qty = p.qty !== undefined ? p.qty : p.quantity;
            const uom = p.uom || '';
            qtyBadge.textContent = `${qty}${uom ? ' ' + uom : ''}`;

            row.appendChild(nameSpan);
            row.appendChild(qtyBadge);
            body.appendChild(row);
        });

        el.appendChild(body);

        // Footer total
        if (summary.length > 1) {
            const footer = document.createElement('div');
            footer.style.cssText = 'padding:6px 14px;border-top:1px solid rgba(255,255,255,0.08);display:flex;justify-content:space-between;align-items:center;background:rgba(255,255,255,0.03);';
            footer.innerHTML = `
                <span style="color:#64748b;font-size:10px;font-style:italic;">Scroll to see all</span>
                <span style="color:#38bdf8;font-size:10px;font-weight:700;">Total: ${totalQty.toFixed(2).replace(/\.?0+$/, '')}</span>`;
            el.appendChild(footer);
        }

        document.body.appendChild(el);
        this._tooltipEl = el;
        this._repositionTooltip(screenX, screenY);

        // Keep tooltip alive while mouse is over it
        el.addEventListener('mouseenter', () => {
            if (this._tooltipHideTimer) {
                clearTimeout(this._tooltipHideTimer);
                this._tooltipHideTimer = null;
            }
        });
        el.addEventListener('mouseleave', () => {
            this._tooltipHideTimer = setTimeout(() => this._hideProductTooltip(), 150);
        });

        // Fade in
        requestAnimationFrame(() => { el.style.opacity = '1'; });
    }

    _repositionTooltip(screenX, screenY) {
        if (!this._tooltipEl) return;
        const el = this._tooltipEl;
        const margin = 14;
        const vw = window.innerWidth;
        const vh = window.innerHeight;
        const elW = el.offsetWidth || 240;
        const elH = el.offsetHeight || 200;
        let left = screenX + margin;
        let top = screenY - elH / 2;
        if (left + elW > vw - 10) left = screenX - elW - margin;
        if (top < 10) top = 10;
        if (top + elH > vh - 10) top = vh - elH - 10;
        el.style.left = `${left}px`;
        el.style.top = `${top}px`;
    }

    _hideProductTooltip() {
        if (this._tooltipHideTimer) {
            clearTimeout(this._tooltipHideTimer);
            this._tooltipHideTimer = null;
        }
        if (this._tooltipEl) {
            this._tooltipEl.remove();
            this._tooltipEl = null;
        }
        if (this._tooltipStyle) {
            this._tooltipStyle.remove();
            this._tooltipStyle = null;
        }
        this._tooltipLocId = null;
    }

    _getLocationAtPos(pos, gridSize) {
        for (let i = this.props.locations.length - 1; i >= 0; i--) {
            const loc = this.props.locations[i];
            const lx = loc.pos_x * gridSize;
            const ly = loc.pos_y * gridSize;
            const lw = (loc.size_x || 2) * gridSize;
            const lh = (loc.size_y || 1) * gridSize;
            if (pos.x >= lx && pos.x <= lx + lw && pos.y >= ly && pos.y <= ly + lh) {
                return loc;
            }
        }
        return null;
    }

    _drawShapeDetails(ctx, loc, x, y, w, h, gridSize, color) {
        const shape = loc.location_shape || 'rack';

        switch (shape) {
            case 'rack': {
                const children = loc.children || [];

                // Rack icon
                ctx.font = `${Math.min(18, gridSize * 0.4)}px sans-serif`;
                ctx.textAlign = "left";
                ctx.fillStyle = "rgba(255,255,255,0.5)";
                ctx.fillText("📦", x + 3, y + 14);

                // 4 corner post dots
                ctx.fillStyle = "rgba(80,80,80,0.7)";
                const dotR = Math.max(2, gridSize * 0.06);
                const pad = 4;
                for (const [cx, cy] of [[x + pad, y + pad], [x + w - pad, y + pad], [x + pad, y + h - pad], [x + w - pad, y + h - pad]]) {
                    ctx.beginPath();
                    ctx.arc(cx, cy, dotR, 0, Math.PI * 2);
                    ctx.fill();
                }

                // Child count badge
                if (children.length > 0) {
                    const badgeText = `${children.length} child${children.length > 1 ? 'ren' : ''}`;
                    const bf = Math.max(7, gridSize * 0.2);
                    ctx.font = `bold ${bf}px Inter, system-ui, sans-serif`;
                    const bw = ctx.measureText(badgeText).width + 8;
                    ctx.fillStyle = "rgba(0,0,0,0.5)";
                    ctx.beginPath();
                    ctx.roundRect(x + w - bw - 3, y + 3, bw, 12, 3);
                    ctx.fill();
                    ctx.fillStyle = "#FFD700";
                    ctx.textAlign = "center";
                    ctx.fillText(badgeText, x + w - bw / 2 - 3, y + 11);
                }
                ctx.textAlign = "center";
                break;
            }
            case 'shelf': {
                const children = loc.children || [];

                // Shelf icon
                ctx.font = `${Math.min(16, gridSize * 0.35)}px sans-serif`;
                ctx.textAlign = "left";
                ctx.fillStyle = "rgba(255,255,255,0.5)";
                ctx.fillText("🗄️", x + 3, y + 14);

                // 4 corner leg dots
                ctx.fillStyle = "rgba(80,80,80,0.7)";
                const legR = Math.max(2, gridSize * 0.06);
                const legPad = 4;
                for (const [cx, cy] of [[x + legPad, y + legPad], [x + w - legPad, y + legPad], [x + legPad, y + h - legPad], [x + w - legPad, y + h - legPad]]) {
                    ctx.beginPath();
                    ctx.arc(cx, cy, legR, 0, Math.PI * 2);
                    ctx.fill();
                }

                // Child count badge
                if (children.length > 0) {
                    const badgeText = `${children.length} child${children.length > 1 ? 'ren' : ''}`;
                    const badgeFontSize = Math.max(7, gridSize * 0.2);
                    ctx.font = `bold ${badgeFontSize}px Inter, system-ui, sans-serif`;
                    const badgeW = ctx.measureText(badgeText).width + 8;
                    ctx.fillStyle = "rgba(0,0,0,0.5)";
                    ctx.beginPath();
                    ctx.roundRect(x + w - badgeW - 3, y + 3, badgeW, 12, 3);
                    ctx.fill();
                    ctx.fillStyle = "#FFD700";
                    ctx.textAlign = "center";
                    ctx.fillText(badgeText, x + w - badgeW / 2 - 3, y + 11);
                }
                ctx.textAlign = "center";
                break;
            }
            case 'bin': {
                ctx.font = `${Math.min(14, gridSize * 0.35)}px sans-serif`;
                ctx.textAlign = "left";
                ctx.fillStyle = "rgba(255,255,255,0.5)";
                ctx.fillText("📥", x + 3, y + 14);
                ctx.textAlign = "center";
                break;
            }
            case 'packing': {
                // Conveyor stripes
                ctx.strokeStyle = "rgba(255,255,255,0.2)";
                ctx.lineWidth = 2;
                for (let px = x + 8; px < x + w; px += 10) {
                    ctx.beginPath();
                    ctx.moveTo(px, y + h * 0.3);
                    ctx.lineTo(px + 5, y + h * 0.7);
                    ctx.stroke();
                }
                ctx.font = `${Math.min(16, gridSize * 0.35)}px sans-serif`;
                ctx.textAlign = "left";
                ctx.fillStyle = "rgba(255,255,255,0.6)";
                ctx.fillText("📋", x + 3, y + 14);
                ctx.textAlign = "center";
                break;
            }
            case 'refrigerator': {
                // Snowflake pattern
                ctx.fillStyle = "rgba(255,255,255,0.15)";
                ctx.font = `${Math.min(20, gridSize * 0.4)}px sans-serif`;
                ctx.textAlign = "center";
                ctx.fillText("❄️", x + w / 2, y + h * 0.35);
                ctx.textAlign = "center";
                break;
            }
            case 'qc_area': {
                // Checkmark
                ctx.strokeStyle = "rgba(255,255,255,0.25)";
                ctx.lineWidth = 2;
                ctx.setLineDash([6, 4]);
                ctx.strokeRect(x + 4, y + 4, w - 8, h - 8);
                ctx.setLineDash([]);
                ctx.font = `${Math.min(16, gridSize * 0.35)}px sans-serif`;
                ctx.textAlign = "left";
                ctx.fillStyle = "rgba(255,255,255,0.5)";
                ctx.fillText("✅", x + 3, y + 14);
                ctx.textAlign = "center";
                break;
            }
            case 'wall': {
                // Solid block for wall
                ctx.fillStyle = loc.location_color || "#34495E";
                ctx.fillRect(x, y, w, h);

                // Subtle 3D top edge highlight to make it pop
                ctx.fillStyle = "rgba(255,255,255,0.15)";
                ctx.fillRect(x, y, w, 4);

                // Subtle bottom shadow
                ctx.fillStyle = "rgba(0,0,0,0.3)";
                ctx.fillRect(x, y + h - 4, w, 4);

                // Draw name tag if space allows
                if (w > gridSize && h > gridSize) {
                    ctx.fillStyle = "rgba(255,255,255,0.8)";
                    ctx.font = `bold ${Math.min(10, gridSize * 0.25)}px sans-serif`;
                    ctx.textAlign = "center";
                    ctx.textBaseline = "middle";
                    ctx.fillText(loc.name || "Wall", x + w / 2, y + h / 2);
                }
                ctx.textAlign = "center";
                break;
            }
            case 'dock': {
                // Ramp stripes
                ctx.strokeStyle = "rgba(255,255,0,0.3)";
                ctx.lineWidth = 2;
                const rot = loc.location_rotation || 0;

                // Rotated 90 or 270 means facing sideways, draw vertical stripes matching the 3d rotation out
                if (rot === 90 || rot === 270) {
                    for (let i = 0; i < 3; i++) {
                        const dx = x + w * 0.2 + i * (w * 0.2);
                        ctx.beginPath();
                        ctx.moveTo(dx, y + 4);
                        ctx.lineTo(dx, y + h - 4);
                        ctx.stroke();
                    }
                } else {
                    for (let i = 0; i < 3; i++) {
                        const dy = y + h * 0.2 + i * (h * 0.2);
                        ctx.beginPath();
                        ctx.moveTo(x + 4, dy);
                        ctx.lineTo(x + w - 4, dy);
                        ctx.stroke();
                    }
                }

                ctx.save();
                ctx.translate(x + w / 2, y + h / 2);
                ctx.rotate(rot * Math.PI / 180);

                ctx.font = `${Math.min(16, gridSize * 0.35)}px sans-serif`;
                ctx.textAlign = "center";
                ctx.textBaseline = "middle";
                ctx.fillStyle = "rgba(255,255,255,0.5)";
                // adjust text position slightly because textBaseline="middle" isn't visually perfectly centered for emojis
                ctx.fillText("🚛", 0, 2);

                ctx.restore();
                break;
            }
            case 'zone': {
                ctx.fillStyle = "rgba(80,80,80,0.4)";
                ctx.fillRect(x, y, w, h);

                // Create a diagonal striped pattern for the border
                const pCanvas = document.createElement('canvas');
                pCanvas.width = 40;
                pCanvas.height = 40;
                const pCtx = pCanvas.getContext('2d');
                pCtx.fillStyle = '#FFDD00';
                pCtx.fillRect(0, 0, 40, 40);
                pCtx.fillStyle = '#222222';
                pCtx.beginPath();
                for (let i = -40; i < 80; i += 40) {
                    pCtx.moveTo(i, 0);
                    pCtx.lineTo(i + 40, 40);
                    pCtx.lineTo(i + 40 + 25, 40);
                    pCtx.lineTo(i + 25, 0);
                }
                pCtx.fill();
                const pattern = ctx.createPattern(pCanvas, 'repeat');

                ctx.strokeStyle = pattern;
                ctx.lineWidth = 10;
                ctx.strokeRect(x, y, w, h);

                // Draw name tag at top-left
                ctx.fillStyle = "white";
                ctx.font = `bold ${Math.min(12, gridSize * 0.3)}px sans-serif`;
                ctx.textAlign = "left";
                ctx.textBaseline = "top";
                ctx.fillText(loc.name || "Zone", x + 10, y + 10);

                // Switch alignment back, not drawing emoji
                ctx.textAlign = "center";
                break;
            }
            case 'floor': {
                // Striped border for zone/floor
                ctx.strokeStyle = "rgba(0,0,0,0.15)";
                ctx.lineWidth = 1;
                ctx.setLineDash([8, 4]);
                ctx.strokeRect(x + 4, y + 4, w - 8, h - 8);
                ctx.setLineDash([]);
                break;
            }
        }
    }

    _getHeatmapColor(pct) {
        // Smooth HSL interpolation: green (120°) → red (0°)
        const clamped = Math.max(0, Math.min(pct, 100));
        const hue = 120 - (clamped / 100) * 120; // 120=green, 0=red
        return `hsl(${hue}, 80%, 45%)`;
    }

    _drawHeatmapLegend(ctx, viewW, viewH) {
        const legW = 200;
        const legH = 14;
        const padX = 18;
        const padY = 18;
        const lx = padX;
        const ly = viewH - padY - legH - 22;

        // Background panel
        ctx.fillStyle = 'rgba(15, 23, 42, 0.82)';
        ctx.beginPath();
        ctx.roundRect(lx - 8, ly - 20, legW + 16, legH + 44, 10);
        ctx.fill();

        // Title
        ctx.font = 'bold 10px Inter, system-ui, sans-serif';
        ctx.fillStyle = '#cbd5e1';
        ctx.textAlign = 'left';
        ctx.textBaseline = 'bottom';
        ctx.fillText('Stock Density', lx, ly - 4);

        // Gradient bar
        const grad = ctx.createLinearGradient(lx, 0, lx + legW, 0);
        grad.addColorStop(0, 'hsl(120, 80%, 45%)');
        grad.addColorStop(0.5, 'hsl(60, 80%, 45%)');
        grad.addColorStop(1, 'hsl(0, 80%, 45%)');
        ctx.fillStyle = grad;
        ctx.beginPath();
        ctx.roundRect(lx, ly, legW, legH, 4);
        ctx.fill();

        // Border
        ctx.strokeStyle = 'rgba(255,255,255,0.15)';
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.roundRect(lx, ly, legW, legH, 4);
        ctx.stroke();

        // Labels
        ctx.font = '9px Inter, system-ui, sans-serif';
        ctx.fillStyle = '#94a3b8';
        ctx.textAlign = 'left';
        ctx.textBaseline = 'top';
        ctx.fillText('0% Empty', lx, ly + legH + 4);
        ctx.textAlign = 'center';
        ctx.fillText('50%', lx + legW / 2, ly + legH + 4);
        ctx.textAlign = 'right';
        ctx.fillText('100% Full', lx + legW, ly + legH + 4);
    }

    _lightenColor(color, percent) {
        const num = parseInt(color.replace("#", ""), 16),
            amt = Math.round(2.55 * (percent * 100)),
            R = (num >> 16) + amt,
            G = (num >> 8 & 0x00FF) + amt,
            B = (num & 0x0000FF) + amt;
        return "#" + (
            0x1000000 +
            (R < 255 ? (R < 1 ? 0 : R) : 255) * 0x10000 +
            (G < 255 ? (G < 1 ? 0 : G) : 255) * 0x100 +
            (B < 255 ? (B < 1 ? 0 : B) : 255)
        ).toString(16).slice(1);
    }

    // ========================================================================
    // Mouse Events
    // ========================================================================

    _screenToCanvas(e) {
        const canvas = this.canvasRef.el;
        const rect = canvas.getBoundingClientRect();
        const zoom = this.props.zoomLevel;
        return {
            x: (e.clientX - rect.left - this._panOffsetX) / zoom,
            y: (e.clientY - rect.top - this._panOffsetY) / zoom,
        };
    }

    _onMouseDown(e) {
        // Always dismiss tooltip immediately on any click — prevents it blocking resize/drag
        this._hideProductTooltip();

        const pos = this._screenToCanvas(e);
        const gridSize = this.props.layoutData.grid_size || 1;

        // Middle mouse or Shift+left = pan
        if (e.button === 1 || (e.button === 0 && e.shiftKey)) {
            this._isPanning = true;
            this._panStartX = e.clientX - this._panOffsetX;
            this._panStartY = e.clientY - this._panOffsetY;
            e.preventDefault();
            return;
        }

        if (e.button !== 0) return;

        // Check CHILD resize handles first (admin only)
        if (this.props.isAdmin) {
            for (const loc of this.props.locations) {
                const px = loc.pos_x * gridSize;
                const py = loc.pos_y * gridSize;
                for (const child of (loc.children || [])) {
                    const cx = px + child.pos_x * gridSize;
                    const cy = py + child.pos_y * gridSize;
                    const cw = (child.size_x || 1) * gridSize;
                    const ch_h = (child.size_y || 1) * gridSize;
                    const hSize = 8;
                    if (pos.x >= cx + cw - hSize && pos.x <= cx + cw &&
                        pos.y >= cy + ch_h - hSize && pos.y <= cy + ch_h) {
                        this._isResizingChild = true;
                        this._resizeChildParentId = loc.id;
                        this._resizeChildId = child.id;
                        this._resizeStartW = child.size_x || 1;
                        this._resizeStartH = child.size_y || 1;
                        this._resizeStartMX = pos.x;
                        this._resizeStartMY = pos.y;
                        e.preventDefault();
                        return;
                    }
                }
            }
        }

        // Check CHILD hit for select / drag
        for (let i = this.props.locations.length - 1; i >= 0; i--) {
            const loc = this.props.locations[i];
            const px = loc.pos_x * gridSize;
            const py = loc.pos_y * gridSize;
            for (const child of (loc.children || [])) {
                const cx = px + child.pos_x * gridSize;
                const cy = py + child.pos_y * gridSize;
                const cw = (child.size_x || 1) * gridSize;
                const ch_h = (child.size_y || 1) * gridSize;
                if (pos.x >= cx && pos.x <= cx + cw &&
                    pos.y >= cy && pos.y <= cy + ch_h) {
                    this._selectedChildId = child.id;
                    this.props.onLocationSelected(loc.id);
                    if (this.props.isAdmin) {
                        this._isDraggingChild = true;
                        this._dragChildParentId = loc.id;
                        this._dragChildId = child.id;
                        this._dragChildOffsetX = pos.x - cx;
                        this._dragChildOffsetY = pos.y - cy;
                    }
                    this._needsRedraw = true;
                    return;
                }
            }
        }

        this._selectedChildId = null;

        // Check PARENT resize handle hit
        if (this.props.isAdmin) {
            // First check Map Objects resize handles
            for (const obj of this.props.mapObjects) {
                const ox = obj.pos_x * gridSize;
                const oy = obj.pos_y * gridSize;
                const ow = (obj.size_x || 1) * gridSize;
                const oh = (obj.size_y || 1) * gridSize;
                const hSize = 10;
                if (pos.x >= ox + ow - hSize && pos.x <= ox + ow &&
                    pos.y >= oy + oh - hSize && pos.y <= oy + oh &&
                    obj.id === this.props.selectedMapObjectId) {
                    this._isResizingMapObj = true;
                    this._resizeMapObjId = obj.id;
                    this._resizeObjType = obj.object_type;
                    this._resizeStartW = obj.size_x || 1;
                    this._resizeStartH = obj.size_y || 1;
                    this._resizeStartMX = pos.x;
                    this._resizeStartMY = pos.y;
                    e.preventDefault();
                    return;
                }
            }

            for (const loc of this.props.locations) {
                const lx = loc.pos_x * gridSize;
                const ly = loc.pos_y * gridSize;
                const lw = (loc.size_x || 2) * gridSize;
                const lh = (loc.size_y || 1) * gridSize;
                const hSize = 10;
                if (pos.x >= lx + lw - hSize && pos.x <= lx + lw &&
                    pos.y >= ly + lh - hSize && pos.y <= ly + lh) {
                    this._isResizing = true;
                    this._resizeLocId = loc.id;
                    this._resizeStartW = loc.size_x || 2;
                    this._resizeStartH = loc.size_y || 1;
                    this._resizeStartMX = pos.x;
                    this._resizeStartMY = pos.y;
                    e.preventDefault();
                    return;
                }
            }
        }

        // Check Map Object hit for select / drag
        for (let i = this.props.mapObjects.length - 1; i >= 0; i--) {
            const obj = this.props.mapObjects[i];
            const ox = obj.pos_x * gridSize;
            const oy = obj.pos_y * gridSize;
            const ow = (obj.size_x || 1) * gridSize;
            const oh = (obj.size_y || 1) * gridSize;
            if (pos.x >= ox && pos.x <= ox + ow && pos.y >= oy && pos.y <= oy + oh) {
                if (this.props.onMapObjectSelected) {
                    this.props.onMapObjectSelected(obj.id);
                }
                if (this.props.isAdmin) {
                    this._isDraggingMapObj = true;
                    this._dragMapObjId = obj.id;
                    this._dragOffsetX = pos.x - ox;
                    this._dragOffsetY = pos.y - oy;
                }
                this._needsRedraw = true;
                return;
            }
        }

        // Check PARENT hit for select / drag
        for (let i = this.props.locations.length - 1; i >= 0; i--) {
            const loc = this.props.locations[i];
            const lx = loc.pos_x * gridSize;
            const ly = loc.pos_y * gridSize;
            const lw = (loc.size_x || 2) * gridSize;
            const lh = (loc.size_y || 1) * gridSize;
            if (pos.x >= lx && pos.x <= lx + lw && pos.y >= ly && pos.y <= ly + lh) {
                this.props.onLocationSelected(loc.id);
                if (this.props.onMapObjectSelected) {
                    this.props.onMapObjectSelected(null);
                }
                if (this.props.isAdmin) {
                    this._isDragging = true;
                    this._dragLocId = loc.id;
                    this._dragOffsetX = pos.x - lx;
                    this._dragOffsetY = pos.y - ly;
                }
                return;
            }
        }

        // Clicked empty space
        this.props.onLocationSelected(null);
        if (this.props.onMapObjectSelected) {
            this.props.onMapObjectSelected(null);
        }
    }

    _onMouseMove(e) {
        const canvas = this.canvasRef.el;
        const pos = this._screenToCanvas(e);
        const gridSize = this.props.layoutData.grid_size || 1;

        if (this._isPanning) {
            this._panOffsetX = e.clientX - this._panStartX;
            this._panOffsetY = e.clientY - this._panStartY;
            this._needsRedraw = true;
            this._hideProductTooltip();
            return;
        }

        // Product tooltip: show when hovering over a location that has products
        if (!this._isDragging && !this._isResizing && !this._isDraggingChild && !this._isResizingChild) {
            const hoveredLoc = this._getLocationAtPos(pos, gridSize);
            if (hoveredLoc && (hoveredLoc.product_summary || []).length > 0) {
                if (this._tooltipLocId !== hoveredLoc.id) {
                    // Small delay to avoid flashing on fast mouse moves
                    if (this._tooltipHideTimer) clearTimeout(this._tooltipHideTimer);
                    this._tooltipHideTimer = setTimeout(() => {
                        this._showProductTooltip(hoveredLoc, e.clientX, e.clientY);
                    }, 280);
                } else {
                    this._repositionTooltip(e.clientX, e.clientY);
                }
            } else {
                if (this._tooltipLocId !== null) {
                    if (this._tooltipHideTimer) clearTimeout(this._tooltipHideTimer);
                    this._tooltipHideTimer = setTimeout(() => this._hideProductTooltip(), 120);
                }
            }
        }

        // Child resize
        if (this._isResizingChild && this._resizeChildId) {
            const dx = pos.x - this._resizeStartMX;
            const dy = pos.y - this._resizeStartMY;
            const newW = Math.max(1, Math.round(this._resizeStartW + dx / gridSize));
            const newH = Math.max(1, Math.round(this._resizeStartH + dy / gridSize));
            this.props.onChildResized(this._resizeChildParentId, this._resizeChildId, newW, newH);
            this._needsRedraw = true;
            return;
        }

        // Child drag
        if (this._isDraggingChild && this._dragChildId) {
            const parent = this.props.locations.find(l => l.id === this._dragChildParentId);
            if (parent) {
                const px = parent.pos_x * gridSize;
                const py = parent.pos_y * gridSize;
                const relX = pos.x - this._dragChildOffsetX - px;
                const relY = pos.y - this._dragChildOffsetY - py;
                const gx = Math.max(0, Math.round(relX / gridSize));
                const gy = Math.max(0, Math.round(relY / gridSize));
                this.props.onChildMoved(this._dragChildParentId, this._dragChildId, gx, gy);
            }
            this._needsRedraw = true;
            return;
        }

        // Parent resize
        if (this._isResizing && this._resizeLocId) {
            const layout = this.props.layoutData;
            const canvasW = layout.canvas_width || 40;
            const canvasH = layout.canvas_height || 30;
            const dx = pos.x - this._resizeStartMX;
            const dy = pos.y - this._resizeStartMY;
            const loc = this.props.locations.find(l => l.id === this._resizeLocId);
            if (loc) {
                const maxW = canvasW - (loc.pos_x || 0);
                const maxH = canvasH - (loc.pos_y || 0);
                const newW = Math.min(maxW, Math.max(1, Math.round(this._resizeStartW + dx / gridSize)));
                const newH = Math.min(maxH, Math.max(1, Math.round(this._resizeStartH + dy / gridSize)));
                if (loc.size_x !== newW || loc.size_y !== newH) {
                    this.props.onLocationResized(this._resizeLocId, newW, newH);
                }
            }
            this._needsRedraw = true;
            return;
        }

        // Map Object resize
        if (this._isResizingMapObj && this._resizeMapObjId) {
            const layout = this.props.layoutData;
            const canvasW = layout.canvas_width || 40;
            const canvasH = layout.canvas_height || 30;
            const dx = pos.x - this._resizeStartMX;
            const dy = pos.y - this._resizeStartMY;

            // Find the object to know its position for max-size clamping
            const obj = this.props.mapObjects.find(o => o.id === this._resizeMapObjId);
            const objPosX = obj ? (obj.pos_x || 0) : 0;
            const objPosY = obj ? (obj.pos_y || 0) : 0;
            const maxW = canvasW - objPosX;
            const maxH = canvasH - objPosY;

            let newW = Math.min(maxW, Math.max(1, Math.round(this._resizeStartW + dx / gridSize)));
            let newH = Math.min(maxH, Math.max(1, Math.round(this._resizeStartH + dy / gridSize)));

            // Walls: only allow extending the length axis, lock the other to 1
            if (this._resizeObjType === 'wall') {
                if (this._resizeStartW === 1 && this._resizeStartH === 1) {
                    if (Math.abs(dx) >= Math.abs(dy)) {
                        newH = 1;
                    } else {
                        newW = 1;
                    }
                } else if (this._resizeStartW > this._resizeStartH) {
                    newH = 1;
                } else {
                    newW = 1;
                }
            }

            if (this.props.onMapObjectResized) {
                this.props.onMapObjectResized(this._resizeMapObjId, newW, newH);
            }
            this._needsRedraw = true;
            return;
        }

        // Map Object drag
        if (this._isDraggingMapObj && this._dragMapObjId) {
            const layout = this.props.layoutData;
            const canvasW = layout.canvas_width || 40;
            const canvasH = layout.canvas_height || 30;
            const obj = this.props.mapObjects.find(o => o.id === this._dragMapObjId);
            const objW = obj ? (obj.size_x || 1) : 1;
            const objH = obj ? (obj.size_y || 1) : 1;
            const gx = Math.min(canvasW - objW, Math.max(0, Math.round((pos.x - this._dragOffsetX) / gridSize)));
            const gy = Math.min(canvasH - objH, Math.max(0, Math.round((pos.y - this._dragOffsetY) / gridSize)));
            if (this.props.onMapObjectMoved) {
                this.props.onMapObjectMoved(this._dragMapObjId, gx, gy);
            }
            this._needsRedraw = true;
            return;
        }

        // Parent drag
        if (this._isDragging && this._dragLocId) {
            const layout = this.props.layoutData;
            const canvasW = layout.canvas_width || 40;
            const canvasH = layout.canvas_height || 30;
            const loc = this.props.locations.find(l => l.id === this._dragLocId);
            const locW = loc ? (loc.size_x || 2) : 2;
            const locH = loc ? (loc.size_y || 1) : 1;
            const gx = Math.min(canvasW - locW, Math.max(0, Math.round((pos.x - this._dragOffsetX) / gridSize)));
            const gy = Math.min(canvasH - locH, Math.max(0, Math.round((pos.y - this._dragOffsetY) / gridSize)));
            this.props.onLocationMoved(this._dragLocId, gx, gy);
            this._needsRedraw = true;
            return;
        }

        // Cursor change — check child handles then parent handles then map objects
        if (this.props.isAdmin) {
            let onHandle = false;
            for (const loc of this.props.locations) {
                const px = loc.pos_x * gridSize;
                const py = loc.pos_y * gridSize;
                // Child handles
                for (const child of (loc.children || [])) {
                    const cx = px + child.pos_x * gridSize;
                    const cy = py + child.pos_y * gridSize;
                    const cw = (child.size_x || 1) * gridSize;
                    const ch_h = (child.size_y || 1) * gridSize;
                    const hSize = 8;
                    if (pos.x >= cx + cw - hSize && pos.x <= cx + cw &&
                        pos.y >= cy + ch_h - hSize && pos.y <= cy + ch_h) {
                        onHandle = true;
                        break;
                    }
                }
                if (onHandle) break;
                // Parent handles
                const lw = (loc.size_x || 2) * gridSize;
                const lh = (loc.size_y || 1) * gridSize;
                const hSize = 10;
                if (pos.x >= px + lw - hSize && pos.x <= px + lw &&
                    pos.y >= py + lh - hSize && pos.y <= py + lh) {
                    onHandle = true;
                    break;
                }
            }
            if (!onHandle) {
                for (const obj of this.props.mapObjects) {
                    if (obj.id !== this.props.selectedMapObjectId) continue;
                    const ox = obj.pos_x * gridSize;
                    const oy = obj.pos_y * gridSize;
                    const ow = (obj.size_x || 1) * gridSize;
                    const oh = (obj.size_y || 1) * gridSize;
                    const hSize = 10;
                    if (pos.x >= ox + ow - hSize && pos.x <= ox + ow &&
                        pos.y >= oy + oh - hSize && pos.y <= oy + oh) {
                        onHandle = true;
                        break;
                    }
                }
            }
            canvas.style.cursor = onHandle ? "nwse-resize" : "default";
        }
    }

    _onMouseUp() {
        if (this._isResizingChild) {
            this._isResizingChild = false;
            this._resizeChildId = null;
            this._resizeChildParentId = null;
        }
        if (this._isDraggingChild) {
            this._isDraggingChild = false;
            this._dragChildId = null;
            this._dragChildParentId = null;
        }
        if (this._isResizing) {
            this._isResizing = false;
            this._resizeLocId = null;
        }
        if (this._isDragging) {
            this._isDragging = false;
            this._dragLocId = null;
        }
        if (this._isResizingMapObj) {
            this._isResizingMapObj = false;
            this._resizeMapObjId = null;
        }
        if (this._isDraggingMapObj) {
            this._isDraggingMapObj = false;
            this._dragMapObjId = null;
        }
        this._isPanning = false;
    }

    _onMouseLeaveCanvas() {
        if (this._tooltipHideTimer) clearTimeout(this._tooltipHideTimer);
        this._tooltipHideTimer = setTimeout(() => this._hideProductTooltip(), 200);
        this._onMouseUp();
    }

    _onWheel(e) {
        e.preventDefault();
        if (e.ctrlKey) return; // zoom handled by toolbar
        this._panOffsetX -= e.deltaX;
        this._panOffsetY -= e.deltaY;
        // Bounds are enforced in _draw via _clampPan
        this._needsRedraw = true;
    }

    _onDragOver(e) {
        e.preventDefault();
    }

    _onDrop(e) {
        e.preventDefault();
        if (!this.props.isAdmin) return;

        const locIdStr = e.dataTransfer.getData("application/x-warehouse-location");
        const objType = e.dataTransfer.getData("application/x-warehouse-map-object");

        const pos = this._screenToCanvas(e);
        const layout = this.props.layoutData;
        const gridSize = layout.grid_size || 1;
        const canvasW = layout.canvas_width || 40;
        const canvasH = layout.canvas_height || 30;
        const gx = Math.min(canvasW - 1, Math.max(0, Math.round(pos.x / gridSize)));
        const gy = Math.min(canvasH - 1, Math.max(0, Math.round(pos.y / gridSize)));

        if (locIdStr) {
            const locId = parseInt(locIdStr, 10);
            if (locId) this.props.onLocationDropped(locId, gx, gy);
        } else if (objType) {
            if (this.props.onMapObjectDropped) {
                this.props.onMapObjectDropped(objType, gx, gy);
            }
        }

        // Force immediate redraw after props update
        this._needsRedraw = true;
        requestAnimationFrame(() => this._draw());
    }
}

// Static lookup — created once, shared across all instances
WarehouseCanvas.SHAPE_ICONS = Object.freeze({
    rack: '📦', shelf: '🗄️', bin: '📥', zone: '🔲',
    dock: '🚛', floor: '⬜', packing: '📋',
    refrigerator: '❄️', qc_area: '✅',
});
