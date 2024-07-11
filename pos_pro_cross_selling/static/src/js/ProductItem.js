/** @odoo-module **/
import { PosStore } from "@point_of_sale/app/store/pos_store";
import { jsonrpc } from "@web/core/network/rpc_service";
import { patch } from "@web/core/utils/patch";
import { ProductConfiguratorPopup } from "@point_of_sale/app/store/product_configurator_popup/product_configurator_popup";
import { ConfirmPopup } from "@point_of_sale/app/utils/confirm_popup/confirm_popup";
import { _t } from "@web/core/l10n/translation";
import { CrossProduct } from "@pos_pro_cross_selling/app/cross_product/cross_product";

//Patching PosStore
patch(PosStore.prototype, {
//    function to add the selected product to the order
    async addProductToCurrentOrder(product, options = {}) {
        jsonrpc('/web/dataset/call_kw/pos.cross.selling/get_cross_selling_products', {
            model: 'pos.cross.selling',
            method: 'get_cross_selling_products',
            args: [[],product.id],
            kwargs: {},
        }).then(async(result) => {
            if (result.length > 0) {
                await this.popup.add(CrossProduct, {
                   product: result
                });
                this.env.services.pos.get_order().add_product(product);
            }
            else {
                return super.addProductToCurrentOrder(...arguments);
            }
        });
    },
});
