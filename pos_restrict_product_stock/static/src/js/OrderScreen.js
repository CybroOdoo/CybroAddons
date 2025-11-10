/** @odoo-module */
import { PosStore } from "@point_of_sale/app/store/pos_store";
import { patch } from "@web/core/utils/patch";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { _t } from "@web/core/l10n/translation";


patch(PosStore.prototype, {
    async pay() {
             var type = this.config.stock_type
             const pay = true
             const body = []
             const pro_id = false
             for (const line of this.get_order().get_orderlines()) {
//                  const isService = product.detailed_type === 'service';
                 if (line.config.is_restrict_product && ((type == 'qty_on_hand') && (line.product_id.qty_available <= 0)) | ((type == 'virtual_qty') && (line.product_id.virtual_available <= 0)) |
                                         ((line.product_id.qty_available <= 0) && (line.product_id.virtual_available <= 0)) && (line.product_id.type != 'service' && (!(line.product_id.to_weight)))) {
                                         // If the product restriction is activated in the settings and quantity is out stock, it show the restrict popup.
                                    body.push(line.product_id.display_name)
                 }
             }
             if (body.length > 0) { // Check if body has items
                const confirmed = this.dialog.add(ConfirmationDialog, {
                    body: _t("%s is out of stock. Click Order, if you still want to add this product?", body),
                    confirmLabel: _t("Order"),
                    confirm: () => {
                        return super.pay();
                    },
                    cancel: () => {
                        return;
                    },
                })
             }
             else {
                return super.pay(); // No restrictions, proceed with payment
             }
    }
})
