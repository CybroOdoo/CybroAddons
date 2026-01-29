/** @odoo-module **/
import Registries from 'point_of_sale.Registries';
import ProductItem from 'point_of_sale.ProductItem';
var rpc = require('web.rpc');
const { hooks } = owl;
const { onWillStart } = hooks;

const ProductStockDisplay = (ProductItem) => class ProductStockDisplay extends ProductItem {

        async willStart() {
           var self = this;
           var result = null
           await rpc.query({
                model: "product.product",
                method: "get_product_quantity",
            }).then(function (data) {
                // Iterate through each product in the data received from the RPC query
                result=data
                data.forEach(function (productData) {
                    // Find the corresponding product in product_by_id by matching product ID
                    var productInDb = self.env.pos.db.product_by_id[productData.id];
                    if (productInDb) {
                        // Compare qty_available and virtual_available between the two data sets
                        if (productInDb.qty_available !== productData.qty_available || productInDb.virtual_available !== productData.virtual_available) {
                            // If there's a change, update the product in product_by_id
                            productInDb.qty_available = productData.qty_available;
                            productInDb.virtual_available = productData.virtual_available;
                        }
                    }
                });
            });
        }
}
Registries.Component.extend(ProductItem, ProductStockDisplay);