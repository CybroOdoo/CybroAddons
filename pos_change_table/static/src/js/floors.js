odoo.define('pos_change_table.floors', function (require) {
"use strict";
    var chrome = require('point_of_sale.chrome');
    var gui = require('point_of_sale.gui');
    var models = require('point_of_sale.models');
    var screens = require('point_of_sale.screens');
    var core = require('web.core');
    var QWeb = core.qweb;
    var floor  = require('pos_restaurant.floors');

// We need to modify the OrderSelector to hide itself when we're on
// the floor plan
chrome.OrderSelectorWidget.include({
    change_floor_button_click_handler: function(){
        this.pos.change_table = true;
        this.pos.previous_order_id = this.pos.get_order();
        this.pos.set_table(null);

    },
    renderElement: function(){
        var self = this;
        this._super();
        if (this.pos.config.iface_floorplan) {
            if (this.pos.get_order()) {
                if (this.pos.table && this.pos.table.floor) {
                    this.$('.orders').prepend(QWeb.render('ChangeFloorButton'));
                    this.$('.change-floor-button').click(function(){
                        self.change_floor_button_click_handler();
                    });
                }
                this.$el.removeClass('oe_invisible');
            } else {
                this.$el.addClass('oe_invisible');
            }
        }
    },
});

// We need to change the way the regular UI sees the orders, it
// needs to only see the orders associated with the current table,
// and when an order is validated, it needs to go back to the floor map.
//
// And when we change the table, we must create an order for that table
// if there is none. 
var _super_posmodel = models.PosModel.prototype;

models.PosModel = models.PosModel.extend({
    initialize: function(session, attributes) {
        this.change_table = false;
        this.previous_order_id= false;
        return _super_posmodel.initialize.call(this,session,attributes);
    },

    // changes the current table.

    set_table: function(table) {
        if (this.change_table){
            if (!table) { // no table ? go back to the floor plan, see ScreenSelector
                this.set_order(null);
            }
            else {
                 this.previous_order_id.table = table;
                 this.change_table = false;
                 // table ? load the associated orders  ...
                 this.table = table;
                 var orders = this.get_order_list();
                 if (orders.length) {
                     this.set_order(orders[0]); // and go to the first one ...
                 } else {
                     this.add_new_order();  // or create a new order with the current table
                 }

            }

        }
        else{
            _super_posmodel.set_table.apply(this,arguments);
        }



        if (!table) { // no table ? go back to the floor plan, see ScreenSelector
            this.set_order(null);
        }
        else {
             if(this.change_table){
                 this.previous_order_id.table = table;
                 this.change_table = false;
             }
                 // table ? load the associated orders  ...
                 this.table = table;
                 var orders = this.get_order_list();
                 if (orders.length) {
                     this.set_order(orders[0]); // and go to the first one ...
                 } else {
                     this.add_new_order();  // or create a new order with the current table
                 }

        }
    },

    
    });

});
