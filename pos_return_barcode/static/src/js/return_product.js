/** @odoo-module **/
//Extended Component to add a button in pos session and for its working to scan barcode and show the products in the orderline
import { _t } from "@web/core/l10n/translation";
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { useService } from "@web/core/utils/hooks";
import { Component } from "@odoo/owl";
import BarcodePopup from "@pos_return_barcode/js/barcode_popup"
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";
export class ReturnProductButton extends Component {
    static template = "point_of_sale.ReturnProduct";
    setup() {
        const pos = useService("pos");
        this.pos = pos
        this.pos_orders = null
        this.pos_orderline = []
        const { popup } = this.env.services;
        this.popup = popup;
        this.orm = useService("orm");
        this.pos.receipt_barcode_reader= null
    }
    async onClick() {
       const { confirmed, payload: inputbarcode} = await this.popup.add(
            BarcodePopup, {
                title: _t('Scan barcode'),
                startingValue: this.pos.get_order().get_barcode_reader()
            });
       if (confirmed) {
            var self = this
            this.pos.receipt_barcode_reader = inputbarcode;
            let barcode = inputbarcode.barcodeValue.toString().replace(/\n/g, "");
            await this.orm.call("pos.order", "action_barcode_return", ["", barcode]).then(function(result){
            if(result == false)
            {
                    self.popup.add(ErrorPopup, {
                        title: _t("Order not found"),
                        body: _t("Invalid data , Order could not be found"),
                    });
            }
            window.location.reload();
            })
       }
    }
}
ProductScreen.addControlButton({
    component: ReturnProductButton,
});
