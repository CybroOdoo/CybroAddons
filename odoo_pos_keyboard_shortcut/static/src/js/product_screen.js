/** @odoo-module */

import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { patch } from "@web/core/utils/patch";
import { useExternalListener } from "@odoo/owl";

patch(ProductScreen.prototype, {
    setup() {
        super.setup(...arguments);
        useExternalListener(document, "keydown", (ev) => {
            if (!document.querySelector('.modal') && !document.querySelector('.o_dialog') && !ev.target.closest('input, textarea')) {
                this._product_screen_shortcuts(ev);
            }
        });
    },
    _product_screen_shortcuts(event) {
        if (this.pos.config.is_enable_keyboard_shortcuts && this.pos.config.select_shortcut_id) {
            const shortcuts = this.pos.models['pos.keyboard.shortcut'].getAll()[0];
            if (!shortcuts) return;

            if (event.ctrlKey && event.key === shortcuts.customer_screen?.toLowerCase()) {
                event.preventDefault();
                this.pos.selectPartner();
            } else if (event.ctrlKey && event.key === shortcuts.select_price?.toLowerCase()) {
                event.preventDefault();
                this.onNumpadClick('price');
            } else if (event.ctrlKey && event.key === shortcuts.select_discount?.toLowerCase()) {
                event.preventDefault();
                this.onNumpadClick('discount');
            } else if (event.ctrlKey && event.key === shortcuts.select_qty?.toLowerCase()) {
                event.preventDefault();
                this.onNumpadClick('quantity');
            } else if (event.ctrlKey && event.key === shortcuts.select_user?.toLowerCase()) {
                event.preventDefault();
                this.pos.showLoginScreen();
            } else if (event.ctrlKey && event.key === shortcuts.close_pos?.toLowerCase()) {
                event.preventDefault();
                this.pos.closeSession();
            } else if (event.ctrlKey && event.key === shortcuts.resume_order?.toLowerCase()) {
                event.preventDefault();
                this.pos.showScreen('TicketScreen');
            } else if (event.ctrlKey && event.key === shortcuts.next_screen?.toLowerCase()) {
                event.preventDefault();
                // Instead of onClickPay which may not exist or has changed, we use pos.showScreen or switchPane
                // But ProductScreen still has a switchPane or we can just click the pay button:
                const PayButton = document.querySelector('.pay-order-button');
                if (PayButton) {
                    PayButton.click();
                } else if (this.onClickPay) {
                    this.onClickPay();
                }
            }
        }
    }
});
