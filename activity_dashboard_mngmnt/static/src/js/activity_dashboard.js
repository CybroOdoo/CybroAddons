/** @odoo-module **/
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Layout } from "@web/search/layout";
import { Component, onWillStart } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";
export class ActivityDashboard extends Component {
    setup() {
        super.setup();
        this.rpc = useService("rpc");
        this.userService = useService("user");
        this.orm = useService('orm');
        onWillStart(async () => await this.render_dashboards());
    }
    async render_dashboards (ev) {
    //Method for rendering dashboard.
        var self = this;
         const planned_activity = await self.orm.call('mail.activity',
         'search_read', [], {
            domain: [["state", "=", 'planned']]
         });
         const today_activity = await self.orm.call('mail.activity',
         'search_read', [], {
            domain: [["state", "=", 'today']]
         });
         const overdue_activity = await self.orm.call('mail.activity',
         'search_read', [], {
            domain: [["state", "=", 'overdue']]
         });
        const done_activity = await self.orm.call('mail.activity',
        'search_read', [],
         {
            domain: [["state", "=", 'done'],['active','in',[true,false]]]
         });
         const activity_type = await self.orm.call('mail.activity.type',
                                                        'search_count', [],
                                                        {domain:[]})
         self.len_all= planned_activity.length+done_activity
         .length+today_activity.length+overdue_activity.length
         self.len_planned=planned_activity.length
         self.len_done=done_activity.length
         self.len_today=today_activity.length
         self.len_overdue=overdue_activity.length
         self.done_activity=done_activity
         self.planned_activity=planned_activity
         self.today_activity=today_activity
         self.overdue_activity=overdue_activity
         self.activity_type=await self.orm.call('mail.activity.type',
                                                        'search_count', [],
                                                        {domain:[]});
    }
   /**
     * Event handler to open the list of all activities.
     */
	show_all_activities(e) {
		e.stopPropagation();
		e.preventDefault();
		var options = {
            on_reverse_breadcrumb: self.on_reverse_breadcrumb,
        };
		this.env.services.action.doAction({
        name: _t("All Activities"),
        type: 'ir.actions.act_window',
        res_model: 'mail.activity',
        view_mode: 'tree,form',
        domain: [['active', 'in', [true,false]]],
        views: [[false, 'list'], [false, 'form']],
        view_mode: 'form',
        target: 'current'
        }, options);
	}
	/**
     * Event handler to open the list of planned activities.
     */
	show_planned_activities(e) {
		e.stopPropagation();
		e.preventDefault();
		var options = {
            on_reverse_breadcrumb: self.on_reverse_breadcrumb,
        };
		this.env.services.action.doAction({
        name: _t("Planned Activities"),
        type: 'ir.actions.act_window',
        res_model: 'mail.activity',
        domain: [['state', '=', 'planned']],
        view_mode: 'tree,form',
        views: [[false, 'list'], [false, 'form']],
        view_mode: 'form',
        target: 'current'
        }, options);
	}
	/**
     * Event handler to open the list of completed activities.
     */
	show_completed_activities(e) {
		e.stopPropagation();
		e.preventDefault();
		var options = {
            on_reverse_breadcrumb: self.on_reverse_breadcrumb,
        };
		this.env.services.action.doAction({
        name: _t("Completed Activities"),
        type: 'ir.actions.act_window',
        res_model: 'mail.activity',
        domain: [['state', '=', 'done'],['active','in',[true,false]]],
        view_mode: 'tree,form',
        views: [[false, 'list'], [false, 'form']],
        view_mode: 'form',
        target: 'current'
        }, options);
	}
	/**
     * Event handler to open the list of today's activities.
     */
	show_today_activities(e) {
		e.stopPropagation();
		e.preventDefault();
		var options = {
            on_reverse_breadcrumb: self.on_reverse_breadcrumb,
        };
		this.env.services.action.doAction({
        name: _t("Today's Activities"),
        type: 'ir.actions.act_window',
        res_model: 'mail.activity',
        domain: [['state', '=', 'today']],
        view_mode: 'tree,form',
        views: [[false, 'list'], [false, 'form']],
        view_mode: 'form',
        target: 'current'
        }, options);
	}/**
     * Event handler to open the list of overdue activities.
     */
	show_overdue_activities(e) {
		e.stopPropagation();
		e.preventDefault();
		var options = {
            on_reverse_breadcrumb: self.on_reverse_breadcrumb,
        };
		this.env.services.action.doAction({
        name: _t("Overdue Activities"),
        type: 'ir.actions.act_window',
        res_model: 'mail.activity',
        domain: [['state', '=', 'overdue']],
        view_mode: 'tree,form',
        views: [[false, 'list'], [false, 'form']],
        view_mode: 'form',
        target: 'current'
        }, options);
	}
	/**
     * Event handler to open the list of activity types.
     */
	show_activity_types(e) {
		e.stopPropagation();
		e.preventDefault();
		var options = {
            on_reverse_breadcrumb: self.on_reverse_breadcrumb,
        };
		this.env.services.action.doAction({
        name: _t("Activity Type"),
        type: 'ir.actions.act_window',
        res_model: 'mail.activity.type',
        view_mode: 'tree,form',
        views: [[false, 'list'], [false, 'form']],
        view_mode: 'form',
        target: 'current'
        }, options);
	}
    /**
     * Event handler for view button click.
     */
	click_view(e) {
	     var id = e.target.value;
        this.env.services.action.doAction({
            type: 'ir.actions.act_window',
            name: 'All Activity',
            res_model: 'mail.activity',
            res_id: parseInt(id),
            views: [[false, 'form']],
            view_mode: 'form',
            target: 'current'
        });
	}
	  /**
     * Event handler for view button click.
     */
	async click_origin(e) {
	    var id = e.target.value;
        var self = this;
        var result =await self.orm.call('mail.activity', 'get_activity',
         [0,parseInt(id)],{})
        self.env.services.action.doAction({
            type: 'ir.actions.act_window',
            name: 'Activity Origin',
            res_model: result.model,
            res_id: result.res_id,
            views: [[false, 'form']],
            view_mode: 'form',
            target: 'current'
        });
	}
}
ActivityDashboard.template = "ActivityDashboard";
ActivityDashboard.components = { Layout };
registry.category("actions").add("activity_dashboard", ActivityDashboard);
