/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { FloorScreen } from "@pos_restaurant/app/floor_screen/floor_screen";
import { jsonrpc } from "@web/core/network/rpc_service";
patch(FloorScreen.prototype, {
    setup() {
        super.setup(...arguments);
    },
    /**
    For payment validation in pos
    **/
    get activeTables() {
        var self = this
        jsonrpc('/active/floor/tables', {'floor_id' : self.activeFloor.id,
        }).then( function(data){
            self.tables = data
        });
        let reserved_tables = []
        for(let rec in self.tables){
            let new_tables = self.activeFloor.tables.find(item => item['id'] == self.tables[rec])
            if (new_tables){
                reserved_tables.push(new_tables)
            }
        }
        reserved_tables.forEach(function(record){
            record.reserved = true;
        });
        return self.activeFloor ? self.activeFloor.tables : null;
    }
});
