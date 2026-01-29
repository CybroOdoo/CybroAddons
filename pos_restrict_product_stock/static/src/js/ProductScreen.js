/** @odoo-module **/
/*
 * This file is used to restrict out of stock product from ordering and show restrict popup
 */
import Registries from 'point_of_sale.Registries';
import ProductScreen from 'point_of_sale.ProductScreen';
import { Gui } from 'point_of_sale.Gui';
var models = require('point_of_sale.models');
models.load_fields('product.product', ['qty_available','virtual_available','detailed_type']);
const RestrictProductScreen = (ProductScreen) => class RestrictProductScreen extends ProductScreen {
    async _clickProduct(event) {
        // Overriding product item click to restrict product out of stock
        const product = event.detail;
        var type = this.env.pos.config.stock_type
        if (this.env.pos.config.is_restrict_product && ((type == 'qty_on_hand') && (product.qty_available <= 0)) | ((type == 'virtual_qty') && (product.virtual_available <= 0)) |
            ((product.qty_available <= 0) && (product.virtual_available <= 0)) && (product.detailed_type != 'service' && (!(product.to_weight)))) {
            // If the product restriction is activated in the settings and quantity is out stock, it show the restrict popup.
            this.showPopup("RestrictStockPopup", {
                body: product.display_name,
                pro_id: product.id
            });
        }
        else{
            await super._clickProduct(event)
        }
    }
    async _onClickPay(){
    var type = this.env.pos.config.stock_type
    var out_of_stock = false
 for (let rec of this.env.pos.get_order().orderlines.models) {
 if (this.env.pos.config.is_restrict_product && ((type == 'qty_on_hand') && (rec.quantity > rec.product.qty_available)) | ((type == 'virtual_qty') && (rec.quantity > rec.product.virtual_available)) |
            ((rec.quantity > rec.product.qty_available) && (rec.quantity > rec.product.virtual_available)) && (rec.product.detailed_type != 'service' && (!(rec.product.to_weight)))) {
               out_of_stock = true
               this.showPopup("OutOfStockPopup", {
                body: rec.product.display_name,
                pro_id: rec.product.id
            });
              break;
            }
        }
        if (out_of_stock==false){
        await super._onClickPay()
}
    }
}
Registries.Component.extend(ProductScreen, RestrictProductScreen);
