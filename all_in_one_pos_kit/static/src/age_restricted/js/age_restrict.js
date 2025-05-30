/** @odoo-module */
import { patch } from "@web/core/utils/patch";
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { ConfirmPopup } from "@point_of_sale/app/utils/confirm_popup/confirm_popup";
import { PosStore } from "@point_of_sale/app/store/pos_store";

patch(PosStore.prototype, {
    async addProductToCurrentOrder(product, options = {}){
                //if product is age restricted it shows the popup and on confirming the popup, it will adds to the order line, on rejecting it will cancel the order
                if(product.is_age_restrict == true ){
                    const { confirmed } = await this.popup.add(ConfirmPopup, {
                    title: ("Age Restricted Product !!!!!!!"),
                    body:('Please get Identity proof from customer.'),
                    });
                    if (confirmed){
                        super.addProductToCurrentOrder(...arguments)
                    }
                }
                else{
                    super.addProductToCurrentOrder(...arguments)
                }
            }
});
