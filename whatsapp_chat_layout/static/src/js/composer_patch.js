import { patch } from "@web/core/utils/patch";
import { Composer } from "@mail/core/common/composer";
import { markEventHandled } from "@web/core/utils/misc";
import { signal } from "@odoo/owl";

patch(Composer.prototype, {
    /**
     * Re-adding missing handlers used by whatsapp_chat_layout templates.
     * Opens emoji picker anchored directly to the clicked button element
     * to avoid reliance on missing refs (picker-target, quick-actions, etc.)
     * that are removed by the custom template replacement.
     */
    setup() {
        super.setup(...arguments);
        // Keep a ref to the emoji button for the custom layout
        this._emojiButtonRef = signal.ref();
    },

    onClickAddEmoji(ev) {
        markEventHandled(ev, "Composer.onClickAddEmoji");
        const action =
            this.composerActions?.actions?.find((a) => a.id === "add-emoji") ??
            this.composerActions?.partition?.quick?.find((a) => a.id === "add-emoji") ??
            this.composerActions?.partition?.pickers?.find((a) => a.id === "add-emoji");
        if (!action) return;

        // In Odoo 20, emoji picker is an actionPanel / popover
        if (action.popover) {
            if (action.isActive) {
                action.actionPanelClose?.();
            } else {
                const buttonEl =
                    (typeof this._emojiButtonRef === "function" ? this._emojiButtonRef() : this._emojiButtonRef?.el) ??
                    ev?.target?.closest("button") ??
                    ev?.currentTarget;
                action.popover.open(buttonEl, action.actionPanelComponentProps);
                action.isActive = true;
            }
            return;
        }

        const previousPicker = this.getActivePicker?.();
        previousPicker?.close?.();

        if (previousPicker === action.picker) {
            this.setActivePicker?.(null);
            return;
        }

        this.setActivePicker?.(action.picker);
        // Use the emoji button element directly as the anchor so the
        // popup has a valid DOM node to position itself against.
        const anchorEl =
            (typeof this._emojiButtonRef === "function" ? this._emojiButtonRef() : this._emojiButtonRef?.el) ??
            ev?.target?.closest("button") ??
            ev?.currentTarget;
        action.picker?.open?.({ el: anchorEl });
    },

    onClickAddAttachment(ev) {
        const action =
            this.composerActions?.actions?.find((a) => a.id === "upload-files") ??
            this.composerActions?.partition?.other?.find((a) => a.id === "upload-files");
        if (action) {
            action.onSelected(ev);
        } else if (typeof this.fileUploaderRef === "function" && this.fileUploaderRef()) {
            this.fileUploaderRef().click();
        }
    },
});
