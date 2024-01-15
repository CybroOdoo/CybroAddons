/** @odoo-module */

import { registry } from '@web/core/registry';
const { Component, useState } = owl;
import { useService } from "@web/core/utils/hooks";

class product_detail_search_barcode_dashboard extends Component {
    setup() {
        this.action = useService("action");
        this.rpc = this.env.services.rpc;
        this.action = useService("action");
        this.orm = useService("orm");
        this.state = useState({
            product_details: [],
            barcode_value: [],
        });
    }

    onProductKeypress(e) {
        this.typed_into = true;
    }

    change_product_barcode(e) {
        var self = this;
        self.state.barcode_value = $("#" + e.target.id).val();
        if (this.typed_into) {
            this.orm.call("product.template", "product_detail_search", ["", self.state.barcode_value]).then(function(result) {
                if (result != false) {
                    self.state.product_details = result;
                } else {
                    self.state.product_details = [];
                }
            });
            this.typed_into = false;
        }
    }
}

product_detail_search_barcode_dashboard.template = 'CustomDashBoardFindProduct';
registry.category("actions").add("product_detail_search_barcode_main_menu", product_detail_search_barcode_dashboard);
