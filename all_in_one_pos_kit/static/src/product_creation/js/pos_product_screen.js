/** @odoo-module **/

import { ControlButtons } from "@point_of_sale/app/screens/product_screen/control_buttons/control_buttons";
import { patch } from "@web/core/utils/patch";
import { CreateProductPopup } from "./product_create_popup";

patch(ControlButtons.prototype, {
    async onClickCreateProduct() {
        this.dialog.add(CreateProductPopup, {});
    }
});
