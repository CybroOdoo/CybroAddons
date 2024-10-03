odoo.define('website_sale.product_customization', function (require) {
'use strict';

var core = require('web.core');
var ajax = require('web.ajax');
var publicWidget = require('web.public.widget');
require('website_sale.website_sale');

publicWidget.registry.WebsiteSale.include({

     /**
     * Overridden to resolve _opened promise on modal
     * when stayOnPageOption is activated.
     *
     * @override
     */
    _submitForm() {
       var image_element = document.getElementsByClassName("design_image_doc")
       if (parseInt(image_element.length) == parseInt(0)) {
            return this._super.apply(this, arguments);
        }
       else {
            if (image_element[0]){
                var design_image = image_element[0].currentSrc
            }
            this.rootProduct.design_image = design_image;
                return this._super.apply(this, arguments);
        };
    },


    /**
     * Submits the form with additional parameters
     * - lang
     * - product_custom_attribute_values: The products custom variant values
     *
     * @private
     * @param {Boolean} goToShop Triggers a page refresh to the url "shop/cart"
     */
    _onModalSubmit: function (goToShop) {
        const $product = $('#product_detail');
        let currency;
        if ($product.length) {
            currency = $product.data('product-tracking-info')['currency'];
        } else {
            // Add to cart from /shop page
            currency = this.$('[itemprop="priceCurrency"]').first().text();
        }
        const productsTrackingInfo = [];
        this.$('.js_product.in_cart').each((i, el) => {
            productsTrackingInfo.push({
                'item_id': parseInt(el.getElementsByClassName('product_id')[0].value),
                'item_name': el.getElementsByClassName('product_display_name')[0].textContent,
                'quantity': parseFloat(el.getElementsByClassName('js_quantity')[0].value),
                'currency': currency,
                'price': parseFloat(el.getElementsByClassName('oe_price')[0].getElementsByClassName('oe_currency_value')[0].textContent),
            });
        });
        if (productsTrackingInfo.length) {
            this.$el.trigger('add_to_cart_event', productsTrackingInfo);
        }

        this.optionalProductsModal.getAndCreateSelectedProducts()
            .then((products) => {
                var product_id = products[0].product_id
                if (document.getElementsByClassName('design_image_doc')[0]){
                 products[0].design_image = document.getElementsByClassName('design_image_doc')[0].currentSrc;
                }
                const productAndOptions = JSON.stringify(products);
                ajax.post('/shop/cart/update_option', {product_and_options: productAndOptions})
                    .then(function (quantity) {
                        if (goToShop) {
                            window.location.pathname = "/shop/cart";
                        }
                        const $quantity = $(".my_cart_quantity");
                        $quantity.parent().parent().removeClass('d-none');
                        $quantity.text(quantity).hide().fadeIn(600);
                    }).then(()=>{
                        this._getCombinationInfo($.Event('click', {target: $("#add_to_cart")}));
                    });
            });
    },

});

return publicWidget.registry.ProductCustomization;
});