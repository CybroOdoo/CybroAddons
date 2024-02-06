/** @odoo-module **/
import { Component } from "@odoo/owl";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { CategorySummaryPopup } from "./CategoryPopup";

export class CategorySummaryButton extends Component {
// Extending Component and Adding Class CategorySummaryButton
    static template = "CategorySummaryButton";
    setup() {
        super.setup();
        this.pos = usePos();
    }
    async onClick() {
// Show category summary popup
        const { confirmed } = await this.pos.popup.add(CategorySummaryPopup,
                        { title: 'Category Summary',}
                      );
    }
}
// Register the component
ProductScreen.addControlButton({
    component: CategorySummaryButton,
    condition: function () {
        return true;
    },
});
