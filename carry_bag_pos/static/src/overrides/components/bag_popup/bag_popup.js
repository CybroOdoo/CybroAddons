/**@odoo-module **/
import { AbstractAwaitablePopup } from "@point_of_sale/app/popup/abstract_awaitable_popup";
/**
 * BagPopup is a popup component for selecting products to add as carry bags.
 */
export class BagPopup extends AbstractAwaitablePopup {
    static template="carry_bag_pos.BagPopup"
    /**
     * Setup function to initialize the component.
     */
    setup() {
        super.setup();
        this.products = this.props.products
    }
    /**
     * _onClickProduct function handles the click event on a product.
     */
    _onClickProduct(id){
        this.props.pos.get_order().add_product(this.props.pos.db.get_product_by_id(id));
    }get_product_by_id
}
