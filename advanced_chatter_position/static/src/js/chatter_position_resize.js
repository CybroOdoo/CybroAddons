/** @odoo-module **/

/**
 * This module manages chatter position (default, bottom, right)
 * and provides resizable functionality for right-side chatter.
 */

import { FormController } from "@web/views/form/form_controller";
import { FormRenderer } from "@web/views/form/form_renderer";
import { FormCompiler } from "@web/views/form/form_compiler";
import { browser } from "@web/core/browser/browser";
import { user } from "@web/core/user";
import { patch } from "@web/core/utils/patch";
import { onMounted, onPatched, onWillUnmount } from "@odoo/owl";
import { session } from "@web/session";

const CHATTER_POSITION_STORAGE_KEY = "advanced_chatter_position.current";

function getCachedChatterPosition() {
    try {
        return browser.localStorage.getItem(CHATTER_POSITION_STORAGE_KEY);
    } catch {
        return null;
    }
}

function setCachedChatterPosition(position) {
    try {
        browser.localStorage.setItem(CHATTER_POSITION_STORAGE_KEY, position);
    } catch {
        // Ignore storage failures and keep working with in-memory state.
    }
}

// 1. Patch FormRenderer to influence the mailLayout
patch(FormRenderer.prototype, {
    mailLayout() {
        const pos = getCachedChatterPosition() || session.chatter_position || "default";
        if (pos === "bottom") {
            return "BOTTOM_CHATTER";
        } else if (pos === "right") {
            return "SIDE_CHATTER";
        }
        return super.mailLayout(...arguments);
    },
});

