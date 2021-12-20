odoo.define('odoo_dynamic_dashboard.Dashboard', function (require) {
"use strict";

var AbstractAction = require('web.AbstractAction');
var ajax = require('web.ajax');
var core = require('web.core');
var rpc = require('web.rpc');
var session = require('web.session');
var web_client = require('web.web_client');
var _t = core._t;
var QWeb = core.qweb;

var DynamicDashboard = AbstractAction.extend({
    template: 'dynamic_dashboard',
    events: {
         'click .add_block': '_onClick_add_block',
         'click .add_grapgh': '_onClick_add_grapgh',
         'click .block_setting': '_onClick_block_setting',
         'click .tile': '_onClick_tile',
    },

    init: function(parent, context) {
        this.action_id = context['id'];
        this._super(parent, context);
        this.block_ids = []
    },

    start: function() {
        var self = this;
        this.set("title", 'Dashboard');

        return this._super().then(function() {
            self.render_dashboards();
        });
    },


    willStart: function() {
        var self = this;
        return $.when(ajax.loadLibs(this), this._super()).then(function() {
             return self.fetch_data();
        });
    },

     fetch_data: function() {
        var self = this;
        var def1 =  this._rpc({
                model: 'dashboard.block',
                method: 'get_dashboard_vals',
                args: [[],this.action_id]
            }).then(function(result) {
                self.block_ids = result;
        });
        return $.when(def1);
    },

    get_colors : function(x_axis) {
        var color = []
        for (var j = 0; j < x_axis.length; j++) {
            var r = Math.floor(Math.random() * 255);
            var g = Math.floor(Math.random() * 255);
            var b = Math.floor(Math.random() * 255);
            color.push("rgb(" + r + "," + g + "," + b + ")");
         }
         return color
    },

    get_values_bar : function(block){
        var labels = block['x_axis']
        var data = {
          labels: labels,
          datasets: [{
            label: "",
            data: block['y_axis'],
                    backgroundColor: this.get_colors(block['x_axis']),
                    borderColor: 'rgba(200, 200, 200, 0.75)',
                    borderWidth: 1
                  }]
                };

        var options = {
                scales: {
                  y: {
                    beginAtZero: true
                  }
                }
            },
        bar_data = [data,options]
        return bar_data;
        },

    get_values_pie : function(block){
        var data = {
        labels: block['x_axis'],
          datasets: [{
            label: '',
            data: block['y_axis'],
            backgroundColor: this.get_colors(block['x_axis']),
            hoverOffset: 4
          }]
        };
        var options = { },
        pie_data = [data,options]
        return pie_data;
    },

    get_values_line : function(block){
        var labels = block['x_axis']
        var data = {
          labels: labels,
          datasets: [{
            label: '',
            data: block['y_axis'],
            fill: false,
            borderColor: 'rgb(75, 192, 192)',
            tension: 0.1
          }]
        };
        var options = { },
        line_data = [data,options]
        return line_data;

    },

    get_values_doughnut : function(block){
        var data = {
        labels: block['x_axis'],
          datasets: [{
            label: '',
            data: block['y_axis'],
            backgroundColor: this.get_colors(block['x_axis']),
            hoverOffset: 4
          }]
        };
        var options = { },
        doughnut_data = [data,options]
        return doughnut_data;


    },

    get_values_radar : function(block){
          var data = {
          labels: block['x_axis'],
          datasets: [{
            label: '',
            data: block['y_axis'],
            fill: true,
            backgroundColor: 'rgba(255, 99, 132, 0.2)',
            borderColor: 'rgb(255, 99, 132)',
            pointBackgroundColor: 'rgb(255, 99, 132)',
            pointBorderColor: '#fff',
            pointHoverBackgroundColor: '#fff',
            pointHoverBorderColor: 'rgb(255, 99, 132)'
          }]
        };
        var options = {
            elements: {
              line: {
                borderWidth: 3
              }
            }
          },
        radar_data = [data,options]
        return radar_data;
    },

    render_dashboards: function() {
        var self = this;
        _.each(this.block_ids, function(block) {
                if (block['type'] == 'tile') {
                    self.$('.o_dynamic_dashboard').append(QWeb.render('DynamicDashboardTile', {widget: block}));
                }
                else{
                    self.$('.o_dynamic_chart').append(QWeb.render('DynamicDashboardChart', {widget: block}));
                    var element = $('[data-id=' + block['id'] + ']')
                    if (!('x_axis' in block)){
                        return false
                    }
                    var ctx =self.$('.chart_graphs').last()
                    var type = block['graph_type']
                    var chart_type = 'self.get_values_' + `${type}(block)`
                    var data = eval(chart_type)
                  //create Chart class object
                  var chart = new Chart(ctx, {
                    type: type,
                    data: data[0],
                    options: data[1]
                  });
                }
        });
    },

    _onClick_block_setting : function(event){
        event.stopPropagation();
        var self = this;
        var id = $(event.currentTarget).closest('.block').attr('data-id');
        this.do_action({
            type: 'ir.actions.act_window',
            res_model: 'dashboard.block',
            view_mode: 'form',
            res_id: parseInt(id),
            views: [[false,'form']],
            context: {'form_view_initial_mode': 'edit'},
        });
    },

    _onClick_add_block : function(e){
         var self = this;
         var type = $(e.currentTarget).attr('data-type');
         ajax.jsonRpc('/create/tile', 'call', {
            'type' : type,
            'action_id' : self.action_id
                }).then(function (result) {
                    if(result['type'] == 'tile'){
                        self.$('.o_dynamic_dashboard').append(QWeb.render('DynamicDashboardTile', {widget: result}));
                    }
                    else{
                        self.$('.o_dynamic_chart').append(QWeb.render('DynamicDashboardChart', {widget: result}));
                        var element = $('[data-id=' + result['id'] + ']')
                        var ctx =self.$('.chart_graphs').last()
                        var options = {
                          type: 'bar',
                          data: {
                            labels: [],
                            datasets: [
                                {
                                  data: [],
                                borderWidth: 1
                                },
                                ]
                          },
                        }
                        var chart = new Chart(ctx, {
                            type: "bar",
                            data: options
                          });
                    }
                });
    },

    _onClick_tile : function(e){
        e.stopPropagation();
        var self = this;
        var id = $(e.currentTarget).attr('data-id');
        ajax.jsonRpc('/tile/details', 'call', {
           'id': id
        }).then(function (result) {
                self.do_action({
                name : result['model_name'],
                type: 'ir.actions.act_window',
                res_model:result['model'] ,
                view_mode: 'tree,form',
                views: [[false, 'list'], [false, 'form']],
                domain: result['filter']
                });
        });
    },



});


core.action_registry.add('dynamic_dashboard', DynamicDashboard);

return DynamicDashboard;

});
