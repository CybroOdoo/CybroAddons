/** @odoo-module **/
/*
 * This file is used to restrict out of stock product from ordering and show restrict popup
 */
import Registries from 'point_of_sale.Registries';
import ProductScreen from 'point_of_sale.ProductScreen';

const RestrictProductScreen = (ProductScreen) => class RestrictProductScreen extends ProductScreen {
    async _clickProduct(event) {
        // Overriding product item click to restrict product out of stock
        const product = event.detail;
        var type = this.env.pos.config.stock_type
        if (this.env.pos.config.is_restrict_product && ((type == 'qty_on_hand') && (product.qty_available <= 0)) | ((type == 'virtual_qty') && (product.virtual_available <= 0)) |
            ((product.qty_available <= 0) && (product.virtual_available <= 0))) {
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
}
Registries.Component.extend(ProductScreen, RestrictProductScreen);
