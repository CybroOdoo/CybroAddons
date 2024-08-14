/** @odoo-module */
import { AbstractAwaitablePopup } from "@point_of_sale/app/popup/abstract_awaitable_popup";
import { _t } from "@web/core/l10n/translation";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { useRef, onMounted } from "@odoo/owl";
/**
* This class represents a custom popup in the Point of Sale.
* It extends the AbstractAwaitablePopup class.
*/
export class CustomButtonPopup extends AbstractAwaitablePopup {
   static template = "pos_traceability_validation.CustomButtonPopup";
   static defaultProps = {
       closePopup: _t("Cancel"),
       body: _t("Product quantity Exceeding the allowed lot quantity"),
       title: _t("Exception"),
   };
}