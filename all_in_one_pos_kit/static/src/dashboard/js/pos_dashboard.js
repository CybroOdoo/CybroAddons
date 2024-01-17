odoo.define('all_in_one_pos_kit.Dashboard', function(require) {
    "use strict";
    var AbstractAction = require('web.AbstractAction');
    var core = require('web.core');
    const {
        loadBundle
    } = require("@web/core/assets");
    var session = require('web.session');
    var rpc = require('web.rpc');
    var _t = core._t;
    var QWeb = core.qweb;
    var date = new Date();
    var yesterday = new Date(date.getTime());
    var PosDashboard = AbstractAction.extend({ //Extended the AbstractAction to create dashboard in pos.
        template: 'PosDashboard',
        events: {
            'click .pos_order_today': 'pos_order_today',
            'click .pos_order': 'pos_order',
            'click .pos_total_sales': 'pos_order',
            'click .pos_session': 'pos_session',
            'click .pos_refund_orders': 'pos_refund_orders',
            'click .pos_refund_today_orders': 'pos_refund_today_orders',
            'change #pos_sales': 'onclick_pos_sales',
        },
        init: function(parent, context) { //Function to Initializes all the values while loading the file
            this._super(parent, context);
            this.dashboards_templates = ['PosOrders', 'PosChart', 'PosCustomer'];
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
        willStart: function() { // returns the function fetch_data when page load.
            var self = this;
            return $.when(loadBundle(this), this._super()).then(function() {
                return self.fetch_data();
            });
        },
        start: function() { //Function return render_dashboards() and render_graphs()
            self = this;
            this.set("title", 'Dashboard');
            return this._super().then(function() {
                self.render_dashboards();
                self.render_graphs();
                self.$el.parent().addClass('oe_background_grey');
            });
        },
        fetch_data: function() { //fetch data and call rpc query to create tile.
            self = this;
            var def1 = this._rpc({
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
                .then(function(res) {
                    self.payment_details = res['payment_details'];
                    self.top_salesperson = res['salesperson'];
                    self.selling_product = res['selling_product'];
                });
            return $.when(def1, def2);
        },
        render_dashboards: function() { //return value to show in tile.
            self = this;
            _.each(this.dashboards_templates, function(template) {
                self.$('.o_pos_dashboard').append(QWeb.render(template, {
                    widget: self
                }));
            });
        },
        render_graphs: function() { //Add function to load in dashboard.
            self = this;
            self.render_top_customer_graph();
            self.render_top_product_graph();
            self.render_product_category_graph();
        },
        pos_order_today: function(e) { //Click function returns today's all pos order tree view.
            self = this;
            yesterday.setDate(date.getDate() - 1);
            e.stopPropagation();
            e.preventDefault();
            session.user_has_group('hr.group_hr_user').then(function(has_group) {
                if (has_group) {
                    self.do_action({
                        name: _t("Today Order"),
                        type: 'ir.actions.act_window',
                        res_model: 'pos.order',
                        view_mode: 'tree,form,calendar',
                        view_type: 'form',
                        views: [
                            [false, 'list'],
                            [false, 'form']
                        ],
                        domain: [
                            ['date_order', '<=', date],
                            ['date_order', '>=', yesterday]
                        ],
                        target: 'current'
                    }, {
                        on_reverse_breadcrumb: self.on_reverse_breadcrumb
                    })
                }
            });
        },
        pos_refund_orders: function(e) { //Click function returns all refund pos order tree view.
            self = this;
            e.stopPropagation();
            e.preventDefault();
            session.user_has_group('hr.group_hr_user').then(function(has_group) {
                if (has_group) {
                    self.do_action({
                        name: _t("Refund Orders"),
                        type: 'ir.actions.act_window',
                        res_model: 'pos.order',
                        view_mode: 'tree,form,calendar',
                        view_type: 'form',
                        views: [
                            [false, 'list'],
                            [false, 'form']
                        ],
                        domain: [
                            ['amount_total', '<', 0.0]
                        ],
                        target: 'current'
                    }, {
                        on_reverse_breadcrumb: self.on_reverse_breadcrumb
                    })
                }
            });
        },
        pos_refund_today_orders: function(e) { //Click function returns all today's refund pos order in tree view.
            self = this;
            yesterday.setDate(date.getDate() - 1);
            e.stopPropagation();
            e.preventDefault();
            session.user_has_group('hr.group_hr_user').then(function(has_group) {
                if (has_group) {
                    self.do_action({
                        name: _t("Refund Orders"),
                        type: 'ir.actions.act_window',
                        res_model: 'pos.order',
                        view_mode: 'tree,form,calendar',
                        view_type: 'form',
                        views: [
                            [false, 'list'],
                            [false, 'form']
                        ],
                        domain: [
                            ['amount_total', '<', 0.0],
                            ['date_order', '<=', date],
                            ['date_order', '>=', yesterday]
                        ],
                        target: 'current'
                    }, {
                        on_reverse_breadcrumb: self.on_reverse_breadcrumb
                    })
                }
            });
        },
        pos_order: function(e) { //Click function returns all pos order in tree view.
            self = this;
            e.stopPropagation();
            e.preventDefault();
            session.user_has_group('hr.group_hr_user').then(function(has_group) {
                if (has_group) {
                    self.do_action({
                        name: _t("Total Order"),
                        type: 'ir.actions.act_window',
                        res_model: 'pos.order',
                        view_mode: 'tree,form,calendar',
                        view_type: 'form',
                        views: [
                            [false, 'list'],
                            [false, 'form']
                        ],
                        target: 'current'
                    }, {
                        on_reverse_breadcrumb: self.on_reverse_breadcrumb
                    })
                }
            });

        },
        pos_session: function(e) { //Click function returns all pos session in tree view.
            self = this;
            e.stopPropagation();
            e.preventDefault();
            session.user_has_group('hr.group_hr_user').then(function(has_group) {
                if (has_group) {
                    self.do_action({
                        name: _t("sessions"),
                        type: 'ir.actions.act_window',
                        res_model: 'pos.session',
                        view_mode: 'tree,form,calendar',
                        view_type: 'form',
                        views: [
                            [false, 'list'],
                            [false, 'form']
                        ],
                        target: 'current'
                    }, {
                        on_reverse_breadcrumb: self.on_reverse_breadcrumb
                    })
                }
            });
        },
        onclick_pos_sales: function(events) { // Function to add filter in pos sales report
            var ctx = this.$("#canvas_1");
            rpc.query({
                model: "pos.order",
                method: "get_department",
                args: [$(events.target).val()],
            }).then(function(arrays) {
                if (window.myCharts != undefined)
                    window.myCharts.destroy();
                window.myCharts = new Chart(ctx, {
                    type: "bar",
                    data: {
                        labels: arrays[1],
                        datasets: [{
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
                        }, ]
                    },
                    options: {
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
                    }
                });
            });
        },
        render_top_customer_graph: function() { //Function to create top customers chart
            var ctx = this.$(".top_customer");
            rpc.query({
                model: "pos.order",
                method: "get_the_top_customer",
            }).then(function(arrays) {
                var chart = new Chart(ctx, { //create Chart class object
                    type: "pie",
                    data: {
                        labels: arrays[1],
                        datasets: [{
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
                    },
                    options: { //options
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
                    }
                });
            });
        },
        render_top_product_graph: function() { //Function to create top product chart.
            var ctx = this.$(".top_selling_product");
            rpc.query({
                model: "pos.order",
                method: "get_the_top_products",
            }).then(function(arrays) {
                var chart = new Chart(ctx, { //create Chart class object
                    type: "horizontalBar",
                    data: {
                        labels: arrays[1],
                        datasets: [{
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
                        }, ]
                    },
                    options: { //options
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
                    }
                });
            });
        },
        render_product_category_graph: function() { //Function to create top categories chart
            var ctx = this.$(".top_product_categories");
            rpc.query({
                model: "pos.order",
                method: "get_the_top_categories",
            }).then(function(arrays) {
                var chart = new Chart(ctx, { //create Chart class object
                    type: "horizontalBar",
                    data: {
                        labels: arrays[1],
                        datasets: [{
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
                        }, ]
                    },
                    options: {
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
                    }
                });
            });
        },
    });
    core.action_registry.add('pos_dashboard', PosDashboard);
    return PosDashboard;
});
