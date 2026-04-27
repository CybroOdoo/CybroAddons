/** @odoo-module */
import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/store/pos_store";
import { unaccent } from "@web/core/utils/strings";
import { rpc } from "@web/core/network/rpc";
import { DebugWidget } from "@point_of_sale/app/debug/debug_widget";
import { useService } from "@web/core/utils/hooks";
import { Dialog } from "@web/core/dialog/dialog";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { _t } from "@web/core/l10n/translation";
patch(DebugWidget.prototype, {
    setup() {
        super.setup()
        this.orm = useService("orm");
        this.dialog = useService("dialog");
    },
    async barcodeScan() {
        if (!this.barcodeReader) {
            return;
        }
        await this.orm.call('multi.barcode.products','get_barcode_val',[this.state.barcodeInput]).then(async (data) => {
            if (data[1]){
                    this.currentOrder = this.pos.get_order();
                    const selectedOrderline = this.pos.get_order().get_selected_orderline()
               var product = this.currentOrder.get_selected_orderline();
                var product = data[1]
                if(product){
                    await this.pos.addLineToCurrentOrder({product_id:product
                    });
                }
                else{
                     this.dialog.add(AlertDialog, {
                        body: _t("Product is not loaded in the POS"),
                     });
                }
            } else{
                await this.barcodeReader.scan(this.state.barcodeInput);
            }
        });
    }
});
