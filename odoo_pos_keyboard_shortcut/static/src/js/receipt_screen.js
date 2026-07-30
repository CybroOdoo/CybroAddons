/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { ReceiptScreen } from "@point_of_sale/app/screens/receipt_screen/receipt_screen";
import { useExternalListener } from "@odoo/owl";

patch(ReceiptScreen.prototype, {
    setup() {
        super.setup(...arguments);
        useExternalListener(document, "keydown", (ev) => {
            if (!document.querySelector('.modal') && !document.querySelector('.o_dialog') && !ev.target.closest('input, textarea')) {
                this._receipt_screen_shortcuts(ev);
            }
        });
    },
    _receipt_screen_shortcuts(event) {
        if (this.pos.config.is_enable_keyboard_shortcuts && this.pos.config.select_shortcut_id) {
            const shortcuts = this.pos.models['pos.keyboard.shortcut'].getAll()[0];
            if (!shortcuts) return;

            if (event.ctrlKey && event.key === shortcuts.print_receipt?.toLowerCase()) {
                event.preventDefault();
                this.doFullPrint.call();
            } else if (event.ctrlKey && event.key === shortcuts.new_order?.toLowerCase()) {
                event.preventDefault();
                this.orderDone();
            } else if (event.ctrlKey && event.key === shortcuts.sent_email?.toLowerCase()) {
                event.preventDefault();
                this.actionSendReceiptOnEmail();
            } else if (event.ctrlKey && event.key === shortcuts.resume_order?.toLowerCase()) {
                event.preventDefault();
                this.pos.showScreen('TicketScreen');
            } else if (event.ctrlKey && event.key === shortcuts.select_user?.toLowerCase()) {
                event.preventDefault();
                this.pos.showLoginScreen();
            } else if (event.ctrlKey && event.key === shortcuts.close_pos?.toLowerCase()) {
                event.preventDefault();
                this.pos.closeSession();
            } else if (event.key === "Enter" && shortcuts.next_screen_show === "Enter") {
                event.preventDefault();
                this.orderDone();
            }
        }
    }
});
