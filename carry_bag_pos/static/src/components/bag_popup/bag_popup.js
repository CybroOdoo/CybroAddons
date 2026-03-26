/** @odoo-module **/
import { Dialog } from "@web/core/dialog/dialog";
import { usePos } from "@point_of_sale/app/hooks/pos_hook";
import { Component } from "@odoo/owl";

export class BagPopup extends Component {
    static template = "carry_bag_pos.BagPopup";
    static components = { Dialog };

    setup() {
        this.pos = usePos();
        this.products = this.props.products || [];
    }

    _onClickProduct(event) {
        const productId = parseInt(event.currentTarget.dataset.productId);
        const product = this.pos.models["product.product"].get(productId);

        if (product) {
            const order = this.pos.getOrder();
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