/** @odoo-module **/
//Extended Component to add a button in pos session and for its working to scan barcode and show the products in the orderlines
import { _t } from 'web.core';
import PosComponent from 'point_of_sale.PosComponent';
import ProductScreen from "point_of_sale.ProductScreen";
import Registries from "point_of_sale.Registries";
import { useListener } from "@web/core/utils/hooks";
var rpc = require('web.rpc');

class ReturnProductButton extends PosComponent {
    setup() {
        super.setup();
        useListener('click', this.onClick);
        this.pos = this.env.pos
        this.pos_orders = null
        this.pos_orderline = []
        this.pos.receipt_barcode_reader= null
    }
    async onClick() {
       const { confirmed, payload: inputbarcode} = await this.showPopup(
            'BarcodePopup', {
                title: _t('Scan barcode'),
                startingValue:  this.env.pos.get_order().get_barcode_reader()
            });
    }
}
ReturnProductButton.template = 'ReturnProduct';
ProductScreen.addControlButton({
        component: ReturnProductButton,
        condition: function() {
            return true;
        },
    });
Registries.Component.add(ReturnProductButton);
