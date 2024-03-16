/**
 * @module all_in_one_schedule_activity_management.activity_dashboard
 * @description This module handles the scheduled activity management.
 */
 odoo.define('all_in_one_schedule_activity_management.activity_dashboard', function (require) {
    'use strict';
    var AbstractAction = require('web.AbstractAction');
    var core = require('web.core');
    var rpc = require('web.rpc');
    var QWeb = core.qweb;
    var session = require('web.session');
    var user = session.user_id
    /**
     * Customized AbstractAction with mail activity dashboard.
     *
     * @class ActivityDashboard
     * @extends AbstractAction
     */
    var ActivityDashboard = AbstractAction.extend({
    template: 'ActivityDashboard',
    events: {
        'click .all_activity': 'all_activity',
        'click .planned_activity': 'planned_activity',
        'click .completed_activity': 'completed_activity',
        'click .today_activity': 'today_activity',
        'click .overdue_activity': 'overdue_activity',
        'click .cancelled_activity': 'cancelled_activity',
        'click .activity_type': 'activity_type',
        'click .click-view': 'click_view',
        'click .click-origin-view': 'click_origin_view'
    },
    /** Initialising function */
    init: function(parent, context) {
        this._super(parent, context);
        this.upcoming_events = [];
        this.dashboards_templates = ['LoginUser', 'ManageActivity', 'ActivityTable'];
        this.login_employee = [];
    },
    /** Creates the start function */
    start: function() {
        var self = this;
        this.set("title", 'Dashboard');
        return this._super().then(function() {
            self.render_dashboards();
        });
    },
    /** Rendering dashboard and calls rpc function to handle the dashboard events */
    render_dashboards: function () {
        var self = this;
        this._rpc({
            model: 'mail.activity',
            method : 'get_activity_count',
            args: [[]]
        }).then(function(result){
            self.$('.table_view').html(QWeb.render('ManageActivity', {
                len_all: result.len_all,
                len_planned: result.len_planned,
                len_done: result.len_done,
                len_today: result.len_today,
                len_overdue: result.len_overdue,
                len_cancel: result.len_cancel
            }));
        });
        self.results = ''
        self._rpc({
            model: 'mail.activity',
            method : 'search_read',
            domain: [["state", "=", 'done'], ["active", "=", false]],
            }).then(function(done_activity){
                self._rpc({
                    model: 'mail.activity',
                    method : 'search_read',
                    domain: [["state", "=", 'planned']],
                }).then(function(planned_activity){
                    self._rpc({
                        model: 'mail.activity',
                        method : 'search_read',
                        domain: [["state", "=", 'today']],
                    }).then(function(today_activity){
                        self._rpc({
                            model: 'mail.activity',
                            method : 'search_read',
                            domain: [["state", "=", 'overdue']],
                        }).then(function(overdue_activity){
                            self.$('.table_view_activity').html(QWeb.render('ActivityTable', {
                                done_activity: done_activity,
                                planned_activity: planned_activity,
                                today_activity: today_activity,
                                overdue_activity: overdue_activity
                            }));
                        });
                    });
                });
            });
       },
    /** This function is shows the all activities. */
    click_view: function(e){
        var id = e.target.value
        this.do_action({
            type: 'ir.actions.act_window',
            name: 'All Activity',
            res_model: 'mail.activity',
            domain: [['id', '=', id]],
            views: [[false, 'list'], [false, 'form']],
            view_mode: 'list,form',
            target: 'current'
        });
    },
    /** This function returns origins of each activity */
    click_origin_view: function(e){
        var id_ = e.target.value;
        var self = this;
        this._rpc({
            model: 'mail.activity',
            method : 'get_activity',
            args: [[],parseInt(id_)],
        }).then(function(result){this
            self.do_action({
            type: 'ir.actions.act_window',
            name: 'Activity Origin',
            res_model: result.model,
            domain: [['id', '=', result.res_id]],
            views: [[false, 'list'], [false, 'form']],
            view_mode: 'list,form',
            target: 'current'
        });
        });
    },
    /** This function is shows the all activities. */
    all_activity: function(e) {
        var self = this;
        e.stopPropagation();
        e.preventDefault();
        var options = {
            on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        };
        this.do_action({
            type: 'ir.actions.act_window',
            name: 'All Activity',
            res_model: 'mail.activity',
            domain: [],
            views: [[false, 'list'], [false, 'form']],
            view_mode: 'list',
            target: 'current'
        });
    },
    /** This function is shows the planned activities. */
    planned_activity: function(e) {
        var self = this;
        e.stopPropagation();
        e.preventDefault();
        var options = {
            on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        };
        this.do_action({
            type: 'ir.actions.act_window',
            name: 'Planned Activity',
            res_model: 'mail.activity',
            domain: [['state', '=', 'planned']],
            views: [[false, 'list'], [false, 'form']],
            view_mode: 'list',
            target: 'current'
        });
    },
    /** This function is shows the completed activities. */
    completed_activity: function(e) {
        var self = this;
        e.stopPropagation();
        e.preventDefault();
        var options = {
            on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        };
        this.do_action({
            type: 'ir.actions.act_window',
            name: 'Completed Activity',
            res_model: 'mail.activity',
            domain: [['state', '=', 'done'], ['active', '=', false]],
            views: [[false, 'list'], [false, 'form']],
            view_mode: 'list',
            target: 'current'
        });
    },
    /** This function is shows the today's activities. */
    today_activity: function(e) {
        var self = this;
        e.stopPropagation();
        e.preventDefault();

        this.do_action({
            type: 'ir.actions.act_window',
            name: "Today's Activities",
            res_model: 'mail.activity',
            domain: [['state', '=', 'today']],
            views: [[false, 'list'], [false, 'form']],
            view_mode: 'list',
            target: 'current'
        });
    },
    /** This function is shows the overdue activities. */
    overdue_activity: function(e) {
        var self = this;
        e.stopPropagation();
        e.preventDefault();
        var options = {
            on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        };
        this.do_action({
            type: 'ir.actions.act_window',
            name: 'Overdue Activity',
            res_model: 'mail.activity',
            domain: [['state', '=', 'overdue']],
            views: [[false, 'list'], [false, 'form']],
            view_mode: 'list',
            target: 'current'
        });

    },
    /** This function is shows the canceled activities. */
    cancelled_activity: function(e) {
        var self = this;
        e.stopPropagation();
        e.preventDefault();
        var options = {
            on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        };
        this.do_action({
            type: 'ir.actions.act_window',
            name: "Today's Activity",
            res_model: 'mail.activity',
            domain: [['state', '=', 'cancel']],
            views: [[false, 'list'], [false, 'form']],
            view_mode: 'list',
            target: 'current'
        });
    },
    /** This function is shows the all activities type. */
    activity_type: function(e) {
        var self = this;
        e.stopPropagation();
        e.preventDefault();
        var options = {
            on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        };
        var action = {
            type: 'ir.actions.act_window',
            name: 'Activity Type',
            res_model: 'activity.type',
            domain: [['state', 'in', ['today']]],
            views: [[false, 'list'], [false, 'form']],
            view_mode: 'list',
            target: 'current'
        }
        this.do_action({
            type: 'ir.actions.act_window',
            name: "Today's Activity",
            res_model: 'mail.activity.type',
            views: [[false, 'list'], [false, 'form']],
            view_mode: 'list',
            target: 'current'
        });
    },

});
   core.action_registry.add("activity_dashboard", ActivityDashboard);
   return ActivityDashboard;
});
