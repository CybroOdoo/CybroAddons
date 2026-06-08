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
                    let title = _t("Error");
                    if (response.error_type === "limit_reached") {
                        title = _t("Delivery Limit");
                    } else if (response.error_type === "missing_date") {
                        title = _t("Missing Delivery Date");
                    }
                    self.dialog.add(ConfirmationDialog, {
                            title: title,
                            body: _t(response.error),
                        });
                    ev.currentTarget.value = ''; // Reset the selection
                }
            });
        }
    },

    _onDateChange: function (ev) {
        const deliveryDate = ev.currentTarget.value;
        const lineId = ev.currentTarget.dataset.lineId;
        if (deliveryDate && lineId) {
            rpc('/shop/cart/set_delivery_date', {
                'delivery_date': deliveryDate,
                'line_id': lineId,
            });
        }
    },
});