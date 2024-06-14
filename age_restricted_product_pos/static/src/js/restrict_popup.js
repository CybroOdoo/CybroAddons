/** @odoo-module */

import { AbstractAwaitablePopup } from "@point_of_sale/app/popup/abstract_awaitable_popup";
import { _t } from "@web/core/l10n/translation";

export class RestrictPopup extends AbstractAwaitablePopup{
    //Defining the template of restrict popup
     static template = "age_restricted_product_pos.RestrictPopup";
    static defaultProps = {
        confirmText: _t('Approve'),
        cancelText: _t('Reject'),
        title: _t('Confirm ?'),
        body: "",
    };
};
