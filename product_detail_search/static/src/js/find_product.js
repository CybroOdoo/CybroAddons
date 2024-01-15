/** @odoo-module **/

import { Component } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { useBarcodeReader } from "@point_of_sale/app/barcode/barcode_reader_hook";

export class FindProductScreen extends Component {
    static template = "product_detail_search.FindProductScreen";

    setup() {
        super.setup(...arguments);
        this.pos = usePos();
        this.orm = useService("orm");
        useBarcodeReader({
            product: this._barcodeProductAction,
        });
    }

    async _barcodeProductAction(code) {
        var self = this;
        await this.orm.call("product.template", "product_detail_search", ["", code.base_code]).then(function(result) {
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

    // Returning the Product Screen
    back() {
        this.pos.showScreen("ProductScreen");
    }
}

registry.category("pos_screens").add("FindProductScreen", FindProductScreen);
