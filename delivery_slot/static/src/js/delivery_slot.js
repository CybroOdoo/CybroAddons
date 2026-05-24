/** @odoo-module */
import publicWidget from '@web/legacy/js/public/public_widget';
import { rpc } from '@web/core/network/rpc';
import { _t } from "@web/core/l10n/translation";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";

publicWidget.registry.websiteDeliverySlot = publicWidget.Widget.extend({
    selector: '.delivery_slot_div',
    events: {
        'change #slot_id': '_onSlotChange',
        'change #date': '_onDateChange',
    },
    init() {
        this.dialog = this.bindService("dialog");
    },

    _showSlotError: function (response) {
        let title = _t("Error");
        if (response.error_type === "limit_reached") {
            title = _t("Delivery Limit");
        } else if (response.error_type === "missing_date") {
            title = _t("Missing Delivery Date");
        } else if (response.error_type === "slot_unavailable") {
            title = _t("Delivery Slot");
        }
        this.dialog.add(ConfirmationDialog, {
            title: title,
            body: _t(response.error),
        });
    },

    _onSlotChange: function (ev) {
        const self = this;
        const deliverySlot = ev.currentTarget.value;
        const lineId = ev.currentTarget.dataset.lineId;
        if (deliverySlot && lineId) {
            rpc('/shop/cart/set_delivery_slot', {
                'delivery_slot': deliverySlot,
                'line_id': lineId,
            }).then(function (response) {
                if (response.error) {
                    self._showSlotError(response);
                    ev.currentTarget.value = ''; // Reset the selection
                }
            });
        }
    },

    _onDateChange: function (ev) {
        const self = this;
        const deliveryDate = ev.currentTarget.value;
        const lineId = ev.currentTarget.dataset.lineId;
        const $container = $(ev.currentTarget).closest('.delivery_slot_div');
        const $slotSelect = $container.find('#slot_id');
        const selectedOption = $("input[type='radio'][name='slot_hour']:checked").val();

        if (deliveryDate && lineId) {
            // Save the date first
            rpc('/shop/cart/set_delivery_date', {
                'delivery_date': deliveryDate,
                'line_id': lineId,
            }).then(function (response) {
                if (response.error) {
                    self._showSlotError(response);
                    $slotSelect.val('');
                    return;
                }
                // Then refresh the slot dropdown to show only available slots
                rpc('/shop/cart/get_available_slots', {
                    'date': deliveryDate,
                    'selected_option': selectedOption,
                }).then(function (result) {
                    if ($slotSelect.length) {
                        $slotSelect.empty();
                        $slotSelect.append(new Option('Select a slot', ''));
                        result.forEach(function (item) {
                            $slotSelect.append(new Option(item[1], item[0]));
                        });
                        $slotSelect.val('');
                    }
                });
            });
        }
    },
});

publicWidget.registry.websiteDeliverySlotCheckout = publicWidget.Widget.extend({
    selector: '.oe_website_sale',
    events: {
        'click a[href^="/shop/checkout"]': '_onCheckoutClick',
    },
    init() {
        this.dialog = this.bindService("dialog");
    },

    _onCheckoutClick: function (ev) {
        const deliverySlotDivs = this.el.querySelectorAll('.delivery_slot_div');
        for (const deliverySlotDiv of deliverySlotDivs) {
            const deliveryDate = deliverySlotDiv.querySelector('#date');
            const deliverySlot = deliverySlotDiv.querySelector('#slot_id');
            if (!deliveryDate || !deliveryDate.value ||
                    !deliverySlot || !deliverySlot.value) {
                ev.preventDefault();
                this.dialog.add(ConfirmationDialog, {
                    title: _t("Delivery Slot"),
                    body: _t("Please choose an available delivery date and slot before checkout."),
                });
                return;
            }
        }
    },
});
