/** @odoo-module **/
import { Component } from "@odoo/owl";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { PaymentSummaryPopup } from "./PaymentPopup";

export class PaymentSummaryButton extends Component {
// Extending Component and Adding Class CategorySummaryButton
    static template = 'PaymentSummaryButton';
        setup() {
            super.setup();
            this.pos = usePos();
        }
        async onClick() {
            //Show payment summary popup
            const { confirmed } = await this.pos.popup.add(PaymentSummaryPopup,
                        { title: 'Payment Summary',}
                      );
        }
    }
ProductScreen.addControlButton({
component: PaymentSummaryButton,
condition: function () {
    return true;
},
});