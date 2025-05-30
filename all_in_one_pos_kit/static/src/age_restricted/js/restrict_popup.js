/** @odoo-module */

import { AbstractAwaitablePopup } from "@point_of_sale/app/popup/abstract_awaitable_popup";
import { registry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation";
    //Restrict Popup widget by extending the Abstract Awaitable popup widget
   export class RestrictPopup extends AbstractAwaitablePopup {
    //Defining the template of restrict popup
    static template = 'RestrictPopup';
    static defaultProps = {
        confirmText: 'Approve',
        cancelText: 'Reject',
        title: 'Confirm ?',
        body: '',
    };
    }
