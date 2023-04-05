odoo.define('dashboard_pos.Dashboard', function (require) {
"use strict";

var AbstractAction = require('web.AbstractAction');
var core = require('web.core');
const { loadBundle } = require("@web/core/assets");
var ajax = require('web.ajax');
var session = require('web.session');
var web_client = require('web.web_client');
var rpc = require('web.rpc');
var _t = core._t;
var QWeb = core.qweb;

var PosDashboard = AbstractAction.extend({
    template: 'PosDashboard',
    events: {
            'click .pos_order_today':'pos_order_today',
            'click .pos_order':'pos_order',
            'click .pos_total_sales':'pos_order',
            'click .pos_session':'pos_session',
            'click .pos_refund_orders':'pos_refund_orders',
            'click .pos_refund_today_orders':'pos_refund_today_orders',
            'change #pos_sales': 'onclick_pos_sales',
    },

    init: function(parent, context) {
        this._super(parent, context);
        this.dashboards_templates = ['PosOrders','PosChart','PosCustomer'];
        this.payment_details = [];
        this.top_salesperson = [];
        this.selling_product = [];
        this.total_sale = [];
        this.total_order_count = [];
        this.total_refund_count = [];
        this.total_session = [];
        this.today_refund_total = [];
        this.today_sale = [];
    },


// willStart: function() {
//        var self = this;
//        return $.when(ajax.loadLibs(this), this._super()).then(function() {
//            return self.fetch_data();
//        });
//    },


    willStart: function() {
        var self = this;
        return $.when(loadBundle(this), this._super()).then(function() {
            return self.fetch_data();
        });
    },
//    willStart: function() {
//        var self = this;
//        return Promise.all([loadBundle(this), this._super()]).then(function() {
//            return self.fetch_data();

    start: function() {
        var self = this;
        this.set("title", 'Dashboard');
        return this._super().then(function() {
            self.render_dashboards();
            self.render_graphs();
            self.$el.parent().addClass('oe_background_grey');
        });
    },

    fetch_data: function() {
        var self = this;
        var def1 =  this._rpc({
                model: 'pos.order',
                method: 'get_refund_details'
        }).then(function(result) {
           self.total_sale = result['total_sale'],
           self.total_order_count = result['total_order_count']
           self.total_refund_count = result['total_refund_count']
           self.total_session = result['total_session']
           self.today_refund_total = result['today_refund_total']
           self.today_sale = result['today_sale']
        });
      var def2 = self._rpc({
            model: "pos.order",
            method: "get_details",
        })
        .then(function (res) {
            self.payment_details = res['payment_details'];
            self.top_salesperson = res['salesperson'];
            self.selling_product = res['selling_product'];
        });
        return $.when(def1,def2);
    },

    render_dashboards: function() {
        var self = this;
            _.each(this.dashboards_templates, function(template) {
                self.$('.o_pos_dashboard').append(QWeb.render(template, {widget: self}));
            });
    },
      render_graphs: function(){
        var self = this;
         self.render_top_customer_graph();
         self.render_top_product_graph();
         self.render_product_category_graph();
    },




       pos_order_today: function(e){
        var self = this;
        var date = new Date();
        var yesterday = new Date(date.getTime());
        yesterday.setDate(date.getDate() - 1);
        e.stopPropagation();
        e.preventDefault();

        session.user_has_group('hr.group_hr_user').then(function(has_group){
            if(has_group){
                var options = {
                    on_reverse_breadcrumb: self.on_reverse_breadcrumb,
                };
                self.do_action({
                    name: _t("Today Order"),
                    type: 'ir.actions.act_window',
                    res_model: 'pos.order',
                    view_mode: 'tree,form,calendar',
                    view_type: 'form',
                    views: [[false, 'list'],[false, 'form']],
                    domain: [['date_order','<=', date],['date_order', '>=', yesterday]],
                    target: 'current'
                }, options)
            }
        });

    },


      pos_refund_orders: function(e){
        var self = this;
        var date = new Date();
        var yesterday = new Date(date.getTime());
        yesterday.setDate(date.getDate() - 1);
        e.stopPropagation();
        e.preventDefault();

        session.user_has_group('hr.group_hr_user').then(function(has_group){
            if(has_group){
                var options = {
                    on_reverse_breadcrumb: self.on_reverse_breadcrumb,
                };
                self.do_action({
                    name: _t("Refund Orders"),
                    type: 'ir.actions.act_window',
                    res_model: 'pos.order',
                    view_mode: 'tree,form,calendar',
                    view_type: 'form',
                    views: [[false, 'list'],[false, 'form']],
                    domain: [['amount_total', '<', 0.0]],
                    target: 'current'
                }, options)
            }
        });

    },
    pos_refund_today_orders: function(e){
        var self = this;
        var date = new Date();
        var yesterday = new Date(date.getTime());
        yesterday.setDate(date.getDate() - 1);
        e.stopPropagation();
        e.preventDefault();

        session.user_has_group('hr.group_hr_user').then(function(has_group){
            if(has_group){
                var options = {
                    on_reverse_breadcrumb: self.on_reverse_breadcrumb,
                };
                self.do_action({
                    name: _t("Refund Orders"),
                    type: 'ir.actions.act_window',
                    res_model: 'pos.order',
                    view_mode: 'tree,form,calendar',
                    view_type: 'form',
                    views: [[false, 'list'],[false, 'form']],
                    domain: [['amount_total', '<', 0.0],['date_order','<=', date],['date_order', '>=', yesterday]],
                    target: 'current'
                }, options)
            }
        });

    },

        pos_order: function(e){
        var self = this;
        var date = new Date();
        var yesterday = new Date(date.getTime());
        yesterday.setDate(date.getDate() - 1);
        e.stopPropagation();
        e.preventDefault();
        session.user_has_group('hr.group_hr_user').then(function(has_group){
            if(has_group){
                var options = {
                    on_reverse_breadcrumb: self.on_reverse_breadcrumb,
                };
                self.do_action({
                    name: _t("Total Order"),
                    type: 'ir.actions.act_window',
                    res_model: 'pos.order',
                    view_mode: 'tree,form,calendar',
                    view_type: 'form',
                    views: [[false, 'list'],[false, 'form']],
                    target: 'current'
                }, options)
            }
        });

    },
    pos_session: function(e){
        var self = this;
        e.stopPropagation();
        e.preventDefault();
        session.user_has_group('hr.group_hr_user').then(function(has_group){
            if(has_group){
                var options = {
                    on_reverse_breadcrumb: self.on_reverse_breadcrumb,
                };
                self.do_action({
                    name: _t("sessions"),
                    type: 'ir.actions.act_window',
                    res_model: 'pos.session',
                    view_mode: 'tree,form,calendar',
                    view_type: 'form',
                    views: [[false, 'list'],[false, 'form']],
                    target: 'current'
                }, options)
            }
        });

    },

     onclick_pos_sales:function(events){
        var option = $(events.target).val();
       var self = this
        var ctx = self.$("#canvas_1");
            rpc.query({
                model: "pos.order",
                method: "get_department",
                args: [option],
            }).then(function (arrays) {
          var data = {
            labels: arrays[1],
            datasets: [
              {
                label: arrays[2],
                data: arrays[0],
                backgroundColor: [
                  "rgba(255, 99, 132,1)",
                  "rgba(54, 162, 235,1)",
                  "rgba(75, 192, 192,1)",
                  "rgba(153, 102, 255,1)",
                  "rgba(10,20,30,1)"
                ],
                borderColor: [
                 "rgba(255, 99, 132, 0.2)",
                  "rgba(54, 162, 235, 0.2)",
                  "rgba(75, 192, 192, 0.2)",
                  "rgba(153, 102, 255, 0.2)",
                  "rgba(10,20,30,0.3)"
                ],
                borderWidth: 1
              },

            ]
          };

  //options
          var options = {
            responsive: true,
            title: {
              display: true,
              position: "top",
              text: "SALE DETAILS",
              fontSize: 18,
              fontColor: "#111"
            },
            legend: {
              display: true,
              position: "bottom",
              labels: {
                fontColor: "#333",
                fontSize: 16
              }
            },
            scales: {
              yAxes: [{
                ticks: {
                  min: 0
                }
              }]
            }
          };

          //create Chart class object
          if (window.myCharts != undefined)
          window.myCharts.destroy();
          window.myCharts = new Chart(ctx, {
            type: "bar",
            data: data,
            options: options
          });

        });
        },


     render_top_customer_graph:function(){
       var self = this
        var ctx = self.$(".top_customer");
            rpc.query({
                model: "pos.order",
                method: "get_the_top_customer",
            }).then(function (arrays) {


          var data = {
            labels: arrays[1],
            datasets: [
              {
                label: "",
                data: arrays[0],
                backgroundColor: [
                  "rgb(148, 22, 227)",
                  "rgba(54, 162, 235)",
                  "rgba(75, 192, 192)",
                  "rgba(153, 102, 255)",
                  "rgba(10,20,30)"
                ],
                borderColor: [
                 "rgba(255, 99, 132,)",
                  "rgba(54, 162, 235,)",
                  "rgba(75, 192, 192,)",
                  "rgba(153, 102, 255,)",
                  "rgba(10,20,30,)"
                ],
                borderWidth: 1
              },

            ]
          };

  //options
          var options = {
            responsive: true,
            title: {
              display: true,
              position: "top",
              text: " Top Customer",
              fontSize: 18,
              fontColor: "#111"
            },
            legend: {
              display: true,
              position: "bottom",
              labels: {
                fontColor: "#333",
                fontSize: 16
              }
            },
            scales: {
              yAxes: [{
                ticks: {
                  min: 0
                }
              }]
            }
          };

          //create Chart class object
          var chart = new Chart(ctx, {
            type: "pie",
            data: data,
            options: options
          });

        });
        },

     render_top_product_graph:function(){
       var self = this
        var ctx = self.$(".top_selling_product");
            rpc.query({
                model: "pos.order",
                method: "get_the_top_products",
            }).then(function (arrays) {
          var data = {

            labels: arrays[1],
            datasets: [
              {
                label: "Quantity",
                data: arrays[0],
                backgroundColor: [
                  "rgba(255, 99, 132,1)",
                  "rgba(54, 162, 235,1)",
                  "rgba(75, 192, 192,1)",
                  "rgba(153, 102, 255,1)",
                  "rgba(10,20,30,1)"
                ],
                borderColor: [
                 "rgba(255, 99, 132, 0.2)",
                  "rgba(54, 162, 235, 0.2)",
                  "rgba(75, 192, 192, 0.2)",
                  "rgba(153, 102, 255, 0.2)",
                  "rgba(10,20,30,0.3)"
                ],
                borderWidth: 1
              },

            ]
          };

  //options
          var options = {
            responsive: true,
            title: {
              display: true,
              position: "top",
              text: " Top products",
              fontSize: 18,
              fontColor: "#111"
            },
            legend: {
              display: true,
              position: "bottom",
              labels: {
                fontColor: "#333",
                fontSize: 16
              }
            },
            scales: {
              yAxes: [{
                ticks: {
                  min: 0
                }
              }]
            }
          };

          //create Chart class object
          var chart = new Chart(ctx, {
            type: "horizontalBar",
            data: data,
            options: options
          });

        });
        },

     render_product_category_graph:function(){
           var self = this
        var ctx = self.$(".top_product_categories");
            rpc.query({
                model: "pos.order",
                method: "get_the_top_categories",
            }).then(function (arrays) {


          var data = {
            labels: arrays[1],
            datasets: [
              {
                label: "Quantity",
                data: arrays[0],
                backgroundColor: [
                  "rgba(255, 99, 132,1)",
                  "rgba(54, 162, 235,1)",
                  "rgba(75, 192, 192,1)",
                  "rgba(153, 102, 255,1)",
                  "rgba(10,20,30,1)"
                ],
                borderColor: [
                 "rgba(255, 99, 132, 0.2)",
                  "rgba(54, 162, 235, 0.2)",
                  "rgba(75, 192, 192, 0.2)",
                  "rgba(153, 102, 255, 0.2)",
                  "rgba(10,20,30,0.3)"
                ],
                borderWidth: 1
              },


            ]
          };

  //options
          var options = {
            responsive: true,
            title: {
              display: true,
              position: "top",
              text: " Top product categories",
              fontSize: 18,
              fontColor: "#111"
            },
            legend: {
              display: true,
              position: "bottom",
              labels: {
                fontColor: "#333",
                fontSize: 16
              }
            },
            scales: {
              yAxes: [{
                ticks: {
                  min: 0
                }
              }]
            }
          };

          //create Chart class object
          var chart = new Chart(ctx, {
            type: "horizontalBar",
            data: data,
            options: options
          });

        });
        },
});


core.action_registry.add('pos_dashboard', PosDashboard);

return PosDashboard;

});
