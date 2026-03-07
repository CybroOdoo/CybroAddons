/** @odoo-module **/
import { Component } from "@odoo/owl";
import { ControlButtons } from "@point_of_sale/app/screens/product_screen/control_buttons/control_buttons";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { usePos } from "@point_of_sale/app/hooks/pos_hook";
import { CategorySummaryPopup } from "./CategoryPopup";
patch(ControlButtons.prototype, {
    setup() {
        super.setup();
        this.pos = usePos();
        this.dialog = useService("dialog");
    },
    async onClick() {
    // Show category summary popup
        const { confirmed } = await this.dialog.add(CategorySummaryPopup, {
         title: 'Category Summary',});
    },

});



