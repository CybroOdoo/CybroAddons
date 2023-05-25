odoo.define('pos_table_merge_orders.PosTablePopup', function(require) {
    "use strict";
    const Popup = require('point_of_sale.ConfirmPopup');
    const Registries = require('point_of_sale.Registries');
    const PosComponent = require('point_of_sale.PosComponent');
    class PosTablePopup extends Popup {
        constructor() {
            super(...arguments);
        }
        setup() {
            super.setup();
            this.selectedTable = [];
        }
        // Floor details can fetch
        get floors() {
            var tables = [];
            var floors = this.env.pos.table.floor
                   floors.tables.forEach(item => {
                        tables.push({'id':item.id, 'name':item.name})
                   })
            return tables;
        }
        // Event for selecting the tables
        click_on_merge_table(event) {
            var self = this;
            if($(event.target).data('click') == '1'){
                $(event.target).data('click','0')
                $(event.target).css("background-color", "#fff");
                var index = this.selectedTable.indexOf($(event.target).data('table_id'))
                this.selectedTable.splice(index,1)
            }
            else{
                $(event.target).data('click','1')
                this.selectedTable.push($(event.target).data('table_id'))
                $(event.target).css("background-color", "#90EE90");
            }
        }
        // Event for adding order lines
        merge_orderline(event) {
            var self = this;
            var select = this.selectedTable
            this.selectedTable.forEach(table => {
            this.env.pos.orders.forEach(item => {
                    if(item.tableId == table){
                        item.orderlines.forEach(line => {
                           this.env.pos.get_order().orderlines.add(line);
                    });
                    this.env.pos.removeOrder(item)
            }
            });
            });
            this.env.pos.get_order().select_orderline(this.env.pos.get_order().get_last_orderline());
                this.env.posbus.trigger('close-popup', {
                popupId: this.props.id }); // close popup
        }
    };
    PosTablePopup.template = 'PosTablePopup';
    Registries.Component.add(PosTablePopup);
    return PosTablePopup;
});
