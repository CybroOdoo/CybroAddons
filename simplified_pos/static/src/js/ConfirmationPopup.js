/** @odoo-module **/
import { Dialog } from "@web/core/dialog/dialog";
import { useService } from "@web/core/utils/hooks";
import  { Component, reactive } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";
import { PrintPopup } from "@simplified_pos/js/PrintPopup";


export class ConfirmationPopup extends Component {
     static template = "ConfirmationPopup";
     static components = { Dialog };
     setup() {
        super.setup();
        this.popup = useService("dialog");
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
