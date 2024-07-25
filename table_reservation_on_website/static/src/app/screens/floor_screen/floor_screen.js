/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { FloorScreen } from "@pos_restaurant/app/floor_screen/floor_screen";
import { jsonrpc } from "@web/core/network/rpc_service";
patch(FloorScreen.prototype, {
    async setup() {
        super.setup(...arguments);
        await this.fetchActiveTables();
    },
    /**
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
    }
});
