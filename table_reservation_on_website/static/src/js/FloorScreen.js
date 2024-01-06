/** @odoo-module **/
import FloorScreen from 'pos_restaurant.FloorScreen';
import rpc from 'web.rpc';
import ajax from 'web.ajax';
import Registries from 'point_of_sale.Registries';
import models from 'point_of_sale.models';
/** To load model into pos **/
models.load_models([{
    model:  'table.reservation',
    fields: ['id', 'floor_id', 'booked_tables_ids', 'date', 'starting_at',
    'ending_at', 'state'],
    loaded: function(self, table_reservation) {
        self.table_reservation = table_reservation;
    }
}]);
const TableFloor = (FloorScreen) =>
class extends FloorScreen {
   /**
    For getting active tables
   **/
   get activeTables(){
    var table_record = []
    var self = this
    const now = new Date();
    const utc530Offset = 330 * 60 * 1000;
    const timeWithOffset = new Date(now.getTime() + utc530Offset);
    const formattedTime = timeWithOffset.toISOString().replace('T', ' ').substr(0, 16);
    const [datePart, timePart] = formattedTime.split(' ');
    self.activeFloor.tables.forEach(function(table){
        self.env.pos.table_reservation.forEach(function(record){
            if(record.floor_id[0] == self.activeFloor.id && record.date == datePart && record.state == "reserved"){
                if(record.starting_at <= timePart && timePart <= record.ending_at){
                    record.booked_tables_ids.forEach(function(rec){
                        if(rec == table['id']){
                            table_record.push(rec);
                        }
                    });
                }
            }
        });
    });
    const updatedData = this.activeFloor.tables.filter(item => !table_record.includes(item["id"]));
    return updatedData;
   }
}
Registries.Component.extend(FloorScreen, TableFloor);
