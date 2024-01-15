/** @odoo-module **/

import { Component } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { useBarcodeReader } from "@point_of_sale/app/barcode/barcode_reader_hook";
import { useService } from "@web/core/utils/hooks";

export class ProductDetails extends Component {
    static template = "product_detail_search.ProductDetails";

    setup() {
        super.setup();
        this.pos = usePos();
        this.orm = useService("orm");

        useBarcodeReader({
            product: this._barcodeProductAction,
        });

        if (this.props.product_details == false) {
            this.product_details = false;
        } else {
            this.product_details = this.props.product_details;
        }
    }

    _barcodeProductAction(code) {
        var self = this;
        this.orm.call("product.template", "product_detail_search", ["", code.base_code]).then(function(result) {
            if (result == false) {
                self.pos.showScreen('ProductDetails', {
                    'product_details': false,
                });
            } else {
                self.product_details = result;
                self.pos.showScreen('ProductDetails', {
                    'product_details': self.product_details,
                });
            }
        });
    }

    back() {
        this.pos.showScreen('FindProductScreen');
    }
}

registry.category("pos_screens").add("ProductDetails", ProductDetails);
