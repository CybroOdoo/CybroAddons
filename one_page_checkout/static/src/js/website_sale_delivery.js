/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import { _t } from "@web/core/l10n/translation";
import { renderToElement } from "@web/core/utils/render";
import { KeepLast } from "@web/core/utils/concurrency";
import { Component } from "@odoo/owl";
import '@website_sale/js/website_sale_delivery';

publicWidget.registry.websiteSaleDelivery.include({
    _getCurrentLocation: async function () {
        const data = await this.rpc("/shop/access_point/get");
        const carriers = this.$el.find('.o_delivery_carrier_select')
        for (let carrier of carriers) {
            const deliveryType = this.$el.find('input[type="radio"]').attr("delivery_type");
            const deliveryName = this.$el.find('.o_delivery_carrier_select label').text();
            const showLoc = this.$el.find(".o_show_pickup_locations");
            if (!showLoc) {
                continue;
            }
            const orderLoc = this.$el.find(".o_order_location");
            if (data[deliveryType + '_access_point'] && data.delivery_name == deliveryName) {
                this.$el.find(".o_order_location_name").text = data.name
                this.$el.find(".o_order_location_address").text = data[deliveryType + '_access_point']
                orderLoc.parent().removeClass('new-parent-class');
                showLoc.addClass("d-none");
                break;
            } else {
                orderLoc.parent().addClass("d-none");
                showLoc.removeClass("d-none");
            }
        }
    },

    /**
     * @private
     * @param {jQuery} $carrierInput
     */
     _showLoading: function (carrierInput) {
        const priceTag = this.$el.find('.o_wsale_delivery_badge_price')
        while (priceTag.firstChild) {
            priceTag.removeChild(priceTag.lastChild);
        }
        const loadingCircle = priceTag.append(document.createElement('span'));
        loadingCircle.addClass("fa", "fa-circle-o-notch", "fa-spin");
     },
    /**
     * Update the total cost according to the selected shipping method
     * @private
     * @param {float} amount : The new total amount of to be paid
     */
    _getCarrierRateShipment: async function(carrierInput) {
      const result = await this.rpc('/shop/carrier_rate_shipment', {
            'carrier_id': carrierInput.value,
      });
    },
    _handleCarrierUpdateResult: async function (carrierInput) {
        //---updating carrier input function
        const result = await this.rpc('/shop/update_carrier', {
            'carrier_id': carrierInput.value,
        })
        this.result = result;
        result.status = true
        this._handleCarrierUpdateResultBadge(result);
        if (carrierInput.checked) {
            var amountDelivery = this.$el.find('#order_delivery .monetary_field');
            var amountUntaxed = this.$el.find('#order_total_untaxed .monetary_field');
            var amountTax = this.$el.find('#order_total_taxes .monetary_field');
            var amountTotal = this.$el.find('#order_total .monetary_field, #amount_total_summary.monetary_field');
            if(amountDelivery){
                amountDelivery.html = result.new_amount_delivery;
            }
            if(amountUntaxed){
                amountUntaxed.html = result.new_amount_untaxed;
            }
            if(amountTax){
                amountTax.html = result.new_amount_tax;
            }
            amountTotal.each(function() {
                this.html = result.new_amount_total;
            });
            if (result.new_amount_total_raw !== undefined) {
                this._updateShippingCost(result.new_amount_total_raw);
                // reload page only when amount_total switches between zero and not zero
                const hasPaymentMethod = this.$el.find(
                    "div[name='o_website_sale_free_cart']"
                ) === null;
                const shouldDisplayPaymentMethod = result.new_amount_total_raw !== 0;
            }
            this._updateShippingCost(result.new_amount_delivery);
        }
        this._enableButton(result.status);
        let currentId = result.carrier_id
        const showLocations = this.$el.find(".o_show_pickup_locations");
        for (const showLoc of showLocations) {
            const currentCarrierId = showLoc.closest("li").find("input")[0].value;
            if (currentCarrierId == currentId) {
                this._specificDropperDisplay(showLoc);
                break;
            }
        }
    },

    _onCarrierClick: async function (ev) {
        //----on carrier click
        const radio = this.$el.find('.o_delivery_carrier_select')[0].firstElementChild
        if (radio.checked && !this._shouldDisplayPickupLocations(ev) && !this.forceClickCarrier) {
            return;
        }
        this.forceClickCarrier = false;
        this._disablePayButton();
        this._showLoading(radio);
        radio.checked = true;
        await this._onClickShowLocations(ev);
        await this._handleCarrierUpdateResult(radio);
        this._disablePayButtonNoPickupPoint(ev);
    },
    /**
     * Handles the result of the carrier update and updates the relevant elements on the order summary.
     * Updates the carrier badge, delivery amount, untaxed amount, tax amount, total amount, and shipping cost (if applicable).
     * @param {Object} result - The result of the carrier update.
     */
    _enableButton(status){
    //----enabling payment button
        var PayButton = this.$el.find('[name="o_payment_submit_button"]');
        PayButton.removeAttr('disabled');
    },
    /**
     * Handles the change event on the address selection element.
     * Determines whether to show the available shipping countries for billing or all countries.
     * Updates the visibility and disabled state of the country and state selection elements accordingly.
     * @param {Event} ev - The change event.
     */
    _onSetAddress: function (ev) {
        var value = $(ev.currentTarget).val();
        var $providerFree = this.$el.find('select[name="country_id"]:not(.o_provider_restricted), select[name="state_id"]:not(.o_provider_restricted)');
        var $providerRestricted = this.$el.find('select[name="country_id"].o_provider_restricted, select[name="state_id"].o_provider_restricted');
        if (value === 0) {
            // Ship to the same address: only show shipping countries available for billing
            $providerFree.hide().attr('disabled', true);
            $providerRestricted.show().attr('disabled', false).change();
        } else {
            // Create a new address: show all countries available for billing
            $providerFree.show().attr('disabled', false).change();
            $providerRestricted.hide().attr('disabled', true);
        }
    },
});
