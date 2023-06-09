odoo.define('pos_kitchen_screen_odoo.dashboard_action', function(require) {
    "use strict";
    var AbstractAction = require('web.AbstractAction');
    var core = require('web.core');
    document.write(
        unescape("%3Cscript src='https://cdn.jsdelivr.net/npm/chart.js' type='text/javascript'%3E%3C/script%3E"));
    const {
        loadBundle
    } = require("@web/core/assets");
    var QWeb = core.qweb;
    var rpc = require('web.rpc');

        //extending abstract actions for the dashboard
    var KitchenCustomDashBoard = AbstractAction.extend({
        template: 'KitchenCustomDashBoard',
        events: {
            'click .cancel_order': 'cancel_order',
            'click .accept_order': 'accept_order',
            'click .accept_order_line': 'accept_order_line',
            'click .done_order': 'done_order',
            'click .ready_stage': 'ready_stage',
            'click .waiting_stage': 'waiting_stage',
            'click .draft_stage': 'draft_stage',
        },

        //set up the dashboard template and fetch the data every 2 seconds from the backend for the dashboard
        init: function(parent, context) {
            var self = this;
            this._super(parent, context);
            setInterval(function() {
                self.fetch_data();
            }, 1000);
            this.dashboards_templates = ['KitchenOrder'];
            this.shop_id = context.context.default_lead_id;
        },
        //returning the fetched data
        willStart: function() {
            var self = this;
            return Promise.all([loadBundle(this), this._super()]).then(function() {
                return self.fetch_data();
            });
        },
        //rendering the dashboard every 2 seconds
        start: function() {
            var self = this;
            this.set("title", 'Dashboard');
            return this._super().then(function() {
                self.render_dashboards();
                setInterval(function() {
                    self.render_dashboards();
                }, 1000);
            });
        },
        //Used to render the dashboard
        render_dashboards: function() {
            var self = this;
            console.log('render_dashboards',self)
            _.each(this.dashboards_templates, function(template) {
                self.$('.o_pj_dashboard').html(QWeb.render(template, {
                    widget: self
                }));
            });
        },
        // fetch pos order details
        fetch_data: function() {
            var self = this;
            var def1 = self._rpc({
                model: 'pos.order',
                method: 'get_details',
                args: [
                    [], self.shop_id, []
                ],
            }).then(function(result) {
                self.total_room = result['orders'];
                self.lines = result['order_lines'];
            });
            return $.when(def1);
        },
        // cancel the order from the kitchen
        cancel_order: function(e) {
            var input_id = this.$("#" + e.target.id).val();
            rpc.query({
                model: 'pos.order',
                method: 'order_progress_cancel',
                args: [
                    [], input_id
                ]
            })
        },
        // accept the order from the kitchen
        accept_order: function(e) {
            var input_id = this.$("#" + e.target.id).val();
            ScrollReveal().reveal("#" + e.target.id, {
                delay: 1000,
                duration: 2000,
                opacity: 0,
                distance: "50%",
                origin: "top",
                reset: true,
                interval: 600,
            });
            rpc.query({
                model: 'pos.order',
                method: 'order_progress_draft',
                args: [
                    [], input_id
                ]
            })
        },
        //set the stage is ready to see the completed stage orders
        ready_stage: function(e) {
            var self = this;
            self.stages = 'ready';
        },
        //set the stage is waiting to see the ready stage orders
        waiting_stage: function(e) {
            var self = this;
            self.stages = 'waiting';
        },
        //set the stage is draft to see the cooking stage orders
        draft_stage: function(e) {
            var self = this;
            self.stages = 'draft';
        },
        // change the status of the order from the kitchen
        done_order: function(e) {
            var input_id = this.$("#" + e.target.id).val();
            rpc.query({
                model: 'pos.order',
                method: 'order_progress_change',
                args: [
                    [], input_id
                ]
            });
        },

        // change the status of the product from the kitchen
        accept_order_line: function(e) {
            var input_id = this.$("#" + e.target.id).val();
            rpc.query({
                model: 'pos.order.line',
                method: 'order_progress_change',
                args: [
                    [], input_id
                ]
            })
        },

    });
    core.action_registry.add('kitchen_custom_dashboard_tags', KitchenCustomDashBoard);
    return KitchenCustomDashBoard;
});