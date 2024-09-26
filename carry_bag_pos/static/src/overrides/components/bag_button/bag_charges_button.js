/**@odoo-module **/
import { _t } from "@web/core/l10n/translation";
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { useService } from "@web/core/utils/hooks";
import { Component } from "@odoo/owl";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { BagPopup } from "../bag_popup/bag_popup"
/**
 * BagChargesButton is a component responsible for opening the bag charges popup.
 */
export class BagChargesButton extends Component {
    static template = "carry_bag_pos.BagChargesButton";
    /**
     * Setup function to initialize the component.
     */
    setup() {
        this.pos = usePos();
        this.popup = useService("popup");
    }
    /**
     * onClick function handles the click event of the bag charges button.
     */
    async onClick() {
          var categoryId = this.pos.config.bag_category_id[0]
          var products = this.pos.db.get_product_by_category(categoryId)
          this.popup.add(BagPopup,{
            products:products,
            pos:this.pos,
          })
    }
}
// Add BagChargesButton component as a control button to Product
ProductScreen.addControlButton({
    component: BagChargesButton,
});
