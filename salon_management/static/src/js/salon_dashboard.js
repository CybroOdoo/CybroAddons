/** @odoo-module */
import { jsonrpc } from "@web/core/network/rpc_service";
import { Component, onMounted, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
const actionRegistry = registry.category("actions");
import { _t } from "@web/core/l10n/translation";
const { useRef } = owl;
/* Create a component named 'SalonDashboard' with extending Component*/
export class SalonDashboard extends Component {
        setup() {
            super.setup(...arguments);
            var self = this;
            this.bookings_count = useRef("bookings_count");
            this.recent_count = useRef("recent_count");
            this.orders_count = useRef("orders_count");
            this.clients_count = useRef("clients_count");
            this.chairs_dashboard_view = useRef("chairs_dashboard_view");
            this.salon_chair = useRef("Salon-Chair");
            this.state = useState({list : []});
            this.orm = useService('orm');
               onMounted(() => {
                    this.render_dashboards();
               });
        }
        /** Function that works that render values into dashboard **/
        async render_dashboards (ev) {
              var self = this
             var result = await this.orm.call('salon.booking', 'get_booking_count', [0], {})
             $(this.bookings_count.el).append("<span class='stat-digit'>" + result.bookings + "</span>");
             $(this.recent_count.el).append("<span class='stat-digit'>" + result.sales + "</span>");
             $(this.orders_count.el).append("<span class='stat-digit'>" + result.orders + "</span>");
             $(this.clients_count.el).append("<span class='stat-digit'>" + result.clients + "</span>");
             this.state.list = await jsonrpc("/salon/chairs", {});
             $(self.chairs_dashboard_view.el).append(this.state.list)
        }
    /** Click function of 'Bookings' card and open bookings list view**/
    show_bookings(ev) {
        ev.stopPropagation();
        ev.preventDefault();
        this.env.services.action.doAction({
            name: _t("Salon Bookings"),
            type: 'ir.actions.act_window',
            res_model: 'salon.booking',
            view_mode: 'tree,form',
            views: [[false, 'list'], [false, 'form']],
            domain: [['state', '=', 'approved']],
            target: 'current'
        });
    }
    /** Click function of 'Recent Works' card in dashboard**/
    show_sales (ev) {
    ev.stopPropagation();
    ev.preventDefault();
    this.env.services.action.doAction({
        name: _t("Recent Works"),
        type: 'ir.actions.act_window',
        res_model: 'salon.order',
        view_mode: 'tree,form',
        views: [[false, 'list'], [false, 'form']],
        domain: [['stage_id', 'in', [3, 4]]],
        target: 'current'
        });
    }
    /** Click function of 'Salon Client' card**/
    show_clients(e) {
    var self = this;
    e.stopPropagation();
    e.preventDefault();
     this.env.services.action.doAction({
        name: _t("Clients"),
        type: 'ir.actions.act_window',
        res_model: 'res.partner',
        view_mode: 'tree,form',
        views: [[false, 'list'], [false, 'form']],
        domain: [['partner_salon', '=', true]],
        target: 'current'
        });
    }
    /** Click function of 'Salon Orders' card**/
    show_orders(ev) {
    var self = this;
    ev.stopPropagation();
    ev.preventDefault();
    this.env.services.action.doAction({
        name: _t("Salon Orders"),
        type: 'ir.actions.act_window',
        res_model: 'salon.order',
        view_mode: 'tree,form,calendar',
        views: [[false, 'list'], [false, 'form']],
        target: 'current'
        });
    }
    /** Click function of dashboard chairs **/
    chairs_click(ev) {
    var self = this;
    ev.stopPropagation();
    ev.preventDefault();
    var active_id = event.target.id
     this.env.services.action.doAction({
        name: _t("Chair Orders"),
        type: 'ir.actions.act_window',
        res_model: 'salon.order',
        view_mode: 'kanban,tree,form',
        views: [[false, 'kanban'], [false, 'list'], [false, 'form']],
        domain: [['chair_id', '=', parseInt(active_id)]],
        context: {
            default_chair_id: parseInt(active_id)
        },
        target: 'current'
    });
    }
    /** Click function of dashboard chair's settings icon **/
    settings_click (ev) {
        var self = this;
        ev.stopPropagation();
        ev.preventDefault();
        var active_id = event.target.id
         this.env.services.action.doAction({
            name: _t("Chair Orders"),
            type: 'ir.actions.act_window',
            res_model: 'salon.chair',
            view_mode: 'form',
            views: [[false, 'form']],
            context: {
                default_name: active_id
            },
            target: 'current'
        });
    }
}
SalonDashboard.template = "SalonSpaDashBoard";
actionRegistry.add("salon_dashboard", SalonDashboard);
