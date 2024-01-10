/** @odoo-module **/
var AbstractAction = require('web.AbstractAction');
var core = require('web.core');
var QWeb = core.qweb;
var session = require('web.session');
var rpc = require('web.rpc');
const Dialog = require('web.Dialog');
var self = this;
var DashBoard = AbstractAction.extend({
    /*The template name used to render the dashboard content.*/
    contentTemplate: 'DashboardDashboard',
    events: {
        'click .rfq': 'on_dashboard_rfq_action',
        'click .rfq_sent': 'on_dashboard_rfq_sent_action',
        'click .rfq_to_approve': 'on_dashboard_to_rfq_approve_action',
        'click .purchase_order': 'on_dashboard_my_purchase_order_action',
        'click .cancelled_order': 'on_dashboard_rfq_cancel_action',
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
     * Initializes the DashBoard widget.
     */
    init: function (parent, context) {
        this._super(parent, context);
        this.dashboards_templates = ['MainSection'];
    },
    /*Rendering each graph at the start*/
    start: function () {
        self = this;
        self.set("title", 'Dashboard');
        return self._super().then(function () {
            self.render_dashboards();
            self.render_vendor_product_graph();
            self.render_product_purchase_graph();
            self.render_current_month_purchase_graph();
            self.render_monthly_purchase_count_graph();
            self.render_monthly_count_graph();
        });
    },
    /*WillStart function - executed before the widget starts*/
    willStart: function () {
        return this._super()
    },
    /**
     * Renders the dashboards by fetching data and appending templates to the DOM.
     */
    render_dashboards: function () {
        self = this;
        self.fetch_data()
        var templates = []
        var templates = ['MainSection'];
        _.each(templates, function (template) {
            self.$('.o_hr_dashboard').append(QWeb.render(template, { widget: self }))
        });
    },
    /*Fetch data from model purchase order*/
    fetch_data: function () {
        self = this
        var def1 = self._rpc({
            model: 'purchase.order',
            method: "get_data",
        }).then(function (result) {
                self.$('#rfq').append('<span>' + result.rfq + '</span>');
                self.$('#rfq_sent').append('<span>' + result.rfq_sent + '</span>');
                self.$('#rfq_to_approve').append('<span>' + result.rfq_to_approve + '</span>');
                self.$('#purchase_order').append('<span>' + result.purchase_order + '</span>');
                self.$('#cancelled_order').append('<span>' + result.cancelled_order + '</span>');
                self.$('#total_spend').append('<span>' + result.amount_total + '</span>');
                self.$('#amount_rfq').append('<span>' + result.amount_rfq + '</span>');
            });
    },
    /*This is to get rfq data according to the filters.*/
    on_dashboard_rfq_action: function (ev) {
        var start_date = $('#start_date').val()
        var end_date = $('#end_date').val()
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
            name: 'RFQ',
            res_model: 'purchase.order',
            views: [[false, 'tree'], [false, 'form']],
            domain: domain,
            target: 'current',
        });
    },
    /*This is to get purchase order data according to the filters.*/
    on_dashboard_my_purchase_order_action: function (ev) {
        ev.preventDefault();
        var $action = $(ev.currentTarget);
        var start_date = this.$('#start_date').val()
        var end_date = this.$('#end_date').val()
        if (start_date && end_date) {
            var domain = [['user_id', '=', session.uid], ['state', '=', 'purchase'], ['date_order', '>=', start_date], ['date_order', '<=', end_date]]
        }
        else if (start_date) {
            var domain = [['user_id', '=', session.uid], ['state', '=', 'purchase'], ['date_order', '>=', start_date]]
        }
        else if (end_date) {
            var domain = [['user_id', '=', session.uid], ['state', '=', 'purchase'], ['date_order', '<=', end_date]]
        }
        else {
            var domain = [['user_id', '=', session.uid], ['state', '=', 'purchase']]
        }
        this.do_action({
            type: 'ir.actions.act_window',
            name: 'Purchase Orders',
            res_model: 'purchase.order',
            views: [[false, 'tree'], [false, 'form']],
            domain: domain,
            target: 'current',
        });
    },
    /*This is to get rfq sent data according to the filters.*/
    on_dashboard_rfq_sent_action: function (ev) {
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
            name: 'RFQ Sent',
            res_model: 'purchase.order',
            views: [[false, 'tree'], [false, 'form']],
            domain: domain,
            target: 'current',
        });
    },
    /*This is to get rfq cancel data according to the filters.*/
    on_dashboard_rfq_cancel_action: function (ev) {
        ev.preventDefault();
        var $action = $(ev.currentTarget);
        this.do_action({
            type: 'ir.actions.act_window',
            name: 'RFQ Cancel',
            res_model: 'purchase.order',
            views: [[false, 'tree'], [false, 'form']],
            domain: [['user_id', '=', session.uid], ['state', '=', 'cancel']],
            target: 'current',
        });
    },
    /*This is to get rfq to be approved data according to the filters.*/
    on_dashboard_to_rfq_approve_action: function (ev) {
        ev.preventDefault();
        var $action = $(ev.currentTarget);
        var start_date = this.$('#start_date').val()
        var end_date = this.$('#end_date').val()
        if (start_date && end_date) {
            var domain = [['user_id', '=', session.uid], ['state', '=', 'to approve'], ['date_order', '>=', start_date], ['date_order', '<=', end_date]]
        }
        else if (start_date) {
            var domain = [['user_id', '=', session.uid], ['state', '=', 'to approve'], ['date_order', '>=', start_date]]
        }
        else if (end_date) {
            var domain = [['user_id', '=', session.uid], ['state', '=', 'to approve'], ['date_order', '<=', end_date]]
        }
        else {
            var domain = [['user_id', '=', session.uid], ['state', '=', 'to approve']]
        }
        this.do_action({
            type: 'ir.actions.act_window',
            name: 'To Approve',
            res_model: 'purchase.order',
            views: [[false, 'tree'], [false, 'form']],
            domain: domain,
            target: 'current',
        });
    },
    /**
     *Handles the onClick event for the date inputs and fetches data based on the selected date range.
     *It empties certain elements on the dashboard and then queries the backend to get purchase order data.
     *If the selected start date is greater than the end date, it displays a warning dialog.
     */
    onClick_this_values() {
        self = this
        self.$('#rfq').empty();
        self.$('#rfq_sent').empty();
        self.$('#rfq_to_approve').empty();
        self.$('#purchase_order').empty();
        self.$('#cancelled_order').empty();
        var start_date = self.$('#start_date').val()
        var end_date = self.$('#end_date').val()
        if (start_date && end_date && start_date > end_date){
            var dialog = new Dialog(null, {
                title: "Warning",
                size: 'medium',
                $content: $('<div/>', {
                    html: 'End date is Less than Start date'
                }),
                buttons: [{
                    text: "Close",
                    close: true
                }]
            });
            dialog.open();
            }
        rpc.query({
            model: 'purchase.order',
            method: 'get_value',
            args: [start_date, end_date],
        }).then(function (data) {
                self.$('#rfq').append('<span>' + data.rfq + '</span>');
                self.$('#rfq_sent').append('<span>' + data.rfq_sent + '</span>');
                self.$('#rfq_to_approve').append('<span>' + data.rfq_to_approve + '</span>');
                self.$('#purchase_order').append('<span>' + data.purchase_order + '</span>');
                self.$('#cancelled_order').append('<span>' + data.cancelled_order + '</span>');
            })
    },
    render_vendor_product_graph: function () {
        /*Graph shows count of products for vendors.*/
        var ctx = this.$("#lead_vendor");
        rpc.query({
            model: 'res.partner',
            method: 'get_vendor_po',
            args: [],
        }).then(function (results) {
                var po_count = results.purchase_order_count;
                var chart = new Chart(ctx, {
                    type: "doughnut",
                    data: {
                        labels: Object.keys(po_count),
                        datasets: [{
                            backgroundColor: [
                                'rgb(150,20,147)',
                                'rgb(186,90,211)',
                                'rgb(10,20,255)',
                                'rgb(30,91,25)',
                                'rgb(10,206,209)',
                                'rgb(32,18,170)',
                                'rgb(173,255,47)',
                                'rgb(205,92,92)',
                                'rgb(178,34,34)',
                                'rgb(0,128,128)',
                            ],
                            data: Object.values(po_count),
                        }]
                    },
                });
            });
    },
    render_product_purchase_graph: function () {
        /*This is to show a product lead graph.*/
        var ctx = this.$("#lead_product");
        rpc.query({
            model: 'product.product',
            method: 'most_purchased_product',
            args: [],
        }).then(function (results) {
                var purchased_qty = results.purchased_qty;
                var chart = new Chart(ctx, {
                    type: "pie",
                    data: {
                        labels: Object.keys(purchased_qty),
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
                            data: Object.values(purchased_qty),
                        }]
                    },
                });
            });
    },
     render_current_month_purchase_graph: function () {
        /*It is to show monthly purchase count graph.*/
        var ctx = this.$("#current_month_purchase");
        rpc.query({
            model: 'purchase.order',
            method: 'get_current_month_purchase',
            args: [],
        }).then(function (results) {
                var current_month_count = results.current_month_count;
                var chart = new Chart(ctx, {
                    type: "bar",
                    data: {
                        labels: Object.keys(current_month_count),
                        datasets: [{
                            label: 'Purchase Order Count',
                            backgroundColor: [
                                'rgb(25,25,112)',
                            ],
                            data: Object.values(current_month_count),
                        }]
                    },
                });
            });
    },
    render_monthly_purchase_count_graph: function () {
        /*This is to show  lead quotations graph.*/
        var ctx = this.$("#monthly_purchase");
        rpc.query({
            model: 'purchase.order',
            method: 'get_monthly_purchase_order',
            args: [],
        }).then(function (results) {
                var monthly_purchase_count = results.monthly_purchase_count;
                var chart = new Chart(ctx, {
                    type: "bar",
                    data: {
                        labels: Object.keys(monthly_purchase_count),
                        datasets: [{
                            label: 'Purchase Order',
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
                                'rgb(40, 0, 40)',
                                'rgb(40, 255, 0)',
                            ],
                            data: Object.values(monthly_purchase_count),
                        }]
                    },
                });
            });
    },
    render_monthly_count_graph: function () {
        /*This is to monthly count graph.*/
        var ctx = this.$("#monthly_count");
        rpc.query({
            model: 'purchase.order',
            method: 'get_monthly_order',
            args: [],
        }).then(function (results) {
                var monthly_count = results.monthly_count;
                var chart = new Chart(ctx, {
                    type: "line",
                    data: {
                        labels: Object.keys(monthly_count),
                        datasets: [{
                            label: 'Monthly Order',
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
                            data: Object.values(monthly_count),
                        }]
                    },
                });
            });
    },
});
/*Add the DashBoard class to the action registry*/
core.action_registry.add('purchase_dashboard', DashBoard);
return DashBoard;
