/** @odoo-module */

import { Component, onWillUpdateProps, proxy } from "@odoo/owl";

// POS component that renders product details after scanning.
export class ProductDetails extends Component {
    static template = "product_detail_search.ProductDetails";

    setup() {
        // Read initial details from props, defaulting to false.
        this.state = proxy({
            product_details: this.props.product_details || false,
        });

        onWillUpdateProps((nextProps) => {
            this.state.product_details = nextProps.product_details || false;
        });
    }
}

