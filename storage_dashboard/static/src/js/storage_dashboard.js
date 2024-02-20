odoo.define("dashboard_dashboard.DashboardDashboard", function (require) {
    "use strict";
    var AbstractAction = require('web.AbstractAction');
    var core = require('web.core');
    var QWeb = core.qweb;
    var _t = core._t;
    var rpc = require('web.rpc');
    var self = this;
/*
    * Extends Action and shows different charts based on database related data
    fetched from python model.
*/
    var DashBoard = AbstractAction.extend({
        //Adding Chart.js on js libraries.
        jsLibs: [
            '/web/static/lib/Chart/Chart.js',
        ],
        contentTemplate: 'DashboardDashboard',
        // Method for Change cart view
        init: function(parent, context) {
           this._super(parent, context);
           this.dashboard_templates = ['MainSection'];
           this.chart = [];
        },
        start: function() {
           var self = this;
           this.set("title", 'Dashboard');
           return this._super().then(function() {
               self.render_dashboards();
           });
        },
        willStart: function(){
            var self = this;
            return this._super()
        },
        render_dashboards: function() {
           var self = this;
           this.fetch_data()
           var templates = ['MainSection'];
           _.each(templates, function(template) {
               self.$('.o_hr_dashboard').append(QWeb.render(template, {widget: self}))
           });
        },
        //  Method for fetching data related for database and model storage
        //  form storage.usage python model.
        fetch_data: function() {
            var self = this
            var def0 = this._rpc({
               model: 'storage.usage',
               method: "get_info",
            })
            .then(function (result) {
                $('#db_info_title').replaceWith('<span>' + result['db_name'] + '</span>');
                $('#db_info_body').replaceWith('<span>' + result['db_version'] + '</span>');
                $('#db_date').replaceWith('<span>' + result['db_date'] + '</span>');
                $('#db_tables').replaceWith('<span>' + result['db_tables'] + '</span>');
                $('#db_size_body').replaceWith('<span>' + result['db_size'] + '</span>');
                $('#total_memory').text(result['total_memory']);
                $('#used_memory').text(result['used_memory']);
                $('#available_memory').text(result['available_memory']);
                $('#cpu_usage').text(result['cpu_usage']);
                $('#ram_usage').text(result['ram_usage']);
                $('#os').text(result['os']);
                $('#soft_limit').text(result['soft_limit']);
                $('#hard_limit').text(result['hard_limit']);
                $('#transient_age_limit').text(result['transient_age_limit']);
                $('#limit_time_cpu').text(result['limit_time_cpu']);
                $('#limit_request').text(result['limit_request']);
                $('#limit_time_real').text(result['limit_time_real']);
                $('#http_port').text(result['http_port']);
                $('#db_user').text(result['db_user']);
            });
            var def1 = this._rpc({
               model: 'storage.usage',
               method: "get_data",
            })
            .then(function (result) {
                var indexModelsArray = result.index_data.map(function(item){
                    return item.model
                });
                var indexSizeArray = result.index_data.map(function(item){
                    return item.index_size
                });
                var modelsArray = result.model_storage.map(function(item) {
                    return item.model;
                });
                var sizesArray = result.model_storage.map(function(item) {
                return item.size;
                });
                const get_colors = () => {
                    var color = []
                        for (var j = 0; j < result.index_data.length; j++) {
                            var r = Math.floor(Math.random() * 255);
                            var g = Math.floor(Math.random() * 255);
                            var b = Math.floor(Math.random() * 255);
                            color.push("rgb(" + r + "," + g + "," + b + ")");
                        }
                    return color
                }
                //  Chart templates.
                self.chart.push(new Chart("chart_example", {
                    type: 'bar',
                    data: {
                        labels: modelsArray, // Labels for each segment
                        datasets: [{
                            label: 'Size Used',
                            backgroundColor: get_colors(),
                            data: sizesArray,
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: true,
                        tooltips: {
                            callbacks: {
                                label: function (tooltipItem, data) {
                                    var label = data.labels[tooltipItem.index];
                                    var value = data.datasets[0].data[tooltipItem.index];
                                    return label + " : " + value.toLocaleString() + " MB";
                                }
                            }
                        }
                    }
                }));

                self.chart.push(new Chart("chart_index", {
                    type: 'line',
                    data: {
                        labels: indexModelsArray, // Labels for each segment
                        datasets: [{
                            label: 'Index Size',
                            fill: false,
                            borderColor: 'rgb(75, 192, 192)',
                            data: indexSizeArray,
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: true,
                        tooltips: {
                            callbacks: {
                                label: function (tooltipItem, data) {
                                    var label = data.labels[tooltipItem.index];
                                    var value = data.datasets[0].data[tooltipItem.index];
                                    return label + " : " + value.toLocaleString() + " MB";
                                }
                            }
                        }
                    }
                }));
            });
        },
   });
   core.action_registry.add('storage_dashboard_tag', DashBoard);
   return DashBoard;
});
