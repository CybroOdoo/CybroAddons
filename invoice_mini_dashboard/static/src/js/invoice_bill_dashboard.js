odoo.define('invoice_mini_dashboard.bill', function(require) {
    "use strict";
    /**
     * This file defines the Invoice Dashboard view (alongside its renderer,
     * model and controller). This Dashboard is added to the top of Bill list
     */
    var core = require('web.core');
    var ListController = require('web.ListController');
    var ListModel = require('web.ListModel');
    var ListRenderer = require('web.ListRenderer');
    var ListView = require('web.ListView');
    var SampleServer = require('web.SampleServer');
    var view_registry = require('web.view_registry');
    const session = require('web.session');
    var QWeb = core.qweb;
    // Add mock of method 'retrieve_in_invoice_dashboard' in SampleServer, so
    // that we can have the sample data in empty bill list view
    let dashboardValues;
    SampleServer.mockRegistry.add('account.move/retrieve_in_invoice_dashboard', () => {
        return Object.assign({}, dashboardValues);
    });
    // Extended the ListRenderer
    var InvoiceBillListDashboardRenderer = ListRenderer.extend({
        events: _.extend({}, ListRenderer.prototype.events, {
            'click .o_dashboard_action': '_onDashboardActionClicked',
        }),
        /**
         * @override _renderView for rendering the template
         */
        _renderView: function() {
            var self = this;
            return this._super.apply(this, arguments).then(function() {
                var values = self.state.dashboardValues;
                var invoice_dashboard = QWeb.render('account.AccountBillDashboardBill', {
                    values: values,
                });
                self.$el.prepend(invoice_dashboard);
            });
        },
        /**
         * Action while clicking the dashboard
         */
        _onDashboardActionClicked: function(e) {
            e.preventDefault();
            var $action = $(e.currentTarget);
            this.trigger_up('dashboard_open_action', {
                action_name: "account.action_move_in_invoice_type",
                action_context: $action.attr('context'),
            });
        },
    });

    var InvoiceBillListDashboardModel = ListModel.extend({
        /**
         * @override init function
         */
        init: function() {
            this.dashboardValues = {};
            this._super.apply(this, arguments);
        },

        /**
         * @override get function
         */
        __get: function(localID) {
            var result = this._super.apply(this, arguments);
            if (_.isObject(result)) {
                result.dashboardValues = this.dashboardValues[localID];
            }
            return result;
        },
        /**
         * @override load function
         * @returns _loadDashboard()
         */
        __load: function() {
            return this._loadDashboard(this._super.apply(this, arguments));
        },
        /**
         * @override __reload function
         * @returns _loadDashboard()
         */
        __reload: function() {
            return this._loadDashboard(this._super.apply(this, arguments));
        },

        /**
         * @param {Promise} super_def a promise that resolves with a dataPoint id
         * @returns {Promise -> string} resolves to the dataPoint id
         */
        _loadDashboard: function(super_def) {
            var self = this;
            var dashboard_def = this._rpc({
                model: 'account.move',
                method: 'retrieve_in_invoice_dashboard',
                context: session.user_context,
            });
            return Promise.all([super_def, dashboard_def]).then(function(results) {
                var id = results[0];
                dashboardValues = results[1];
                self.dashboardValues[id] = dashboardValues;
                return id;
            });
        },
    });

    // Extended the ListController
    var InvoiceBillListDashboardController = ListController.extend({
        custom_events: _.extend({}, ListController.prototype.custom_events, {
            dashboard_open_action: '_onDashboardOpenAction',
        }),
        /**
         * Function for opening the dashboard
         */
        _onDashboardOpenAction: function(e) {
            return this.do_action(e.data.action_name, {
                additional_context: JSON.parse(e.data.action_context),
                clear_breadcrumbs: true,
            });
        },
    });

    // Extended ListView
    var InvoiceBillListDashboardView = ListView.extend({
        config: _.extend({}, ListView.prototype.config, {
            Model: InvoiceBillListDashboardModel,
            Renderer: InvoiceBillListDashboardRenderer,
            Controller: InvoiceBillListDashboardController,
        }),
    });
    view_registry.add('bill_dashboard_list', InvoiceBillListDashboardView);
    return {
        InvoiceBillListDashboardModel: InvoiceBillListDashboardModel,
        InvoiceBillListDashboardRenderer: InvoiceBillListDashboardRenderer,
        InvoiceBillListDashboardController: InvoiceBillListDashboardController,
    };
});
