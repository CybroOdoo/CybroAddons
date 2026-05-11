/** @odoo-module **/

import { Component,useState } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
import { useService } from "@web/core/utils/hooks";
import { usePos } from "@point_of_sale/app/hooks/pos_hook";
import { useBarcodeReader } from "@point_of_sale/app/hooks/barcode_reader_hook";
import { ProductDetails } from "./product_details";

// POS dialog that listens for barcode scans and shows product info.
export class FindProductDialog extends Component {
    static template = "product_detail_search.FindProductDialog";
    static components = { Dialog , ProductDetails };

    setup() {
        // Set up POS helpers and initial dialog state.
        this.pos = usePos();
        this.orm = useService("orm");
        this.state = useState({
            product_details: null, // null = not scanned yet
        });

        // Register barcode handler for product scans.
        useBarcodeReader({
            product: this._barcodeProductAction.bind(this),
        });
    }

    async _barcodeProductAction(code) {
        // Resolve product details from the scanned barcode.
        const result = await this.orm.call(
            "product.template",
            "product_detail_search",
            ["", code.base_code]
        );

        this.state.product_details = result || false;

    }

    close() {
        // Close the dialog.
        this.props.close();
    }
    back() {
        // Return to the scan prompt inside the dialog.
        this.state.product_details = false;
    }
}


