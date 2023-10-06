/** @odoo-module **/

const ProductWidget = require('point_of_sale.ProductsWidget');
const { useListener } = require("@web/core/utils/hooks");
const Registries = require('point_of_sale.Registries');
var rpc = require('web.rpc');
    const PosProductWidget = (ProductWidget) =>
    class extends ProductWidget {
     setup() {
            super.setup();
            useListener('click', this.get_data_from_backend);
        }
        async get_data_from_backend(){
        //This function will update the product in the pos backend
        if(this.env.pos.res_allow_sync.length){
          //Check if the 'Allow Auto Sync Product Data' field is enabled in the configuration settings.
          if (this.env.pos.res_allow_sync[this.env.pos.res_allow_sync.length - 1].allow_data_auto_sync === true) {
           //if enabled, trigger the function for loading product in background that in the pos models.
            await this.env.pos.loadProductsBackground();
          }
        }
    }
};
Registries.Component.extend(ProductWidget, PosProductWidget);
return ProductWidget;
