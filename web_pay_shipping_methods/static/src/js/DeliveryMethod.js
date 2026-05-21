/** @odoo-module **/

import { rpc } from "@web/core/network/rpc";
import { _t } from '@web/core/l10n/translation';
import { patch } from "@web/core/utils/patch";
import { Checkout } from "@website_sale/interactions/checkout";

// Patch Checkout to listen for delivery method updates
patch(Checkout.prototype, {
    setup() {
        super.setup();

        if (!this.mainButton) {
            this.mainButton = document.querySelector(
                'button[name="o_payment_submit_button"]'
            );
        }

        this._onDeliveryMethodUpdated = this._onDeliveryMethodUpdated.bind(this);
        window.addEventListener(
            'deliveryMethodsUpdated',
            this._onDeliveryMethodUpdated
        );
    },

    destroy() {
        window.removeEventListener(
            'deliveryMethodsUpdated',
            this._onDeliveryMethodUpdated
        );
        if (super.destroy) {
            super.destroy();
        }
    },

    _onDeliveryMethodUpdated(ev) {
        if (ev.detail) {
            this._updateCartSummary(ev.detail);
        }
        this._enableMainButton();
    },

    async selectDeliveryMethod(ev) {
        const checkedRadio = ev.currentTarget;

        if (checkedRadio.disabled) {
            return;
        }

        this._disableMainButton();
        this._hidePickupLocation();

        await this._updateDeliveryMethod(checkedRadio);

        this._enableMainButton();
        await this._showPickupLocation(checkedRadio);
    },

    async _prepareDeliveryMethods() {
        this.dmRadios = Array.from(
            document.querySelectorAll('input[name="o_delivery_radio"]')
        );

        const visibleRadios = this.dmRadios.filter(radio => {
            const container = radio.closest('.delivery_method_list');
            return container && !container.classList.contains('d-none');
        });

        if (visibleRadios.length > 0) {
            const checkedRadio = visibleRadios.find(radio => radio.checked);
            this._disableMainButton();

            if (checkedRadio) {
                await this._updateDeliveryMethod(checkedRadio);
                this._enableMainButton();
            }
        }

        const uncheckedVisibleRadios = visibleRadios.filter(
            radio => !radio.checked
        );

        await Promise.all(uncheckedVisibleRadios.map(async radio => {
            this._showLoadingBadge(radio);
            const rateData = await this._getDeliveryRate(radio);
            this._updateAmountBadge(radio, rateData);
        }));
    },

    async _updateDeliveryMethod(radio) {
        this._showLoadingBadge(radio);

        const result = await this._setDeliveryMethod(radio.dataset.dmId);

        this._updateAmountBadge(radio, result);
        this._updateCartSummary(result);

        return result;
    },

    async _showPickupLocation(radio) {
        if (!radio.dataset.isPickupLocationRequired || radio.disabled) {
            return;
        }

        const deliveryMethodContainer =
            this._getDeliveryMethodContainer(radio);
        const pickupLocation =
            deliveryMethodContainer.querySelector('[name="o_pickup_location"]');

        const editPickupLocationButton = pickupLocation.querySelector(
            'span[name="o_pickup_location_selector"]'
        );

        if (editPickupLocationButton.dataset.pickupLocationData) {
            await this._setPickupLocation(
                editPickupLocationButton.dataset.pickupLocationData
            );
        }

        pickupLocation.classList.remove('d-none');
    },

    _hidePickupLocation() {
        const pickupLocations = document.querySelectorAll(
            '[name="o_pickup_location"]:not(.d-none)'
        );
        pickupLocations.forEach(el => el.classList.add('d-none'));
    },

    async _setPickupLocation(pickupLocationData) {
        await rpc('/website_sale/set_pickup_location', {
            pickup_location_data: pickupLocationData,
        });
    },

    _updateAmountBadge(radio, rateData) {
        const deliveryPriceBadge = this._getDeliveryPriceBadge(radio);

        if (rateData.success) {
            if (rateData.compute_price_after_delivery) {
                deliveryPriceBadge.textContent = _t("Computed after delivery");
            } else if (rateData.is_free_delivery) {
                deliveryPriceBadge.textContent = _t("Free");
            } else {
                deliveryPriceBadge.innerHTML = rateData.amount_delivery;
            }
            this._toggleDeliveryMethodRadio(radio);
        } else {
            deliveryPriceBadge.textContent = rateData.error_message;
            this._toggleDeliveryMethodRadio(radio, true);
        }
    },

    _toggleDeliveryMethodRadio(radio, disable = false) {
        const container = this._getDeliveryMethodContainer(radio);
        radio.disabled = disable;

        if (disable) {
            container.classList.add('text-muted');
        } else {
            container.classList.remove('text-muted');
        }
    },

    _updateCartSummary(result) {
        const cartSummaries = document.querySelectorAll(
            '#o_cart_summary_offcanvas, .o_total_card'
        );

        cartSummaries.forEach(summaryContainer => {
            const amountDelivery = summaryContainer.querySelector(
                '#order_delivery .monetary_field, tr[name="o_order_delivery"] .monetary_field'
            );

            const amountUntaxed = summaryContainer.querySelector(
                '#order_total_untaxed .monetary_field, tr[name="o_order_total_untaxed"] .monetary_field'
            );

            const amountTax = summaryContainer.querySelector(
                '#order_total_taxes .monetary_field, tr[name="o_order_total_taxes"] .monetary_field'
            );

            const amountTotal = summaryContainer.querySelectorAll(
                '#order_total .monetary_field, tr[name="o_order_total"] .monetary_field, #amount_total_summary.monetary_field'
            );

            if (amountDelivery) {
                const deliveryRow = amountDelivery.closest('tr');
                if (deliveryRow) {
                    deliveryRow.classList.remove('d-none');
                }

                const noDeliveryMsg = amountDelivery.querySelector(
                    'span[name="o_message_no_dm_set"]'
                );
                if (noDeliveryMsg) {
                    noDeliveryMsg.classList.add('d-none');
                }

                amountDelivery.innerHTML = result.amount_delivery;
            }

            if (amountUntaxed) {
                amountUntaxed.innerHTML = result.amount_untaxed;
            }

            if (amountTax) {
                amountTax.innerHTML = result.amount_tax;
            }

            amountTotal.forEach(el => {
                el.innerHTML = result.amount_total;
            });
        });

        const standaloneDelivery = document.querySelector(
            '#order_delivery .monetary_field'
        );
        if (
            standaloneDelivery &&
            !standaloneDelivery.closest(
                '.o_total_card, #o_cart_summary_offcanvas'
            )
        ) {
            standaloneDelivery.innerHTML = result.amount_delivery;
        }
    },

    async _setDeliveryMethod(dmId) {
        return await rpc('/shop/set_delivery_method', { dm_id: dmId });
    },

    async _getDeliveryRate(radio) {
        return await rpc('/shop/get_delivery_rate', {
            dm_id: radio.dataset.dmId,
        });
    },

    _disableMainButton() {
        this.mainButton?.classList.add('disabled');
    },

    _enableMainButton() {
        if (this._isDeliveryMethodReady()) {
            this.mainButton?.classList.remove('disabled');
        }
    },

    _showLoadingBadge(radio) {
        const badge = this._getDeliveryPriceBadge(radio);
        this._clearElement(badge);
        badge.appendChild(this._createLoadingElement());
    },

    _clearElement(el) {
        while (el.firstChild) {
            el.removeChild(el.lastChild);
        }
    },

    _createLoadingElement() {
        const el = document.createElement('i');
        el.classList.add('fa', 'fa-circle-o-notch', 'fa-spin', 'center');
        return el;
    },

    _isDeliveryMethodReady() {
        const visibleRadios = Array.from(
            document.querySelectorAll('input[name="o_delivery_radio"]')
        ).filter(radio => {
            const container = radio.closest('.delivery_method_list');
            return container && !container.classList.contains('d-none');
        });

        if (visibleRadios.length === 0) {
            return true;
        }

        const checkedRadio = visibleRadios.find(radio => radio.checked);
        return (
            checkedRadio &&
            !checkedRadio.disabled &&
            !this._isPickupLocationMissing(checkedRadio)
        );
    },

    _getDeliveryPriceBadge(radio) {
        const container = this._getDeliveryMethodContainer(radio);
        return container.querySelector('.o_wsale_delivery_price_badge');
    },

    _isPickupLocationMissing(radio) {
        if (!this._isPickupLocationRequired(radio)) return false;
        const container = this._getDeliveryMethodContainer(radio);
        return !container.querySelector(
            'span[name="o_pickup_location_selector"]'
        ).dataset.locationId;
    },

    _getDeliveryMethodContainer(el) {
        return el.closest('[name="o_delivery_method"]');
    },

    _isPickupLocationRequired(radio) {
        return Boolean(radio.dataset.isPickupLocationRequired);
    },
});
