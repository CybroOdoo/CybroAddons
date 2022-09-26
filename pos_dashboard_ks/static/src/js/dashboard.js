odoo.define('pos_dashboard_ks.dashboard_kanban', function (require) {
    "use strict";

    var AbstractAction = require('web.AbstractAction');
    var core = require('web.core');
    var session = require('web.session');
    var QWeb = core.qweb;
    var DashboardKanban = AbstractAction.extend({
        template: 'dashboard_template',
        events:{
            'click .start_order_line': '_onStartOrEndOrderLine',
            'click .end_order_line': '_onStartOrEndOrderLine',
            'click .show_note': '_onShowNote',
        },
        show_pending_orders: true,
        show_in_progress_orders: true,
        show_done_orders: true,
        category_ids: [],
        pos_config_ids: [],


        init: function(parent, action) {
            this._super(parent, action);
        },

        start: function() {
            var self = this;
            this._rpc({
                model: 'res.users',
                method: 'search_read',
                args: [[['id', '=', session.uid]], ['kitchen_category_ids']],
                args: [[['id', '=', session.uid]], ['kitchen_category_ids', 'pos_config_ids']],
            }).then(function (data) {
                self.category_ids = data[0].kitchen_category_ids;
                self.pos_config_ids = data[0].pos_config_ids;
                self.load_data();
            });
            setInterval(function() {
                self.load_data();
            }, 30000);
        },

        load_data: function () {
            var self = this;
            if ($('.dashboard_container').length === 0) {
                self.$('.kanban_view').html(QWeb.render('dashboard_orders', {}));
            }
            var today = new Date();
            var dd = String(today.getDate()).padStart(2, '0');
            var mm = String(today.getMonth() + 1).padStart(2, '0');
            var yyyy = today.getFullYear();

            today = yyyy + '-' + mm + '-' + dd;
            var fields = ['id', 'dashboard_state', 'name', 'start_date', 'user_id', 'pos_reference', 'table_id', 'create_date', 'customer_count'];
            self._rpc({
                model: 'pos.order.line',
                method: 'search_read',
                args: [[
                    ['create_date', '>=', today],
                    ['product_id.pos_categ_id.id', 'in', self.category_ids],
                    ['order_id.session_id.config_id.id', 'in', self.pos_config_ids]],
                    ['dashboard_state', 'full_product_name', 'qty', 'order_id', 'product_id', 'note']
                ],
            }).then(function(lines) {
                console.log('lim', lines);
                self._rpc({
                    model: 'pos.order',
                    method: 'search_read',
                    args: [[['create_date', '>=', today], ['dashboard_state', '=', ['pending', 'in_progress', 'done']]], fields],
                }).then(function(orders) {
                    orders.forEach(function(order) {
                        order.user_id = order.user_id && order.user_id.length > 0 ? order.user_id[1] : '';
                        order.table_id = order.table_id && order.table_id.length > 0 ? order.table_id[1] : '';
                        order.create_date = self.convertDateToLocale(new Date(order.create_date));
                    });
                    if (self.show_pending_orders) {
                        self.getPendingOrders(lines, orders);
                    }
                    if (self.show_in_progress_orders) {
                        self.getInProgressOrders(lines, orders);
                    }
                    if (self.show_done_orders) {
                        self.getDoneOrders(lines, orders);
                    }
                  
                });
               
            });

        },

        convertDateToLocale: function(date) {
            var newDate = new Date(date.getTime()+date.getTimezoneOffset()*60*1000);
            var offset = date.getTimezoneOffset() / 60;
            var hours = date.getHours();
            newDate.setHours(hours - offset);
            return newDate.toLocaleString();
        },
        getPendingOrders: function(lines, orders) {
            var self = this;
            var all_orders = this.getOrdersWithLines(orders, lines);
            orders = all_orders.filter((o) => o.dashboard_state === 'pending');
            var processing_orders = all_orders.filter((o) => o.dashboard_state === 'in_progress');
            var done_orders = all_orders.filter((o) => o. dashboard_state === 'done');

            this.$('.kitchen_grid.pending .pending_content').html(QWeb.render('dashboard_orders', {
                orders: orders
            }));

            this.$('.kitchen_grid.prepare .preparing_content').html(QWeb.render('dashboard_orders', {
                orders: processing_orders
            }));

            this.$('.kitchen_grid.done .done_content').html(QWeb.render('dashboard_orders', {
                orders: done_orders
            }));

        },
    
        getInProgressOrders: function(lines, orders) {
            var self = this;
            orders = this.getOrdersWithLines(orders, lines);
            orders = orders.filter((order) => {
                const in_progress_lines = order.lines.filter((line) => line.dashboard_state === 'in_progress');
                const pending_lines = order.lines.filter((line) => line.dashboard_state === 'pending');
                const done_lines = order.lines.filter((line) => line.dashboard_state === 'done');
                return (in_progress_lines.length > 0) || (pending_lines.length > 0 && done_lines.length > 0);
            });
        },
    
        
    
        getDoneOrders: function(lines, orders) {
            var self = this;
            orders = this.getOrdersWithLines(orders, lines);
            orders = orders.filter((order) => {
                return order.lines.filter((line) => line.dashboard_state !== 'done').length === 0;
            });
        },
        getOrdersWithLines: function(orders, lines) {
            orders.forEach(function(order) {
                order.lines = lines.filter((line) => line.order_id[0] === order.id);
            });
            orders = orders.filter((order) => order.lines.length > 0);
            return orders;
        },
        _onStartOrEndOrderLine: function (ev) {
            var today = new Date();
            var date = today.getFullYear()+'-'+String(today.getMonth()+1).padStart(2, '0') + '-'+String(today.getDate()).padStart(2, '0');
            var time = String(today.getHours()).padStart(2, '0') + ":" + String(today.getMinutes()).padStart(2, '0') + ":" + String(today.getSeconds()).padStart(2, '0');
            var dateTime = date+' '+time;
            var self = this;
            ev.stopPropagation();
            var values = {}
            var id = $(ev.currentTarget).parent().data( "id");
            values[$(ev.currentTarget).data( "type") === 'start' ? 'start_date' : 'end_date'] = dateTime;

            this._rpc({
                model: 'pos.order.line',
                method: 'state_change',
                args: [[id], values],
            }).then(function () {
                self.load_data();
            });
        },
         _onShowNote: function (ev) {
            var note = $(ev.currentTarget).data( "note");
            var html_data = '<div class="icon-close-container"><div class="recipie_description">' + note + '</div>';
            html_data += '</div>';
            self.$('.note_container').html(html_data);
            self.$('.note_container').show();

        },


    });

    core.action_registry.add("dashboard_kanban", DashboardKanban);
    });