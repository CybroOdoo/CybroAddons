odoo.define('pos_custom_message.CustomMessageWarnPopup', function (require) {
    "use strict";

    const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
    const Registries = require('point_of_sale.Registries');
    const { _t } = require('web.core');
    /**
     * CustomMessageWarnPopup component for displaying custom messages as warning popup.
     * Inherits from AbstractAwaitablePopup.
    */
    class CustomMessageWarnPopup extends AbstractAwaitablePopup {}

    CustomMessageWarnPopup.template = 'CustomMessageWarnPopup';
    CustomMessageWarnPopup.defaultProps = {
        confirmText: _t('Ok'),
        title: _t(''),
        body: '',
    };

    Registries.Component.add(CustomMessageWarnPopup);

    return CustomMessageWarnPopup;
});
