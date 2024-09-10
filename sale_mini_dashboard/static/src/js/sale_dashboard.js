odoo.define('sale_mini_dashboard.sale_dashboard', function(require) {
    "use strict";
    var core = require('web.core');
    var ListModel = require('web.ListModel');
    var ListRenderer = require('web.ListRenderer');
    var ListView = require('web.ListView');
    var KanbanRenderer = require('web.KanbanRenderer');
    var KanbanView = require('web.KanbanView');
    var KanbanModel = require('web.KanbanModel');
    var view_registry = require('web.view_registry');
    var SampleServer = require('web.SampleServer');
    var QWeb = core.qweb;
    const session = require('web.session');


    // Add mock of method 'retrieve_dashboard' in SampleServer, so that we can have
    // the sample data in empty purchase kanban and list view
    let dashboardValues;
    SampleServer.mockRegistry.add('sale.order/get_dashboard_values', () => {
        return Object.assign({}, dashboardValues);
    });
    /**
     * Sale Dashboard component for managing sales data and filters.
     * @extends AbstractAction
     */
    var SaleDashBoard = ListRenderer.extend({
        events: _.extend({}, ListRenderer.prototype.events, {
            'click .g-col-4': 'setSearchContext',
        }),
        /**
         * @override
         * @private
         * @returns {Promise}
         */
        _renderView: function() {
            var self = this;
            return this._super.apply(this, arguments).then(function() {
                var values = self.state.dashboardValues;
                var sale_mini_dashboard = QWeb.render('sale_mini_dashboard.SaleDashboard', {
                    values: values,
                });
                self.$el.prepend(sale_mini_dashboard);
            });
        },

        async setSearchContext(ev) {
            try {
                // Extract filter names from the button attribute
                let filter_name = ev.currentTarget.getAttribute("title");
                let filters = filter_name.split(',');
                var search_view = this.getParent();
                // Clear the current search query
                let searchInput = search_view.el.querySelector('.o_searchview_input_container');
                if (!searchInput) {
                    console.error("Search input element is not found");
                    return;
                }
                let facets = searchInput.querySelectorAll('.o_facet_remove');
                for (const facet of facets) {
                    facet.click(); // This will call _onFacetRemove
                }
                // Wait for UI updates before continuing
                await this.waitForFacetsToClear();
                // Activate filters in the search model
                var searchItems = _.filter(search_view.searchModel.get('filters'), function(item) {
                    return filters.includes(item.description);
                });
                for (const item of searchItems) {
                    this.getParent().searchModel.dispatch("toggleFilter", item.id);
                }
            } catch (error) {
                console.error("Error in setSearchContext:", error);
            }
        },

        // Helper function to wait for facets to be removed
        waitForFacetsToClear() {
            return new Promise((resolve) => {
                // Check if there are no active facets left
                let interval = setInterval(() => {
                    let search_view = this.getParent();
                    let activeFilters = search_view.searchModel.get('filters').filter(f => f.isActive);
                    if (activeFilters.length === 0) {
                        clearInterval(interval);
                        resolve();
                    }
                }, 100); // Check every 100ms
            });
        },
    });
    var SaleListDashboardModel = ListModel.extend({
        /**
         * @override
         */
        init: function() {
            this.dashboardValues = {};
            this._super.apply(this, arguments);
        },

        /**
         * @override
         */
        __get: function(localID) {
            var result = this._super.apply(this, arguments);
            if (_.isObject(result)) {
                result.dashboardValues = this.dashboardValues[localID];
            }
            return result;
        },
        /**
         * @override
         * @returns {Promise}
         */
        __load: function() {
            return this._loadDashboard(this._super.apply(this, arguments));
        },
        /**
         * @override
         * @returns {Promise}
         */
        __reload: function() {
            return this._loadDashboard(this._super.apply(this, arguments));
        },

        /**
         * @private
         * @param {Promise} super_def a promise that resolves with a dataPoint id
         * @returns {Promise -> string} resolves to the dataPoint id
         */
        _loadDashboard: function(super_def) {
            var self = this;
            var dashboard_def = this._rpc({
                model: 'sale.order',
                method: 'get_dashboard_values',
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

    var SaleListDashboardView = ListView.extend({
        config: _.extend({}, ListView.prototype.config, {
            Model: SaleListDashboardModel,
            Renderer: SaleDashBoard,
        }),

    });


    //--------------------------------------------------------------------------
    // Kanban View
    //--------------------------------------------------------------------------
    var SaleKanbanDashBoard = KanbanRenderer.extend({
        events: _.extend({}, KanbanRenderer.prototype.events, {
            'click .g-col-4': 'setSearchContext',
        }),
        /**
         * @override
         * @private
         * @returns {Promise}
         */
        _renderView: function() {
            var self = this;
            return this._super.apply(this, arguments).then(function() {
                var values = self.state.dashboardValues;
                var sale_mini_dashboard = QWeb.render('sale_mini_dashboard.SaleDashboard', {
                    values: values,
                });

                self.$el.prepend(sale_mini_dashboard);
            });
        },

        /**
         * @private
         * @param {MouseEvent}
         */
        _onDashboardActionClicked: function(e) {
            e.preventDefault();
            var $action = $(e.currentTarget);
            this.trigger_up('sale_dashboard_open_action', {
                action_name: "sale.view_quotation_tree_with_onboarding",
                action_context: $action.attr('filter_name'),
            });
        },

        async setSearchContext(ev) {
            try {
                // Extract filter names from the button attribute
                let filter_name = ev.currentTarget.getAttribute("title");
                let filters = filter_name.split(',');
                var search_view = this.getParent();
                // Clear the current search query
                let searchInput = search_view.el.querySelector('.o_searchview_input_container');
                if (!searchInput) {
                    console.error("Search input element is not found");
                    return;
                }
                let facets = searchInput.querySelectorAll('.o_facet_remove');
                for (const facet of facets) {
                    facet.click(); // This will call _onFacetRemove
                }
                // Wait for UI updates before continuing
                await this.waitForFacetsToClear();
                // Activate filters in the search model
                var searchItems = _.filter(search_view.searchModel.get('filters'), function(item) {
                    return filters.includes(item.description);
                });
                for (const item of searchItems) {
                    this.getParent().searchModel.dispatch("toggleFilter", item.id);
                }
            } catch (error) {
                console.error("Error in setSearchContext:", error);
            }
        },

        // Helper function to wait for facets to be removed
        waitForFacetsToClear() {
            return new Promise((resolve) => {
                // Check if there are no active facets left
                let interval = setInterval(() => {
                    let search_view = this.getParent();
                    let activeFilters = search_view.searchModel.get('filters').filter(f => f.isActive);
                    if (activeFilters.length === 0) {
                        clearInterval(interval);
                        resolve();
                    }
                }, 100); // Check every 100ms
            });
        },

    });
    var SaleKanbanDashboardModel = KanbanModel.extend({
        /**
         * @override
         */
        init: function() {
            this.dashboardValues = {};
            this._super.apply(this, arguments);
        },

        /**
         * @override
         */
        __get: function(localID) {
            var result = this._super.apply(this, arguments);
            if (_.isObject(result)) {
                result.dashboardValues = this.dashboardValues[localID];
            }
            return result;
        },
        /**
         * @override
         * @returns {Promise}
         */
        __load: function() {
            return this._loadDashboard(this._super.apply(this, arguments));
        },
        /**
         * @override
         * @returns {Promise}
         */
        __reload: function() {
            return this._loadDashboard(this._super.apply(this, arguments));
        },

        /**
         * @private
         * @param {Promise} super_def a promise that resolves with a dataPoint id
         * @returns {Promise -> string} resolves to the dataPoint id
         */
        _loadDashboard: function(super_def) {
            var self = this;
            var dashboard_def = this._rpc({
                model: 'sale.order',
                method: 'get_dashboard_values',
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
    var SaleKanbanDashboardView = KanbanView.extend({
        config: _.extend({}, KanbanView.prototype.config, {
            Model: SaleKanbanDashboardModel,
            Renderer: SaleKanbanDashBoard,
        }),

    });

    view_registry.add('sale_list_dashboard', SaleListDashboardView);
    view_registry.add('sale_kanban_dashboard', SaleKanbanDashboardView);

    return {
        SaleListDashboardModel: SaleListDashboardModel,
        SaleDashBoard: SaleDashBoard,
        SaleKanbanDashboardModel: SaleKanbanDashboardModel,
        SaleKanbanDashBoard: SaleKanbanDashBoard,
    };
});
