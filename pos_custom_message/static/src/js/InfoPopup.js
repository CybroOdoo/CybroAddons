/** @odoo-module */
import AbstractAwaitablePopup from 'point_of_sale.AbstractAwaitablePopup';
import Registries from 'point_of_sale.Registries';
import {
    _lt
} from "@web/core/l10n/translation";

/**
 * CustomMessageInfoPopup component for displaying custom messages as an informational popup.
 * Inherits from AbstractAwaitablePopup.
 */
class CustomMessageInfoPopup extends AbstractAwaitablePopup {}
CustomMessageInfoPopup.template = 'CustomMessageInfoPopup';
CustomMessageInfoPopup.defaultProps = {
    confirmText: _lt('Ok'),
    title: '',
    body: '',
};
// Add the CustomMessageInfoPopup component to the Point of Sale registries.
Registries.Component.add(CustomMessageInfoPopup);
return CustomMessageInfoPopup;