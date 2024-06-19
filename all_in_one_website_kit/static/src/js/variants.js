/**
 * VariantMixin module for Odoo e-commerce platform.
 * Overrides the _onChangeCombination method of the sale.VariantMixin module to add additional functionality.
 * This mixin checks if the selected product variant is available or not and displays an appropriate message to the user.
 *
 * @module website_hide_variants.VariantMixin
 * @requires sale.VariantMixin
 * @requires web.core
 * @requires web.rpc
 * @augments sale.VariantMixin
 */
odoo.define('website_hide_variants.VariantMixin', function (require) {
'use strict';
    var VariantMixin =require('sale.VariantMixin')
    var core = require('web.core')
    var rpc = require('web.rpc')
    VariantMixin._onChangeCombination = async function (ev, $parent, combination) {
        var count = false
           // Check if the selected combination has a valid product ID
        if(combination.product_id){
            await rpc.query({
                model: 'product.product',
                method: 'search_read',
                args: [[['id','=',parseInt(combination.product_id)]]],
        }).then(function (res) {
                        // Check if the product is marked as "website_hide_variants"
            if(res[0].website_hide_variants){
                                // Disable the combination and display an appropriate message to the user
                combination.is_combination_possible = false
                count = true
            }
            });
        }
                // Update the product variant information
            var $price = $parent.find(".oe_price:first .oe_currency_value");
            var $default_price = $parent.find(".oe_default_price:first .oe_currency_value");
            var $optional_price = $parent.find(".oe_optional:first .oe_currency_value");
            $price.text(this._priceToStr(combination.price));
            $default_price.text(this._priceToStr(combination.list_price));
            var isCombinationPossible = true;
            if (!_.isUndefined(combination.is_combination_possible)) {
                isCombinationPossible = combination.is_combination_possible;
            }
            this._toggleDisable($parent, isCombinationPossible);
            if (combination.has_discounted_price) {
                $default_price.closest('.oe_website_sale').addClass("discount");
                $optional_price.closest('.oe_optional').removeClass('d-none').css('text-decoration', 'line-through');
                $default_price.parent().removeClass('d-none');
            } else {
                $default_price.closest('.oe_website_sale').removeClass("discount");
                $optional_price.closest('.oe_optional').addClass('d-none');
                $default_price.parent().addClass('d-none');
            }
            var rootComponentSelectors = [
                'tr.js_product',
                '.oe_website_sale',
                '.o_product_configurator'
            ];
            if (!combination.product_id ||
                !this.last_product_id ||
                combination.product_id !== this.last_product_id) {
                this.last_product_id = combination.product_id;
                this._updateProductImage(
                    $parent.closest(rootComponentSelectors.join(', ')),
                    combination.display_image,
                    combination.product_id,
                    combination.product_template_id,
                    combination.carousel,
                    isCombinationPossible
                );
            }
            $parent.find('.product_id').first().val(combination.product_id || 0).trigger('change');
            $parent.find('.product_display_name').first().text(combination.display_name);
            $parent.find('.js_raw_price').first().text(combination.price).trigger('change');
            this.handleCustomValues($(ev.target));
        // Display appropriate message to the user based on the availability of the selected variant
            if(count){
                $('.css_not_available_msg')[0].innerText = "This Product is Out-of-stock."
            }else{
                $('.css_not_available_msg')[0].innerText = "This combination does not exist."
            }
        }
    });