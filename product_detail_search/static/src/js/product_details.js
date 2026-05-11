/** @odoo-module **/

import { Component } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { usePos } from "@point_of_sale/app/hooks/pos_hook";
import { useBarcodeReader } from "@point_of_sale/app/hooks/barcode_reader_hook";
import { useService } from "@web/core/utils/hooks";

// POS screen component that renders product details after scanning.
export class ProductDetails extends Component {
    static template = "product_detail_search.ProductDetails";

    setup() {
        // Read initial details from props, defaulting to false.
          this.product_details = this.props.product_details || false;
    }

    back() {
        // Return to the scan prompt by clearing the details in parent props.
        this.props.product_details = false;
    }
}

// Register the screen in the POS screens registry.
registry.category("pos_screens").add("ProductDetails", ProductDetails);
