/** @odoo-module **/
import { Component } from "@odoo/owl";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { OrderSummaryPopup } from "./OrderPopup";

export class OrderSummaryButton extends Component {
// Extending Component and Adding Class OrderSummaryButton
    static template = 'OrderSummaryButton';
    setup() {
        super.setup();
        this.pos = usePos();
    }
    async onClick() {
            //Show order summary popup
            const { confirmed } = await this.pos.popup.add(OrderSummaryPopup,
                        { title: 'Order Summary',}
                      );
        }
    }
ProductScreen.addControlButton({
    component: OrderSummaryButton,
    condition: function () {
        return true;
    },
});
