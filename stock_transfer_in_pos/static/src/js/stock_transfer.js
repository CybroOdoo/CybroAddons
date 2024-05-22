/** @odoo-module **/
/**
     * This file is used to register the a new button for stock transfer
*/

import { Component } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { _t } from "@web/core/l10n/translation";
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";
import { CreateTransferPopup } from "./transfer_create_popup";


class StockTransferButton extends Component {
    static template = 'StockTransferButton';
    setup() {
        this.orm = useService("orm");
        this.pos = usePos();
    }
    async onClick() {
        // This will show a popup to transfer stock with selected products and customer
        var self = this
        if ((this.pos.get_order().orderlines) == 0) {
            this.pos.popup.add(ErrorPopup, {
                title: _t("Select Products"),
                body: _t(
                    "Please Select at least one product for transferring"
                ),
            });
        } else {
            await this.orm.call(
                "pos.config", "get_stock_transfer_list", [], {}
            ).then(function(result) {
                self.pos.popup.add(CreateTransferPopup, {
                    data: result
                });
            })
        }
    }
}
ProductScreen.addControlButton({
    component: StockTransferButton,
    condition: () => true
})