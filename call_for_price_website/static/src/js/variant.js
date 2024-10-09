/** @odoo-module **/

import VariantMixin from "@website_sale_stock/js/variant_mixin";
const oldChangeCombinationStock = VariantMixin._onChangeCombinationStock;
/**
 * Displays call for price button in the product form if call for price feature is enabled
 * for the product.
 *
 * @override
 */
VariantMixin._onChangeCombinationStock = function (ev, $parent, combination) {
    oldChangeCombinationStock.apply(this, arguments);
    const addToCart = $parent.find('#add_to_cart_wrap');
    const contactUsButton = $parent.find('#contact_us_wrapper');
    const productPrice = $parent.find('.product_price');
    const quantity = $parent.find('.css_quantity');
    const product_unavailable = $parent.find('#product_unavailable');
    if (combination.price_call) {
        productPrice.removeClass('d-inline-block').addClass('d-none');
        quantity.removeClass('d-inline-flex').addClass('d-none');
        addToCart.removeClass('d-inline-flex').addClass('d-none');
        product_unavailable.removeClass('d-none').addClass('d-flex')
    }
};
