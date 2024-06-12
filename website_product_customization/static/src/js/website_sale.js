/** @odoo-module **/

import { WebsiteSale } from '@website_sale/js/website_sale';
import { patch } from '@web/core/utils/patch';
import { jsonrpc } from "@web/core/network/rpc_service";
// Patch the WebsiteSale class with custom modifications
patch(WebsiteSale.prototype,{
    // Override the _submitForm method

    async _submitForm(){
        var image_element = document.getElementsByClassName("design_image_doc")
        if (parseInt(image_element.length) == parseInt(0)) {
            return super._submitForm(...arguments);
        }
         else {
        const params = this.rootProduct;
        if (document.getElementsByClassName('design_image_doc')[0]){
                    var design_image = document.getElementsByClassName('design_image_doc')[0].currentSrc;
        }
        params.design_image = design_image;
            return super._submitForm(...arguments);
        };
    },

    // Override the _onModalSubmit method
    _onModalSubmit: function (goToShop) {
        const mainProduct = this.$('.js_product.in_cart.main_product').children('.product_id');
        const productTrackingInfo = mainProduct.data('product-tracking-info');
        if (productTrackingInfo) {
            const currency = productTrackingInfo['currency'];
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
        }
        const callService = this.call.bind(this)
        this.optionalProductsModal.getAndCreateSelectedProducts()
            .then((products) => {
                var product_id = products[0].product_id
                if (document.getElementsByClassName('design_image_doc')[0]){
                 products[0].design_image = document.getElementsByClassName('design_image_doc')[0].currentSrc;
                }
                const productAndOptions = JSON.stringify(products);
                this.rpc('/shop/cart/update_option', {
                    product_and_options: productAndOptions,
                    ...this._getOptionalCombinationInfoParam(),
                }).then(function (values) {
                    if (goToShop) {
                        window.location.pathname = "/shop/cart";
                    } else {
                        wSaleUtils.updateCartNavBar(values);
                        wSaleUtils.showCartNotification(callService, values.notification_info);
                    }
                }).then(() => {
                    this._getCombinationInfo($.Event('click', {target: $("#add_to_cart")}));
                });
            });
    }
})