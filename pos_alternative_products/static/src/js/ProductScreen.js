/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { AlternativeProductPopup } from "@pos_alternative_products/js/AlternativeProductPopup";
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { _t } from "@web/core/l10n/translation";

patch(ProductScreen.prototype, {
    setup(){
       super.setup();
       this.orm = useService("orm");
    },

    async addProductToOrder(product) {
        const productsToDisplay = this.env.services.pos.productsToDisplay;
        const alternativeIds = product.raw.alternative_product_ids || [];
        console.log(111, productsToDisplay, alternativeIds)
        // Filter products whose raw.id is in the alternativeIds array
        const matchedProducts = productsToDisplay.filter(p =>
            alternativeIds.includes(p.raw.id)
        );
        console.log('matchedProducts', matchedProducts)
        for(var i=0; i < matchedProducts.length; i++){
            matchedProducts[i]['image_url'] = window.location.origin + "/web/image/product.template/" + matchedProducts[i].id + "/image_128";
        }
        if (matchedProducts.length == 0) {
            return super.addProductToOrder(...arguments);
        }
        if(product.raw.qty_available == 0){
            this.dialog.add(AlternativeProductPopup, {
                title: _t("Alternative Product"),
                cancelText: _t("Cancel"),
                body: matchedProducts,
            });
        }
        else {
            return super.addProductToOrder(...arguments);
        }
//        return this._super(...arguments);
    },
//    async addProductToOrder(product) {
//        let selectedProduct = product.product_tmpl_id
////        let selectedProduct = product.model.fields.alternative_product_ids
//        console.log(this, product, product.product_variant_ids[0].id)
//        const alternativeIds = selectedProduct.alternative_product_ids.map(prod => prod.id);
//        const alter_products = this.pos.product_template.filter(dataObj => {
//            return alternativeIds.includes(dataObj.id);
//        });
//        for(var i=0; i < alter_products.length; i++){
//            alter_products[i]['image_url'] = window.location.origin + "/web/image/product.template/" + alter_products[i].id + "/image_128";
//        }
//        if (alter_products.length == 0) {
//            return super.addProductToOrder(...arguments);
//        }
//        if(selectedProduct.qty_available == 0){
//            this.dialog.add(AlternativeProductPopup, {
//                title: _t("Alternative Product"),
//                cancelText: _t("Cancel"),
//                body: alter_products,
//            });
//        }
//        else {
//            return super.addProductToOrder(...arguments);
//        }
//    },
});