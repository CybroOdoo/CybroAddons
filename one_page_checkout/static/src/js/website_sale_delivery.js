odoo.define('one_page_checkout.checkout', function (require) {
'use strict';

var core = require('web.core');
var publicWidget = require('web.public.widget');

var _t = core._t;
var concurrency = require('web.concurrency');
var dp = new concurrency.DropPrevious();

publicWidget.registry.OPCWebsiteSaleDelivery = publicWidget.Widget.extend({
    selector: '.single_pg_checkout_layout',
    events: {
        'change select[name="shipping_id"]': '_onSetAddress',
        'click #delivery_carrier .o_delivery_carrier_select': '_onCarrierClick',
    },
    /**
     * @override
     */
    start: function () {
        var self = this;
        var $carriers = $('#delivery_carrier input[name="delivery_type"]');
        // Asynchronously retrieve every carrier price
        _.each($carriers, function (carrierInput, k) {
            self._showLoading($(carrierInput));
            self._rpc({
                route: '/shop/carrier_rate_shipment',
                params: {
                    'carrier_id': carrierInput.value,
                },
            }).then(self._handleCarrierUpdateResultBadge.bind(self));
        });
        return this._super.apply(this, arguments);
    },
    /**
     * @private
     * @param {jQuery} $carrierInput
     */
    _showLoading: function ($carrierInput) {
        $carrierInput.siblings('.o_wsale_delivery_badge_price').empty();
        $carrierInput.siblings('.o_wsale_delivery_badge_price').append('<span class="fa fa-circle-o-notch fa-spin"/>');
    },
    /**
     * Update the total cost according to the selected shipping method
     *
     * @private
     * @param {float} amount : The new total amount of to be paid
     */
    _updateShippingCost: function(amount){
        core.bus.trigger('update_shipping_cost', amount);
    },
    /**
     * Handles the result of the carrier update and updates the relevant elements on the order summary.
     * Updates the carrier badge, delivery amount, untaxed amount, tax amount, total amount, and shipping cost (if applicable).
     * @param {Object} result - The result of the carrier update.
     */
    _handleCarrierUpdateResult: function (result) {
        this._handleCarrierUpdateResultBadge(result);
        var $amountDelivery = $('#order_delivery .monetary_field');
        var $amountUntaxed = $('#order_total_untaxed .monetary_field');
        var $amountTax = $('#order_total_taxes .monetary_field');
        var $amountTotal = $('#order_total .monetary_field, #amount_total_summary.monetary_field');

        if (result.status === true) {
            $amountDelivery.html(result.new_amount_delivery);
            $amountUntaxed.html(result.new_amount_untaxed);
            $amountTax.html(result.new_amount_tax);
            $amountTotal.html(result.new_amount_total);
        } else {
            $amountDelivery.html(result.new_amount_delivery);
            $amountUntaxed.html(result.new_amount_untaxed);
            $amountTax.html(result.new_amount_tax);
            $amountTotal.html(result.new_amount_total);
        }
        if (result.new_amount_total_raw !== undefined) {
            this._updateShippingCost(result.new_amount_total_raw);
        }
    },
    /**
     * Handles the result of the carrier update and updates the carrier badge accordingly.
     * Updates the badge text and styling based on the result status and amount.
     * @param {Object} result - The result of the carrier update.
     */
    _handleCarrierUpdateResultBadge: function (result) {
        var $carrierBadge = $('#delivery_carrier input[name="delivery_type"][value=' + result.carrier_id + '] ~ .o_wsale_delivery_badge_price');

        if (result.status === true) {
            // If free delivery (`free_over` field), show 'Free', not '$0'
            if (result.is_free_delivery) {
                $carrierBadge.text(_t('Free'));
            } else {
                $carrierBadge.html(result.new_amount_delivery);
            }
            $carrierBadge.removeClass('o_wsale_delivery_carrier_error');
        } else {
            $carrierBadge.addClass('o_wsale_delivery_carrier_error');
            $carrierBadge.text(result.error_message);
        }
    },
    /**
     * Handles the click event on a carrier element.
     * Updates the selected carrier by sending an RPC request to update the carrier.
     * Shows a loading indicator while the request is being processed.
     * @param {Event} ev - The click event.
     */
    _onCarrierClick: function (ev) {
        var $radio = $(ev.currentTarget).find('input[type="radio"]');
        this._showLoading($radio);
        $radio.prop("checked", true);
        dp.add(this._rpc({
            route: '/shop/update_carrier',
            params: {
                carrier_id: $radio.val(),
            },
        })).then(this._handleCarrierUpdateResult.bind(this));
    },
    /**
     * Handles the change event on the address selection element.
     * Determines whether to show the available shipping countries for billing or all countries.
     * Updates the visibility and disabled state of the country and state selection elements accordingly.
     * @param {Event} ev - The change event.
     */
    _onSetAddress: function (ev) {
        var value = $(ev.currentTarget).val();
        var $providerFree = $('select[name="country_id"]:not(.o_provider_restricted), select[name="state_id"]:not(.o_provider_restricted)');
        var $providerRestricted = $('select[name="country_id"].o_provider_restricted, select[name="state_id"].o_provider_restricted');
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
});
