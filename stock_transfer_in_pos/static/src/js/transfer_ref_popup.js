/** @odoo-module **/
/**
     * This file is used to register the a popup for viewing reference number of  transferred stock
*/

import { AbstractAwaitablePopup } from "@point_of_sale/app/popup/abstract_awaitable_popup";
import { _t } from "@web/core/l10n/translation";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { useRef } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

/**
 * This class represents a custom popup for capturing signatures in the Point of Sale.
 * It extends the AbstractAwaitablePopup class.
 */
export class TransferRefPopup extends AbstractAwaitablePopup {
    static template = "TransferRefPopup";
    static defaultProps = {
        confirmText: _t("Save"),
        cancelText: _t("Discard"),
        clearText: _t("Clear"),
        title: "",
        body: "",
    };
    setup() {
        super.setup();
    }
   stock_view() {
   // This will used to redirect the page to corresponding stock transfer
     var ref_id = this.props.data.id
     location.href = '/web#id='+ ref_id +'&&model=stock.picking&view_type=form'
   }
}
