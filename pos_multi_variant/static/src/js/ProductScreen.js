/** @odoo-module **/

import ProductScreen from 'point_of_sale.ProductScreen';
import Registries from 'point_of_sale.Registries';
import NumberBuffer from 'point_of_sale.NumberBuffer';
import rpc from 'web.rpc';

const ProductScreenExtend = (ProductScreen) =>
class extends ProductScreen {
    setup() {
        super.setup();
    }

    async _clickProduct(event) {
        await super._clickProduct(...arguments)
            if (!this.currentOrder) {
                this.env.pos.add_new_order();
            }
        const product = event.detail;
        var variant_product = ''
        await rpc.query({
            model: 'variants.tree',
            method: 'search_read',
            fields: ['extra_price','attribute_id','value_ids', 'variants_id'],
            args: [[['variants_id','=',event.detail.product_tmpl_id]]]
            }).then(function (data) {
                variant_product = data
        });
        var li=[]
        for(var i=0; i<variant_product.length; ++i) {
            variant_product[i].value_ids.forEach(function (field) {
                li.push(field)
            });
        }
        var variant_details = ''
        await rpc.query({
                model: 'product.attribute.value',
                method: 'search_read',
                fields: ['name'],
                domain: [['id', 'in', li]],
                }).then(function (result) {
                variant_details = result
            });
        const options = await this._getAddProductOptions(product);
        // Do not add product if options is undefined.
        if (!options) return;
        NumberBuffer.reset();
        if(product.is_pos_variants){
            this.showPopup('ProductsPopup',{
                title:  product.display_name,
                products: variant_product,
                product_tmpl_id: event.detail.id,
                variant_details: variant_details,
            });
        }
    }
};

Registries.Component.extend(ProductScreen, ProductScreenExtend);
