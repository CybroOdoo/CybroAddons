/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { useService } from "@web/core/utils/hooks";
import { Component } from "@odoo/owl";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { MergeTablePopup } from "@pos_table_merge_orders/js/table_popup";

export class PosTableButton extends Component {
    static template = "pos_table_merge_orders.PosTableButton";

    setup() {
        this.pos = usePos();
        this.popup = useService("popup");
    }

//    function to merge the tableOrders
    async onClick() {
        const { confirmed, payload } = await this.popup.add(MergeTablePopup, {
           title: _t("Merge Table"),
           tables: this.pos.currentFloor.tables,
           confirmText: 'Merge',
           cancelText: 'Cancel',
           currentTable:this.pos.table.id,
       });

       if(confirmed){
            if(payload.length > 0){
                const order = this.pos.get_order();
                const orders = this.pos.get_order_list();
                const tableOrders = orders.filter(
                    (order) => payload.includes(order.tableId) && !order.finalized && order.tableId !== this.pos.table.id
                );
                tableOrders.forEach(item => {
                        item.orderlines.forEach(line => {
                            order.orderlines.add(line);
                        });
                        this.pos.removeOrder(item)
                });
            }
       }
    }
}

ProductScreen.addControlButton({
    component: PosTableButton,
    position: ["before", "OrderlineNoteButton"],
    condition: function () {
        return this.pos.config.allow_merge_tables;
    },
});
