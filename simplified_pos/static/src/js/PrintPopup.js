odoo.define('simplified_pos.PrintPopup', function(require) {
    'use strict';
    const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
    const Registries = require('point_of_sale.Registries');
    class PrintPopup extends AbstractAwaitablePopup {
        setup() {
            super.setup();
        }
        async printReceipt() {
            /*create a new window to hold the content to be printed*/
            var printWindow = window.open('', 'PrintWindow', 'height=600,width=400');
            /* get the HTML content of the popup, excluding the buttons*/
            var content = this.el.innerHTML;
            content = content.replace(/<footer[^>]*>[\s\S]*<\/footer>/gi, '');
            content = content.replace(/<header[^>]*>[\s\S]*<\/header>/gi, '');
            /* set the content of the new window to the modified HTML*/
            printWindow.document.write(content);
            /* print the content and close the window*/
            printWindow.print();
            window.location.reload();
        }
        async cancel() {
            /*Orders are cancelled through the cancel function.*/
            window.location.reload();
        }
        get company_details() {
            return this.env.pos
        }
        orderlines() {
            /*Selected order lines are passed to UI.*/
            var self = this;
            var orderlines = this.env.pos.get_order().orderlines
            var orderlinesList = []
            orderlines.forEach(function(orderlines) {
                var totalprice = orderlines.price * orderlines.quantity
                orderlinesList.push([orderlines.product.display_name, orderlines.quantity, orderlines.price, self.env.pos.currency.symbol+totalprice])
            })
            return orderlinesList;
        }
        get total() {
            /*Total is calculated and passed*/
            var total = 0
            var totalvalues = this.env.pos.get_order().get_paymentlines()
            totalvalues.forEach(function(totalvalues) {
                total = total + totalvalues.amount
            })
            return this.env.pos.currency.symbol + total;
        }
        get currentOrder() {
             /*Get current order*/
            return this.env.pos.get_order();
        }
        get paymentlines(){
             /*Get payment lines*/
            return this.currentOrder.get_paymentlines();
        }
        get total_rounded(){
             /*Get rounded amount */
            var total = this.currentOrder.get_total_with_tax() + this.currentOrder.get_rounding_applied()
            return  this.env.pos.currency.symbol+ " "+ total
        }

    }
    PrintPopup.template = 'PrintPopup';
    Registries.Component.add(PrintPopup);
    return PrintPopup;
});