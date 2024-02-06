/** @odoo-module **/
import { Component } from "@odoo/owl";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { ProductSummaryPopup } from "./ProductPopup";

export class ProductSummaryButton extends Component {
// Extending Component and Adding Class ProductSummaryButton
    static template = 'ProductSummaryButton';
        setup() {
            super.setup();
            this.pos = usePos();
        }
        async onClick() {
            //Show payment summary popup
            const { confirmed } = await this.pos.popup.add(ProductSummaryPopup,
                        { title: 'Product Summary',}
                      );
        }
    }
ProductScreen.addControlButton({
component: ProductSummaryButton,
condition: function () {
    return true;
},
});