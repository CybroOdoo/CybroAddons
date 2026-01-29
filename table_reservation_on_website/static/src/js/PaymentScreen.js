/** @odoo-module **/
import PaymentScreen from 'point_of_sale.PaymentScreen';
import rpc from 'web.rpc';
import ajax from 'web.ajax';
import Registries from 'point_of_sale.Registries';

const TableReservation = (PaymentScreen) =>
class extends PaymentScreen {
    /**
    For payment validation in pos
    **/
    async _finalizeValidation() {
        var self = this
        if (this.currentOrder.table){
            ajax.jsonRpc('/table/reservation/pos','call',{
            'partner_id' : this.currentOrder.changed.client.id,
            'table_id': this.currentOrder.table.id,
            }).then( function(data){});
        }
        return super._finalizeValidation()
    }
}
Registries.Component.extend(PaymentScreen, TableReservation);
