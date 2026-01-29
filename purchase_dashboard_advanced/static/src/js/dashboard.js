odoo.define('purchase_dashboard_advanced.PurchaseDashboard', function (require) {
    'use strict';
    var AbstractAction = require('web.AbstractAction');
    var core = require('web.core');
    var _t = core._t;
    var QWeb = core.qweb;
    var ajax = require('web.ajax');
    var rpc = require('web.rpc');

    var PurchaseDashboard = AbstractAction.extend({
        template: 'PurchaseDashboard',
        events: {
            'click .purchase_order_all': 'purchase_order_all',
            'click .po_priority_orders': 'po_priority_orders',
            'change #select_mode': 'onchange_select_mode',
            'change #select_chart': 'onchange_select_chart',
            'change #product_categ_selection': 'onchange_product_categ',
            'change #vendor_selection': 'onchange_vendor_selection',
        },
        init: function () {
            /**
            * Initializes an object with a list of dashboard template names.
            *
            * @returns {undefined}
            */
            this._super.apply(this, arguments);
            this.dashboard_templates = ['PurchaseMain', 'Top'];
        },

        start: function() {
            /**
            * Initializes the PurchaseDashboard and renders dashboards and graphs.
            *
            * @function
            * @memberof PurchaseDashboard
            * @returns {Promise<void>} A Promise that resolves when rendering is complete.
            */
            var self = this;
            this.set("title", 'PurchaseDashboard');
            return this._super().then(function() {
                self.render_dashboards();
                self.render_graphs();
            });
        },

        willStart: function() {
            /**
            * Executes a series of asynchronous operations and returns a Promise that resolves when all operations are complete.
            *
            * @returns {Promise} A Promise that resolves when all asynchronous operations are complete.
            */
            var self = this;
            return $.when(ajax.loadLibs(this), this._super()).then(function() {
                return self.fetch_data();
            });
        },

        render_graphs: function(){
            /**
            * Renders the graphs for the PurchaseDashboard.
            *
            * @function
            * @memberof PurchaseDashboard
            * @returns {void}
            */
            var self = this;
            self.render_top_product();
            self.render_line_chart();
            self.render_product_categ_analysis();
            self.render_fusion_chart();
        },

        render_dashboards: function() {
            /**
            * Renders the dashboards for the PurchaseDashboard.
            *
            * @function
            * @memberof PurchaseDashboard
            * @returns {void}
            */
            var self = this;
            _.each(this.dashboard_templates, function(template) {
                    self.$el.find('.o_purchase_dashboard').append(QWeb.render(template, {widget: self}));
            });
        },

        purchase_order_all: function(e) {
            /**
            * Handles the click event of the "Purchase Order All" button, opening a list view of purchase orders.
            *
            * @function
            * @memberof PurchaseDashboard
            * @param {MouseEvent} e - The click event.
            * @returns {void}
            */
            var self = this;
            e.stopPropagation();
            e.preventDefault();
            if(this.purchase_orders) {
                var options = {
                    on_reverse_breadcrumb: self.on_reverse_breadcrumb,
                };
                self.do_action({
                    name: _t("Purchase Order"),
                    type: 'ir.actions.act_window',
                    res_model: 'purchase.order',
                    view_mode: 'tree,form',
                    views: [[false, 'list'],[false, 'form']],
                    domain: [['state','in', ['purchase', 'done']]],
                    target: 'current'
                }, options)
            }
        },

        render_line_chart: function(e) {
        var self=this
            /**
            * Renders a line chart of purchase orders by month.
            *
            * @function
            * @memberof PurchaseDashboard
            * @param {MouseEvent} e - The click event (optional).
            * @returns {void}
            */
            rpc.query({
                model: "purchase.order",
                method: 'get_orders_by_month',
            }).then(function (arrays) {
                var ctx = self.el.querySelector("#canvas");
                var month = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                var count = arrays.count;
                new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: month,
                        datasets: [{
                            label: 'Count',
                            data: count,
                            backgroundColor: '#ac3973',
                            borderColor: '#ac3973',
                            barPercentage: 0.5,
                            barThickness: 6,
                            maxBarThickness: 8,
                            minBarLength: 0,
                            borderWidth: 1,
                            type: 'bar',
                            fill: false
                        }]
                    },
                    options: {
                        scales: {
                            y: {
                                beginAtZero: true
                            },
                        },
                        responsive: true,
                        maintainAspectRatio: false,
                    }
                });
           });
        },

        render_product_categ_analysis: function(e) {
            /**
            Render the product category analysis chart based on the purchase order lines.
            @function
            @name render_product_categ_analysis
            @memberof PurchaseDashboardWidget
            @param {Event} e - The event object.
            @returns {void}
            */
            var self = this
            rpc.query({
                model: "purchase.order.line",
                method: 'product_categ_analysis',
            }).then(function (result) {
                var ctx = self.$el.find("#product_categ_purchases");
                var count = result[0].count
                var category_name = result[1].category_name
                var category_id = result[1].category_id
                var count = 0;
                Object.entries(result[1].category_name).forEach(([key, value]) => {
                    if(count == 0){
                        self.$el.find('#product_categ_selection').append('<option id="'+key+'" value="'+category_id[count]+'" selected="selected">'+value+'</option>')
                        count++;
                    }else{
                        self.$el.find('#product_categ_selection').append('<option id="'+key+'" value="'+category_id[count]+'">'+value+'</option>')
                        count++;
                    }
                });
                self.$el.find('#product_categ_table').hide();
                var option = self.$el.find( "#product_categ_selection" ).val();
                rpc.query({
                    model: "purchase.order.line",
                    method: "product_categ_data",
                    args: [option]
                }).then(function(result) {
                    var ctx = self.$el.find("#product_categ_purchases");
                    var name = result.name
                    var count = result.count;
                    new Chart(ctx, {
                        type: 'line',
                        data: {
                            labels: name,
                            datasets: [{
                                label: 'Quantity Done',
                                data: count,
                                backgroundColor: '#003f5c',
                                borderColor: '#003f5c',
                                barPercentage: 0.5,
                                barThickness: 6,
                                maxBarThickness: 8,
                                minBarLength: 0,
                                borderWidth: 1,
                                type: 'line',
                                fill: false
                            }]
                        },
                        options: {
                            scales: {
                                y: {
                                    beginAtZero: true
                                },
                            },
                            responsive: true,
                            maintainAspectRatio: false,
                        }
                    });
                });
            });
        },

        po_priority_orders: function(e) {
            /**
            Renders priority purchase orders based on the priority field value.
            @param {Event} e - The click event.
            */
            var self = this;
            e.stopPropagation();
            e.preventDefault();
            if(this.priority_orders) {
                var options = {
                    on_reverse_breadcrumb: self.on_reverse_breadcrumb,
                };
                self.do_action({
                    name: _t("Priority Order"),
                    type: 'ir.actions.act_window',
                    res_model: 'purchase.order',
                    view_mode: 'tree,form',
                    views: [[false, 'list'],[false, 'form']],
                    domain: [['priority','=', 1]],
                    target: 'current'
                }, options)
            }
        },

        onchange_select_mode: function(e) {
            /**
            Handles onchange event of select mode dropdown and fetches data from server accordingly
            @param {Event} e - Event object
            @returns {void}
            */
            var option = e.target.value
            var self = this
            rpc.query({
                model: 'purchase.order',
                method: 'get_select_mode_data',
                args: [option]
            }).then(function (result) {
                self.$el.find('#purchase_order').empty()
                self.$el.find('#amount').empty()
                self.$el.find('#priority').empty()
                self.$el.find('#partner').empty()
                self.$el.find('#purchase_orders').empty()
                self.$el.find('#purchase_amount').empty()
                self.$el.find('#priority_orders').empty()
                self.$el.find('#vendors').empty()
                self.$el.find('#purchase_orders').append(result['purchase_orders'])
                self.$el.find('#purchase_amount').append(result['purchase_amount'])
                self.$el.find('#priority_orders').append(result['priority_orders'])
                self.$el.find('#vendors').append(result['vendors'])
            });
        },

        fetch_data: function() {
            /**
            Fetches purchase data and assigns it to the corresponding properties of the current object.
            @returns {Promise} A Promise that resolves with the fetched data.
            */
            var self = this
            var fetchMonthlyData = this._rpc({
                model: 'purchase.order',
                method: "get_monthly_data",
                args: ['this_month']
            })
            .then(function (result) {
                self.purchase_orders = result['purchase_orders']
                self.purchase_amount = result['purchase_amount']
                self.priority_orders = result['priority_orders']
                self.vendors = result['vendors']
            });
            var fetchPendingPurchaseData = self._rpc({
                model: 'purchase.order',
                method: 'get_pending_purchase_data'
            }).then(function (res) {
             var order = Object.values(res['order'])
             var vendor = Object.values(res['vendor'])
             var amount = Object.values(res['amount'])
             var date = Object.values(res['date'])
             var state = Object.values(res['state'])
             self.data = res['data']
            });
            var test = this
            var fetchUpcomingPurchaseData = self._rpc({
                model: 'purchase.order',
                method: 'get_upcoming_purchase_data'
            }).then((res) => {
             var order = Object.values(res['order'])
             var vendor = Object.values(res['vendor'])
             var amount = Object.values(res['amount'])
             var date = Object.values(res['date'])
             var state = Object.values(res['state'])
             self.upcoming_data = res['data']
            });
            return $.when(fetchMonthlyData, fetchPendingPurchaseData, fetchUpcomingPurchaseData)
        },

        onchange_select_chart: function (e) {
            /**
            Function to handle the onchange event of select chart
            @param {Event} e - The event object
            */
            var option = e.target.value
            var self = this
            var ctx = self.$el.find(".top_pie_chart");
            var background_color = [];
            rpc.query({
                model: "purchase.order",
                method: 'get_top_chart_data',
                args: [option]
            }).then(function (arrays) {
                arrays[0].forEach((div) => {
                    var randomColor = '#' + Math.floor(Math.random() * 16777215).toString(16);
                    background_color.push(randomColor)
                });
                var randomColor= background_color
                var data = {
                    labels : arrays[1],
                    datasets: [{
                    label: "",
                    data: arrays[0],
                    backgroundColor:randomColor,
                    borderColor:randomColor,
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
                if (window.myCharts_top_priority != undefined)
                    window.myCharts_top_priority.destroy();
                window.myCharts_top_priority = new Chart(ctx, {
                    type: "doughnut",
                    data: data,
                    options: options
                });
            });
        },

        onchange_product_categ: function (events) {
            /**
            Function to handle the change in product category and display the data related to the product category.
            @param {Event} events - The event object.
            */
            var option = events.target.value;
            var self = this
            rpc.query({
                model: "purchase.order.line",
                method: "product_categ_data",
                args: [option]
            }).then(function(result) {
                var ctx = self.$el.find("#product_categ_purchases");
                var name = result.name
                var count = result.count;
                var index = 0;
                self.$el.find('#product_categ_table td').remove();
                Object.entries(result.count).forEach(([key, value]) => {
                    self.$el.find('#product_categ_table').append('<tr><td>'+name[index]+'</td><td>'+value+'</td></tr>')
                index++;
                });
                self.$el.find('#product_categ_table').hide();
                new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: name,
                        datasets: [{
                            label: 'Quantity',
                            data: count,
                            backgroundColor: '#003f5c',
                            borderColor: '#003f5c',
                            barPercentage: 0.5,
                            barThickness: 6,
                            maxBarThickness: 8,
                            minBarLength: 0,
                            borderWidth: 1,
                            type: 'line',
                            fill: false
                        }]
                    },
                    options: {
                        scales: {
                            y: {
                                beginAtZero: true
                            },
                        },
                        responsive: true,
                        maintainAspectRatio: false,
                    }
                });
            });
        },

        render_top_product: function() {
            /**
            Render top products chart.
            @function
            @name render_top_product
            @memberof module:purchases_dashboard
            @returns {void}
            */
            var self = this
            var ctx = self.$el.find(".top_pie_chart");
            var background_color = [];
            rpc.query({
                model: "purchase.order",
                method: 'get_top_chart_data',
                args: ['top_product']
            }).then(function (arrays) {
                arrays[0].forEach((div) => {
                    var randomColor = '#' + Math.floor(Math.random() * 16777215).toString(16);
                    background_color.push(randomColor)
                });
                var randomColor= background_color
                var data = {
                    labels : arrays[1],
                    datasets: [{
                    label: "",
                    data: arrays[0],
                    backgroundColor:randomColor,
                    borderColor:randomColor,
                    borderWidth: 1
                    },]
                };
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
                window.myCharts_top_priority = new Chart(ctx, {
                    type: "doughnut",
                    data: data,
                    options: options
                });
            });
        },

        render_fusion_chart: function(e) {
            /**
            Renders a Fusion chart by making a RPC call to retrieve purchase vendor data
            @function
            @param {Object} e - Event object
            @returns {void}
            */
            var self = this
            rpc.query({
                model: "purchase.order",
                method: 'purchase_vendors',
            }).then(function (result) {
                var ctx = self.$el.find("#purchase_vendors");
                var partner_id = result.partner_id;
                var partner_name = result.partner_name;
                var count = 0;
                Object.entries(result.partner_name).forEach(([key, value]) => {
                    if(count == 0){
                        self.$el.find('#vendor_selection').append('<option id="'+key+'" value="'+partner_id[count]+'" selected="selected">'+value+'</option>')
                        count++;
                    }else{
                        self.$el.find('#vendor_selection').append('<option id="'+key+'" value="'+partner_id[count]+'">'+value+'</option>')
                        count++;
                    }
                });
                var option = self.$el.find( "#vendor_selection" ).val();
                rpc.query({
                    model: "purchase.order",
                    method: 'purchase_vendor_details',
                    args: [option]
                }).then(function (result) {
                    self.$el.find("#purchase_vendors").empty();
                    var ctx = self.$el.find("#purchase_vendors");
                    if (result) {
                        self.$el.find('#purchase_vendors').append('<div class="graph_canvas" style="margin-top: 30px;"><canvas id="partner_graph" height="500px" width="150px"/></div>')
                        var ctx = self.$("#partner_graph");
                        var name = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                        var sum = result.purchase_amount
                        var po_count = result.po_count
                        var draft_total = result.draft_amount
                        var draft_count = result.draft_count
                        var approve_amount = result.approve_amount
                        var approve_count = result.approve_count
                        var cancel_amount = result.cancel_amount
                        var cancel_count = result.cancel_count
                        var index = 0;
                        if (window.myChart_year != undefined)
                            window.myChart_year.destroy();
                        window.myChart_year = new Chart(ctx, {
                            type: 'line',
                            data: {
                                labels: name,
                                datasets: [
                                {
                                    label: 'Purchase Order Total',
                                    data: sum,
                                    backgroundColor: '#0000ff',
                                    borderColor: '#0000ff',
                                    barPercentage: 0.5,
                                    barThickness: 6,
                                    maxBarThickness: 8,
                                    minBarLength: 0,
                                    borderWidth: 1,
                                    type: 'line',
                                    fill: false
                                },
                                {
                                    label: 'Draft Order Total',
                                    data: draft_total,
                                    backgroundColor: '#71d927',
                                    borderColor: '#71d927',
                                    barPercentage: 0.5,
                                    barThickness: 6,
                                    maxBarThickness: 8,
                                    minBarLength: 0,
                                    borderWidth: 1,
                                    type: 'line',
                                    fill: false
                                },
                                {
                                    label: 'To Approve',
                                    data: approve_amount,
                                    backgroundColor: '#ff0066',
                                    borderColor: '#ff0066',
                                    barPercentage: 0.5,
                                    barThickness: 6,
                                    maxBarThickness: 8,
                                    minBarLength: 0,
                                    borderWidth: 1,
                                    type: 'line',
                                    fill: false
                                },
                                {
                                    label: 'Cancelled Orders',
                                    data: cancel_amount,
                                    backgroundColor: '#ffff1a',
                                    borderColor: '#ffff1a',
                                    barPercentage: 0.5,
                                    barThickness: 6,
                                    maxBarThickness: 8,
                                    minBarLength: 0,
                                    borderWidth: 1,
                                    type: 'line',
                                    fill: false
                                },
                                ]
                            },
                            options: {
                                scales: {
                                    y: {
                                        beginAtZero: true
                                    },
                                },
                                responsive: true,
                                maintainAspectRatio: false,
                            }
                        });
                    }
                });
            });
        },

        onchange_vendor_selection: function(events) {
            /**
            Function to handle the change event of vendor selection dropdown.
            @param {Event} events - The change event object
            */
            var option = events.target.value;
            var self = this
            rpc.query({
                model: "purchase.order",
                method: 'purchase_vendor_details',
                args: [option]
            }).then(function(result) {
                self.$("#purchase_vendors").empty();
                var ctx = self.$el.find("#purchase_vendors");
                if (result) {
                    self.$el.find('#purchase_vendors').append('<div class="graph_canvas" style="margin-top: 30px;"><canvas id="partner_graph" height="500px" width="150px"/></div>')
                    var ctx = self.$el.find("#partner_graph");
                    var name = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                    var sum = result.purchase_amount
                    var po_count = result.po_count
                    var draft_total = result.draft_amount
                    var draft_count = result.draft_count
                    var approve_amount = result.approve_amount
                    var approve_count = result.approve_count
                    var cancel_amount = result.cancel_amount
                    var cancel_count = result.cancel_count
                    var index = 0;

                    if (window.myChart_year != undefined)
                        window.myChart_year.destroy(); window.myChart_year = new Chart(ctx, {
                            type: 'line',
                            data: {
                                labels: name,
                                datasets: [
                                    {
                                        label: 'Purchase Order Total',
                                        data: sum,
                                        backgroundColor: '#0000ff',
                                        borderColor: '#0000ff',
                                        barPercentage: 0.5,
                                        barThickness: 6,
                                        maxBarThickness: 8,
                                        minBarLength: 0,
                                        borderWidth: 1,
                                        type: 'line',
                                        fill: false
                                    },
                                    {
                                        label: 'Draft Order Total',
                                        data: draft_total,
                                        backgroundColor: '#71d927',
                                        borderColor: '#71d927',
                                        barPercentage: 0.5,
                                        barThickness: 6,
                                        maxBarThickness: 8,
                                        minBarLength: 0,
                                        borderWidth: 1,
                                        type: 'line',
                                        fill: false
                                    },
                                    {
                                        label: 'To Approve',
                                        data: approve_amount,
                                        backgroundColor: '#ff0066',
                                        borderColor: '#ff0066',
                                        barPercentage: 0.5,
                                        barThickness: 6,
                                        maxBarThickness: 8,
                                        minBarLength: 0,
                                        borderWidth: 1,
                                        type: 'line',
                                        fill: false
                                    },
                                    {
                                        label: 'Cancelled Orders',
                                        data: cancel_amount,
                                        backgroundColor: '#ffff1a',
                                        borderColor: '#ffff1a',
                                        barPercentage: 0.5,
                                        barThickness: 6,
                                        maxBarThickness: 8,
                                        minBarLength: 0,
                                        borderWidth: 1,
                                        type: 'line',
                                        fill: false
                                    },
                                ]
                            },
                            options: {
                                scales: {
                                    y: {
                                        beginAtZero: true
                                    },
                                },
                                responsive: true,
                                maintainAspectRatio: false,
                            }
                        });
                }
            });
        },
    });
    core.action_registry.add('purchase_dashboard', PurchaseDashboard);
    return PurchaseDashboard;
});
