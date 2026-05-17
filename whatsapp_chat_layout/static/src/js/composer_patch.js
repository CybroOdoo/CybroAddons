/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { Composer } from "@mail/core/common/composer";
import { markEventHandled } from "@web/core/utils/misc";
import { useRef } from "@odoo/owl";

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
        this._emojiButtonRef = useRef("emoji-button");
    },

    onClickAddEmoji(ev) {
        markEventHandled(ev, "Composer.onClickAddEmoji");
        const action = this.composerActions?.partition?.pickers?.find(
            (a) => a.id === "add-emoji"
        );
        if (!action) return;

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
            this._emojiButtonRef?.el ??
            ev?.target?.closest("button") ??
            ev?.currentTarget;
        action.picker.open({ el: anchorEl });
    },

    onClickAddAttachment(ev) {
        const action = this.composerActions?.partition?.other?.find(
            (a) => a.id === "upload-files"
        );
        if (action) {
            action.onSelected(ev);
        }
    },
});
