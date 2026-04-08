/** @odoo-module */
/**
 * Extends the Message model with pin/unpin behavior.
 * Adds two methods that toggle the pinned state of a message by calling
 * the backend `toggle_pin` method. When successful, the local state updates
 * instantly for UI reactivity.
 */
import { Message } from "@mail/core/common/message_model";
import { patch } from "@web/core/utils/patch";

patch(Message.prototype, {
    async onClickPin() {
        try {
            await this.Model.store.env.services.orm.call("mail.message", "toggle_pin", [[this.id]]);
            this.is_pinned = !this.is_pinned;
        } catch (error) {
            console.error("Error toggling pin status:", error);
        }
    },
    async onMessagePin(){
        await this.Model.store.env.services.orm.call("mail.message", "toggle_pin", [[this.id]]);
        this.is_pinned = !this.is_pinned;
    }
});
