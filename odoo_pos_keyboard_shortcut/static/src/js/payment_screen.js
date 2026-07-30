/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { useExternalListener } from "@odoo/owl";

patch(PaymentScreen.prototype, {
    setup() {
        super.setup(...arguments);
        useExternalListener(document, "keydown", (ev) => {
            if (!document.querySelector('.modal') && !document.querySelector('.o_dialog') && !ev.target.closest('input, textarea')) {
                this._payment_screen_shortcuts(ev);
            }
        });
    },
    _payment_screen_shortcuts(event) {
        if (this.pos.config.is_enable_keyboard_shortcuts && this.pos.config.select_shortcut_id) {
            const shortcuts = this.pos.models['pos.keyboard.shortcut'].getAll()[0];
            if (!shortcuts) return;

            if (event.ctrlKey && event.key === shortcuts.select_invoice?.toLowerCase()) {
                event.preventDefault();
                this.toggleIsToInvoice();
            } else if (event.ctrlKey && event.key === shortcuts.back_screen?.toLowerCase()) {
                event.preventDefault();
                const BackButton = document.querySelector('.back');
                if (BackButton) {
                    BackButton.click();
                } else if (this.showScreen) {
                    this.pos.showScreen('ProductScreen');
                }
            } else if (event.ctrlKey && event.key === shortcuts.validate_order?.toLowerCase()) {
                event.preventDefault();
                this.validateOrder();
            } else if (event.ctrlKey && event.key === shortcuts.select_user?.toLowerCase()) {
                event.preventDefault();
                this.pos.showLoginScreen();
            } else if (event.ctrlKey && event.key === shortcuts.close_pos?.toLowerCase()) {
                event.preventDefault();
                this.pos.closeSession();
            } else if (event.ctrlKey && event.key === shortcuts.resume_order?.toLowerCase()) {
                event.preventDefault();
                this.pos.showScreen('TicketScreen');
            }

            const paymentShortcuts = this.pos.models['pos.payment.method.key'].getAll();
            for (const paymentShortcut of paymentShortcuts) {
                if (paymentShortcut && event.ctrlKey && event.key === paymentShortcut.key_code?.toLowerCase()) {
                    event.preventDefault();
                    const pmId = paymentShortcut.payment_method_id?.id || (Array.isArray(paymentShortcut.payment_method_id) ? paymentShortcut.payment_method_id[0] : paymentShortcut.payment_method_id);
                    const paymentMethod = this.pos.models['pos.payment.method'].get(pmId);
                    if (paymentMethod) {
                        this.addNewPaymentLine(paymentMethod);
                    }
                    break;
                }
            }
        }
    }
});
