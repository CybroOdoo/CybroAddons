odoo.define("product_management_app.ProductDashboard", function (require) {
    "use strict";
    var AbstractAction = require('web.AbstractAction');
    var core = require('web.core');
    var QWeb = core.qweb;
    var web_client = require('web.web_client');
    var session = require('web.session');
    var ajax = require('web.ajax');
    var _t = core._t;
    var rpc = require('web.rpc');
    var self = this;
    var DashBoard = AbstractAction.extend({
        contentTemplate: 'ProductDashboard',
        events: {
            'change #prod_selection': 'onchange_prod_selection',
            'change #product_location_selection': 'onchange_location_selection',
        },

        init: function(parent, context) {
            this._super(parent, context);
            this.dashboard_templates = ['ProductMainSection', 'ProductGraphs'];
        },
        start: function() {
            var self = this;
            this.set("title", 'Dashboard');
            return this._super().then(function() {
                self.render_dashboards();
                self.render_graphs();
            });
        },
        willStart: function(){
            var self = this;
            return this._super()
        },
        render_dashboards: function() {
            var self = this;
            this.fetch_data()
            var templates = []
            var templates = ['ProductMainSection', 'ProductGraphs'];
            _.each(templates, function(template) {
                self.$('.o_hr_dashboard').append(QWeb.render(template, {widget: self}))
            });
        },
        fetch_data: function() {
            var self = this
//          fetch data to the tiles
            var def1 = this._rpc({
                model: 'product.template',
                method: "get_data",
            })
            .then(function (result) {
                $('#product_templates').append('<span>' + result.product_templates + '</span>');
                $('#variants_count').append('<span>' + result.product_variants + '</span>');
                $('#products_storable').append('<span>' + result.storable + '</span>');
                $('#product_consumable').append('<span>' + result.consumable + '</span>');
                $('#product_service').append('<span>' + result.service + '</span>');
                $('#product_categ').append('<span>' + result.category + '</span>');
                $('#product_pricelist').append('<span>' + result.price_list + '</span>');
                $('#product_attribute').append('<span>' + result.product_attribute + '</span>');
            });
        },
        on_reverse_breadcrumb: function() {
            var self = this;
            web_client.do_push_state({});
            this.update_cp();
            this.fetch_data().then(function() {
                self.$('.o_hr_dashboard').reload();
                self.render_dashboards();
            });
        },
        render_graphs: function(){
            var self = this;
            self.render_top_sold_product();
            self.render_top_purchase_product();
            self.render_monthly_chart();
            self.render_product_categ_analysis();
        },
        render_top_sold_product: function() {
            var self = this
            var ctx = self.$(".top_sale_chart");
            rpc.query({
                model: "product.template",
                method: 'get_top_sale_data',
            }).then(function (arrays) {
                var data = {
                    labels : arrays[1],
                    datasets: [{
                        label: "",
                        data: arrays[0],
                        backgroundColor: [
                            "#1E90FF",
                            "#95B9C7",
                            "#66CDAA",
                            "#FF7F50",
                            "#F67280",
                            "#810541",
                            "#7D0552",
                            "#D58A94",
                            "#B041FF"
                        ],
                        borderColor: [
                            "#1E90FF",
                            "#95B9C7",
                            "#66CDAA",
                            "#FF7F50",
                            "#F67280",
                            "#810541",
                            "#7D0552",
                            "#D58A94",
                            "#B041FF"
                        ],
                        borderWidth: 1
                    },]
                };

                //options
                var options = {
                    responsive: true,
                    title: false,
                    legend: {
                        display: true,
                        position: "right",
                        labels: {
                            fontColor: "#333",
                            fontSize: 16
                        }
                    },
                    scales: {
                        yAxes: [{
                            gridLines: {
                                color: "rgba(0, 0, 0, 0)",
                                display: false,
                            },
                            ticks: {
                                min: 0,
                                display: false,
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
        render_top_purchase_product: function() {
            var self = this
            var ctx = self.$(".top_purchase_chart");
            rpc.query({
                model: "product.template",
                method: 'get_top_purchase_data',
            }).then(function (arrays) {
                var data = {
                    labels : arrays[1],
                    datasets: [{
                        label: "",
                        data: arrays[0],
                        backgroundColor: [
                            "#003f5c",
                            "#2f4b7c",
                            "#f95d6a",
                            "#665191",
                            "#d45087",
                            "#ff7c43",
                            "#ffa600",
                            "#a05195",
                            "#6d5c16"
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
                            "#6d5c16"
                        ],
                        borderWidth: 1
                    },]
                };

                //options
                var options = {
                    responsive: true,
                    title: false,
                    legend: {
                        display: true,
                        position: "right",
                        labels: {
                            fontColor: "#333",
                            fontSize: 16
                        }
                    },
                    scales: {
                        yAxes: [{
                            gridLines: {
                                color: "rgba(0, 0, 0, 0)",
                                display: false,
                            },
                            ticks: {
                                min: 0,
                                display: false,
                            }
                        }]
                    }
                };
                //create Chart class object
                var chart = new Chart(ctx, {
                    type: "doughnut",
                    data: data,
                    options: options
                });
            });
        },
        render_product_categ_analysis: function() {
            rpc.query({
                model: "product.template",
                method: 'get_product_location_analysis',
            }).then(function (result) {
                var ctx = $("#product_categ_purchases");
//                var name = result[0].name // Add data values to array
//                var count = result[0].count
                var location_name = result.location_name
                var location_id = result.location_id
                var j = 0;
                var k = 0;
                Object.entries(result.location_name).forEach(([key, value]) => {
                    if(k == 0){
                        $('#product_location_selection').append('<option id="'+key+'" value="'+location_id[k]+'" selected="selected">'+value+'</option>')
                        k++;
                    }else{
                        $('#product_location_selection').append('<option id="'+key+'" value="'+location_id[k]+'">'+value+'</option>')
                        k++;
                    }

                });
                $('#product_categ_table').hide();
                var option = $( "#product_location_selection" ).val();
                rpc.query({
                    model: "product.template",
                    method: "get_product_qty_by_loc",
                    args: [option]
                }).then(function(result) {
                    var product = result.products
                    var product = result.quantity
                    var ctx = $("#product_qty");
                    var myChart = new Chart(ctx, {
                        type: 'bar',
                        data: {
                            labels: product,//x axis
                            datasets: [{
                                label: 'Count', // Name the series
                                data: product, // Specify the data values array
                                backgroundColor: '#ac3973',
                                borderColor: '#ac3973',
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
            });

        },
        render_monthly_chart: function(e) {
            rpc.query({
                model: "product.template",
                method: 'get_products',
            }).then(function (result) {
                var ctx = $("#purchase_product");

                var product_id = result.product_id
                var product_name = result.product_name
                var j = 0;
                var k = 0;
                Object.entries(result.product_name).forEach(([key, value]) => {
                    if(k == 0){
                        $('#prod_selection').append('<option id="'+key+'" value="'+product_id[k]+'" selected="selected">'+value+'</option>')
                        k++;
                    }else{
                        $('#prod_selection').append('<option id="'+key+'" value="'+product_id[k]+'">'+value+'</option>')
                        k++;
                    }

                });
                var option = $( "#prod_selection" ).val();
                rpc.query({
                    model: "product.template",
                    method: 'get_prod_details',
                    args: [option]
                }).then(function (result) {
                    $("#purchase_product").empty();
                    var ctx = $("#purchase_product");
                    var name = result.name
                    var count = result.count;
                    var sum = result.sum;
                    var j = 0;
                    if (result) {
                    $('#purchase_product').append('
                    <div class="graph_canvas" style="margin-top: 30px;">
                        <canvas id="partner_graph" height="500px" width="150px"/>
                    </div>')
                    var ctx = $("#partner_graph");
                    var name = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

                    var j = 0;

                    if (window.myChart_year != undefined)
                        window.myChart_year.destroy();
                    window.myChart_year = new Chart(ctx, {
                        type: 'line',
                        data: {
                            labels: name,//x axis
                            datasets: [
                            {
                                label: 'Product Moves', // Name the series
                                data: count, // Specify the data values array
                                backgroundColor: '#0000ff',
                                borderColor: '#0000ff',
                                barPercentage: 0.5,
                                barThickness: 6,
                                maxBarThickness: 8,
                                minBarLength: 0,
                                borderWidth: 1, // Specify bar border width
                                type: 'line', // Set this data to a line chart
                                fill: false
                            },]
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
            });
        },
        onchange_prod_selection: function() {
            var option = $( "#prod_selection" ).val();
            rpc.query({
                model: "product.template",
                method: 'get_prod_details',
                args: [option]
            }).then(function (result) {
                $("#purchase_product").empty();
                var ctx = $("#purchase_product");
                var name = result.name
                var count = result.count;
                var sum = result.sum;
                var j = 0;
                if (result) {
                $('#purchase_product').append('
                <div class="graph_canvas" style="margin-top: 30px;">
                    <canvas id="partner_graph" height="500px" width="150px"/>
                </div>')
                var ctx = $("#partner_graph");
                var name = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

                var j = 0;

                if (window.myChart_year != undefined)
                    window.myChart_year.destroy();
                window.myChart_year = new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: name,//x axis
                        datasets: [
                        {
                            label: 'Purchase Order Total', // Name the series
                            data: count, // Specify the data values array
                            backgroundColor: '#0000ff',
                            borderColor: '#0000ff',
                            barPercentage: 0.5,
                            barThickness: 6,
                            maxBarThickness: 8,
                            minBarLength: 0,
                            borderWidth: 1, // Specify bar border width
                            type: 'line', // Set this data to a line chart
                            fill: false
                        },]
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
        onchange_location_selection: function() {
            var option = $( "#product_location_selection" ).val();
            rpc.query({
                model: "product.template",
                method: "get_product_qty_by_loc",
                args: [option]
            }).then(function(result) {
                var product = result.products
                var quantity = result.quantity
                var ctx = $("#product_qty");
                var myChart = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: product,//x axis
                        datasets: [{
                            label: 'Count', // Name the series
                            data: quantity, // Specify the data values array
                            backgroundColor: '#ac3973',
                            borderColor: '#ac3973',
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
    });
    core.action_registry.add('product_dashboard_tag', DashBoard);
    return DashBoard;
});