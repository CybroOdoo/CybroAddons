odoo.define('hotel_management_odoo.dashboard_action', function (require){
"use strict";
var AbstractAction = require('web.AbstractAction');
var core = require('web.core');
var QWeb = core.qweb;
var rpc = require('web.rpc');
var ajax = require('web.ajax');
document.write(
  unescape("%3Cscript src='https://cdn.jsdelivr.net/npm/chart.js' type='text/javascript'%3E%3C/script%3E"));
var _t = core._t;
const { loadBundle } = require("@web/core/assets");
var CustomDashBoard = AbstractAction.extend({
   template: 'CustomDashBoard',
   //Click Events
     events: {
            'click .total_room':'total_rooms',
            'click .check_in':'check_ins',
            'click .available_room':'available_rooms',
            'click .reservations':'reservations',
            'click .today_check_out':'check_outs',
            'click .total_vehicle':'fetch_total_vehicle',
            'click .available_vehicle':'fetch_available_vehicle',
            'click .total_events':'view_total_events',
            'click .today_events':'fetch_today_events',
            'click .pending_event':'fetch_pending_events',
            'click .food_item':'fetch_food_item',
            'click .food_order':'fetch_food_order',
            'click .total_staff':'fetch_total_staff',
    },
     init: function(parent, context) {
       this._super(parent, context);
       this.dashboards_templates = ['HotelOrder'];
       this.total = [];
       this.today_reservation = [];
       this.total_sale = [];
       this.total_food_items = [];
       this.total_events = [];
     },
     reload: function () {
        window.location.href = this.href;
     },
     willStart: function() {
       var self = this;
       return Promise.all([loadBundle(this), this._super()]).then(function() {
           return self.fetch_data();
       });
     },
       start: function() {
           var self = this;
           this.set("title", 'Dashboard');
           return this._super().then(function() {
               self.render_dashboards();//Call to Render Dashboard function
           });
       },
     fetch_data: function() {
       var self = this;
       //RPC call for retrieving data for displaying on dashboard tiles
       var def1= self._rpc({
           model:'room.booking',
           method:'get_details',
           args: [''],
       }).then(function(result){
            document.getElementsByClassName("total_room").innerHTML=['total_room']
            self.total_room=result['total_room']
            self.available_room=result['available_room']
            self.staff=result['staff']
            self.check_in=result['check_in']
            self.reservation=result['reservation']
            self.check_out=result['check_out']
            self.total_vehicle=result['total_vehicle']
            self.available_vehicle=result['available_vehicle']
            self.total_event=result['total_event']
            self.today_events=result['today_events']
            self.pending_events=result['pending_events']
            self.food_items=result['food_items']
            self.food_order=result['food_order']
            if(result['currency_position']=='before'){
                self.total_revenue=result['currency_symbol']+" "+result['total_revenue']
                self.today_revenue=result['currency_symbol']+" "+result['today_revenue']
                self.pending_payment=result['currency_symbol']+" "+result['pending_payment']
            }
            else{
                self.total_revenue=+result['total_revenue']+" "+result['currency_symbol']
                self.today_revenue=result['today_revenue']+" "+result['currency_symbol']
                self.pending_payment=result['pending_payment']+" "+result['currency_symbol']
            }

       });
           return $.when(def1);

     },
       render_dashboards: function(){
       var self = this;
       //Render Template
       _.each(this.dashboards_templates, function(template) {
               self.$('.o_pj_dashboard').append(QWeb.render(template,
                {widget: self}));
           });
   },
    total_rooms: function(e){
        var self = this;
        e.stopPropagation();
        e.preventDefault();
                this.do_action({
                    name: _t("Rooms"),
                    type:'ir.actions.act_window',
                    res_model:'hotel.room',
                    view_mode:'tree,form',
                    view_type:'form',
                    views:[[false,'list'],[false,'form']],
                    target:'current'
                },{ on_reverse_breadcrum: function(){return self.reload();}})
    },

//    check-in
    check_ins: function(e){
        var self = this;
        e.stopPropagation();
        e.preventDefault();
        this.do_action({
            name: _t("Check-In"),
            type:'ir.actions.act_window',
            res_model:'room.booking',
            view_mode:'tree,form',
            view_type:'form',
            views:[[false,'list'],[false,'form']],
            domain: [['state', '=', 'check_in']],
            target:'current'
        },{ on_reverse_breadcrum: function(){return self.reload();}})
    },
    //    Total Events
    view_total_events: function(e){
        var self = this;
        e.stopPropagation();
        e.preventDefault();
        this.do_action({
            name: _t("Total Events"),
            type:'ir.actions.act_window',
            res_model:'event.event',
            view_mode:'kanban,tree,form',
            view_type:'form',
            views:[[false,'kanban'],[false,'list'],[false,'form']],
            domain: [],
            target:'current'
        },{ on_reverse_breadcrum: function(){return self.reload();}})
    },
        //    Today's Events
    fetch_today_events: function(e){
        var self = this;
        e.stopPropagation();
        e.preventDefault();
        this.do_action({
            name: _t("Today's Events"),
            type:'ir.actions.act_window',
            res_model:'event.event',
            view_mode:'kanban,tree,form',
            view_type:'form',
            views:[[false,'kanban'],[false,'list'],[false,'form']],
            domain:  [['date_end', '>=', moment().startOf('day').format('YYYY-MM-DD')],
            ['date_end', '<=', moment().endOf('day').format('YYYY-MM-DD')]],
            target:'current'
        },{ on_reverse_breadcrum: function(){return self.reload();}})
    },
        //    Pending Events
    fetch_pending_events: function(e){
        var self = this;
        e.stopPropagation();
        e.preventDefault();
        this.do_action({
            name: _t("Pending Events"),
            type:'ir.actions.act_window',
            res_model:'event.event',
            view_mode:'kanban,tree,form',
            view_type:'form',
            views:[[false,'kanban'],[false,'list'],[false,'form']],
            domain:  [['date_end', '>=', moment().startOf('day').format('YYYY-MM-DD')]],
            target:'current'
        },{ on_reverse_breadcrum: function(){return self.reload();}})
    },
        //    Total staff
    fetch_total_staff: function(e){
        var self = this;
        e.stopPropagation();
        e.preventDefault();
        this.do_action({
            name: _t("Total Staffs"),
            type:'ir.actions.act_window',
            res_model:'res.users',
            view_mode:'tree,form',
            view_type:'form',
            views:[[false,'list'],[false,'form']],
            domain: [['groups_id.name', 'in',['Admin',
                       'Cleaning Team User',
                       'Cleaning Team Head',
                       'Receptionist',
                       'Maintenance Team User',
                       'Maintenance Team Leader'
                   ]]],
            target:'current'
        },{ on_reverse_breadcrum: function(){return self.reload();}})
    },
    //    check-out
    check_outs: function(e){
        var self = this;
        e.stopPropagation();
        e.preventDefault();
        this.do_action({
            name: _t("Today's Check-Out"),
            type:'ir.actions.act_window',
            res_model:'room.booking',
            view_mode:'tree,form',
            view_type:'form',
            views:[[false,'list'],[false,'form']],
            domain: [['room_line_ids.checkout_date', '>=', moment().startOf('day').format('YYYY-MM-DD')],
                ['room_line_ids.checkout_date', '<=', moment().endOf('day').format('YYYY-MM-DD HH:mm:ss')]],
            target:'current'
        },{ on_reverse_breadcrum: function(){return self.reload();}})
    },
//    Available rooms
    available_rooms: function(e){
        var self = this;
        e.stopPropagation();
        e.preventDefault();
        this.do_action({
            name: _t("Available Room"),
            type:'ir.actions.act_window',
            res_model:'hotel.room',
            view_mode:'tree,form',
            view_type:'form',
            views:[[false,'list'],[false,'form']],
            domain: [['status', '=', 'available']],
            target:'current'
        },{ on_reverse_breadcrum: function(){return self.reload();}})
    },
//    Reservations
    reservations: function(e){
        var self = this;
        e.stopPropagation();
        e.preventDefault();
        this.do_action({
            name: _t("Total Reservations"),
            type:'ir.actions.act_window',
            res_model:'room.booking',
            view_mode:'tree,form',
            view_type:'form',
            views:[[false,'list'],[false,'form']],
            domain: [['state', '=', 'reserved']],
            target:'current'
        },{ on_reverse_breadcrum: function(){return self.reload();}})
    },
//    Food Items
    fetch_food_item: function(e){
        var self = this;
        e.stopPropagation();
        e.preventDefault();
        this.do_action({
            name: _t("Food Items"),
            type:'ir.actions.act_window',
            res_model:'lunch.product',
            view_mode:'tree,form',
            view_type:'form',
            views:[[false,'list'],[false,'form']],
            domain: [],
            target:'current'
        },{ on_reverse_breadcrum: function(){return self.reload();}})
    },
//    food Orders
    fetch_food_order: function(e){
        var self = this;
        e.stopPropagation();
        e.preventDefault();
        rpc.query({
        model: 'food.booking.line',
        method: 'search_food_orders',
        args:[[]]
      }).then(function (result) {
        self.do_action({
            name: _t("Food Orders"),
            type:'ir.actions.act_window',
            res_model:'food.booking.line',
            view_mode:'tree,form',
            view_type:'form',
            views:[[false,'list'],[false,'form']],
           domain: [['id','in', result]],
            target:'current'
        },{ on_reverse_breadcrum: function(){return self.reload();}})
        });
    },
//    total vehicle
    fetch_total_vehicle: function(e){
        var self = this;
        e.stopPropagation();
        e.preventDefault();
        this.do_action({name: _t("Total Vehicles"),
                    type:'ir.actions.act_window',
                    res_model:'fleet.vehicle.model',
                    view_mode:'tree,form',
                    view_type:'form',
                    views:[[false,'list'],[false,'form']],
                    target:'current'
                },{ on_reverse_breadcrum: function(){return self.reload();}})
    },
//    Available Vehicle
    fetch_available_vehicle: function(e){
        var self = this;
        e.stopPropagation();
        e.preventDefault();
        rpc.query({
    model: 'fleet.booking.line',
    method: 'search_available_vehicle',
    args:[[]]
  }).then(function (result) {
        self.do_action({
            name: _t("Available Vehicle"),
            type:'ir.actions.act_window',
            res_model:'fleet.vehicle.model',
            view_mode:'tree,form',
            view_type:'form',
            views:[[false,'list'],[false,'form']],
            domain: [['id','not in', result]],
            target:'current'
        },{ on_reverse_breadcrum: function(){return self.reload();}})
        });
    },
})
core.action_registry.add('custom_dashboard_tags', CustomDashBoard);
return CustomDashBoard;
})
