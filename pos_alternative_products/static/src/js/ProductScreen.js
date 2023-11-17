odoo.define('pos_alternative_products.AlternativeProductScreen', function(require) {
    'use strict';
//By extending the product screen
    const Registries = require('point_of_sale.Registries');
    const ProductScreen = require('point_of_sale.ProductScreen');
    const { format } = require('web.field_utils');
    var { Gui } = require('point_of_sale.Gui');
    const NumberBuffer = require('point_of_sale.NumberBuffer');
    var core = require('web.core');
    var _t = core._t;
    var { PosGlobalState } = require('point_of_sale.models');
    const PosTotalGlobalState = (PosGlobalState) => class PosTotalGlobalState extends PosGlobalState {
        //@Override
        async _processData(loadedData) {
            await super._processData(loadedData);
            this.product_template = loadedData['product.template'];
            }
        }
        Registries.Model.extend(PosGlobalState, PosTotalGlobalState);
         const AlternativeProduct = (ProductScreen) =>
            class extends ProductScreen {
            //Overrides the click function of the product
               async _clickProduct(event) {
                    var alter_products = this.env.pos.product_template.filter(function(dataObj){
                        return event.detail.alternative_product_ids.includes (dataObj.id)
                        })
                    for(var i=0; i < alter_products.length; i++){
                           alter_products[i]['image_url'] = window.location.origin + "/web/image/product.template/" + alter_products[i].id + "/image_128";
                    }
                    var response = await this.rpc({
                        model: 'stock.quant',
                        method: "pos_stock_product",
                        args:[,event.detail.id]
                        })
                    if (response == 0){
                        Gui.showPopup("AlternativeProduct", {
                               title: this.env._t('Alternative Product'),
                               cancelText: this.env._t("Cancel"),
                               body: alter_products,
                           });}
                    else{
                        if (!this.currentOrder) {
                                this.env.pos.add_new_order();
                            }
                            const product = event.detail;
                            const options = await this._getAddProductOptions(product);
                            // Do not add product if options is undefined.
                            if (!options) return;
                            // Add the product after having the extra information.
                            await this._addProduct(product, options);
                            NumberBuffer.reset();
                        }
                    }
               }
         Registries.Component.extend(ProductScreen, AlternativeProduct);
        return ProductScreen;
    });