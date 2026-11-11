import { onWillDestroy, proxy, useListener } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
import { clamp } from "@web/core/utils/numbers";
import { patch } from "@web/core/utils/patch";

/** Smallest size a dialog can be resized to, in pixels. */
export const MIN_DIALOG_WIDTH = 300;
export const MIN_DIALOG_HEIGHT = 150;

/**
 * Make backend dialogs resizable from a handle in their bottom-right corner.
 *
 * Odoo already lets the user move a dialog by its header. The size is kept in
 * the component state and rendered through ``contentStyle``, so moving the
 * dialog (which re-renders that style) keeps the chosen size.
 */
patch(Dialog.prototype, {
    setup() {
        super.setup();
        this.contentSize = proxy({ width: 0, height: 0 });
        this.stopResize = null;
        if (this.isMovable) {
            // The window size changed: go back to the default size, as Odoo
            // does for the position.
            useListener(window, "resize", () => this.resetContentSize());
        }
        onWillDestroy(() => this.stopResize?.());
    },

    get isResizable() {
        return this.isMovable && !this.isFullscreen;
    },

    get contentStyle() {
        let style = super.contentStyle;
        if (this.isResizable && this.contentSize.width) {
            style += ` width: ${this.contentSize.width}px; height: ${this.contentSize.height}px; max-width: none;`;
        }
        return style;
    },

    resetContentSize() {
        this.contentSize.width = 0;
        this.contentSize.height = 0;
    },

    onResizeStart(ev) {
        if (ev.button !== 0 || !this.isResizable) {
            return;
        }
        ev.preventDefault();
        ev.stopPropagation();
        const rect = ev.currentTarget.closest(".modal-content").getBoundingClientRect();
        const start = { x: ev.clientX, y: ev.clientY, width: rect.width, height: rect.height };
        const onMove = (moveEv) => {
            this.contentSize.width = clamp(
                start.width + moveEv.clientX - start.x,
                MIN_DIALOG_WIDTH,
                Math.max(MIN_DIALOG_WIDTH, window.innerWidth)
            );
            this.contentSize.height = clamp(
                start.height + moveEv.clientY - start.y,
                MIN_DIALOG_HEIGHT,
                Math.max(MIN_DIALOG_HEIGHT, window.innerHeight)
            );
        };
        const stop = () => {
            window.removeEventListener("pointermove", onMove);
            window.removeEventListener("pointerup", stop);
            this.stopResize = null;
        };
        window.addEventListener("pointermove", onMove);
        window.addEventListener("pointerup", stop);
        this.stopResize = stop;
    },
});
