odoo.define("inventory_dashboard.dashboard", function (require) {
    "use strict";
    var AbstractAction = require('web.AbstractAction');
    var core = require('web.core');
    var rpc = require('web.rpc');
    var QWeb = core.qweb;
    var ajax = require('web.ajax');
    var web_client = require('web.web_client');
    var _t = core._t;
    var framework = require('web.framework');
    var session = require('web.session');
    var operation_types;
    var result_2;
    var result_3;
    var DashBoard = AbstractAction.extend({
        contentTemplate: 'Dashboard',
        events: {
            'change #top_product_selection': 'onclick_top_product_selection',
            'change #stock_moves_selection': 'onclick_stock_moves_selection',
            'change #product_move_selection': 'onclick_product_moves_selection',
            'click .col-lg-3': 'onclick_tiles',
            'click .dashboard-card__stat_late': 'onclick_late_status',
            'click .dashboard-card__stat_waiting': 'onclick_waiting_status',
            'click .dashboard-card__stat_backorder': 'onclick_backorders_status',
            'click #top_product_info': 'onclick_top_product_info',
            'click #pro_cate_info': 'onclick_pro_cate_info',
            'click #location_info': 'onclick_location_info',
            'click #operation_type_info': 'onclick_operation_type_info',
            'click #dead_stock_info': 'onclick_dead_stock_info',
            'click #out_of_stock_info': 'onclick_out_of_stock_info',
            'click #product_move_info': 'onclick_product_move_info',
            'click #stock_move_info': 'onclick_stock_move_info',
        },
        init: function(parent, context) {
        this._super(parent, context);
        this.dashboards_templates = ['InventoryTiles', 'ProductSaleBarGraph'];
        },
        willStart: function() {
            var self = this;
            return $.when(this._super()).then(function() {
                return;
            });
        },
        start: function() {
            var self = this;
            this.set("title", 'Dashboard');
            return this._super().then(function() {
                self.render_dashboards();
                self.render_graphs();
                self.$el.parent().addClass('oe_background_grey');
            });
        },
        render_dashboards: function() {
            var self = this;
                _.each(this.dashboards_templates, function(template) {
                    self.$('.o_hr_dashboard').append(QWeb.render(template, {widget: self}));
                });
        },
        render_graphs: function(){
            var self = this;
            self.render_operation_tile();
            self.render_top_product_bar_graph();
            self.render_stock_moves();
            self.render_product_move_graph_this_month();
            self.render_product_category();
            self.render_storage_location();
            self.render_out_of_stock_graph();
            self.render_dead_of_stock_graph();
        },
    //     fetch data function-operation type tiles and graph include this function
        render_operation_tile: function() {
            var self = this;
            var def1 =  this._rpc({
                model: 'stock.picking',
                method: 'get_operation_types'
            }).then(function(result) {
               operation_types = result[0];
               var late = result[1];
               var waiting = result[2];
               var backorder = result[4];
                var r = 1;
                var g = 0;
                result_3 = result[3];
                Object.entries(result[0]).forEach(([key, value]) => {
                    r++;
                    var result_1 = key;
                    result_2 = value;
                    const colors = ["red", "blue","green","orange","purple","steel","rebecca","brown","pink","grey","black"];
                    $('#set').append('<div class="col-sm-12 col-md-6 col-lg-3" id="' + result_1 +  '">
                    <div class="dashboard-card dashboard-card--border-top dashboard-card--border-top-' + colors[g] +  '">
                    <div class="dashboard-card__details"><span class="dashboard-card__title">' + result[3][result_1] + '</span>
                    <span class="count-container">' + result_2 +  '</span></div> <ul class="dashboard-card__stats"></ul></div></div>');
                    g++;
                    if (key in late) {
                        $('#' + key +  ' .dashboard-card__stats').append('<li class="dashboard-card__stat_late" id="' + result_1 +  '">
                        <div class="d-flex justify-content-between align-items-center text-dark text-decoration-none">
                        <div class="dashboard-card__stat-title_late">Late</div><div class="dashboard-card__stat-count_late">' + result[1][key] + '</div></div></li>');
                    }
                    if (key in waiting) {
                        $('#' + key +  ' .dashboard-card__stats').append('<li class="dashboard-card__stat_waiting" id="' + result_1 +  '">
                        <div class="d-flex justify-content-between align-items-center text-dark text-decoration-none">
                        <div class="dashboard-card__stat-title_waiting">Waiting</div><div class="dashboard-card__stat-count_waiting">' + result[2][key] +  '</div></div></li>');
                    }
                    if (key in backorder) {
                        $('#' + key +  ' .dashboard-card__stats').append('<li class="dashboard-card__stat_backorder" id="' + result_1 +  '">
                        <div class="d-flex justify-content-between align-items-center text-dark text-decoration-none">
                        <div class="dashboard-card__stat-title_back">Backorder</div><div class="dashboard-card__stat-count_backorder">' + result[4][key] +  '</div></div></li>');
                    }
                });
                var ctx = self.$("#operation");
                        // Define the data
                    var name = Object.values(result[3]) // Add data values to array
                    var count = Object.values(result[0])
                    var j = 0;
                    for (var c in count) {
                        $('#operation_type_table').append('<tr><td>'+name[j]+'</td><td>'+count[c]+'</td></tr>')
                        j++;
                    };
                    $('#operation_type_table').hide();
                    var myChart = new Chart(ctx, {
                        type: 'bar',
                        data: {
                            labels: name,//x axis
                            datasets: [{
                                label: 'Count', // Name the series
                                data: count, // Specify the data values array
                                backgroundColor: [
                                    "#003f5c",
                                    "#2f4b7c",
                                    "#f95d6a",
                                    "#665191",
                                    "#d45087",
                                    "#ff7c43",
                                    "#ffa600",
                                    "#a05195",
                                    "#6d5c16",
                                    "#CCCCFF"
                                ],
                                borderColor: [
                                    "#003f5c",
                                    "#2f4b7c",
                                    "#f95d6a",
                                    "#665191",
                                    "#d45087",
                                    "#ff7c43",
                                    "#ffa600",
                                    "#a05195",
                                    "#6d5c16",
                                    "#CCCCFF"
                                ],
                                barPercentage: 0.5,
                                barThickness: 6,
                                maxBarThickness: 8,
                                minBarLength: 0,
                                borderWidth: 1, // Specify bar border width
                                type: 'bar', // Set this data to a line chart
                                fill: false
                            }]
                        },
                        options: {
                            scales: {
                                y: {
                                    beginAtZero: true
                                },
                            },
                            responsive: true, // Instruct chart js to respond nicely.
                            maintainAspectRatio: false, // Add to prevent default behaviour of full-width/height
                        }
                    });
            });
        },
    //    top ten bar graph
        render_top_product_bar_graph:function(){
            var self = this
            rpc.query({
                model: "stock.move",
                method: "get_the_top_products",
            }).then(function (result) {
                var ctx = self.$("#canvaspie");
                var products = result.products // Add data values to array
                var count = result.count;
                var j = 0;
                Object.entries(result.count).forEach(([key, value]) => {
                    $('#pro_info').append('<tr><td>'+products[j]+'</td><td>'+value+'</td></tr>')
                    j++;
                    });
                $('#pro_info').hide();
                var myChart = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: products,//x axis
                        datasets: [{
                            label: 'Count', // Name the series
                            data: count, // Specify the data values array
                            backgroundColor: [
                                "#003f5c",
                                "#2f4b7c",
                                "#f95d6a",
                                "#665191",
                                "#d45087",
                                "#ff7c43",
                                "#ffa600",
                                "#a05195",
                                "#6d5c16",
                                "#CCCCFF"
                            ],
                            borderColor: [
                                "#003f5c",
                                "#2f4b7c",
                                "#f95d6a",
                                "#665191",
                                "#d45087",
                                "#ff7c43",
                                "#ffa600",
                                "#a05195",
                                "#6d5c16",
                                "#CCCCFF"
                            ],
                            barPercentage: 0.5,
                            barThickness: 6,
                            maxBarThickness: 8,
                            minBarLength: 0,
                            borderWidth: 1, // Specify bar border width
                            type: 'bar', // Set this data to a line chart
                            fill: false
                        }]
                    },
                    options: {
                        scales: {
                            y: {
                                beginAtZero: true
                            },
                        },
                        responsive: true, // Instruct chart js to respond nicely.
                        maintainAspectRatio: false, // Add to prevent default behaviour of full-width/height
                    }//                                borderColor: '#66aecf',
                });
            });
        },
    //    product categories doughnut graph
        render_product_category:function(){
            var self = this
            rpc.query({
                model: "stock.picking",
                method: "get_product_category",
            }).then(function (result) {
                var ctx = self.$("#product_category");
                // Define the data
                var name = result.name // Add data values to array
                var count = result.count
                var j = 0;
                Object.entries(result.count).forEach(([key, value]) => {
                    $('#category_table').append('<tr><td>'+name[j]+'</td><td>'+value+'</td></tr>')
                    j++;
                });
                $('#category_table').hide();
                var myChart = new Chart(ctx, {
                    type: 'doughnut',
                    data: {
                        labels: name,//x axis
                        datasets: [{
                            label: 'Quantity Done', // Name the series
                            data: count, // Specify the data values array
                            backgroundColor: [
                                "#003f5c",
                                "#2f4b7c",
                                "#f95d6a",
                                "#665191",
                                "#d45087",
                                "#ff7c43",
                                "#ffa600",
                                "#a05195",
                                "#6d5c16",
                                "#CCCCFF"
                            ],
                            borderColor: [
                                "#003f5c",
                            ],
                            barPercentage: 0.5,
                            barThickness: 6,
                            maxBarThickness: 8,
                            minBarLength: 0,
                            borderWidth: 1, // Specify bar border width
                            type: 'doughnut', // Set this data to a line chart
                            fill: false
                        }]
                    },
                    options: {
                        scales: {
                            y: {
                                beginAtZero: true
                            },
                        },
                        responsive: true, // Instruct chart js to respond nicely.
                        maintainAspectRatio: false, // Add to prevent default behaviour of full-width/height
                    }
                });
            });
        },
        //    product move line graph
        render_product_move_graph_this_month:function(){
            var self = this
            rpc.query({
                model: "stock.move.line",
                method: "get_product_moves",
            }).then(function (result) {
                var ctx = self.$("#product_move_graph");
                var name = result[0].name // Add data values to array
                var count = result[0].count
                var category_name = result[1].category_name
                var category_id = result[1].category_id
                 var j = 0;
                 var k = 0;
                Object.entries(result[1].category_name).forEach(([key, value]) => {
                    if(k == 0){
                        $('#product_move_selection').append('<option id="'+key+'" value="'+category_id[k]+'" selected="selected">'+value+'</option>')
                        k++;
                    }else{
                        $('#product_move_selection').append('<option id="'+key+'" value="'+category_id[k]+'">'+value+'</option>')
                        k++;
                    }
                });
                var opti = $(self.target).val();
            var option = $( "#product_move_selection" ).val();
            $('#product_move_table').hide();
            rpc.query({
                    model: "stock.move.line",
                    method: "product_move_by_category",
                    args: [option]
                }).then(function(result) {
                    var ctx = self.$("#product_move_graph");
                    var name = result.name
                    var count = result.count;
                    var j = 0;
                    Object.entries(result.count).forEach(([key, value]) => {
                        $('#product_move_table').append('<tr><td>'+name[j]+'</td><td>'+value+'</td></tr>')
                    j++;
                    });
                    $('#product_move_table').hide();
                    var myChart = new Chart(ctx, {
                        type: 'line',
                    data: {
                        labels: name,//x axis
                        datasets: [{
                            label: 'Quantity Done', // Name the series
                            data: count, // Specify the data values array
                            backgroundColor: '#003f5c',
                            borderColor: '#003f5c',
                            barPercentage: 0.5,
                            barThickness: 6,
                            maxBarThickness: 8,
                            minBarLength: 0,
                            borderWidth: 1, // Specify bar border width
                            type: 'line', // Set this data to a line chart
                            fill: false
                        }]
                    },
                    options: {
                        scales: {
                            y: {
                                beginAtZero: true
                            },
                        },
                        responsive: true, // Instruct chart js to respond nicely.
                        maintainAspectRatio: false, // Add to prevent default behaviour of full-width/height
                    }
                    });
                });
            });
        },
    //    stock moves pie graph
        render_stock_moves:function(){
            rpc.query({
                model: "stock.move",
                method: "get_stock_moves",
            }).then(function (result) {
                var ctx = self.$("#stock_moves");
                var name = result.name
                var count = result.count;
                var j = 0;
                Object.entries(result.count).forEach(([key, value]) => {
                    $('#stock_move_table').append('<tr><td>'+name[j]+'</td><td>'+value+'</td></tr>')
                    j++;
                    });
                $('#stock_move_table').hide();
                var myChart = new Chart(ctx, {
                    type: 'pie',
                    data: {
                        labels: name,//x axis
                        datasets: [{
                            label: 'Count', // Name the series
                            data: count, // Specify the data values array
                            backgroundColor: [
                                "#003f5c",
                                "#2f4b7c",
                                "#f95d6a",
                                "#665191",
                                "#d45087",
                                "#ff7c43",
                                "#ffa600",
                                "#a05195",
                                "#6d5c16",
                                "#CCCCFF"
                            ],
                            borderColor: [
                                "#003f5c",
                                "#2f4b7c",
                                "#f95d6a",
                                "#665191",
                                "#d45087",
                                "#ff7c43",
                                "#ffa600",
                                "#a05195",
                                "#6d5c16",
                                "#CCCCFF"
                            ],
                            barPercentage: 0.5,
                            barThickness: 6,
                            maxBarThickness: 8,
                            minBarLength: 0,
                            borderWidth: 1, // Specify bar border width
                            type: 'pie', // Set this data to a line chart
                            fill: false
                        }]
                    },
                    options: {
                        scales: {
                            y: {
                                beginAtZero: true
                            },
                        },
                        responsive: true, // Instruct chart js to respond nicely.
                        maintainAspectRatio: false, // Add to prevent default behaviour of full-width/height
                    }
                });
            });
        },
    //    location-on hand table
        render_storage_location:function(){
            var self = this
                rpc.query({
                    model: "stock.picking",
                    method: "get_locations",
                }).then(function (result) {
                     Object.entries(result).forEach(([key, value]) => {

                     $('#location_table').append('<tr><td>'+key+'</td><td class="location_table_value">'+value+'</td></tr>')
                });
            });
        },
//out of stock graph
        render_out_of_stock_graph:function(){
            var self = this
            rpc.query({
                model: "stock.quant",
                method: "get_out_of_stock",
            }).then(function (result) {
                if (result) {
                $('#graphs').append('<div class="year_to_date_graph_div col-sm-12 col-md-6 my-4">
                <div class="chart-container card-shadow" id="tiles"><div style="height: 20px; max-height: 20px;"><h2>Out of Stock Products</h2>
                <button class="btn_info" id="out_of_stock_info" title="Show Details"><i class="fa fa-ellipsis-v"></i></button>
                <table class="graph_details_table" id="out_of_stock_table"><tr><th>Products</th><th>Out of Quantity</th>
                </tr></table>
                </div><hr/><div class="graph_canvas" style="margin-top: 30px;"><canvas id="out_of_stock_graph" height="500px" width="150px"/>
                </div></div></div>')
                var ctx = self.$("#out_of_stock_graph");
                var name = result.product_name // Add data values to array
                var count = result.total_quantity
                var j = 0;
                Object.entries(name).forEach(([key, value]) => {
                    $('#out_of_stock_table').append('<tr><td>'+value+'</td><td>'+count[j]+'</td></tr>')
                    j++;
                });
                $('#out_of_stock_table').hide();
                var myChart = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: name,//x axis
                        datasets: [{
                            label: 'Current Stock', // Name the series
                            data: count, // Specify the data values array
                            backgroundColor: '#003f5c',
                            borderColor: '#003f5c',
                            barPercentage: 0.5,
                            barThickness: 6,
                            maxBarThickness: 8,
                            minBarLength: 0,
                            borderWidth: 1, // Specify bar border width
                            type: 'bar', // Set this data to a line chart
                            fill: false
                        }]
                    },
                    options: {
                        scales: {
                            y: {
                                beginAtZero: true
                            },
                        },
                        responsive: true, // Instruct chart js to respond nicely.
                        maintainAspectRatio: false, // Add to prevent default behaviour of full-width/height
                    }
                });
                }
            });
        },
//dead stock graph
        render_dead_of_stock_graph:function(){
            var self = this
            rpc.query({
                model: "stock.move",
                method: "get_dead_of_stock",
            }).then(function (result) {
                if (result) {
                $('#graphs').append('<div class="year_to_date_graph_div col-sm-12 col-md-6 my-4">
                <div class="chart-container card-shadow" id="tiles"><div style="height: 20px; max-height: 20px;"><h2>Dead Stock</h2>
                <button class="btn_info" id="dead_stock_info" title="Show Details"><i class="fa fa-ellipsis-v"></i></button>
                <table class="graph_details_table" id="dead_stock_table"><tr><th>Products</th><th>Dead Quantity</th>
                </tr></table>
                </div><hr/><div class="graph_canvas" style="margin-top: 30px;"><canvas id="dead_stock_graph" height="500px" width="150px"/>
                </div></div></div>')
                var ctx = self.$("#dead_stock_graph");
                var name = result.product_name // Add data values to array
                var count = result.total_quantity
                var j = 0;
                Object.entries(name).forEach(([key, value]) => {
                    $('#dead_stock_table').append('<tr><td>'+value+'</td><td>'+count[j]+'</td></tr>')
                    j++;
                });
                $('#dead_stock_table').hide();
                var myChart = new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: name,//x axis
                        datasets: [{
                            label: 'Current Stock', // Name the series
                            data: count, // Specify the data values array
                            backgroundColor: '#003f5c',
                            borderColor: '#003f5c',
                            barPercentage: 0.5,
                            barThickness: 6,
                            maxBarThickness: 8,
                            minBarLength: 0,
                            borderWidth: 1, // Specify bar border width
                            type: 'line', // Set this data to a line chart
                            fill: false
                        }]
                    },
                    options: {
                        scales: {
                            y: {
                                beginAtZero: true
                            },
                        },
                        responsive: true, // Instruct chart js to respond nicely.
                        maintainAspectRatio: false, // Add to prevent default behaviour of full-width/height
                    }
                });
                }
            });
        },
    //    event functions
    //top product selection
        onclick_top_product_selection:function(events){
            var option = $(events.target).val();
            if (option == 'top_last_10_days'){
            var self = this
            rpc.query({
                model: "stock.move",
                method: "top_products_last_ten",
            }).then(function (result) {
                var ctx = self.$("#canvaspie");
                // Define the data
                var products = result.products // Add data values to array
                var count = result.count;
                var j = 0;
                $('#pro_info td').remove();
                Object.entries(result.count).forEach(([key, value]) => {
                    $('#pro_info').append('<tr><td>'+products[j]+'</td><td>'+value+'</td></tr>')
                    j++;
                    });
                $('#pro_info').hide();
                var myChart = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: products,//x axis
                        datasets: [{
                            label: 'Count', // Name the series
                            data: count, // Specify the data values array
                            backgroundColor: [
                                "#003f5c",
                                "#2f4b7c",
                                "#f95d6a",
                                "#665191",
                                "#d45087",
                                "#ff7c43",
                                "#ffa600",
                                "#a05195",
                                "#6d5c16",
                                "#CCCCFF"
                            ],
                            borderColor: [
                                "#003f5c",
                                "#2f4b7c",
                                "#f95d6a",
                                "#665191",
                                "#d45087",
                                "#ff7c43",
                                "#ffa600",
                                "#a05195",
                                "#6d5c16",
                                "#CCCCFF"
                            ],
                            barPercentage: 0.5,
                            barThickness: 6,
                            maxBarThickness: 8,
                            minBarLength: 0,
                            borderWidth: 1, // Specify bar border width
                            type: 'bar', // Set this data to a line chart
                            fill: false
                        }]
                    },
                    options: {
                        scales: {
                            y: {
                                beginAtZero: true
                            },
                        },
                        responsive: true, // Instruct chart js to respond nicely.
                        maintainAspectRatio: false, // Add to prevent default behaviour of full-width/height
                    }
                });
            });
            }
            if (option == 'top_last_30_days'){
                var self = this;
                rpc.query({
                model: "stock.move",
                method: "top_products_last_thirty",
            }).then(function (result) {
                var ctx = self.$("#canvaspie");
                // Define the data
                var products = result.products // Add data values to array
                var count = result.count;
                var j = 0;
                $('#pro_info td').remove();
                Object.entries(result.count).forEach(([key, value]) => {
                    $('#pro_info').append('<tr><td>'+products[j]+'</td><td>'+value+'</td></tr>')
                    j++;
                    });
                $('#pro_info').hide();
                var myChart = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: products,//x axis
                        datasets: [{
                            label: 'Count', // Name the series
                            data: count, // Specify the data values array
                            backgroundColor: [
                                "#003f5c",
                                "#2f4b7c",
                                "#f95d6a",
                                "#665191",
                                "#d45087",
                                "#ff7c43",
                                "#ffa600",
                                "#a05195",
                                "#6d5c16",
                                "#CCCCFF"
                            ],
                            borderColor: [
                                "#003f5c",
                                "#2f4b7c",
                                "#f95d6a",
                                "#665191",
                                "#d45087",
                                "#ff7c43",
                                "#ffa600",
                                "#a05195",
                                "#6d5c16",
                                "#CCCCFF"
                            ],
                            barPercentage: 0.5,
                            barThickness: 6,
                            maxBarThickness: 8,
                            minBarLength: 0,
                            borderWidth: 1, // Specify bar border width
                            type: 'bar', // Set this data to a line chart
                            fill: false
                        }]
                    },
                    options: {
                        scales: {
                            y: {
                                beginAtZero: true
                            },
                        },
                        responsive: true, // Instruct chart js to respond nicely.
                        maintainAspectRatio: false, // Add to prevent default behaviour of full-width/height
                    }
                });
            });
            }
            if (option == 'top_last_3_month'){
                var self = this;
                rpc.query({
                model: "stock.move",
                method: "top_products_last_three_months",
            }).then(function (result) {
                var ctx = self.$("#canvaspie");
                var products = result.products // Add data values to array
                var count = result.count;
                var j = 0;
                $('#pro_info td').remove();
                Object.entries(result.count).forEach(([key, value]) => {
                    $('#pro_info').append('<tr><td>'+products[j]+'</td><td>'+value+'</td></tr>')
                    j++;
                    });
                $('#pro_info').hide();
                var myChart = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: products,//x axis
                        datasets: [{
                            label: 'Count', // Name the series
                            data: count, // Specify the data values array
                            backgroundColor: [
                                "#003f5c",
                                "#2f4b7c",
                                "#f95d6a",
                                "#665191",
                                "#d45087",
                                "#ff7c43",
                                "#ffa600",
                                "#a05195",
                                "#6d5c16",
                                "#CCCCFF"
                            ],
                            borderColor: [
                                "#003f5c",
                                "#2f4b7c",
                                "#f95d6a",
                                "#665191",
                                "#d45087",
                                "#ff7c43",
                                "#ffa600",
                                "#a05195",
                                "#6d5c16",
                                "#CCCCFF"
                            ],

                            barPercentage: 0.5,
                            barThickness: 6,
                            maxBarThickness: 8,
                            minBarLength: 0,
                            borderWidth: 1, // Specify bar border width
                            type: 'bar', // Set this data to a line chart
                            fill: false
                        }]
                    },
                    options: {
                        scales: {
                            y: {
                                beginAtZero: true
                            },
                        },
                        responsive: true, // Instruct chart js to respond nicely.
                        maintainAspectRatio: false, // Add to prevent default behaviour of full-width/height
                    }
                });
            });
            }
            if (option == 'top_last_year'){
                var self = this;
                rpc.query({
                model: "stock.move",
                method: "top_products_last_year",
            }).then(function (result) {
                var ctx = self.$("#canvaspie");
                var products = result.products // Add data values to array
                var count = result.count;
                var j = 0;
                $('#pro_info td').remove();
                Object.entries(result.count).forEach(([key, value]) => {
                    $('#pro_info').append('<tr><td>'+products[j]+'</td><td>'+value+'</td></tr>')
                    j++;
                    });
                $('#pro_info').hide();
                var myChart = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: products,//x axis
                        datasets: [{
                            label: 'Count', // Name the series
                            data: count, // Specify the data values array
                            backgroundColor: [
                                "#003f5c",
                                "#2f4b7c",
                                "#f95d6a",
                                "#665191",
                                "#d45087",
                                "#ff7c43",
                                "#ffa600",
                                "#a05195",
                                "#6d5c16",
                                "#CCCCFF"
                            ],
                            borderColor: [
                                "#003f5c",
                                "#2f4b7c",
                                "#f95d6a",
                                "#665191",
                                "#d45087",
                                "#ff7c43",
                                "#ffa600",
                                "#a05195",
                                "#6d5c16",
                                "#CCCCFF"
                            ],
                            barPercentage: 0.5,
                            barThickness: 6,
                            maxBarThickness: 8,
                            minBarLength: 0,
                            borderWidth: 1, // Specify bar border width
                            type: 'bar', // Set this data to a line chart
                            fill: false
                        }]
                    },
                    options: {
                        scales: {
                            y: {
                                beginAtZero: true
                            },
                        },
                        responsive: true, // Instruct chart js to respond nicely.
                        maintainAspectRatio: false, // Add to prevent default behaviour of full-width/height
                    }
                });
            });
            }
        },
    //    stock moves this_mont,last_year change
        onclick_stock_moves_selection:function(events){
            var option = $(events.target).val();
            if (option == 'last_10_days'){
                rpc.query({
                    model: "stock.move",
                    method: "stock_move_last_ten_days",
                    args: [option]
                }).then(function(result) {
                    var ctx = self.$("#stock_moves");
                    var name = result.name
                    var count = result.count;
                    $('#stock_move_table td').remove();
                    var j = 0;
                    Object.entries(result.count).forEach(([key, value]) => {
                        $('#stock_move_table').append('<tr><td>'+name[j]+'</td><td>'+value+'</td></tr>')
                        j++;
                        });
                    $('#stock_move_table').hide();
                    var myChart = new Chart(ctx, {
                        type: 'pie',
                        data: {
                            labels: name,//x axis
                            datasets: [{
                                label: 'Count', // Name the series
                                data: count, // Specify the data values array
                                backgroundColor: [
                                    "#003f5c",
                                    "#2f4b7c",
                                    "#f95d6a",
                                    "#665191",
                                    "#d45087",
                                    "#ff7c43",
                                    "#ffa600",
                                    "#a05195",
                                    "#6d5c16",
                                    "#CCCCFF"
                                ],
                                borderColor: [
                                    "#003f5c",
                                    "#2f4b7c",
                                    "#f95d6a",
                                    "#665191",
                                    "#d45087",
                                    "#ff7c43",
                                    "#ffa600",
                                    "#a05195",
                                    "#6d5c16",
                                    "#CCCCFF"
                                ],
                                barPercentage: 0.5,
                                barThickness: 6,
                                maxBarThickness: 8,
                                minBarLength: 0,
                                borderWidth: 1, // Specify bar border width
                                type: 'pie', // Set this data to a line chart
                                fill: false
                            }]
                        },
                        options: {
                            scales: {
                                y: {
                                    beginAtZero: true
                                },
                            },
                            responsive: true, // Instruct chart js to respond nicely.
                            maintainAspectRatio: false, // Add to prevent default behaviour of full-width/height
                        }
                    });
                });
            }
            if (option == 'this_month'){
                rpc.query({
                    model: "stock.move",
                    method: "this_month",
                    args: [option]
                }).then(function(result) {
                    var ctx = self.$("#stock_moves");
                    var name = result.name
                    var count = result.count;
                    var j = 0;
                    $('#stock_move_table td').remove();
                    Object.entries(result.count).forEach(([key, value]) => {
                        $('#stock_move_table').append('<tr><td>'+name[j]+'</td><td>'+value+'</td></tr>')
                    j++;
                    });
                $('#stock_move_table').hide();
                    var myChart = new Chart(ctx, {
                        type: 'pie',
                        data: {
                            labels: name,//x axis
                            datasets: [{
                                label: 'Count', // Name the series
                                data: count, // Specify the data values array
                                backgroundColor: [
                                    "#003f5c",
                                    "#2f4b7c",
                                    "#f95d6a",
                                    "#665191",
                                    "#d45087",
                                    "#ff7c43",
                                    "#ffa600",
                                    "#a05195",
                                    "#6d5c16",
                                    "#CCCCFF"
                                ],
                                borderColor: [
                                    "#003f5c",
                                    "#2f4b7c",
                                    "#f95d6a",
                                    "#665191",
                                    "#d45087",
                                    "#ff7c43",
                                    "#ffa600",
                                    "#a05195",
                                    "#6d5c16",
                                    "#CCCCFF"
                                ],
                                barPercentage: 0.5,
                                barThickness: 6,
                                maxBarThickness: 8,
                                minBarLength: 0,
                                borderWidth: 1, // Specify bar border width
                                type: 'pie', // Set this data to a line chart
                                fill: false
                            }]
                        },
                        options: {
                            scales: {
                                y: {
                                    beginAtZero: true
                                },
                            },
                            responsive: true, // Instruct chart js to respond nicely.
                            maintainAspectRatio: false, // Add to prevent default behaviour of full-width/height
                        }
                    });
                });
            }
            if (option == 'last_3_month'){
                rpc.query({
                    model: "stock.move",
                    method: "last_three_month",
                    args: [option]
                }).then(function(result) {
                    var ctx = self.$("#stock_moves");
                    var name = result.name
                    var count = result.count;
                    var j = 0;
                    $('#stock_move_table td').remove();
                    Object.entries(result.count).forEach(([key, value]) => {
                        $('#stock_move_table').append('<tr><td>'+name[j]+'</td><td>'+value+'</td></tr>')
                    j++;
                    });
                $('#stock_move_table').hide();
                    var myChart = new Chart(ctx, {
                        type: 'pie',
                        data: {
                            labels: name,//x axis
                            datasets: [{
                                label: 'Count', // Name the series
                                data: count, // Specify the data values array
                                backgroundColor: [
                                    "#003f5c",
                                    "#2f4b7c",
                                    "#f95d6a",
                                    "#665191",
                                    "#d45087",
                                    "#ff7c43",
                                    "#ffa600",
                                    "#a05195",
                                    "#6d5c16",
                                    "#CCCCFF"
                                ],
                                borderColor: [
                                    "#003f5c",
                                    "#2f4b7c",
                                    "#f95d6a",
                                    "#665191",
                                    "#d45087",
                                    "#ff7c43",
                                    "#ffa600",
                                    "#a05195",
                                    "#6d5c16",
                                    "#CCCCFF"
                                ],
                                barPercentage: 0.5,
                                barThickness: 6,
                                maxBarThickness: 8,
                                minBarLength: 0,
                                borderWidth: 1, // Specify bar border width
                                type: 'pie', // Set this data to a line chart
                                fill: false
                            }]
                        },
                        options: {
                            scales: {
                                y: {
                                    beginAtZero: true
                                },
                            },
                            responsive: true, // Instruct chart js to respond nicely.
                            maintainAspectRatio: false, // Add to prevent default behaviour of full-width/height
                        }
                    });
                });
            }
            else if (option == 'last_year'){
                rpc.query({
                    model: "stock.move",
                    method: "last_year",
                    args: [option]
                }).then(function(result) {
                var ctx = self.$("#stock_moves");
                    var name = result.name
                    var count = result.count;
                    var j = 0;
                    $('#stock_move_table td').remove();
                    Object.entries(result.count).forEach(([key, value]) => {
                        $('#stock_move_table').append('<tr><td>'+name[j]+'</td><td>'+value+'</td></tr>')
                    j++;
                    });
                $('#stock_move_table').hide();
                    var myChart = new Chart(ctx, {
                        type: 'pie',
                        data: {
                            labels: name,//x axis
                            datasets: [{
                                label: 'Count', // Name the series
                                data: count, // Specify the data values array
                                backgroundColor: [
                                    "#003f5c",
                                    "#2f4b7c",
                                    "#f95d6a",
                                    "#665191",
                                    "#d45087",
                                    "#ff7c43",
                                    "#ffa600",
                                    "#a05195",
                                    "#6d5c16",
                                    "#CCCCFF"
                                ],
                                borderColor: [
                                    "#003f5c",
                                    "#2f4b7c",
                                    "#f95d6a",
                                    "#665191",
                                    "#d45087",
                                    "#ff7c43",
                                    "#ffa600",
                                    "#a05195",
                                    "#6d5c16",
                                    "#CCCCFF"
                                ],
                                barPercentage: 0.5,
                                barThickness: 6,
                                maxBarThickness: 8,
                                minBarLength: 0,
                                borderWidth: 1, // Specify bar border width
                                type: 'pie', // Set this data to a line chart
                                fill: false
                            }]
                        },
                        options: {
                            scales: {
                                y: {
                                    beginAtZero: true
                                },
                            },
                            responsive: true, // Instruct chart js to respond nicely.
                            maintainAspectRatio: false, // Add to prevent default behaviour of full-width/height
                        }
                    });
                });
            }
        },
