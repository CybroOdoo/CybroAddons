/** @odoo-module **/
//Extended Component to add a button in pos session and for its working to scan barcode and show the products in the orderline
import { _t } from "@web/core/l10n/translation";
import { patch } from "@web/core/utils/patch";
import { ControlButtons } from "@point_of_sale/app/screens/product_screen/control_buttons/control_buttons";
import { BarcodePopup } from "@pos_return_barcode/js/barcode_popup";
import { useService } from "@web/core/utils/hooks";


patch(ControlButtons.prototype, {
    setup() {
        super.setup();
        this.dialog = useService("dialog")
        this.orm = useService("orm");
    },

    async onClickReturn() {
        const { confirmed, payload } = await this.dialog.add(BarcodePopup);
    }
});
