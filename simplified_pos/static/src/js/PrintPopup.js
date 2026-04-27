/** @odoo-module **/
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { Dialog } from "@web/core/dialog/dialog";
import { Component, reactive } from "@odoo/owl";

export  class PrintPopup extends Component {
     static template = "PrintPopup";
     static components = { Dialog };
         setup() {
            super.setup();
            this.pos = usePos();
        }
        async printReceipt() {
            /*create a new window to hold the content to be printed*/
            var printWindow = window.open('', 'PrintWindow', 'height=600,width=400');
            /* get the HTML content of the popup, excluding the buttons*/
            var content = this.__owl__.bdom.bdom.el.innerHTML;
            printWindow.document.write(content);
            /* print the content and close the window*/
            printWindow.print();
            printWindow.close();
            window.location.reload();
        }
        async cancel() {
            /*Orders are cancelled through the cancel function.*/
            window.location.reload();
        }
        get orderlines() {
           /*Selected order lines are passed to UI.*/
            var orderlines = this.pos.selectedOrder.lines
            var orderlinesList = []
            orderlines.forEach(function (orderlines) {
                var totalprice = orderlines.price_subtotal_incl
                orderlinesList.push([orderlines.product_id.display_name, orderlines.qty, orderlines.price_subtotal_incl, totalprice])
            })
            return orderlinesList;
        }
        get total() {
          /*Total is calculated and passed*/
            var total = 0
            var totalvalues = this.pos.selectedOrder.payment_ids
            totalvalues.forEach(function (totalvalues) {
                total = total + totalvalues.amount
            })
            return total;
        }
    }
