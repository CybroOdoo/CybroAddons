/** @odoo-module */
import AbstractAwaitablePopup from 'point_of_sale.AbstractAwaitablePopup';
import Registries from 'point_of_sale.Registries';
import {
    _lt
} from "@web/core/l10n/translation";
/**
 * CustomMessageWarnPopup component for displaying custom messages as a warning popup.
 * Inherits from AbstractAwaitablePopup.
 */
class CustomMessageWarnPopup extends AbstractAwaitablePopup {}
CustomMessageWarnPopup.template = 'CustomMessageWarnPopup';
CustomMessageWarnPopup.defaultProps = {
    confirmText: _lt('Ok'),
    title: '',
    body: '',
};
// Add the CustomMessageWarnPopup component to the Point of Sale registries.
Registries.Component.add(CustomMessageWarnPopup);
return CustomMessageWarnPopup;