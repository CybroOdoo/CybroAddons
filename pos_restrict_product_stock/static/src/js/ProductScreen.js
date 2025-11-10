/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { useService } from "@web/core/utils/hooks";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { _t } from "@web/core/l10n/translation";


patch(ProductScreen.prototype, {
setup() {
    super.setup();
        this.dialog = useService("dialog");
        },
    async addProductToOrder(...args) {
        var type = this.pos.config.stock_type
        console.log("ar",args[0])
        if (this.pos.config.is_restrict_product && ((type == 'qty_on_hand') && (args['0'].qty_available <= 0)) | ((type == 'virtual_qty') && (args['0'].virtual_available <= 0)) |
            ((args['0'].qty_available <= 0) && (args['0'].virtual_available <= 0)) && (args['0'].type != 'service' && (!(args['0'].to_weight)))) {
            // If the product restriction is activated in the settings and quantity is out stock, it show the restrict popup.
            this.dialog.add(ConfirmationDialog, {
            body: _t("%s is out of stock. Do you want to proceed?", args['0'].display_name),
                confirmLabel: _t("Order"),
                confirm: () => {
                    const product = args['0'];
                    product.order_status = true;
                    super.addProductToOrder(...args)
                },
                cancel: () => {},
            });
        }
        else{
            await super.addProductToOrder(...args)
        }
    },
});
