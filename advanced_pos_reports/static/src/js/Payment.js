/** @odoo-module **/
import { Component } from "@odoo/owl";
import { ControlButtons } from "@point_of_sale/app/screens/product_screen/control_buttons/control_buttons";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { usePos } from "@point_of_sale/app/hooks/pos_hook";
import { PaymentSummaryPopup } from "./PaymentPopup";

patch(ControlButtons.prototype, {
// Extending Component and Adding Class CategorySummaryButton
        setup() {
            super.setup();
            this.pos = usePos();
            this.dialog = useService("dialog");

        },
        async onClickPaymentSummary() {
            //Show payment summary popup
            const { confirmed } = await this.dialog.add(PaymentSummaryPopup,
                        { title: 'Payment Summary',}
                      );
        },
});
