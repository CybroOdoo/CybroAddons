/** @odoo-module */
import { AbstractAwaitablePopup } from "@point_of_sale/app/popup/abstract_awaitable_popup";
import { _lt } from '@web/core/l10n/translation';
/**
 * CustomMessageInfoPopup component for displaying custom messages as an informational popup.
 * Inherits from AbstractAwaitablePopup.
 */
export class CustomMessageInfoPopup extends AbstractAwaitablePopup {
     static template = "pos_custom_message.CustomMessageInfoPopup";
     static defaultProps = {
         confirmText: _lt('Ok'),
         title: '',
         body: '',
         };
}
