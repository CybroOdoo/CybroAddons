/** @odoo-module */

import { Navbar } from "@point_of_sale/app/components/navbar/navbar";
import { patch } from "@web/core/utils/patch";
import { FindProductDialog } from "./find_product";

// Extend the POS navbar to open the Find Product dialog.
patch(Navbar.prototype, {

    async find_product() {
            // Launch the barcode-based product lookup dialog.
            this.env.services.dialog.add(FindProductDialog);
    },
});
