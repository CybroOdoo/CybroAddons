odoo.define('pos_custom_message.CustomMessageAlertPopup', function (require) {
    "use strict";

    const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
    const Registries = require('point_of_sale.Registries');
    const { _t } = require('web.core');
    /**
     * CustomMessageAlertPopup component for displaying custom messages as an alert popup.
     * Inherits from AbstractAwaitablePopup.
    */
    class CustomMessageAlertPopup extends AbstractAwaitablePopup {}

    CustomMessageAlertPopup.template = 'CustomMessageAlertPopup';
    CustomMessageAlertPopup.defaultProps = {
        confirmText: _t('Ok'),
        title: _t(''),
        body: '',
    };

    Registries.Component.add(CustomMessageAlertPopup);

    return CustomMessageAlertPopup;
});
