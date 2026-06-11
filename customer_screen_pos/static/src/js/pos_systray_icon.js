/** @odoo-module */
import { Navbar } from "@point_of_sale/app/navbar/navbar";
import { rpc } from "@web/core/network/rpc";
import { patch } from "@web/core/utils/patch";

patch(Navbar.prototype, {
    setup() {
        super.setup();
    },
    async openCustomerDisplay(){
       var self = this
       var total = 0
       var totalvalues = this.pos.selectedOrder.lines
           totalvalues.forEach(function (totalvalues) {
                total = total + (totalvalues.price_subtotal_incl)
           })
           var orderlines = this.pos.selectedOrder.lines
           var orderlinelist = [];
           orderlines.forEach(function(orderline) {
               if (!orderlinelist.includes(orderline.product_id.display_name)) {
                   orderlinelist.push({
                       'id' : orderline.product_id.id,
                       'name' : orderline.product_id.display_name,
                       'price' : (orderline.price_subtotal_incl),
                       'qty' : orderline.qty,
                       'session': self.pos.selectedOrder.session_id.id,
                       'partner_id': self.pos.selectedOrder.partner_id ? self.pos.selectedOrder.partner_id.id : null,
                       'order_name': self.pos.selectedOrder.name,
                       'total': total
                   });

               }
           });
           if (this.pos.res_setting && this.pos.res_setting.allow_customer_screen) {
            const encodedResult = await rpc('/add/my/review', {
                'orderlinelist': orderlinelist,
                'total': total
            });
            const response = await fetch("/customer/screen/");
            const data = await response.text();
            const modifiedData = data.replace('<body>', '<body>' + encodedResult);

            const newWindow = window.open("", 'Customer Display Screen');
            newWindow.document.open();
            newWindow.document.write(modifiedData);
            newWindow.document.close();
        } else {
            await super.openCustomerDisplay();
        }

        return this.pos.selectedOrder;
    }
});
