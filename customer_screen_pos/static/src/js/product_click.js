/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { rpc } from "@web/core/network/rpc";

patch(ProductScreen.prototype, {
    setup() {
        super.setup();
    },

    async addProductToOrder(product) {
        if (this.pos.res_setting && this.pos.res_setting.allow_product_click) {
            await super.addProductToOrder(product);

            let total = 0;
            const orderlines = this.pos.selectedOrder.lines;
            const orderlinelist = [];

            orderlines.forEach((orderline) => {
                total += orderline.price_subtotal_incl;

                if (!orderlinelist.some(ol => ol.id === orderline.product_id.id)) {
                    orderlinelist.push({
                        'id': orderline.product_id.id,
                        'name': orderline.product_id.display_name,
                        'price': orderline.price_subtotal_incl,
                        'qty': orderline.qty,
                        'session': this.pos.selectedOrder.session_id.id,
                        'partner_id': this.pos.selectedOrder.partner_id?.id || null,
                        'order_name': this.pos.selectedOrder.name,
                        'total': total
                    });
                }
            });

            const encodedResult = await rpc('/add/my/review', {
                orderlinelist: orderlinelist,
                total: total
            });

            const response = await fetch("/customer/screen/");
            const data = await response.text();
            const modifiedData = data.replace('<body>', '<body>' + encodedResult);

            const newWindow = window.open("", 'Customer Display Screen', 'height=500,width=900');
            newWindow.document.open();
            newWindow.document.write(modifiedData);
            newWindow.document.close();

            return this.pos.selectedOrder;
        } else {
            return await super.addProductToOrder(product);
        }
    }
});
