/** @odoo-module **/
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Layout } from "@web/search/layout";
import { Component, onWillStart, proxy } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";

export class ActivityDashboard extends Component {
    setup() {
        super.setup();
        this.orm = useService('orm');
        this.action = useService('action');
        this.notification = useService('notification');

        this.state = proxy({
            planned_activity: [],
            today_activity: [],
            overdue_activity: [],
            done_activity: [],
            len_all: 0,
            len_planned: 0,
            len_done: 0,
            len_today: 0,
            len_overdue: 0,
            activity_type: 0,
        });

        // Backward-compatible method aliases for templates
        this.render_dashboards = this.renderDashboards.bind(this);
        this.show_all_activities = this.showAllActivities.bind(this);
        this.show_planned_activities = this.showPlannedActivities.bind(this);
        this.show_completed_activities = this.showCompletedActivities.bind(this);
        this.show_today_activities = this.showTodayActivities.bind(this);
        this.show_overdue_activities = this.showOverdueActivities.bind(this);
        this.show_activity_types = this.showActivityTypes.bind(this);
        this.click_view = this.clickView.bind(this);
        this.click_origin = this.clickOrigin.bind(this);

        onWillStart(async () => await this.renderDashboards());
    }

    get len_all() { return this.state.len_all; }
    get len_planned() { return this.state.len_planned; }
    get len_done() { return this.state.len_done; }
    get len_today() { return this.state.len_today; }
    get len_overdue() { return this.state.len_overdue; }
    get activity_type() { return this.state.activity_type; }
    get planned_activity() { return this.state.planned_activity; }
    get today_activity() { return this.state.today_activity; }
    get done_activity() { return this.state.done_activity; }
    get overdue_activity() { return this.state.overdue_activity; }

    async renderDashboards() {
        try {
            const fields = ['display_name', 'activity_type_id', 'user_id', 'date_deadline'];
            const planned_activity = await this.orm.searchRead('mail.activity', [["state", "=", 'planned']], fields) || [];
            const today_activity = await this.orm.searchRead('mail.activity', [["state", "=", 'today']], fields) || [];
            const overdue_activity = await this.orm.searchRead('mail.activity', [["state", "=", 'overdue']], fields) || [];
            const done_activity = await this.orm.searchRead('mail.activity', [["state", "=", 'done'], ['active', 'in', [true, false]]], fields) || [];
            const activity_type_count = await this.orm.searchCount('mail.activity.type', []);

            this.state.planned_activity = planned_activity;
            this.state.today_activity = today_activity;
            this.state.overdue_activity = overdue_activity;
            this.state.done_activity = done_activity;

            this.state.len_planned = planned_activity.length;
            this.state.len_today = today_activity.length;
            this.state.len_overdue = overdue_activity.length;
            this.state.len_done = done_activity.length;
            this.state.len_all = this.state.len_planned + this.state.len_today + this.state.len_overdue + this.state.len_done;
            this.state.activity_type = activity_type_count;
        } catch (error) {
            this.notification.add(_t("Could not load activity dashboard data."), { type: "danger" });
        }
    }

    showAllActivities(e) {
        if (e) {
            e.stopPropagation();
            e.preventDefault();
        }
        this.action.doAction({
            name: _t("All Activities"),
            type: 'ir.actions.act_window',
            res_model: 'mail.activity',
            domain: [['active', 'in', [true, false]]],
            view_mode: 'list,form',
            views: [[false, 'list'], [false, 'form']],
            target: 'current',
            context: {
                create: false,
            },
        });
    }

    showPlannedActivities(e) {
        if (e) {
            e.stopPropagation();
            e.preventDefault();
        }
        this.action.doAction({
            name: _t("Planned Activities"),
            type: 'ir.actions.act_window',
            res_model: 'mail.activity',
            domain: [['state', '=', 'planned']],
            view_mode: 'list,form',
            views: [[false, 'list'], [false, 'form']],
            target: 'current',
            context: {
                create: false,
            },
        });
    }

    showCompletedActivities(e) {
        if (e) {
            e.stopPropagation();
            e.preventDefault();
        }
        this.action.doAction({
            name: _t("Completed Activities"),
            type: 'ir.actions.act_window',
            res_model: 'mail.activity',
            domain: [['state', '=', 'done'], ['active', 'in', [true, false]]],
            view_mode: 'list,form',
            views: [[false, 'list'], [false, 'form']],
            target: 'current',
            context: {
                create: false,
            },
        });
    }

    showTodayActivities(e) {
        if (e) {
            e.stopPropagation();
            e.preventDefault();
        }
        this.action.doAction({
            name: _t("Today's Activities"),
            type: 'ir.actions.act_window',
            res_model: 'mail.activity',
            domain: [['state', '=', 'today']],
            view_mode: 'list,form',
            views: [[false, 'list'], [false, 'form']],
            target: 'current',
            context: {
                create: false,
            },
        });
    }

    showOverdueActivities(e) {
        if (e) {
            e.stopPropagation();
            e.preventDefault();
        }
        this.action.doAction({
            name: _t("Overdue Activities"),
            type: 'ir.actions.act_window',
            res_model: 'mail.activity',
            domain: [['state', '=', 'overdue']],
            view_mode: 'list,form',
            views: [[false, 'list'], [false, 'form']],
            target: 'current',
            context: {
                create: false,
            },
        });
    }

    showActivityTypes(e) {
        if (e) {
            e.stopPropagation();
            e.preventDefault();
        }
        this.action.doAction({
            name: _t("Activity Type"),
            type: 'ir.actions.act_window',
            res_model: 'mail.activity.type',
            view_mode: 'list,form',
            views: [[false, 'list'], [false, 'form']],
            target: 'current',
        });
    }

    clickView(e) {
        const id = e && e.currentTarget ? e.currentTarget.value : (e && e.target ? e.target.value : null);
        if (!id) return;
        this.action.doAction({
            type: 'ir.actions.act_window',
            name: 'All Activity',
            res_model: 'mail.activity',
            res_id: parseInt(id, 10),
            views: [[false, 'form']],
            view_mode: 'form',
            target: 'current',
        });
    }

    async clickOrigin(e) {
        const id = e && e.currentTarget ? e.currentTarget.value : (e && e.target ? e.target.value : null);
        if (!id) return;
        const result = await this.orm.call('mail.activity', 'get_activity', [parseInt(id, 10)], {});
        if (!result || !result.model || !result.res_id) {
            this.notification.add(
                _t("This activity has no linked document."),
                { type: "warning" }
            );
            return;
        }
        this.action.doAction({
            type: 'ir.actions.act_window',
            name: 'Activity Origin',
            res_model: result.model,
            res_id: result.res_id,
            views: [[false, 'form']],
            view_mode: 'form',
            target: 'current',
        });
    }
}
ActivityDashboard.template = "ActivityDashboard";
ActivityDashboard.components = { Layout };
registry.category("actions").add("activity_dashboard", ActivityDashboard);

