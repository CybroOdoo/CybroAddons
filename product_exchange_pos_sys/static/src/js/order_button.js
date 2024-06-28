/** @odoo-module **/
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
class OrderLineALLButton extends ProductScreen {
    static template = "OrderLineALL";
    setup() {
        super.setup();
    }
    async onClick() {
//      Order line button Onclick()
        let data = await this.orm.call('pos.order', 'get_pos_orders',[])
        await this.pos.showScreen('CustomOrderScreen', {
                orders: this.env.services.pos.pos_orders,
                data: data,
                pos: this.env.services.pos
            });
    }
}
ProductScreen.addControlButton({
    component: OrderLineALLButton,
});
