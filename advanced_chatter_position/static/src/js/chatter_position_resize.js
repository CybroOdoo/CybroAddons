/** @odoo-module **/

/**
 * This module manages chatter position (default, bottom, right)
 * and provides resizable functionality for right-side chatter.
 *
 * Resize-on-screen-change is handled via:
 *  1. ResizeObserver  – watches the form root for width changes and re-evaluates layout.
 *  2. MutationObserver – watches Odoo's dynamic class injection and prevents flex-column.
 */

import { FormController } from "@web/views/form/form_controller";
import { FormCompiler } from "@web/views/form/form_compiler";
import { patch } from "@web/core/utils/patch";
import { onMounted, onPatched, onWillUnmount } from "@odoo/owl";
import { session } from "@web/session";
import { user } from "@web/core/user";

patch(FormController.prototype, {
    setup() {
        super.setup();
        this._resizerCleanup = null;
        this._resizerRafId = null;
        this._resizeObserver = null;
        this._mutationObserver = null;
        this._observerAttached = false;
        
        this.user = user;
        this._chatterPosition = session.chatter_position || "default";

        onMounted(() => {
            this._syncChatterFromForm();
            this._setChatter();
            this._attachObservers();
        });
        
        onPatched(() => {
            this._syncChatterFromForm();
            this._setChatter();
        });
        
        onWillUnmount(() => {
            if (this._resizerRafId) {
                cancelAnimationFrame(this._resizerRafId);
                this._resizerRafId = null;
            }
            this._removeResizer();
            this._detachObservers();
        });
    },

    _attachObservers() {
        if (this._observerAttached) return;
        const root = this.rootRef.el;
        if (!root) return;

        // ResizeObserver: re-evaluates chatter layout if container size changes
        this._resizeObserver = new ResizeObserver(() => {
            if (this.rootRef.el) {
                this._onContainerResized();
            }
        });
        this._resizeObserver.observe(root);

        // MutationObserver: stops Odoo from reactively re-injecting 'flex-column' in right mode
        this._mutationObserver = new MutationObserver((mutations) => {
            if (this._chatterPosition !== "right") return;
            
            mutations.forEach((mutation) => {
                if (mutation.attributeName === "class") {
                    const target = mutation.target;
                    if (target.classList.contains("flex-column")) {
                        target.classList.remove("flex-column");
                        target.classList.add("flex-nowrap", "h-100");
                    }
                }
            });
        });

        // The target for mutation is the .o_form_renderer which is inside the root, or sometimes the root itself
        const renderer = root.querySelector(".o_form_renderer") || root;
        this._mutationObserver.observe(renderer, { attributes: true, attributeFilter: ["class"] });
        
        this._observerAttached = true;
    },

    _detachObservers() {
        if (this._resizeObserver) {
            this._resizeObserver.disconnect();
            this._resizeObserver = null;
        }
        if (this._mutationObserver) {
            this._mutationObserver.disconnect();
            this._mutationObserver = null;
        }
        this._observerAttached = false;
    },

    _onContainerResized() {
        if (this._chatterPosition === "right") {
            const root = this.rootRef.el;
            if (!root) return;
            
            const sheet = root.querySelector(".o_form_sheet_bg");
            const chatter = root.querySelector(".o-mail-Form-chatter");
            
            if (sheet && chatter) {
                this._ensureResizer(root, sheet, chatter);
                this._restoreSavedWidth(root, sheet, chatter);
            }
        }
    },

    _syncChatterFromForm() {
        const record = this.model?.root;

        if (!record || record.resModel !== "res.users" || record.resId !== this.user.userId) {
            return;
        }

        const newPos = record.data?.chatter_position;
        if (!newPos) return;

        if (this._chatterPosition !== newPos) {
            this._chatterPosition = newPos;
            session.chatter_position = newPos;
            this._setChatter();
        }
    },

    _isChatterOnRight() {
        const root = this.rootRef.el;
        if (!root) return false;

        const chatter = root.querySelector(".o-mail-Form-chatter");
        const sheet = root.querySelector(".o_form_sheet_bg");

        if (!chatter || !sheet) return false;

        const sheetRect = sheet.getBoundingClientRect();
        const chatterRect = chatter.getBoundingClientRect();

        return chatterRect.left >= sheetRect.right - 10;
    },

    _setChatter() {
        const root = this.rootRef.el;
        if (!root) return;

        const pos = this._chatterPosition || "default";
        const sheet = root.querySelector(".o_form_sheet_bg");
        const chatter = root.querySelector(".o-mail-Form-chatter");

        if (!sheet || !chatter) return;

        root.classList.remove("chatter-bottom", "chatter-right");

        // BOTTOM MODE
        if (pos === "bottom") {
            this._removeResizer(root);

            sheet.style.maxWidth = "100%";
            sheet.style.width = "100%";
            sheet.style.flex = "1 1 100%";

            chatter.style.width = "100%";
            chatter.style.flex = "1 1 100%";

            if (!sheet.contains(chatter)) {
                sheet.append(chatter);
            }

            root.classList.add("chatter-bottom");
        }

        // RIGHT MODE
        else if (pos === "right") {
            root.classList.add("chatter-right");
            chatter.classList.add("o-full-width");

            // Force renderer to be flex-nowrap to override Odoo's default breakpoint
            const renderer = root.querySelector(".o_form_renderer");
            if (renderer) {
                renderer.classList.remove("flex-column");
                renderer.classList.add("flex-nowrap", "h-100");
            }

            if (sheet.contains(chatter)) {
                sheet.after(chatter);
            }

            this._ensureResizer(root, sheet, chatter);
            this._restoreSavedWidth(root, sheet, chatter);
        }

        // DEFAULT MODE
        else {
            this._removeResizer(root);

            sheet.style.flex = "";
            chatter.style.flex = "";
            sheet.style.width = "";
            chatter.style.width = "";
            chatter.classList.remove("o-full-width");

            if (this._resizerRafId) {
                cancelAnimationFrame(this._resizerRafId);
            }
            this._resizerRafId = requestAnimationFrame(() => {
                this._resizerRafId = null;
                if (!this.rootRef.el) return;
                if (this._isChatterOnRight()) {
                    this._addResizer(root, sheet, chatter);
                }
            });
        }
    },

    _ensureResizer(root, sheet, chatter) {
        if (root.querySelector(".chatter-resizer")) return;
        this._addResizer(root, sheet, chatter);
    },

    _removeResizer(root) {
        if (this._resizerCleanup) {
            this._resizerCleanup();
            this._resizerCleanup = null;
        }
        const el = (root || this.rootRef?.el)?.querySelector(".chatter-resizer");
        if (el) el.remove();
    },

    _applyWidthPercent(sheet, chatter, percent) {
        const chatterPercent = Math.min(Math.max(percent, 0.2), 0.7);
        const sheetPercent = 1 - chatterPercent;
        sheet.style.flex = `${sheetPercent.toFixed(6)} 1 0%`;
        chatter.style.flex = `${chatterPercent.toFixed(6)} 1 0%`;
        sheet.style.maxWidth = 'none';
        chatter.style.maxWidth = 'none';
        chatter.style.width = 'auto';
    },

    _restoreSavedWidth(root, sheet, chatter) {
        if (this._resizerRafId) {
            cancelAnimationFrame(this._resizerRafId);
        }
        this._resizerRafId = requestAnimationFrame(() => {
            this._resizerRafId = null;
            if (!root || !root.isConnected) return;

            let savedPercent;
            try {
                savedPercent = localStorage.getItem("chatterWidthPercent");
            } catch (e) {
                savedPercent = null;
            }
            if (!savedPercent) return;

            const percent = parseFloat(savedPercent);
            if (isNaN(percent)) return;

            this._applyWidthPercent(sheet, chatter, percent);
        });
    },

    _addResizer(root, sheet, chatter) {
        if (root.querySelector(".chatter-resizer")) return;

        const resizer = document.createElement("div");
        resizer.className = "chatter-resizer";
        chatter.before(resizer);

        const pos = session.chatter_position || "default";

        let isDragging = false;

        // ── Shared drag logic ──────────────────────────────────────────────
        const startDrag = () => {
            isDragging = true;
            resizer.classList.add("dragging");
            if (this.rootRef.el) {
                this.rootRef.el.style.cursor = "col-resize";
                this.rootRef.el.style.userSelect = "none";
            }
        };

        const doDrag = (clientX) => {
            if (!isDragging) return;

            const rect = root.getBoundingClientRect();
            const totalWidth = rect.width;
            if (!totalWidth) return;

            const chatterWidth = rect.right - clientX;
            // On narrow screens (tablets ~768-1024px) use a smaller minimum so
            // dragging is actually possible; on desktop keep 250px.
            const MIN = totalWidth < 900 ? Math.min(150, totalWidth * 0.25) : 250;
            const MAX = totalWidth * 0.75;

            // Clamp instead of hard-rejecting so the handle always moves
            const clampedChatterWidth = Math.min(Math.max(chatterWidth, MIN), MAX);
            const percent = clampedChatterWidth / totalWidth;

            if (pos === "right" || this._isChatterOnRight()) {
                this._applyWidthPercent(sheet, chatter, percent);
            }

            localStorage.setItem("chatterWidthPercent", percent);
        };

        const endDrag = () => {
            if (!isDragging) return;
            isDragging = false;
            resizer.classList.remove("dragging");
            if (this.rootRef.el) {
                this.rootRef.el.style.cursor = "";
                this.rootRef.el.style.userSelect = "";
            }
        };

        // ── Mouse events (desktop) ─────────────────────────────────────────
        const onMouseDown = () => startDrag();
        const onMouseMove = (e) => doDrag(e.clientX);
        const onMouseUp = () => endDrag();

        // ── Touch events (mobile / tablet) ────────────────────────────────
        const onTouchStart = (e) => {
            e.preventDefault();          // prevent scroll while dragging
            startDrag();
        };
        const onTouchMove = (e) => {
            e.preventDefault();          // prevent scroll while dragging
            if (e.touches.length > 0) {
                doDrag(e.touches[0].clientX);
            }
        };
        const onTouchEnd = () => endDrag();

        resizer.addEventListener("mousedown", onMouseDown);
        window.addEventListener("mousemove", onMouseMove);
        window.addEventListener("mouseup", onMouseUp);

        // passive:false is required so e.preventDefault() is allowed inside touch handlers
        resizer.addEventListener("touchstart", onTouchStart, { passive: false });
        window.addEventListener("touchmove", onTouchMove, { passive: false });
        window.addEventListener("touchend", onTouchEnd);

        this._resizerCleanup = () => {
            resizer.removeEventListener("mousedown", onMouseDown);
            window.removeEventListener("mousemove", onMouseMove);
            window.removeEventListener("mouseup", onMouseUp);

            resizer.removeEventListener("touchstart", onTouchStart);
            window.removeEventListener("touchmove", onTouchMove);
            window.removeEventListener("touchend", onTouchEnd);
        };
    },
});

patch(FormCompiler.prototype, {
    compile(node, params) {
        const res = super.compile(node, params);

        if (session.chatter_position === "right") {
            const renderer = res.querySelector(".o_form_renderer");
            if (renderer) {
                const classes = renderer.getAttribute("t-attf-class") || "";
                const newClasses = classes.replace(
                    /\{\{\s*__comp__\.uiService\.size\s*<\s*\d+\s*\?\s*"flex-column"\s*:\s*"flex-nowrap h-100"\s*\}\}/,
                    "flex-nowrap h-100"
                );
                renderer.setAttribute("t-attf-class", newClasses);
            }
        }
        return res;
    },
});