/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import RestrictStockPopup from "@pos_restrict_product_stock/js/RestrictStockPopup"
import { PosStore } from "@point_of_sale/app/store/pos_store";

patch(PosStore.prototype, {
    async addProductToCurrentOrder(...args) {
        var type = this.config.stock_type
        if (this.config.is_restrict_product && ((type == 'qty_on_hand') && (args['0'].qty_available <= 0)) | ((type == 'virtual_qty') && (args['0'].virtual_available <= 0)) |
            ((args['0'].qty_available <= 0) && (args['0'].virtual_available <= 0))) {
            // If the product restriction is activated in the settings and quantity is out stock, it show the restrict popup.
            this.popup.add(RestrictStockPopup, {
                body: args['0'].display_name,
                pro_id: args['0'].id
            });
        }
        else{
            await super.addProductToCurrentOrder(...args)
        }
    },
});
