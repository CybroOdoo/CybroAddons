/**
 * CustomVariantMixin module for Odoo.
 * This module extends the VariantMixin functionality from website_sale to handle custom behavior.
 */
odoo.define('call_for_price_website.CustomVariantMixin', function(require) {
    'use strict';

    // Import the VariantMixin from website_sale module
    var VariantMixin = require('website_sale.VariantMixin');
    // Store a reference to the original onChangeCombination function
    const originalOnChangeCombination = VariantMixin._onChangeCombination;
    // Override the onChangeCombination function to implement custom behavior
    VariantMixin._onChangeCombination = function(ev, $parent, combination) {
        const $pricePerUom = $parent.find(".o_base_unit_price:first .oe_currency_value");
        if ($pricePerUom) {
            if (combination.is_combination_possible !== false && combination.base_unit_price != 0) {
                $pricePerUom.parents(".o_base_unit_price_wrapper").removeClass("d-none");
                $pricePerUom.text(this._priceToStr(combination.base_unit_price));
                $parent.find(".oe_custom_base_unit:first").text(combination.base_unit_name);
            } else {
                $pricePerUom.parents(".o_base_unit_price_wrapper").addClass("d-none");
            }
        }
        // Triggers a new JS event with the correct payload, which is then handled
        // by the google analytics tracking code.
        // Indeed, every time another variant is selected, a new view_item event
        // needs to be tracked by google analytics.
        if ('product_tracking_info' in combination) {
            const $product = $('#product_detail');
            $product.data('product-tracking-info', combination['product_tracking_info']);
            $product.trigger('view_item_event', combination['product_tracking_info']);
        }
        const addToCart = $parent.find('#add_to_cart_wrap');
        const contactUsButton = $parent.find('#contact_us_wrapper');
        const productPrice = $parent.find('.product_price');
        const quantity = $parent.find('.css_quantity');
        const product_unavailable = $parent.find('#product_unavailable');
        const price_call_div = $parent.find('#price_call_hide');

        if (combination.prevent_zero_price_sale) {
            productPrice.removeClass('d-inline-block').addClass('d-none');
            quantity.removeClass('d-inline-flex').addClass('d-none');
            addToCart.removeClass('d-inline-flex').addClass('d-none');
            contactUsButton.removeClass('d-none').addClass('d-flex');
            product_unavailable.removeClass('d-none').addClass('d-flex')
        } else if (combination.price_call) {
            productPrice.removeClass('d-inline-block').addClass('d-none');
            quantity.removeClass('d-inline-flex').addClass('d-none');
            addToCart.removeClass('d-inline-flex').addClass('d-none');
            contactUsButton.removeClass('d-none').addClass('d-flex');
            price_call_div.removeClass('d-none').addClass('d-flex');
            this.$el.find('#add_to_cart')[0].style.display = "none";
            this.$el.find('#price_of_product')[0].style.display = "none";
            this.$el.find('#price_of_product')[0].style.display = "none";
        } else {
            productPrice.removeClass('d-none').addClass('d-inline-block');
            quantity.removeClass('d-none').addClass('d-inline-flex');
            addToCart.removeClass('d-none').addClass('d-inline-flex');
            contactUsButton.removeClass('d-flex').addClass('d-none');
            product_unavailable.removeClass('d-flex').addClass('d-none')
            price_call_div.removeClass('d-flex').addClass('d-none')
            this.$el.find('#add_to_cart')[0].style.display = "block";
            this.$el.find('#price_of_product')[0].style.display = "block";
            this.$el.find('#price_of_product')[0].style.display = "block";
        }
        // Call the original onChangeCombination function
        originalOnChangeCombination.apply(this, [ev, $parent, combination]);
    };
});