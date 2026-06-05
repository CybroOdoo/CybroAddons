/** @odoo-module */
import { AbstractAwaitablePopup } from "@point_of_sale/app/popup/abstract_awaitable_popup";
import { _lt } from '@web/core/l10n/translation';
/**
 * CustomMessageWarnPopup component for displaying custom messages as a warning popup.
 * Inherits from AbstractAwaitablePopup.
 */
export class CustomMessageWarnPopup extends AbstractAwaitablePopup {
     static template = "pos_custom_message.CustomMessageWarnPopup";
     static defaultProps = {
         confirmText: _lt('Ok'),
         title: '',
         body: '',
         };
}
