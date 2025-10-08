/** @odoo-module **/
import { WebsiteSale } from 'website_sale.website_sale';
import { patch } from '@web/core/utils/patch';
import { useRef, useState } from "@odoo/owl";

var ajax = require('web.ajax');
// Patch the WebsiteSale class with custom modifications
patch(WebsiteSale.prototype, 'custom/website_product_customization/static/src/js/website_sale.js.WebsiteSale',{
    // Override the _submitForm method

    _submitForm(){
        var image_element = document.getElementsByClassName("design_image_doc")
        if (parseInt(image_element.length) == parseInt(0)) {
            return this._super(...arguments);
        }
         else {
        const params = this.rootProduct;
        if (document.getElementsByClassName('design_image_doc')[0]){
                    var design_image = document.getElementsByClassName('design_image_doc')[0].currentSrc;
        }
        params.design_image = design_image;
        return this._super(...arguments);
        };
    },

    // Override the _onModalSubmit method
    _onModalSubmit(goToShop){
        const $product = $('#product_detail');
        let currency;
        if ($product.length) {
            currency = $product.data('product-tracking-info')['currency'];
        }
        else {
            // Add to cart from /shop page
            currency = this.$('[itemprop="priceCurrency"]').first().text();
        }
        const productsTrackingInfo = [];
        this.$('.js_product.in_cart').each((i, el) => {
            productsTrackingInfo.push({
                'item_id': el.getElementsByClassName('product_id')[0].value,
                'item_name': el.getElementsByClassName('product_display_name')[0].textContent,
                'quantity': el.getElementsByClassName('js_quantity')[0].value,
                'currency': currency,
                'price': el.getElementsByClassName('oe_price')[0].getElementsByClassName('oe_currency_value')[0].textContent,
            });
        });
        if (productsTrackingInfo) {
            this.$el.trigger('add_to_cart_event', productsTrackingInfo);
        }
        this.optionalProductsModal.getAndCreateSelectedProducts()
            .then((products) => {
                var product_id = products[0].product_id
                if (document.getElementsByClassName('design_image_doc')[0]){
                 products[0].design_image = document.getElementsByClassName('design_image_doc')[0].currentSrc;
                }
                const productAndOptions = JSON.stringify(products);
                // Send a POST request to update the cart options
                ajax.post('/shop/cart/update_option', {
                    product_and_options: productAndOptions,
                    ...this._getOptionalCombinationInfoParam()
                }).then(function (quantity) {
                        if (goToShop) {
                            window.location.pathname = "/shop/cart";
                        }
                        const $quantity = $(".my_cart_quantity");
                        $quantity.parent().parent().removeClass('d-none');
                        $quantity.text(quantity).hide().fadeIn(600);
                        sessionStorage.setItem('website_sale_cart_quantity', quantity);
                    });
            });
    }
})