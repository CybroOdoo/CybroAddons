/** @odoo-module **/
import { ControlButtons } from "@point_of_sale/app/screens/product_screen/control_buttons/control_buttons";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { usePos } from "@point_of_sale/app/hooks/pos_hook";
import { ProductSummaryPopup } from "./ProductPopup";

patch(ControlButtons.prototype, {
// Extending Component and Adding Class ProductSummaryButton
    setup() {
        super.setup();
        this.pos = usePos();
        this.dialog = useService("dialog");

    },
    async onClickProductSummary() {
        //Show payment summary popup
        const { confirmed } = await this.dialog.add(ProductSummaryPopup,
                    { title: 'Product Summary',}
                  );
    },
});