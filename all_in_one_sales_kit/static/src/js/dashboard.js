odoo.define("all_in_one_sales_kit.dashboard", function (require) {
    "use strict";
    var AbstractAction = require('web.AbstractAction');
    var core = require('web.core');
    var QWeb = core.qweb;
    var session = require('web.session');
    var rpc = require('web.rpc');
    var self = this;
    var DashBoard = AbstractAction.extend({
        contentTemplate: 'DashboardDashboard',
        events: {
            'click .quotation': 'on_dashboard_quotation_action',
            'click .my_sale_order': 'on_dashboard_my_sale_order_action',
            'click .quotation_sent': 'on_dashboard_quotation_sent_action',
            'click .quotation_cancel': 'on_dashboard_quotation_cancel_action',
            'click .customers': 'on_dashboard_customers_action',
            'click .products': 'on_dashboard_products_action',
            'click .to_invoice': 'on_dashboard_to_invoice_action',
            'change #start_date': function (e) {
                /*This function works on change of start date.*/
                e.stopPropagation();
                var $target = $(e.target);
                var values = $target.val();
                this.onClick_this_values($target.val());
            },
            'change #end_date': function (e) {
                /*This function works on change of end date.*/
                e.stopPropagation();
                var $target = $(e.target);
                var values = $target.val();
                this.onClick_this_values($target.val());
            },
        },
        /**
         * Initializes the object with the given parent and context.
         *
         * @param {Object} parent - The parent object.
         * @param {Object} context - The context object.
         */
        init: function (parent, context) {
            this._super(parent, context);
            this.dashboards_templates = ['LoginUser', 'MainSection'];
        },
        /**
         * Initializes the object and renders various dashboards and graphs.
         * Sets the title to 'Dashboard'.
         *
         * @returns {Promise} A promise that resolves after the initialization is complete.
         */
        start: function () {
            var self = this;
            this.set("title", 'Dashboard');
            return this._super().then(function () {
                self.render_dashboards();
                self.render_customer_leads_graph();
                self.render_product_leads_graph();
                self.render_quotation_leads_graph();
                self.render_sales_team_graph();
                self.render_my_monthly_comparison_graph();
                self.render_least_sold_graph();
            });
        },
        /**
         * Executes before the object starts its initialization process.
         *
         * @returns {Promise} A promise that resolves after the pre-initialization is complete.
         */
        willStart: function () {
            var self = this;
            return this._super()
        },
        render_dashboards: function () {
        /*It is to render data to the dashboard*/
            var self = this;
            this.fetch_data()
            var templates = []
            var templates = ['LoginUser', 'MainSection'];
            _.each(templates, function (template) {
                self.$('.o_hr_dashboard').append(QWeb.render(template, { widget: self }))
            });
        },
        /**
         * Fetches data related to sale orders from the server and updates corresponding HTML elements.
         *
         * @returns {Promise} A promise that resolves when the data fetching and updates are complete.
         */
        fetch_data: function () {
            var self = this
            var def1 = this._rpc({
                model: 'sale.order',
                method: "get_data",
            })
                .then(function (result) {
                    $('#quotation_templates').append('<span>' + result.quotation + '</span>');
                    $('#my_sale_order_templates').append('<span>' + result.my_sale_order_templates + '</span>');
                    $('#quotation_sent').append('<span>' + result.quotation_sent + '</span>');
                    $('#quotation_cancel').append('<span>' + result.quotation_cancel + '</span>');
                    $('#customers').append('<span>' + result.customers + '</span>');
                    $('#products').append('<span>' + result.products + '</span>');
                    $('#to_invoice').append('<span>' + result.to_invoice + '</span>');
                });
        },
        on_dashboard_quotation_action: function (ev) {
            /*This is to get quotation data according to the filters.*/
            var start_date = this.$('#start_date').val()
            var end_date = this.$('#end_date').val()
            if (start_date && end_date) {
                var domain = [['user_id', '=', session.uid], ['state', '=', 'draft'], ['date_order', '>=', start_date], ['date_order', '<=', end_date]]
            }
            else if (start_date) {
                var domain = [['user_id', '=', session.uid], ['state', '=', 'draft'], ['date_order', '>=', start_date]]
            }
            else if (end_date) {
                var domain = [['user_id', '=', session.uid], ['state', '=', 'draft'], ['date_order', '<=', end_date]]
            }
            else {
                var domain = [['user_id', '=', session.uid], ['state', '=', 'draft']]
            }
            this.do_action({
                type: 'ir.actions.act_window',
                name: 'Quotations',
                res_model: 'sale.order',
                views: [[false, 'tree'], [false, 'form']],
                domain: domain,
                target: 'current',
            });
        },
        on_dashboard_my_sale_order_action: function (ev) {
            /*This is to get sale order data according to the filters.*/
            ev.preventDefault();
            var $action = $(ev.currentTarget);
            var start_date = this.$('#start_date').val()
            var end_date = this.$('#end_date').val()
            if (start_date && end_date) {
                var domain = [['user_id', '=', session.uid], ['state', '=', 'sale'], ['date_order', '>=', start_date], ['date_order', '<=', end_date]]
            }
            else if (start_date) {
                var domain = [['user_id', '=', session.uid], ['state', '=', 'sale'], ['date_order', '>=', start_date]]
            }
            else if (end_date) {
                var domain = [['user_id', '=', session.uid], ['state', '=', 'sale'], ['date_order', '<=', end_date]]
            }
            else {
                var domain = [['user_id', '=', session.uid], ['state', '=', 'sale']]
            }
            this.do_action({
                type: 'ir.actions.act_window',
                name: 'Sale orders',
                res_model: 'sale.order',
                views: [[false, 'tree'], [false, 'form']],
                domain: domain,
                target: 'current',
            });
        },
        on_dashboard_quotation_sent_action: function (ev) {
            /*This is to get quotation sent data according to the filters.*/
            ev.preventDefault();
            var $action = $(ev.currentTarget);
            var start_date = this.$('#start_date').val()
            var end_date = this.$('#end_date').val()
            if (start_date && end_date) {
                var domain = [['user_id', '=', session.uid], ['state', '=', 'sent'], ['date_order', '>=', start_date], ['date_order', '<=', end_date]]
            }
            else if (start_date) {
                var domain = [['user_id', '=', session.uid], ['state', '=', 'sent'], ['date_order', '>=', start_date]]
            }
            else if (end_date) {
                var domain = [['user_id', '=', session.uid], ['state', '=', 'sent'], ['date_order', '<=', end_date]]
            }
            else {
                var domain = [['user_id', '=', session.uid], ['state', '=', 'sent']]
            }
            this.do_action({
                type: 'ir.actions.act_window',
                name: 'Quotations Sent',
                res_model: 'sale.order',
                views: [[false, 'tree'], [false, 'form']],
                domain: domain,
                target: 'current',
            });
        },
        on_dashboard_quotation_cancel_action: function (ev) {
            /*This is to get quotation cancel data according to the filters.*/
            ev.preventDefault();
            var $action = $(ev.currentTarget);
            this.do_action({
                type: 'ir.actions.act_window',
                name: 'Quotations Cancel',
                res_model: 'sale.order',
                views: [[false, 'tree'], [false, 'form']],
                domain: [['user_id', '=', session.uid], ['state', '=', 'cancel']],
                target: 'current',
            });
        },
        on_dashboard_customers_action: function (ev) {
            /*This is to get customers.*/
            ev.preventDefault();
            var $action = $(ev.currentTarget);
            this.do_action({
                type: 'ir.actions.act_window',
                name: 'Customers',
                res_model: 'res.partner',
                views: [[false, 'kanban'], [false, 'tree'], [false, 'form']],
                target: 'current',
            });
        },
        on_dashboard_to_invoice_action: function (ev) {
            /*This is to get quotation
             to be invoiced data according to the filters.*/
            ev.preventDefault();
            var $action = $(ev.currentTarget);
            var start_date = this.$('#start_date').val()
            var end_date = this.$('#end_date').val()
            if (start_date && end_date) {
                var domain = [['user_id', '=', session.uid], ['invoice_status', '=', 'to invoice'], ['date_order', '>=', start_date], ['date_order', '<=', end_date]]
            }
            else if (start_date) {
                var domain = [['user_id', '=', session.uid], ['invoice_status', '=', 'to invoice'], ['date_order', '>=', start_date]]
            }
            else if (end_date) {
                var domain = [['user_id', '=', session.uid], ['invoice_status', '=', 'to invoice'], ['date_order', '<=', end_date]]
            }
            else {
                var domain = [['user_id', '=', session.uid], ['invoice_status', '=', 'to invoice']]
            }
            this.do_action({
                type: 'ir.actions.act_window',
                name: 'To invoice',
                res_model: 'sale.order',
                views: [[false, 'tree'], [false, 'form']],
                domain: domain,
                target: 'current',
            });
        },
        on_dashboard_products_action: function (ev) {
            /*This is to get products.*/
            ev.preventDefault();
            var $action = $(ev.currentTarget);
            this.do_action({
                type: 'ir.actions.act_window',
                name: 'Products',
                res_model: 'product.template',
                views: [[false, 'kanban'], [false, 'tree'], [false, 'form']],
                target: 'current',
            });
        },
        /**
         * Event handler for a button click, fetching and displaying values based on user input.
         * Clears existing content in specified HTML elements and updates them with data retrieved from the server.
         */
        onClick_this_values() {
        // Clear existing content in HTML elements
            this.$('#quotation_templates').empty();
            this.$('#my_sale_order_templates').empty();
            this.$('#quotation_sent').empty();
            this.$('#quotation_cancel').empty();
            this.$('#customers').empty();
            this.$('#products').empty();
            this.$('#to_invoice').empty();
            var self = this
            var start_date = this.$('#start_date').val()
            var end_date = this.$('#end_date').val()
            // Use rpc.query to fetch data from the server
            rpc.query({
                model: 'sale.order',
                method: 'get_value',
                args: [start_date, end_date],
            })
                .then(function (data) {
                // Update HTML elements with fetched data
                    $('#quotation_templates').append('<span>' + data.quotation + '</span>');
                    $('#my_sale_order_templates').append('<span>' + data.my_sale_order_templates + '</span>');
                    $('#quotation_sent').append('<span>' + data.quotation_sent + '</span>');
                    $('#quotation_cancel').append('<span>' + data.quotation_cancel + '</span>');
                    $('#customers').append('<span>' + data.customers + '</span>');
                    $('#products').append('<span>' + data.products + '</span>');
                    $('#to_invoice').append('<span>' + data.to_invoice + '</span>');

                })
        },
        render_customer_leads_graph: function () {
            /*This is to show a customer lead graph.*/
            var self = this;
            var ctx = self.$("#lead_customer");
            rpc.query({
                model: 'sale.order',
                method: 'get_lead_customer',
                args: [],
            })
                .then(function (results) {
                    var lead_templates = results.lead_templates;
                    var chart = new Chart(ctx, {
                        type: "doughnut",
                        data: {
                            labels: Object.keys(lead_templates),
                            datasets: [{

                                backgroundColor: [
                                    'rgb(255,20,147)',
                                    'rgb(186,85,211)',
                                    'rgb(0,0,255)',
                                    'rgb(0,191,255)',
                                    'rgb(0,206,209)',
                                    'rgb(32,178,170)',
                                    'rgb(173,255,47)',
                                    'rgb(205,92,92)',
                                    'rgb(178,34,34)',
                                    'rgb(0,128,128)',
                                ],
                                data: Object.values(lead_templates),
                            }]
                        },
                    });
                });
        },
        render_product_leads_graph: function () {
            /*This is to show a product lead graph.*/
            var self = this;
            var ctx = self.$("#lead_product");
            rpc.query({
                model: 'sale.order',
                method: 'get_lead_product',
                args: [],
            })
                .then(function (results) {
                    var lead_templates = results.lead_templates;
                    var chart = new Chart(ctx, {
                        type: "doughnut",
                        data: {
                            labels: Object.keys(lead_templates),
                            datasets: [{

                                backgroundColor: [
                                    'rgb(255, 99, 132)',
                                    'rgb(255, 159, 64)',
                                    'rgb(75, 192, 192)',
                                    'rgb(54, 162, 235)',
                                    'rgb(255, 209, 219)',
                                    'rgb(255, 205, 86)',
                                    'rgb(99, 255, 222)',
                                    'rgb(132, 255, 99)',
                                    'rgb(139, 139, 184)',
                                    'rgb(40, 255, 40)',
                                ],
                                data: Object.values(lead_templates),
                            }]
                        },
                    });
                });
        },
        render_quotation_leads_graph: function () {
            /*This is to show  lead quotations graph.*/
            var self = this;
            var ctx = self.$("#lead_order");
            rpc.query({
                model: 'sale.order',
                method: 'get_lead_order',
                args: [],
            })
                .then(function (results) {
                    var lead_templates = results.lead_templates;
                    var chart = new Chart(ctx, {
                        type: "bar",
                        data: {
                            labels: Object.keys(lead_templates),
                            datasets: [{
                                label: 'Sale Amount',
                                backgroundColor: [
                                    'rgb(255, 99, 132)',
                                    'rgb(255, 159, 64)',
                                    'rgb(75, 192, 192)',
                                    'rgb(54, 162, 235)',
                                    'rgb(255, 209, 219)',
                                    'rgb(255, 205, 86)',
                                    'rgb(99, 255, 222)',
                                    'rgb(132, 255, 99)',
                                    'rgb(139, 139, 184)',
                                    'rgb(40, 255, 40)',
                                ],
                                data: Object.values(lead_templates),
                            }]
                        },
                    });
                });
        },
        render_sales_team_graph: function () {
            /*This is to show sales team graph.*/
            var self = this;
            var ctx = self.$("#team");
            rpc.query({
                model: 'sale.order',
                method: 'get_sales_team',
                args: [],
            })
                .then(function (results) {
                    var lead_templates = results.lead_templates;
                    var chart = new Chart(ctx, {
                        type: "pie",
                        data: {
                            labels: Object.keys(lead_templates),
                            datasets: [{
                                backgroundColor: [
                                    'rgb(25,25,112)',
                                    'rgb(135,206,235)',
                                    'rgb(75, 192, 192)',
                                    'rgb(54, 162, 235)',
                                    'rgb(255, 209, 219)',
                                    'rgb(255, 205, 86)',
                                    'rgb(99, 255, 222)',
                                    'rgb(132, 255, 99)',
                                    'rgb(139, 139, 184)',
                                    'rgb(40, 255, 40)',
                                ],
                                data: Object.values(lead_templates),
                            }]
                        },
                    });
                });
        },
        render_my_monthly_comparison_graph: function () {
            /*It is to show monthly sale count graph.*/
            var self = this;
            var ctx = self.$("#my_monthly_comparison");
            rpc.query({
                model: 'sale.order',
                method: 'get_my_monthly_comparison',
                args: [],
            })
                .then(function (results) {
                    var lead_templates = results.lead_templates;
                    var chart = new Chart(ctx, {
                        type: "line",
                        data: {
                            labels: Object.keys(lead_templates),
                            datasets: [{
                                label: 'Quotation Count',
                                backgroundColor: [
                                    'rgb(25,25,112)',
                                ],
                                data: Object.values(lead_templates),
                            }]
                        },
                    });
                });
        },
        render_least_sold_graph: function () {
            /*This is to show least sold products graph.*/
            var self = this;
            var ctx = self.$("#least_sold");
            rpc.query({
                model: 'sale.order',
                method: 'get_least_sold',
                args: [],
            })
                .then(function (results) {
                    var lead_templates = results.lead_templates;
                    var chart = new Chart(ctx, {
                        type: "bar",
                        data: {
                            labels: Object.keys(lead_templates),
                            datasets: [{
                                label: 'Product Count',
                                backgroundColor: [
                                    'rgb(25,25,112)',
                                    'rgb(135,206,235)',
                                    'rgb(75, 192, 192)',
                                    'rgb(54, 162, 235)',
                                    'rgb(255, 209, 219)',
                                    'rgb(255, 205, 86)',
                                    'rgb(99, 255, 222)',
                                    'rgb(132, 255, 99)',
                                    'rgb(139, 139, 184)',
                                    'rgb(40, 255, 40)',
                                ],
                                data: Object.values(lead_templates),
                            }]
                        },
                    });
                });
        },
    });
    core.action_registry.add('sale_dashboard', DashBoard);
    return DashBoard;
});
