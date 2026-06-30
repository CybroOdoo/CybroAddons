/** @odoo-module **/
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { rpc } from "@web/core/network/rpc";;
import { patch } from "@web/core/utils/patch";
import { CrossProduct } from "@pos_pro_cross_selling/app/cross_product/cross_product";
import { reactive } from "@odoo/owl";

//Patching ProductScreen
patch(ProductScreen.prototype, {
//    function to add the selected product to the order
    async addProductToOrder(product, options = {}) {
        var ProductSelected = await reactive(this.pos).addLineToCurrentOrder({ product_id: product }, {});
        rpc('/web/dataset/call_kw/pos.cross.selling/get_cross_selling_products', {
            model: 'pos.cross.selling',
            method: 'get_cross_selling_products',
            args: [[],ProductSelected?._raw.product_id.id],
            kwargs: {},
        }).then(async(result) => {
            if (result.length > 0) {
                await this.dialog.add(CrossProduct, {
                   product: result
                });
            }
        });
    },
});
