/** @odoo-module **/

/**
 * This module defines a popup component used in POS to display
 * and select carry bag products, allowing users to add them to the order.
 */

import { Dialog } from "@web/core/dialog/dialog";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { Component } from "@odoo/owl";

export class BagPopup extends Component {
    static template = "carry_bag_pos.BagPopup";
    static components = { Dialog };

    /**
     * Setup function to initialize the component.
     */
    setup() {
        this.pos = usePos();
        this.products = this.props.products || [];
    }

    /**
     * _onClickProduct function handles the click event on a product.
     */
    _onClickProduct(productId) {
        const product = this.pos.models["product.product"].get(productId);

        if (product) {
            const order = this.pos.get_order();

            this.pos.models["pos.order.line"].create({
                order_id: order,
                product_id: product,
                qty: 1,
                price_unit: product.lst_price,
            });

            this.props.close();
        }
    }
}