/** @odoo-module **/
import { Component } from "@odoo/owl";
import { ControlButtons } from "@point_of_sale/app/screens/product_screen/control_buttons/control_buttons";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { usePos } from "@point_of_sale/app/hooks/pos_hook";
import { OrderSummaryPopup } from "./OrderPopup";

patch(ControlButtons.prototype, {
// Extending Component and Adding Class OrderSummaryButton
    setup() {
        super.setup();
        this.pos = usePos();
        this.dialog = useService("dialog");

    },
    async onClickOrderSummary() {
            //Show order summary popup
            const { confirmed } =  await this.dialog.add(OrderSummaryPopup,
                        { title: 'Order Summary',}
                      );
    },
});
