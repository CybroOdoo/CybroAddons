/**@odoo-module **/
import { _t } from "@web/core/l10n/translation";
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { useService } from "@web/core/utils/hooks";
import { Component } from "@odoo/owl";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { CreateProductPopup } from "./product_create_popup";
/**
 * OrderlineProductCreateButton is a component responsible for creating a
   product and adding it to the order line.
*/
export class OrderlineProductCreateButton extends Component {
    static template = "point_of_sale.ProductCreateButton";
    /**
     * Setup function to initialize the component.
     */
    setup() {
        this.pos = usePos();
        this.popup = useService("popup");
    }
    /**
     * Getter function to fetch a list of products based on the search criteria.
     * @returns {Object[]} List of products.
     */
    get products() {
        let list;
        if (this.state.search && this.state.search.trim() !== "") {
            list = this.env.pos.db.search_product_in_category(
                0,
                this.state.search.trim()
            );
        } else {
            list = this.env.pos.db.get_product_by_category(0);
        }
        return list.sort(function(a, b) {
            return a.display_name.localeCompare(b.display_name);
        });
    }
    /**
     * Click event handler for the create product button.
     */
    async onClick() {
        this.popup.add(CreateProductPopup, {
            product: this.props.product,
        })
    }
}
/**
 * Add the OrderlineProductCreateButton component to the control buttons in
   the ProductScreen.
 */
ProductScreen.addControlButton({
    component: OrderlineProductCreateButton,
});
