odoo.define('all_in_one_pos_kit.restrict_popup', function(require) {
    'use strict';
    const AbstractAwaitablePopup =
    require('point_of_sale.AbstractAwaitablePopup');
    const Registries = require('point_of_sale.Registries');
    const { _lt } = require('@web/core/l10n/translation');
    //Restrict Popup widget by extending the Abstract Awaitable popup widget
    class RestrictPopup extends AbstractAwaitablePopup {
    }
    //Defining the template of restrict popup
    RestrictPopup.template = 'RestrictPopup';
    RestrictPopup.defaultProps = {
        confirmText: _lt('Approve'),
        cancelText: _lt('Reject'),
        title: _lt('Confirm ?'),
        body: '',
    };
    Registries.Component.add(RestrictPopup);
    return RestrictPopup;
});
