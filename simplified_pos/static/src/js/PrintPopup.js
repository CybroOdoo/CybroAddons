/** @odoo-module **/
import { Component } from "@odoo/owl";
import { _lt, _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { AbstractAwaitablePopup } from "@point_of_sale/app/popup/abstract_awaitable_popup";
import { usePos } from "@point_of_sale/app/store/pos_hook";

export  class PrintPopup extends AbstractAwaitablePopup {
     static template = "PrintPopup";
         setup() {
            super.setup();
            this.pos = usePos();
        }
        async printReceipt() {
            console.log(this,'this,,,,,,,')
            /*create a new window to hold the content to be printed*/
            var printWindow = window.open('', 'PrintWindow', 'height=600,width=400');
            console.log(this.__owl__.bdom.el.innerHTML,'owl..........')
            /* get the HTML content of the popup, excluding the buttons*/
            var content = this.__owl__.bdom.el.innerHTML;
            printWindow.document.write(content);
            /* print the content and close the window*/
            printWindow.print();
            window.location.reload();
        }
        async cancel() {
            /*Orders are cancelled through the cancel function.*/
            window.location.reload();
        }
        get orderlines() {
            /*Selected order lines are passed to UI.*/
            var orderlines = this.pos.selectedOrder.orderlines
            var orderlinesList = []
            orderlines.forEach(function (orderlines) {
                var totalprice = orderlines.price * orderlines.quantity
                orderlinesList.push([orderlines.product.display_name, orderlines.quantity, orderlines.price, totalprice])
            })
            return orderlinesList;
        }
        get total() {
            /*Total is calculated and passed*/
            var total = 0
            var totalvalues = this.pos.selectedOrder.paymentlines
            totalvalues.forEach(function (totalvalues) {
                total = total + totalvalues.amount
            })
            return total;
        }
    }
