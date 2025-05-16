/** @odoo-module **/

import { PosStore } from "@point_of_sale/app/store/pos_store";
import { patch } from "@web/core/utils/patch";
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { AlternativeProduct } from "./AbstractAwaitablePopup";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";


patch(PosStore.prototype, {
    async _processData(loadedData) {
     //@override
         await super._processData(...arguments);
         this.product_template = loadedData['product.template'];
    },
    async addProductToCurrentOrder(product, options = {}) {
           // Generate a popup when clicking on a product having alternative products
           const alter_products = this.product_template.filter(function(dataObj){
                    return product.alternative_product_ids.includes(dataObj.id)
           })
          for(var i=0; i < alter_products.length; i++){
              alter_products[i]['image_url'] = window.location.origin + "/web/image/product.template/" + alter_products[i].id + "/image_128";
          }
          var response = await this.orm.call('stock.quant','pos_stock_product', [product.id]);
          if (response && alter_products.length > 0){
                this.popup.add(AlternativeProduct, {
                   title: _t('Alternative Product'),
                   cancelText: _t("Cancel"),
                   body: alter_products
                });
          }
          else if (response == 0 && alter_products.length == 0) {
             this.popup.add(AlternativeProduct, {
                   title: _t('Not in Stock'),
                   cancelText: _t("Cancel"),
             });
          }
          else{
            return super.addProductToCurrentOrder(...arguments);
          }
    },
});
