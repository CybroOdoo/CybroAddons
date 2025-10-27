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
        const product = args[0];
        const type = this.pos.config.stock_type;
        const product_type = product.type || null;
        if (product_type === 'service' || product_type === 'consu') {
            console.log('Cybro Ignorando stock para tipo:', product_type);
            super.addProductToOrder(...args);
        }
        
        if (this.pos.config.is_restrict_product && ((type == 'qty_on_hand') && (args['0'].qty_available <= 0)) | ((type == 'virtual_qty') && (args['0'].virtual_available <= 0)) |
            ((args['0'].qty_available <= 0) && (args['0'].virtual_available <= 0))) {
            // If the product restriction is activated in the settings and quantity is out stock, it show the restrict popup.
            this.dialog.add(ConfirmationDialog, {
            body: _t("%s is out of stock. Do you want to proceed?", args['0'].display_name),
                confirmLabel: _t("Order"),
                confirm: () => {
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
