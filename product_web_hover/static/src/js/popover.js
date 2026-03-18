/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { usePopover } from "@web/core/popover/popover_hook";
import { Component } from "@odoo/owl";

/** ------------------------------
 *  POPOVER COMPONENT
 * ------------------------------ */
export class productDetailPopover extends Component {
    setup() {
        this.actionService = useService("action");
    }
}

productDetailPopover.template = "product_web_hover.productDetailPopover";

/** ------------------------------
 *  WIDGET ON ICON HOVER
 * ------------------------------ */
export class productDetailWidget extends Component {
    setup() {
        this.orm = useService("orm");
        this.popover = usePopover(this.constructor.components.Popover, {
            position: "bottom",
        });
        this.productDetails = null; // Correct initial state
    }

    async fetchProductDetails(productId) {
        const product = await this.orm.call(
            "product.product",
            "read",
            [[productId], [
                "name",
                "image_1920",
                "lst_price",
                "categ_id",
                "default_code",
                "qty_available",
                "standard_price"
            ]]
        );
        return product[0];
    }

    async onMouseEnter(ev) {
        const target = ev.currentTarget;

        if (!target || !target.isConnected) {
            return;
        }

        const productId = this.props.record.data.product_id?.id;
        if (!productId) {
            return;
        }

        const details = await this.fetchProductDetails(productId);
        this.productDetails = details;

        if (!target || !target.isConnected) {
            return;
        }

        this.popover.open(target, {
            record: this.props.record,
            productDetails: this.productDetails,
        });
    }


    onMouseLeave() {
        this.popover.close();
    }
}

productDetailWidget.components = { Popover: productDetailPopover };
productDetailWidget.template = "product_web_hover.productDetail";

export const ProductDetailWidget = {
    component: productDetailWidget,
};

registry.category("view_widgets").add(
    "product_detail_popover_widget",
    ProductDetailWidget
);
