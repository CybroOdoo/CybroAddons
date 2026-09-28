/** @odoo-module */
import { Component } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";
/**
* This class represents a custom popup in the Point of Sale.
* It extends the AbstractAwaitablePopup class.
*/
export class ErrorPopup extends Component {
   static template = "pos_keyboard_shortcut.ErrorPopup";
   static defaultProps = {
       cancelText: _t("cancel"),
       title: _t("WARNING"),
   };
}