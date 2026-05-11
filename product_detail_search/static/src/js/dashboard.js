/** @odoo-module */

import { registry } from '@web/core/registry';
const { Component, useState } = owl;
import { useService } from "@web/core/utils/hooks";

// Dashboard client action for barcode-based product lookup in Inventory.
class product_detail_search_barcode_dashboard extends Component {
    setup() {
        // Initialize services and reactive state for barcode lookups.
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
        // Track that the user typed to avoid triggering on blur-only changes.
        this.typed_into = true;
    }

    change_product_barcode(e) {
        var self = this;
        // Update barcode input and query the server only when typed.
        this.state.barcode_value = e.target.value
        if (this.typed_into) {
            // Fetch product details for the entered barcode.
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

// Register client action for the dashboard menu item.
product_detail_search_barcode_dashboard.template = 'CustomDashBoardFindProduct';
registry.category("actions").add("product_detail_search_barcode_main_menu", product_detail_search_barcode_dashboard);
