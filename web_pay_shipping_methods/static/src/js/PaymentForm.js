/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { PaymentForm } from "@payment/interactions/payment_form";
import { rpc } from "@web/core/network/rpc";

patch(PaymentForm.prototype, {
    setup() {
        super.setup();
        this._setupDeliveryMethodListeners();

        const checkedRadio = document.querySelector('input[name="o_payment_radio"]:checked');
        if (checkedRadio) {
            const providerId = checkedRadio.dataset.providerId;
            if (providerId) {
                this._processProviderShippingUpdate(providerId);
            }
        }
    },

    _setupDeliveryMethodListeners() {
        document.addEventListener('change', async (ev) => {
            if (ev.target && ev.target.name === 'o_delivery_radio') {
                await this._handleDeliveryMethodChange(ev.target);
            }
        });
    },

    async _handleDeliveryMethodChange(radio) {
        if (radio.disabled) {
            return;
        }

        try {
            const result = await rpc('/shop/set_delivery_method', {
                dm_id: radio.dataset.dmId
            });

            this._updateCartSummary(result);

        } catch (error) {
            // silently fail (or handle if needed)
        }
    },

    async selectPaymentOption(ev) {
        await super.selectPaymentOption(ev);
        const providerId = ev.target.dataset['providerId'];
        await this._processProviderShippingUpdate(providerId);
    },

    async _processProviderShippingUpdate(providerId) {
        const carriers = await rpc('/web/dataset/call_kw/payment.provider/read', {
            model: 'payment.provider',
            method: 'read',
            args: [[parseInt(providerId)], ['delivery_carrier_ids']],
            kwargs: {}
        });

        const allDeliveryElements = document.querySelectorAll('[id^="delivery_method_"]');
        allDeliveryElements.forEach(element => {
            element.classList.add('d-none');
            const radioButton = element.querySelector('input[type="radio"]');
            if (radioButton) {
                radioButton.disabled = true;
                radioButton.checked = false;
                const container = radioButton.closest('[name="o_delivery_method"]');
                if (container) {
                    container.classList.add('text-muted');
                }
            }
        });

        if (carriers[0].delivery_carrier_ids.length > 0) {
            const visibleRadios = [];

            carriers[0].delivery_carrier_ids.forEach((id) => {
                if (id) {
                    const deliveryMethod = '#delivery_method_' + id;
                    const deliveryElement = $(deliveryMethod)[0];

                    if (deliveryElement) {
                        deliveryElement.classList.remove('d-none');

                        const radioButton = deliveryElement.querySelector('input[type="radio"]');
                        if (radioButton) {
                            radioButton.disabled = false;

                            const container = radioButton.closest('[name="o_delivery_method"]');
                            if (container) {
                                container.classList.remove('text-muted');
                            }

                            visibleRadios.push(radioButton);
                        }
                    }
                }
            });

            const noShippingMethodElement = $('#NoShippingMethod')[0];
            if (noShippingMethodElement) {
                noShippingMethodElement.classList.add('d-none');
            }

            if (!document.querySelector('input[name="o_delivery_radio"]:checked') && visibleRadios.length > 0) {
                const firstRadio = visibleRadios[0];
                firstRadio.checked = true;
                firstRadio.dispatchEvent(new Event('change', { bubbles: true }));

                const result = await rpc('/shop/set_delivery_method', {
                    dm_id: firstRadio.dataset.dmId
                });
                this._updateCartSummary(result);
            }

            await this._fetchDeliveryRatesAndSelectFirst(visibleRadios);

        } else {
            const noShippingMethodElement = $('#NoShippingMethod')[0];
            if (noShippingMethodElement) {
                noShippingMethodElement.classList.remove('d-none');
            }
        }
    },

    async _fetchDeliveryRatesAndSelectFirst(visibleRadios) {
        for (const radio of visibleRadios) {
            const container = radio.closest('[name="o_delivery_method"]');
            const badge = container?.querySelector('.o_wsale_delivery_price_badge');

            if (badge) {
                this._showLoadingBadge(badge);

                try {
                    const rateData = await rpc('/shop/get_delivery_rate', {
                        dm_id: radio.dataset.dmId
                    });

                    this._updateDeliveryBadge(badge, radio, rateData, container);

                    if (rateData.success && !document.querySelector('input[name="o_delivery_radio"]:checked')) {
                        radio.checked = true;
                        radio.dispatchEvent(new Event('change', { bubbles: true }));

                        const result = await rpc('/shop/set_delivery_method', {
                            dm_id: radio.dataset.dmId
                        });

                        this._updateCartSummary(result);

                        window.dispatchEvent(new CustomEvent('deliveryMethodsUpdated', {
                            detail: result
                        }));
                    }

                } catch (error) {
                    badge.textContent = 'Error';
                }
            }
        }
    },

    _showLoadingBadge(badge) {
        while (badge.firstChild) {
            badge.removeChild(badge.lastChild);
        }
        const loadingElement = document.createElement('i');
        loadingElement.classList.add('fa', 'fa-circle-o-notch', 'fa-spin', 'center');
        badge.appendChild(loadingElement);
    },

    _updateDeliveryBadge(badge, radio, rateData, container) {
        if (rateData.success) {
            if (rateData.compute_price_after_delivery) {
                badge.textContent = "Computed after delivery";
            } else if (rateData.is_free_delivery) {
                badge.textContent = "Free";
            } else {
                badge.innerHTML = rateData.amount_delivery;
            }
            radio.disabled = false;
            container.classList.remove('text-muted');
        } else {
            badge.textContent = rateData.error_message || 'Error';
            radio.disabled = true;
            container.classList.add('text-muted');
        }
    },

    _updateCartSummary(result) {
        const cartSummaries = document.querySelectorAll('#o_cart_summary_offcanvas, .o_total_card');

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
                const noDeliveryMsg = amountDelivery.querySelector('span[name="o_message_no_dm_set"]');
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

            amountTotal.forEach(total => {
                total.innerHTML = result.amount_total;
            });
        });
    },
});
