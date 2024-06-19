odoo.define('all_in_one_pos_kit.age_restrict', function (require) {
"use strict";
    const Registries = require('point_of_sale.Registries');
    const ProductScreen = require('point_of_sale.ProductScreen');
        //Extending the product screen and on click function of the products in product screen ,it shows warnings as age restricted product,if it is age restricted one.
        const _product = (ProductScreen) => class extends ProductScreen {
        //Click function of the products.
            async _clickProduct(event) {
                //if product is age restricted it shows the popup and on confirming the popup, it will adds to the order line, on rejecting it will cancel the order
                if(event.detail.is_age_restrict == true ){
                    const { confirmed } = await this.showPopup('RestrictPopup',
                        {
                            title: ('Age Restricted Product !!!!!!!'),
                            body:('Please get Identity proof from customer.'),
                        });
                    if (confirmed){
                        super._clickProduct(event)
                    }
                }
                else{
                    super._clickProduct(event)
                }
            }
        }
    Registries.Component.extend(ProductScreen, _product);
});
