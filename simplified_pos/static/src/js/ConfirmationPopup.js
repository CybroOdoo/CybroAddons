/** @odoo-module **/
import { Component } from "@odoo/owl";
import { _lt, _t } from "@web/core/l10n/translation";
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { registry } from "@web/core/registry";
import { AbstractAwaitablePopup } from "@point_of_sale/app/popup/abstract_awaitable_popup";
import { PrintPopup } from "@simplified_pos/js/PrintPopup";
import { useService } from "@web/core/utils/hooks";

export class ConfirmationPopup extends AbstractAwaitablePopup {
     static template = "ConfirmationPopup";
     setup() {
        super.setup();
        this.popup = useService("popup");
        }
    async confirm(ev) {
         this.popup.add(PrintPopup, {
            title: _t('Print order'),
            confirmText: _t('Print'),
            cancelText: _t('Cancel'),
        });
        this.env.bus.trigger('close-popup', {
            popupId: this.props.id,
            response: { confirmed: true, payload: await this.getPayload() },
        });
    }
    async getPayload() {
        return null;
    }
    cancel(ev) {
        window.location.reload();
    }
    get nextScreen() {
        return !this.error ? 'ProductScreen' : 'ProductScreen';
    }
}
