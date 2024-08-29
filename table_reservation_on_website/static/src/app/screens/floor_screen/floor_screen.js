/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { FloorScreen } from "@pos_restaurant/app/floor_screen/floor_screen";
import { jsonrpc } from "@web/core/network/rpc_service";
patch(FloorScreen.prototype, {
    async setup() {
        super.setup(...arguments);
        await this.fetchActiveTables();
    },
    /** onSelectTable
    For showing reserved tables in pos floor screen
    **/
    async fetchActiveTables() {
        try {
            var self = this
            const data = await jsonrpc('/active/floor/tables', { 'floor_id': this.activeFloor.id});
            this.tables = data;
            let reserved_tables = [];
            for (let rec in this.tables) {
                let new_table = this.activeFloor.tables.find(item => item['id'] == this.tables[rec]);
                if (new_table) {
                    reserved_tables.push(new_table);
                }
            }
            reserved_tables.forEach(function(record) {
                record.reserved = true;
            });
        } catch (error) {
            console.error('Error fetching active tables:', error);
        }
    },
    get activeTables() {
        this.fetchActiveTables();
        return this.activeFloor ? this.activeFloor.tables : null;
    },
    async onSelectTable(table, ev) {
//        if (table['reserved'] == true){
//            console.log("hello welcome", this.env.services.pos)
//            var data = await this.orm.call('table.reservation', 'add_payment', [table.id, table.floor.id])
//            const current_order = this.pos.get_order();
//            console.log("prod", current_order)
//            if (this.pos.get_order){
//            }
//            this.pos.get_order().add_product(product, {
//                quantity: 1,
//            });
//        }
        if (this.pos.isEditMode) {
            if (ev.ctrlKey || ev.metaKey) {
                this.state.selectedTableIds.push(table.id);
            } else {
                this.state.selectedTableIds = [];
                this.state.selectedTableIds.push(table.id);
            }
        } else {
            if (this.pos.orderToTransfer && table.order_count > 0) {
                const { confirmed } = await this.popup.add(ConfirmPopup, {
                    title: _t("Table is not empty"),
                    body: _t(
                        "The table already contains an order. Do you want to proceed and transfer the order here?"
                    ),
                    confirmText: _t("Yes"),
                });
                if (!confirmed) {
                    // We don't want to change the table if the transfer is not done.
                    table = this.pos.tables_by_id[this.pos.orderToTransfer.tableId];
                    this.pos.orderToTransfer = null;
                }
            }
            if (this.pos.orderToTransfer) {
                await this.pos.transferTable(table);
            } else {
                try {
                    await this.pos.setTable(table);
                } catch (e) {
                    if (!(e instanceof ConnectionLostError)) {
                        throw e;
                    }
                    // Reject error in a separate stack to display the offline popup, but continue the flow
                    Promise.reject(e);
                }
            }
            const order = this.pos.get_order();
            this.pos.showScreen(order.get_screen_data().name);
        }
    }
});
