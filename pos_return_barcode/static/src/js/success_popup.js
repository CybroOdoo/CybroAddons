/** @odoo-module **/
const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
import Registries from 'point_of_sale.Registries';
const { _lt } = require('@web/core/l10n/translation');

class SuccessPopup extends AbstractAwaitablePopup {
    setup() {
        super.setup();
        }
    }
SuccessPopup.template = 'pos_return_barcode.SuccessPopup';
SuccessPopup.defaultProps = {
    confirmText: _lt('Back'),
    title: '',
    body: '',
};
Registries.Component.add(SuccessPopup);
return SuccessPopup;
