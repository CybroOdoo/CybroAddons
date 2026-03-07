/** @odoo-module **/
import { Component } from "@odoo/owl";
import { ControlButtons } from "@point_of_sale/app/screens/product_screen/control_buttons/control_buttons";
import { patch } from "@web/core/utils/patch";
import { usePos } from "@point_of_sale/app/hooks/pos_hook";
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { useService } from "@web/core/utils/hooks";
import { LocationSummaryPopup } from "./LocationPopup";
patch(ControlButtons.prototype, {
// Extending Component and Adding Class LocationSummaryButton
    setup() {
        super.setup();
        this.pos = usePos();
        this.orm = useService("orm");
        this.dialog = useService("dialog");

    },
    async onClickLocation() {
        // Show popup with locations
        const { confirmed } = await this.dialog.add(LocationSummaryPopup, {
            title: 'Location Summary',
        });
    },

});
