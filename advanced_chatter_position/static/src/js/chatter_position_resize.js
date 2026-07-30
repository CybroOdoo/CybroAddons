/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { browser } from "@web/core/browser/browser";
import { SIZES } from "@web/core/ui/ui_service";
import { session } from "@web/session";
import { onMounted, onPatched, onWillUnmount } from "@odoo/owl";
import { FormController } from "@web/views/form/form_controller";

const CHATTER_POSITION_STORAGE_KEY = "advanced_chatter_position.current";
const CHATTER_WIDTH_STORAGE_KEY = "advanced_chatter_position.width";

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
        // Ignore storage failures.
    }
}

function getPreferredChatterPosition() {
    return getCachedChatterPosition() || session.chatter_position || "default";
}

function getPrimaryChatterElements(root) {
    const renderer = root?.querySelector(".o_form_renderer");
    if (!renderer) {
        return {};
    }
    const sheet = renderer.querySelector(":scope > .o_form_sheet_bg");
    const chatter = renderer.querySelector(":scope > .o-mail-Form-chatter");
    return { renderer, sheet, chatter };
}

patch(FormController.prototype, {
    setup() {
        super.setup();
        this._resizerCleanup = null;
        this._resizerRafId = null;
        this._chatterPosition = getPreferredChatterPosition();
        this._chatterPositionPromise = null;

        onMounted(() => {
            this._syncChatterPositionFromUserForm();
            this._setChatterLayout();
            this._refreshChatterPosition();
        });
        onPatched(() => {
            this._syncChatterPositionFromUserForm();
            this._setChatterLayout();
        });
        onWillUnmount(() => {
            if (this._resizerRafId) {
                browser.cancelAnimationFrame(this._resizerRafId);
                this._resizerRafId = null;
            }
            this._removeResizer();
        });
    },

    _syncChatterPositionFromUserForm() {
        const record = this.model?.root;
        if (record?.resModel !== "res.users" || record.resId !== this.user.userId) {
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

    _getSelectedChatterPosition() {
        this._syncChatterPositionFromUserForm();
        return this._chatterPosition || session.chatter_position || "default";
    },

    _getEffectiveLayout() {
        const position = this._getSelectedChatterPosition();
        if (position === "default") {
            return this.ui.size >= SIZES.XXL ? "right" : "bottom";
        }
        return position;
    },

    _setChatterLayout() {
        const root = this.rootRef.el;
        if (!root) {
            return;
        }

        const { sheet, chatter } = getPrimaryChatterElements(root);
        if (!sheet || !chatter) {
            this._removeResizer();
            root.classList.remove("chatter-bottom", "chatter-right");
            return;
        }

        const position = this._getEffectiveLayout();
        root.classList.remove("chatter-bottom", "chatter-right");
        this._resetChatterStyles(sheet, chatter);

        if (position === "bottom") {
            this._removeResizer();
            chatter.classList.remove("o-aside", "o-full-width");
            chatter.classList.add("mt-4", "mt-md-0");
            root.classList.add("chatter-bottom");
            return;
        }

        if (position === "right") {
            root.classList.add("chatter-right");
            chatter.classList.remove("mt-4", "mt-md-0");
            chatter.classList.add("o-aside", "o-full-width");
            this._ensureResizer(root, sheet, chatter);
            return;
        }

        this._removeResizer();
        if (this._resizerRafId) {
            browser.cancelAnimationFrame(this._resizerRafId);
        }
        this._resizerRafId = browser.requestAnimationFrame(() => {
            this._resizerRafId = null;
            if (!this.rootRef.el?.isConnected) {
                return;
            }
            const activeElements = getPrimaryChatterElements(this.rootRef.el);
            if (!activeElements.chatter || !activeElements.sheet) {
                return;
            }
            if (activeElements.chatter.classList.contains("o-aside")) {
                this._addResizer(this.rootRef.el, activeElements.sheet, activeElements.chatter);
            }
        });
    },

    _resetChatterStyles(sheet, chatter) {
        chatter.classList.remove("o-full-width", "o-aside", "mt-4", "mt-md-0");
        sheet.style.flex = "";
        sheet.style.maxWidth = "";
        sheet.style.width = "";
        chatter.style.flex = "";
        chatter.style.maxWidth = "";
        chatter.style.width = "";
    },

    async _refreshChatterPosition() {
        if (this._chatterPositionPromise) {
            return this._chatterPositionPromise;
        }
        this._chatterPositionPromise = this.orm
            .read("res.users", [this.user.userId], ["chatter_position"], {
                context: { active_test: false },
            })
            .then((records) => {
                const position = records?.[0]?.chatter_position || "default";
                this._chatterPosition = position;
                setCachedChatterPosition(position);
                session.chatter_position = position;
                if (this.rootRef?.el?.isConnected) {
                    this._setChatterLayout();
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
        if (root.querySelector(".chatter-resizer")) {
            return;
        }
        this._addResizer(root, sheet, chatter);
    },

    _removeResizer(root) {
        if (this._resizerCleanup) {
            this._resizerCleanup();
            this._resizerCleanup = null;
        }
        const resizer = (root || this.rootRef?.el)?.querySelector(".chatter-resizer");
        if (resizer) {
            resizer.remove();
        }
    },

    _applyWidthPercent(sheet, chatter, percent) {
        const chatterPercent = Math.min(Math.max(percent, 0.2), 0.7);
        const sheetPercent = 1 - chatterPercent;
        sheet.style.flex = `${sheetPercent.toFixed(6)} 1 0%`;
        chatter.style.flex = `${chatterPercent.toFixed(6)} 1 0%`;
        sheet.style.maxWidth = "none";
        chatter.style.maxWidth = "none";
        sheet.style.width = "auto";
        chatter.style.width = "auto";
    },

    _addResizer(root, sheet, chatter) {
        if (root.querySelector(".chatter-resizer")) {
            return;
        }

        const resizer = document.createElement("div");
        resizer.className = "chatter-resizer";
        chatter.before(resizer);

        if (this._resizerRafId) {
            browser.cancelAnimationFrame(this._resizerRafId);
        }
        this._resizerRafId = browser.requestAnimationFrame(() => {
            this._resizerRafId = null;
            if (!root.isConnected) {
                return;
            }
            let savedPercent;
            try {
                savedPercent = browser.localStorage.getItem(CHATTER_WIDTH_STORAGE_KEY);
            } catch {
                savedPercent = null;
            }
            if (!savedPercent) {
                return;
            }
            const percent = parseFloat(savedPercent);
            if (!Number.isNaN(percent)) {
                this._applyWidthPercent(sheet, chatter, percent);
            }
        });

        let isDragging = false;

        const onMouseDown = (ev) => {
            ev.preventDefault();
            isDragging = true;
            resizer.classList.add("dragging");
            document.body.style.cursor = "col-resize";
            document.body.style.userSelect = "none";
        };

        const onMouseMove = (ev) => {
            if (!isDragging) {
                return;
            }

            const rect = root.getBoundingClientRect();
            const totalWidth = rect.width;
            if (!totalWidth) {
                return;
            }

            const chatterWidth = rect.right - ev.clientX;
            const minWidth = 250;
            const maxWidth = totalWidth * 0.7;
            if (chatterWidth < minWidth || chatterWidth > maxWidth) {
                return;
            }

            const percent = chatterWidth / totalWidth;
            this._applyWidthPercent(sheet, chatter, percent);

            try {
                browser.localStorage.setItem(CHATTER_WIDTH_STORAGE_KEY, String(percent));
            } catch {
                // Ignore storage failures.
            }
        };

        const onMouseUp = () => {
            if (!isDragging) {
                return;
            }
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
