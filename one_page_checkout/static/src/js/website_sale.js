/** @odoo-module **/

import wSaleUtils from "@website_sale/js/website_sale_utils";
import VariantMixin from "@website_sale/js/sale_variant_mixin";
import publicWidget from '@web/legacy/js/public/public_widget';
import { cartHandlerMixin } from '@website_sale/js/website_sale_utils';
import { WebsiteSale } from '@website_sale/js/website_sale';
import { _t } from "@web/core/l10n/translation";

publicWidget.registry.OnePageCheckoutWebsiteSale = publicWidget.Widget.extend(
VariantMixin, cartHandlerMixin, {
        selector: '.single_pg_checkout_layout',
        events: Object.assign({}, VariantMixin.events || {}, {
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
            this.rpc = this.bindService("rpc");
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
        var self = this
        if (!this.$el.find("#country_id").val()) {
            return;
        }
        return this.rpc("/shop/country_infos/" + $("#country_id").val(), {
            mode: this.$el.find("#country_id").attr('mode'),
        }).then(function (data) {
            // placeholder phone_code
            self.$el.find("input[name='phone']").attr('placeholder', data.phone_code !== 0 ? '+'+ data.phone_code : '');

            // populate states and display
            var selectStates = self.$el.find("select[name='state_id']");
            // dont reload state at first loading (done in qweb)
            if (selectStates.data('init')===0 || selectStates.find('option').length===1) {
                if (data.states.length || data.state_required) {
                    selectStates.html('');
                    data.states.forEach((x) => {
                        var opt = self.$el.find('<option>').text(x[1])
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

            // manage fields order / visibility
            if (data.fields) {
                if (data.fields.indexOf("zip") > data.fields.indexOf("city")){
                    self.$el.find(".div_zip").before(self.$el.find(".div_city"));
                } else {
                    self.$el.find(".div_zip").after(self.$el.find(".div_city"));
                }
                var all_fields = ["street", "zip", "city", "country_name"]; // "state_code"];
                all_fields.forEach((field) => {
                    self.$el.find(".checkout_autoformat .div_" + field.split('_')[0]).toggle(data.fields.indexOf(field)>=0);
                });
            }

            if (self.$el.find("label[for='zip']").length) {
                self.$el.find("label[for='zip']").toggleClass('label-optional', !data.zip_required);
                self.$el.find("label[for='zip']").get(0).toggleAttribute('required', !!data.zip_required);
            }
            if (self.$el.find("label[for='zip']").length) {
                self.$el.find("label[for='state_id']").toggleClass('label-optional', !data.state_required);
                self.$el.find("label[for='state_id']").get(0).toggleAttribute('required', !!data.state_required);
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
            if (this.$(ev.currentTarget).is('#products_grid .a-submit') && !forceSubmit) {
                return;
            }
            var $aSubmit = this.$(ev.currentTarget);
            if (!ev.isDefaultPrevented() && !$aSubmit.is(".disabled")) {
                ev.preventDefault();
                $aSubmit.closest('form').submit();
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
            this.$el.find(".show_coupon").hide();
            this.$el.find('.coupon_form').removeClass('d-none');
        },
        /**
         * Handles the change event on the country field and triggers the country
            change functionality.
         * If the checkout_autoformat element is not present, the function does
            nothing.
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
            var $elem = this.$(ev.currentTarget);
            if ($elem.hasClass('fa-chevron-down')) {
                $elem.removeClass('fa-chevron-down');
                $elem.addClass('fa-chevron-up');
            } else {
                $elem.removeClass('fa-chevron-up');
                $elem.addClass('fa-chevron-down');
            }
            var $summary_div = this.$el.find('.toggle_summary_div');
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
        var $old = this.$el.find('.all_shipping').find('.card.border.border-primary');
        $old.find('.btn-ship').toggle();
        $old.addClass('js_change_shipping');
        $old.removeClass('border border-primary');

        var $new = this.$(ev.currentTarget).parent('div.one_kanban').find('.card');
        $new.find('.btn-ship').toggle();
        $new.removeClass('js_change_shipping');
        $new.addClass('border border-primary');

        var $form = this.$(ev.currentTarget).parent('div.one_kanban').find('form.d-none');
        this.$.post($form.attr('action'), $form.serialize()+'&xhr=1');
    },
    /**
     * Handles the click event on the "Edit Address" element.
     * Prevents the default action of the click event.
     * Updates the action attribute of the corresponding form and submits it.
     * @param {Event} ev - The click event.
     */
    _onClickEditAddress: function (ev) {
        ev.preventDefault();
        this.$(ev.currentTarget).closest('div.one_kanban').find('form.d-none').attr('action', '/shop/address').submit();
    }
});
return {
    OnePageCheckoutWebsiteSale: publicWidget.registry.OnePageCheckoutWebsiteSale,
    OnePageCheckoutWebsiteSaleCart: publicWidget.registry.OnePageCheckoutWebsiteSaleCart,
};
