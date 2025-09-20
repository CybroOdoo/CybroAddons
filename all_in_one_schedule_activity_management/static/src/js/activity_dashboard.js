/** @odoo-module **/
/**
 * @module all_in_one_schedule_activity_management.activity_dashboard
 * @description This module handles the scheduled activity management.
 */
import { Component, onWillStart} from "@odoo/owl";
import { session } from "@web/session";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { rpc } from "@web/core/network/rpc";

class ActivityDashboard extends Component {
     static template = 'all_in_one_schedule_activity_management.ActivityDashboard';
    setup() {
        super.setup();
      this.orm = useService("orm");
      this.action = useService("action");
      this.manage_activities = {}
        this.dashboards_templates = ['LoginUser', 'ManageActivity', 'ActivityTable'];
         onWillStart(this.willStart);
    }
    async willStart() {
        this.title = 'Dashboard';
        await this.render_dashboards();
    }
    async render_dashboards() {
        this.manage_activities = await rpc('/web/dataset/call_kw', {
            model: 'mail.activity',
            method : 'get_activity_count',
            args: [[]],
            kwargs: {},
        });
        this.manage_activities.done_activity = await this.orm.searchRead("mail.activity",  [["state", "=", 'done'], ["active", "=", false]],);
        this.manage_activities.planned_activity = await this.orm.searchRead("mail.activity",[["state", "=", 'planned']],)
        this.manage_activities.today_activity = await this.orm.searchRead("mail.activity", [["state", "=", 'today']],)
        this.manage_activities.overdue_activity = await this.orm.searchRead("mail.activity",[["state", "=", 'overdue']],)
    }

    async click_view(lineId) {
          this.action.doAction({
            type: 'ir.actions.act_window',
            name: 'All Activity',
            res_model: 'mail.activity',
            domain: ['|',['active', '=', false], ['active', '=', true],['id', '=', lineId]],
            views: [[false, 'list'], [false, 'form']],
            view_mode: 'list,form',
            target: 'current'
          });
    }

    async click_origin_view(e) {
        const id_ = e.target.value;
        const result =  await rpc('/web/dataset/call_kw', {
            model: 'mail.activity',
            method : 'get_activity',
            args: [[],parseInt(id_)],
            kwargs: {},
        });
        this.env.services.action.doAction({
            type: 'ir.actions.act_window',
            name: 'Activity Origin',
            res_model: result.model,
            domain: [['id', '=', result.res_id]],
            views: [[false, 'list'], [false, 'form']],
            view_mode: 'list,form',
            target: 'current'
        });
    }

    all_activity(e) {
        e.stopPropagation();
        e.preventDefault();
        this.env.services.action.doAction({
            type: 'ir.actions.act_window',
            name: 'All Activity',
            res_model: 'mail.activity',
            domain: [],
            views: [[false, 'list'], [false, 'form']],
            view_mode: 'list',
            target: 'current'
        });
    }

    planned_activity(e) {
        e.stopPropagation();
        e.preventDefault();
        this.env.services.action.doAction({
            type: 'ir.actions.act_window',
            name: 'Planned Activity',
            res_model: 'mail.activity',
            domain: [['state', '=', 'planned']],
            views: [[false, 'list'], [false, 'form']],
            view_mode: 'list',
            target: 'current'
        });
    }

    completed_activity(e) {
        e.stopPropagation();
        e.preventDefault();
        this.env.services.action.doAction({
            type: 'ir.actions.act_window',
            name: 'Completed Activity',
            res_model: 'mail.activity',
            domain: [['state', '=', 'done'], ['active', '=', false]],
            views: [[false, 'list'], [false, 'form']],
            view_mode: 'list',
            target: 'current'
        });
    }
    today_activity(e) {
        e.stopPropagation();
        e.preventDefault();
        this.env.services.action.doAction({
            type: 'ir.actions.act_window',
            name: "Today's Activities",
            res_model: 'mail.activity',
            domain: [['state', '=', 'today']],
            views: [[false, 'list'], [false, 'form']],
            view_mode: 'list',
            target: 'current'
        });
    }
    overdue_activity(e) {
        e.stopPropagation();
        e.preventDefault();
        this.env.services.action.doAction({
            type: 'ir.actions.act_window',
            name: 'Overdue Activity',
            res_model: 'mail.activity',
            domain: [['state', '=', 'overdue']],
            views: [[false, 'list'], [false, 'form']],
            view_mode: 'list',
            target: 'current'
        });
    }
    cancelled_activity(e) {
        e.stopPropagation();
        e.preventDefault();
        this.env.services.action.doAction({
            type: 'ir.actions.act_window',
            name: "Today's Activity",
            res_model: 'mail.activity',
            domain: [['state', '=', 'cancel']],
            views: [[false, 'list'], [false, 'form']],
            view_mode: 'list',
            target: 'current'
        });
    }
    activity_type(e) {
        e.stopPropagation();
        e.preventDefault();
       this.env.services.action.doAction({
            type: 'ir.actions.act_window',
            name: "Today's Activity",
            res_model: 'mail.activity.type',
            views: [[false, 'list'], [false, 'form']],
            view_mode: 'list',
            target: 'current'
        });
    }
}
registry.category("actions").add("activity_dashboard", ActivityDashboard);
export default ActivityDashboard;