//    product move selection
        onclick_product_moves_selection:function(events){
            var option = $(events.target).val();
                var self = this
                rpc.query({
                    model: "stock.move.line",
                    method: "product_move_by_category",
                    args: [option]
                }).then(function(result) {
                    var ctx = self.$("#product_move_graph");
                    var name = result.name
                    var count = result.count;
                    var j = 0;
                    $('#product_move_table td').remove();
                    Object.entries(result.count).forEach(([key, value]) => {
                        $('#product_move_table').append('<tr><td>'+name[j]+'</td><td>'+value+'</td></tr>')
                    j++;
                    });
                    $('#product_move_table').hide();
                    var myChart = new Chart(ctx, {
                        type: 'line',
                    data: {
                        labels: name,//x axis
                        datasets: [{
                            label: 'Quantity Done', // Name the series
                            data: count, // Specify the data values array
                            backgroundColor: '#003f5c',
                            borderColor: '#003f5c',
                            barPercentage: 0.5,
                            barThickness: 6,
                            maxBarThickness: 8,
                            minBarLength: 0,
                            borderWidth: 1, // Specify bar border width
                            type: 'line', // Set this data to a line chart
                            fill: false
                        }]
                    },
                    options: {
                        scales: {
                            y: {
                                beginAtZero: true
                            },
                        },
                        responsive: true, // Instruct chart js to respond nicely.
                        maintainAspectRatio: false, // Add to prevent default behaviour of full-width/height
                    }
                    });
                });
        },
    //    tile click
        onclick_tiles: function(f) {
            var id = parseInt(this.$(f.currentTarget).attr('id'));
            var options = {
                on_reverse_breadcrumb: this.on_reverse_breadcrumb,
            };
            this.do_action({
                name: _t(result_3[this.$(f.currentTarget).attr('id')]),
                type: 'ir.actions.act_window',
                res_model: 'stock.picking',
                view_mode: 'tree,form,calendar',
                views: [[false, 'list'],[false, 'form']],
                domain: [['picking_type_id', '=', id]],
                target: 'current',
            }, options);
        },
    //    tile late status onclick
        onclick_late_status: function(f) {
            f.stopPropagation();
            var id = parseInt(this.$(f.currentTarget).attr('id'));
            var v ='/Late'
            var options = {
                on_reverse_breadcrumb: this.on_reverse_breadcrumb,
            };
            this.do_action({
                name: _t(result_3[id]+v),
                type: 'ir.actions.act_window',
                res_model: 'stock.picking',
                view_mode: 'tree,form,calendar',
                views: [[false, 'list'],[false, 'form']],
                domain: [['picking_type_id', '=', id],['state', 'in', ['assigned', 'waiting', 'confirmed']],['scheduled_date', '<=', moment().format('YYYY-MM-DD')],],
                target: 'current',
            }, options)
        },
    //    tile waiting status onclick
        onclick_waiting_status: function(f) {
            f.stopPropagation();
            var id = parseInt(this.$(f.currentTarget).attr('id'));
            var options = {
                on_reverse_breadcrumb: this.on_reverse_breadcrumb,
            };
            this.do_action({
                name: _t(result_3[id]+'/Waiting'),
                type: 'ir.actions.act_window',
                res_model: 'stock.picking',
                view_mode: 'tree,form,calendar',
                views: [[false, 'list'],[false, 'form']],
                domain: [['picking_type_id', '=', id],['state', '=', 'confirmed']],
                target: 'current',
            }, options)
        },
    //    tile backorder status onclick
        onclick_backorders_status: function(f) {
            f.stopPropagation();
            var id = parseInt(this.$(f.currentTarget).attr('id'));
            var options = {
                on_reverse_breadcrumb: this.on_reverse_breadcrumb,
            };
            this.do_action({
                name: _t(result_3[id]+'/Backorders'),
                type: 'ir.actions.act_window',
                res_model: 'stock.picking',
                view_mode: 'tree,form,calendar',
                views: [[false, 'list'],[false, 'form']],
                domain: [['picking_type_id', '=', id],['backorder_id', '!=', false]],
                target: 'current',
            }, options)
        },
    //    top ten product show details button click
        onclick_top_product_info: function(f) {
            var x = document.getElementById("pro_info");
            if (x.style.display === "none") {
                x.style.display = "block";
              } else {
                x.style.display = "none";
            }
        },
    //    product category graph show details button click
        onclick_pro_cate_info: function(f) {
            var x = document.getElementById("category_table");
            if (x.style.display === "none") {
                x.style.display = "block";
              } else {
                x.style.display = "none";
            }
        },
    //    stock moves show details button click
        onclick_location_info: function(f) {
            var x = document.getElementById("location_table");
            if (x.style.display === "none") {
                x.style.display = "block";
              } else {
                x.style.display = "none";
            }
        },
    //    operation types table show details button click
        onclick_operation_type_info: function(f) {
            var x = document.getElementById("operation_type_table");
            if (x.style.display === "none") {
                x.style.display = "block";
              } else {
                x.style.display = "none";
            }
        },
        //    dead stock table show details button click
        onclick_dead_stock_info: function(f) {
            var x = document.getElementById("dead_stock_table");
            if (x.style.display === "none") {
                x.style.display = "block";
              } else {
                x.style.display = "none";
            }
        },
        //    out of stock table show details button click
        onclick_out_of_stock_info: function(f) {
            var x = document.getElementById("out_of_stock_table");
            if (x.style.display === "none") {
                x.style.display = "block";
              } else {
                x.style.display = "none";
            }
        },
//    click product move info
        onclick_product_move_info: function(f) {
            var x = document.getElementById("product_move_table");
            if (x.style.display === "none") {
                x.style.display = "block";
              } else {
                x.style.display = "none";
            }
        },
//    click stock move info
        onclick_stock_move_info: function(f) {
            var x = document.getElementById("stock_move_table");
            if (x.style.display === "none") {
                x.style.display = "block";
              } else {
                x.style.display = "none";
            }
        },
    });
    core.action_registry.add('inventory_dashboard_tag', DashBoard);
    return;
});
