/** @odoo-module */

import { Component, proxy } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

// Dashboard client action for barcode-based product lookup in Inventory.
class ProductDetailSearchBarcodeDashboard extends Component {
    static template = "CustomDashBoardFindProduct";

    setup() {
        // Initialize services and reactive state for barcode lookups.
        this.action = useService("action");
        this.orm = useService("orm");
        this.state = proxy({
            product_details: [],
            barcode_value: "",
        });
    }

    onProductKeypress(e) {
        // Track that the user typed to avoid triggering on blur-only changes.
        this.typed_into = true;
    }

    change_product_barcode(e) {
        // Update barcode input and query the server only when typed.
        this.state.barcode_value = e.target.value;
        if (this.typed_into) {
            // Fetch product details for the entered barcode.
            this.orm.call("product.template", "product_detail_search", ["", this.state.barcode_value]).then((result) => {
                if (result) {
                    this.state.product_details = result;
                } else {
                    this.state.product_details = [];
                }
            });
            this.typed_into = false;
        }
    }
}

// Register client action for the dashboard menu item.
registry.category("actions").add("product_detail_search_barcode_main_menu", ProductDetailSearchBarcodeDashboard);
