odoo.define('pos_custom_message.CustomMessageInfoPopup', function (require) {
    "use strict";

    const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
    const Registries = require('point_of_sale.Registries');
    const { _t } = require('web.core');
    /**
     * CustomMessageInfoPopup component for displaying custom messages as an Information popup.
     * Inherits from AbstractAwaitablePopup.
    */
    class CustomMessageInfoPopup extends AbstractAwaitablePopup {}

    CustomMessageInfoPopup.template = 'CustomMessageInfoPopup';
    CustomMessageInfoPopup.defaultProps = {
        confirmText: _t('Ok'),
        title: _t(''),
        body: '',
    };

    Registries.Component.add(CustomMessageInfoPopup);

    return CustomMessageInfoPopup;
});
