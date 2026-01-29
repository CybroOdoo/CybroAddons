odoo.define('one_page_checkout.website_sale', function (require) {
'use strict';

var core = require('web.core');
var config = require('web.config');
var publicWidget = require('web.public.widget');
var VariantMixin = require('website_sale.VariantMixin');
var wSaleUtils = require('website_sale.utils');
const cartHandlerMixin = wSaleUtils.cartHandlerMixin;
require("web.zoomodoo");
const dom = require('web.dom');

publicWidget.registry.OnePageCheckoutWebsiteSale = publicWidget.Widget.extend(
    VariantMixin, cartHandlerMixin, {
        selector: '.single_pg_checkout_layout',
        events: _.extend({}, VariantMixin.events || {}, {
            'click .a-submit': '_onClickSubmit',
            'click .show_coupon': '_onClickShowCoupon',
            'change select[name="country_id"]': '_onChangeCountry',
            'click span[title="Details"]': '_onCartDetailClick',
        }),

        /**
         * Initializes the widget.
         * Sets the `isWebsite` property to `true`.
         */
        init: function () {
            this._super.apply(this, arguments);
            this.isWebsite = true;
        },

        /**
         * Starts the widget.
         * Calls the super method and returns the resulting promise.
         * @returns {Promise} A promise representing the start of the widget.
         */
        start() {
            const def = this._super(...arguments);
            return def;
        },

        /**
         * Destroys the widget.
         * Calls the super method and performs any necessary cleanup.
         */
        destroy() {
            this._super.apply(this, arguments);
            this._cleanupZoom();
        },
        /**
         * Changes the country and updates the corresponding fields
            based on the selected country.
         */
        _changeCountry: function () {
            if (!$("#country_id").val()) {
                return;
            }
            // Get country information via RPC call
            this._rpc({
                route: "/shop/country_infos/" + $("#country_id").val(),
                params: {
                    mode: $("#country_id").attr('mode'),
                },
            }).then(function (data) {
                $("input[name='phone']").attr('placeholder', data.phone_code !== 0 ? '+'+ data.phone_code : '');            // populate states and display
                var selectStates = $("select[name='state_id']");
                // Dont reload state at first loading (done in qweb)
                if (selectStates.data('init')===0 || selectStates.find('option').length===1) {
                    if (data.states.length || data.state_required) {
                        selectStates.html('');
                        _.each(data.states, function (x) {
                            var opt = $('<option>').text(x[1])
                                .attr('value', x[0])
                                .attr('data-code', x[2]);
                            selectStates.append(opt);
                        });
                        selectStates.parent('div').show();
                    } else {
                        selectStates.val('').parent('div').hide();
                    }
                    selectStates.data('init', 0);
                } else {
                    selectStates.data('init', 0);
                }
                // Manage fields order / visibility
                if (data.fields) {
                    if ($.inArray('zip', data.fields) > $.inArray('city', data.fields)){
                        $(".div_zip").before($(".div_city"));
                    } else {
                        $(".div_zip").after($(".div_city"));
                    }
                    var all_fields = ["street", "zip", "city", "country_name"]; // "state_code"];
                    _.each(all_fields, function (field) {
                        $(".checkout_autoformat .div_" + field.split('_')[0]).toggle($.inArray(field, data.fields)>=0);
                    });
                }
                if ($("label[for='zip']").length) {
                    $("label[for='zip']").toggleClass('label-optional', !data.zip_required);
                    $("label[for='zip']").get(0).toggleAttribute('required', !!data.zip_required);
                }
                if ($("label[for='zip']").length) {
                    $("label[for='state_id']").toggleClass('label-optional', !data.state_required);
                    $("label[for='state_id']").get(0).toggleAttribute('required', !!data.state_required);
                }
            });
        },
        /**
         * Handles the click event on submit buttons and performs the necessary actions.
         * @param {Event} ev - The click event.
         * @param {boolean} forceSubmit - Determines whether to force the submission
            even if certain conditions are not met.
         */
        _onClickSubmit: function (ev, forceSubmit) {
            if ($(ev.currentTarget).is('#products_grid .a-submit') && !forceSubmit) {
                return;
            }
            // Hide the 'address_public_user' div
            var $aSubmit = $(ev.currentTarget);
            if (!ev.isDefaultPrevented() && !$aSubmit.is(".disabled")) {
                ev.preventDefault();
                $aSubmit.closest('form').submit();
            }
            if ($aSubmit.hasClass('a-submit-disable')) {
                $aSubmit.addClass("disabled");
            }
            if ($aSubmit.hasClass('a-submit-loading')) {
                var loading = '<span class="fa fa-cog fa-spin"/>';
                var fa_span = $aSubmit.find('span[class*="fa"]');
                if (fa_span.length) {
                    fa_span.replaceWith(loading);
                } else {
                    $aSubmit.append(loading);
                }
            }
        },
        /**
         * Handles the click event to show the coupon form by hiding the
            "show coupon" button and displaying the coupon form.
         * @param {Event} ev - The click event.
         */
        _onClickShowCoupon: function (ev) {
            $(".show_coupon").hide();
            $('.coupon_form').removeClass('d-none');
        },
        /**
         * Handles the change event on the country field and triggers the country
            change functionality.
         * If the checkout_autoformat element is not present, the function does
            nothing.one_page_checkout_cart
         * This function internally calls the _changeCountry function.
         * @param {Event} ev - The change event.
         */
        _onChangeCountry: function (ev) {
            if (!this.$('.checkout_autoformat').length) {
                return;
            }
            this._changeCountry();
        },
        /**
         * Handles the click event on the cart detail element.
         * Toggles the chevron icon and shows/hides the summary div accordingly.
         * @param {Event} ev - The click event.
         */
        _onCartDetailClick: function(ev) {
            var $elem = $(ev.currentTarget);
            if ($elem.hasClass('fa-chevron-down')) {
                $elem.removeClass('fa-chevron-down');
                $elem.addClass('fa-chevron-up');
            } else {
                $elem.removeClass('fa-chevron-up');
                $elem.addClass('fa-chevron-down');
            }
            var $summary_div = $('.toggle_summary_div');
            $summary_div.toggleClass('d-none');
        }
});
/**
 * This widget is used for the one-page checkout cart functionality.
 * It adds events to change shipping and edit address.
 */
publicWidget.registry.OnePageCheckoutWebsiteSaleCart = publicWidget.Widget.extend({
    selector: '.single_pg_checkout_layout .oe_cart',
    events: {
        'click .js_change_shipping': '_onClickChangeShipping',
        'click .js_edit_address': '_onClickEditAddress',
    },
    /**
     * Handles the click event on the "Change Shipping" element.
     * Updates the shipping options by toggling visibility and applying CSS classes.
     * Performs a POST request to update the selected shipping option via AJAX.
     * @param {Event} ev - The click event.
     */
    _onClickChangeShipping: function (ev) {
        var $old = $('.all_shipping').find('.card.border.border-primary');
        $old.find('.btn-ship').toggle();
        $old.addClass('js_change_shipping');
        $old.removeClass('border border-primary');

        var $new = $(ev.currentTarget).parent('div.one_kanban').find('.card');
        $new.find('.btn-ship').toggle();
        $new.removeClass('js_change_shipping');
        $new.addClass('border border-primary');

        var $form = $(ev.currentTarget).parent('div.one_kanban').find('form.d-none');
        $.post($form.attr('action'), $form.serialize()+'&xhr=1');
    },
    /**
     * Handles the click event on the "Edit Address" element.
     * Prevents the default action of the click event.
     * Updates the action attribute of the corresponding form and submits it.
     * @param {Event} ev - The click event.
     */
    _onClickEditAddress: function (ev) {
        ev.preventDefault();
        $(ev.currentTarget).closest('div.one_kanban').find('form.d-none').attr('action', '/shop/address').submit();
    }
});
/**
 * Returns an object with two properties representing publicWidget registries.
 * - OnePageCheckoutWebsiteSale: Represents the publicWidget registry for the OnePageCheckoutWebsiteSale.
 * - OnePageCheckoutWebsiteSaleCart: Represents the publicWidget registry for the OnePageCheckoutWebsiteSaleCart.
 * @returns {Object} An object with publicWidget registries.
 */
return {
    OnePageCheckoutWebsiteSale: publicWidget.registry.OnePageCheckoutWebsiteSale,
    OnePageCheckoutWebsiteSaleCart: publicWidget.registry.OnePageCheckoutWebsiteSaleCart,
};
});
