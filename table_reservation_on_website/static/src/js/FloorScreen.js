/** @odoo-module **/
import FloorScreen from 'pos_restaurant.FloorScreen';
import rpc from 'web.rpc';
import ajax from 'web.ajax';
import Registries from 'point_of_sale.Registries';
const TableFloor = (FloorScreen) =>
class extends FloorScreen {
/**
For getting active tables
**/
     get activeTables() {
        var self = this
        ajax.jsonRpc('/active/floor/tables','call',{
            'floor_id' : self.activeFloor.id,
        }).then( function(data){
            self.tables = data
        });
        self.activeFloor.tables.forEach(function(record){
            for(let rec in self.tables){
                    if(self.tables[rec] == record['id']){
                        let new_tables = self.activeFloor.tables.filter(item => item['id'] !== self.tables[rec])
                        self.activeFloor.tables = new_tables;
                    }
            }
        });
        return self.activeFloor.tables;
    }
}
Registries.Component.extend(FloorScreen, TableFloor);
