odoo.define('simplified_pos.ConfirmationPopup', function(require) {
    'use strict';
    const {
        _lt
    } = require('@web/core/l10n/translation');
    const PaymentScreen = require('point_of_sale.PaymentScreen');
    const Registries = require('point_of_sale.Registries');
    const {
        useBus
    } = require('@web/core/utils/hooks');
    class ConfirmationPopup extends PaymentScreen {
        /*This is to add the workings inside confirmationPopup.*/
        setup() {
            super.setup();
            if (this.props.confirmKey) {
                useBus(this.env.posbus, `confirm-popup-${this.props.id}`, this.confirm);
            }
        }
        async confirm(ev) {
            /*Once confirm is clicked, the confirm function is activated,
             and a PrintPopup is displayed, confirming the order.*/
            this.showPopup("PrintPopup", {
                title: _lt('Print order'),
                confirmText: _lt('Print'),
                cancelText: this.env._t('Cancel'),
            });
            this.validateOrder(false)
        }
        async getPayload() {
            return null;
        }
        async cancel(ev) {
            /*Orders are cancelled through the cancel function.*/
            window.location.reload();
        }
        get nextScreen() {
            return !this.error ? 'ProductScreen' : 'ProductScreen';
        }
    }
    ConfirmationPopup.template = 'ConfirmationPopup';
    Registries.Component.add(ConfirmationPopup);
    return ConfirmationPopup;
});