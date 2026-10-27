/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { DebugWidget } from "@point_of_sale/app/utils/debug/debug_widget";
import { useService } from "@web/core/utils/hooks";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { _t } from "@web/core/l10n/translation";

patch(DebugWidget.prototype, {
    /**
     * Initialize required services.
     */
    setup() {
        super.setup();
        this.orm = useService("orm");
        this.dialog = useService("dialog");
    },

    /**
     * Handle barcode scan.
     * Checks custom barcode mapping and adds product to order.
     */
    async barcodeScan() {
        if (!this.barcodeReader) {
            return;
        }
        const [barcode, productTmplId] = await this.orm.call(
            "multi.barcode.products",
            "get_barcode_val",
            [this.state.barcodeInput]
        );
        if (barcode && productTmplId) {
            await this.pos.addLineToCurrentOrder({
                product_tmpl_id: productTmplId,
            });
        } else if (barcode) {
            this.dialog.add(AlertDialog, {
                title: _t("Product not found"),
                body: _t("Product is not loaded in the POS"),
            });
        } else {
            await this.barcodeReader.scan(this.state.barcodeInput);
        }
    },
});
