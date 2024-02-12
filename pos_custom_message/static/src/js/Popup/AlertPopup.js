/** @odoo-module */
import { AbstractAwaitablePopup } from "@point_of_sale/app/popup/abstract_awaitable_popup";
import { _lt } from '@web/core/l10n/translation';
/**
 * CustomMessageAlertPopup component for displaying custom messages as an alert popup.
 * Inherits from AbstractAwaitablePopup.
 */
export class CustomMessageAlertPopup extends AbstractAwaitablePopup {
     static template = "pos_custom_message.CustomMessageAlertPopup";
     static defaultProps = {
         confirmText: _lt('Ok'),
         title: '',
         body: '',
         };
}
