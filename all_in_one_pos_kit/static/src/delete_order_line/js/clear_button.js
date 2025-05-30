/**@odoo-module **/
import { _t } from "@web/core/l10n/translation";
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { useService } from "@web/core/utils/hooks";
import { Component } from "@odoo/owl";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { ConfirmPopup } from "@point_of_sale/app/utils/confirm_popup/confirm_popup";
/**
 * Represents a component to delete all order lines in the Point of Sale.
 * @extends Component
 */
export class DeleteOrderLines extends Component {
    static template = "pos_delete_orderline.OrderLineClearALL";
    /**
     * Set up the DeleteOrderLines component.
     * @override
     */
    setup() {
        this.pos = usePos();
        this.popup = useService("popup");
        this.notification = useService("pos_notification");
    }
    /**
     * Handle the click event to confirm and delete all order lines.
     * @async
     */
    async onClick() {
        var order = this.pos.get_order();
        var lines = order.get_orderlines();
        if (lines.length) {
            await this.popup.add(ConfirmPopup, {
                title: 'Clear Orders?',
                body: 'Are you sure you want to delete all orders from the cart?',
            }).then(({confirmed}) =>  {
                if (confirmed == true) {
                    lines.filter(line => line.get_product())
                        .forEach(line => order.removeOrderline(line));
                }else {
                    return false;
                }
            })
        }else{
            this.notification.add(_t("No Items to remove."), 3000);
        }
    }
}
/**
 * Adds the DeleteOrderLines component as a control button to the ProductScreen.
 */
ProductScreen.addControlButton({
    component: DeleteOrderLines,
});
