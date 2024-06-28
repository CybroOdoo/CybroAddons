/** @odoo-module */
import { AbstractAwaitablePopup } from "@point_of_sale/app/popup/abstract_awaitable_popup";
import { _t } from "@web/core/l10n/translation";

//Extending AbstractAwaitablePopup to create a popup
export class MultiImagePopup extends AbstractAwaitablePopup {
    static template = "multi_image_in_pos.MultiImagePopup"
    static defaultProps = {
        cancelText: _t("Close"),
    };
}