// 2. Patch FormCompiler to handle the renderer layout classes
patch(FormCompiler.prototype, {
    compile(node, params) {
        const res = super.compile(node, params);
        // Find the form renderer div
        const renderer = res.classList?.contains("o_form_renderer") ? res : res.querySelector(".o_form_renderer");
        if (renderer) {
            const pos = getCachedChatterPosition() || session.chatter_position || "default";
            const classes = renderer.getAttribute("t-attf-class") || "";

            // Search for Odoo's native layout ternary in the class attribute
            // This ternary forces flex-column on small screens and flex-nowrap on large screens.
            // We replace it with our own forced class if a preference is set.
            const ternaryRegex = /\{\{\s*__comp__\.uiService\.size\s*<\s*[^?]+\?\s*['"]flex-column['"]\s*:\s*['"]flex-nowrap h-100['"]\s*\}\}/;

            if (pos === "right") {
                const newClasses = classes.replace(ternaryRegex, "flex-nowrap h-100");
                renderer.setAttribute("t-attf-class", newClasses);
            } else if (pos === "bottom") {
                const newClasses = classes.replace(ternaryRegex, "flex-column");
                renderer.setAttribute("t-attf-class", newClasses);
            }
        }
        return res;
    },
});

// 3. Patch FormController to handle the resizer
patch(FormController.prototype, {
    setup() {
        super.setup();
        this._resizerCleanup = null;
        this._resizerRafId = null;
        this._chatterPosition = getCachedChatterPosition() || session.chatter_position || "default";
        this._chatterPositionPromise = null;

        onMounted(() => {
            this._syncChatterPositionFromUserForm();
            this._setChatter();
            this._refreshChatterPosition();
        });
        onPatched(() => {
            this._syncChatterPositionFromUserForm();
            this._setChatter();
        });
        onWillUnmount(() => {
            if (this._resizerRafId) {
                cancelAnimationFrame(this._resizerRafId);
                this._resizerRafId = null;
            }
            this._removeResizer();
        });
    },

    _isChatterOnRight() {
        const root = this.rootRef.el;
        if (!root) return false;

        const chatter = root.querySelector(".o-mail-Form-chatter");
        const sheet = root.querySelector(".o_form_sheet_bg");

        if (!chatter || !sheet) return false;

        // Check if aside class is present (added by native mail compiler if mailLayout is SIDE_CHATTER)
        if (chatter.classList.contains("o-aside")) return true;

        const sheetRect = sheet.getBoundingClientRect();
        const chatterRect = chatter.getBoundingClientRect();

        return chatterRect.left >= sheetRect.right - 10;
    },

    _setChatter() {
        const root = this.rootRef.el;
        if (!root) return;

        const pos = this._getSelectedChatterPosition();
        const sheet = root.querySelector(".o_form_sheet_bg");
        const chatter = root.querySelector(".o-mail-Form-chatter");

        if (!sheet || !chatter) return;

        root.classList.remove("chatter-bottom", "chatter-right");
        this._resetChatterStyles(sheet, chatter);

        if (pos === "bottom") {
            this._removeResizer(root);
            root.classList.add("chatter-bottom");
        } else if (pos === "right") {
            root.classList.add("chatter-right");
            chatter.classList.add("o-full-width");
            this._ensureResizer(root, sheet, chatter);
        } else {
            this._removeResizer(root);
            if (this._resizerRafId) {
                cancelAnimationFrame(this._resizerRafId);
                this._resizerRafId = null;
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

    _syncChatterPositionFromUserForm() {
        const record = this.model?.root;
        if (record?.resModel !== "res.users" || record.resId !== user.userId) {
            return;
        }
        const recordPosition = record.data?.chatter_position;
        if (!recordPosition) {
            return;
        }
        this._chatterPosition = recordPosition;
        setCachedChatterPosition(recordPosition);
        session.chatter_position = recordPosition;
    },

    _resetChatterStyles(sheet, chatter) {
        chatter.classList.remove("o-full-width");
        sheet.style.flex = "";
        sheet.style.maxWidth = "";
        sheet.style.width = "";
        chatter.style.flex = "";
        chatter.style.maxWidth = "";
        chatter.style.width = "";
    },

    _getSelectedChatterPosition() {
        this._syncChatterPositionFromUserForm();
        return this._chatterPosition || session.chatter_position || "default";
    },

    async _refreshChatterPosition() {
        if (this._chatterPositionPromise) {
            return this._chatterPositionPromise;
        }
        this._chatterPositionPromise = this.orm.silent
            .read("res.users", [user.userId], ["chatter_position"], {
                context: { active_test: false },
            })
            .then((records) => {
                const position = records?.[0]?.chatter_position || "default";
                this._chatterPosition = position;
                setCachedChatterPosition(position);
                session.chatter_position = position;
                if (this.rootRef?.el?.isConnected) {
                    this._setChatter();
                }
                return position;
            })
            .catch(() => this._chatterPosition)
            .finally(() => {
                this._chatterPositionPromise = null;
            });
        return this._chatterPositionPromise;
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
        // Overrides necessary because of Odoo internal o-aside widths
        sheet.style.width = 'auto';
        chatter.style.width = 'auto';
    },

    _addResizer(root, sheet, chatter) {
        if (root.querySelector(".chatter-resizer")) return;

        const resizer = document.createElement("div");
        resizer.className = "chatter-resizer";
        chatter.before(resizer);

        const pos = this._getSelectedChatterPosition();

        // Restore saved width
        if (this._resizerRafId) {
            cancelAnimationFrame(this._resizerRafId);
        }
        this._resizerRafId = requestAnimationFrame(() => {
            this._resizerRafId = null;
            if (!root.isConnected) return;

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

        let isDragging = false;

        const onMouseDown = (e) => {
            e.preventDefault();
            isDragging = true;
            resizer.classList.add("dragging");
            document.body.style.cursor = "col-resize";
            document.body.style.userSelect = "none";
        };

        const onMouseMove = (e) => {
            if (!isDragging) return;

            const rect = root.getBoundingClientRect();
            const totalWidth = rect.width;
            if (!totalWidth) return;

            const chatterWidth = rect.right - e.clientX;
            const MIN = 250;
            const MAX = totalWidth * 0.7;

            if (chatterWidth < MIN || chatterWidth > MAX) return;

            const percent = chatterWidth / totalWidth;

            if (pos === "right" || this._isChatterOnRight()) {
                this._applyWidthPercent(sheet, chatter, percent);
            }

            localStorage.setItem("chatterWidthPercent", percent);
        };

        const onMouseUp = () => {
            if (!isDragging) return;
            isDragging = false;
            resizer.classList.remove("dragging");
            document.body.style.cursor = "";
            document.body.style.userSelect = "";
        };

        resizer.addEventListener("mousedown", onMouseDown);
        window.addEventListener("mousemove", onMouseMove);
        window.addEventListener("mouseup", onMouseUp);

        this._resizerCleanup = () => {
            resizer.removeEventListener("mousedown", onMouseDown);
            window.removeEventListener("mousemove", onMouseMove);
            window.removeEventListener("mouseup", onMouseUp);
            document.body.style.cursor = "";
            document.body.style.userSelect = "";
        };
    },
});
