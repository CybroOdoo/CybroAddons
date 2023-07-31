/** @odoo-module */
import AbstractAwaitablePopup from 'point_of_sale.AbstractAwaitablePopup';
import Registries from 'point_of_sale.Registries';
import { _lt } from "@web/core/l10n/translation";
/**
 * CustomMessageAlertPopup component for displaying custom messages as an alert popup.
 * Inherits from AbstractAwaitablePopup.
 */
class CustomMessageAlertPopup extends AbstractAwaitablePopup {}
CustomMessageAlertPopup.template = 'CustomMessageAlertPopup';
CustomMessageAlertPopup.defaultProps = {
    confirmText: _lt('Ok'),
    title: '',
    body: '',
};
// Add the CustomMessageAlertPopup component to the Point of Sale registries.
Registries.Component.add(CustomMessageAlertPopup);
return CustomMessageAlertPopup