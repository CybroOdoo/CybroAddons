odoo.define('hrms_dashboard.Dashboard', function (require) {
"use strict";
var ajax = require('web.ajax');
var ControlPanelMixin = require('web.ControlPanelMixin');
var core = require('web.core');
var Dialog = require('web.Dialog');
var session = require('web.session');
var rpc = require('web.rpc');
var utils = require('web.utils');
var web_client = require('web.web_client');
var Widget = require('web.Widget');
var session = require('web.session');
var _t = core._t;
var QWeb = core.qweb;

var HrDashboard = Widget.extend(ControlPanelMixin, {
    template: "hrms_dashboard.HrDashboardMain",
    events: {
        'click .hr_leave_request_approve': 'leaves_to_approve',
        'click .hr_leave_allocations_approve': 'leave_allocations_to_approve',
        'click .hr_timesheets': 'hr_timesheets',
        'click .hr_job_application_approve': 'job_applications_to_approve',
        'click .hr_payslip':'hr_payslip',
        'click .hr_contract':'hr_contract',
        'click .hr_employee':'hr_employee',
        'click .leaves_request_month':'leaves_request_month',
        'click .leaves_request':'leaves_request'
    },

    init: function(parent, context) {
        this._super(parent, context);
        this.login_employee = true;
        this.employee_birthday = [];
        this._super(parent,context);

    },

    start: function() {
        var self = this;
        for(var i in self.breadcrumbs){
            self.breadcrumbs[i].title = "Dashboard";
        }
        self.update_control_panel({breadcrumbs: self.breadcrumbs}, {clear: true});
        rpc.query({
            model: "hr.employee",
            method: "get_user_employee_details",
        })
        .then(function (result) {
            self.login_employee =  result[0];
            $('.o_hr_dashboard').html(QWeb.render('ManagerDashboard', {widget: self}));
            $('.o_hr_dashboard').prepend(QWeb.render('LoginEmployeeDetails', {widget: self}));
            /*need to check user access levels*/
            session.user_has_group('hr.group_hr_manager').then(function(has_group){
                if(has_group == false){
                    $('.employee_dashboard_main').css("display", "none");
                }
            });
        });
        var today = new Date().toJSON().slice(0,10).replace(/-/g,'/');
        rpc.query({
            model: "hr.employee",
            method: "search_read",
            args: [
                [['birthday', '!=', false]],
                ['name', 'birthday','image']
            ],
        })
        .then(function (res) {
            for (var i = 0; i < res.length; i++) {
                var bday_dt = new Date(res[i]['birthday']);
                var bday_month = bday_dt.getMonth();
                var bday_day = bday_dt.getDate();
                var today_dt = new Date( today);
                var today_month = today_dt.getMonth();
                var today_day = today_dt.getDate();
                var day = new Date();
                var next_day = new Date(day.setDate(day.getDate() + 7));
                var next_week = next_day.toJSON().slice(0,10).replace(/-/g,'/');
                var bday_date = bday_dt.toJSON().slice(0,10).replace(/-/g,'/');;
                if (bday_month == today_month  && bday_day >= today_day && next_week >= bday_date){
                    self.employee_birthday.push(res[i]);
                    var flag = 1;
                }
            }
                if (flag !=1){
                    self.employee_birthday = false;
                }
            $('.o_hr_birthday_reminder').html(QWeb.render('BirthdayEventDashboard', {widget: self}));
        });
        return this._super().then(function() {
            self.$el.parent().addClass('oe_background_grey');
        });
    },

    hr_payslip: function(e){
        var self = this;
        e.stopPropagation();
        e.preventDefault();
        this.do_action({
            name: _t("Employee Payslips"),
            type: 'ir.actions.act_window',
            res_model: 'hr.payslip',
            view_mode: 'tree,form,calendar',
            view_type: 'form',
            views: [[false, 'list'],[false, 'form']],
            target: 'current'
        })
    },

    hr_contract: function(e){
        var self = this;
        e.stopPropagation();
        e.preventDefault();
        this.do_action({
            name: _t("Contracts"),
            type: 'ir.actions.act_window',
            res_model: 'hr.contract',
            view_mode: 'tree,form,calendar',
            view_type: 'form',
            views: [[false, 'list'],[false, 'form']],
            target: 'current'
        })
    },

    leaves_request_month: function(e) {
        var self = this;
        e.stopPropagation();
        e.preventDefault();
        var date = new Date();
        var firstDay = new Date(date.getFullYear(), date.getMonth(), 1);
        var lastDay = new Date(date.getFullYear(), date.getMonth() + 1, 0);
        var fday = firstDay.toJSON().slice(0,10).replace(/-/g,'-');
        var lday = lastDay.toJSON().slice(0,10).replace(/-/g,'-');
        this.do_action({
            name: _t("Leave Request"),
            type: 'ir.actions.act_window',
            res_model: 'hr.holidays',
            view_mode: 'tree,form,calendar',
            view_type: 'form',
            views: [[false, 'list'],[false, 'form']],
            domain: [['date_from','>', fday],['state','=','confirm'],['date_from','<', lday]],
            target: 'current'
        })
    },

    leaves_request: function(e) {
        var self = this;
        e.stopPropagation();
        e.preventDefault();
        this.do_action({
            name: _t("Leave Request"),
            type: 'ir.actions.act_window',
            res_model: 'hr.holidays',
            view_mode: 'tree,form,calendar',
            view_type: 'form',
            views: [[false, 'list'],[false, 'form']],
            domain: [['type','=','add']],
            target: 'current'
        })
    },
    leaves_to_approve: function(e) {
        var self = this;
        e.stopPropagation();
        e.preventDefault();
        this.do_action({
            name: _t("Leave Request"),
            type: 'ir.actions.act_window',
            res_model: 'hr.holidays',
            view_mode: 'tree,form,calendar',
            view_type: 'form',
            views: [[false, 'list'],[false, 'form']],
            context: {'search_default_approve': true},
            domain: [['type','=','remove'],],
            target: 'current'
        })
    },
    leave_allocations_to_approve: function(e) {
        var self = this;
        e.stopPropagation();
        e.preventDefault();
        this.do_action({
            name: _t("Leave Allocation Request"),
            type: 'ir.actions.act_window',
            res_model: 'hr.holidays',
            view_mode: 'tree,form,calendar',
            view_type: 'form',
            views: [[false, 'list'],[false, 'form']],
            context: {'search_default_approve': true},
            domain: [['type','=','add'],],
            target: 'current'
        })
    },

    hr_timesheets: function(e) {
         var self = this;
        event.stopPropagation();
        event.preventDefault();
        this.do_action({
            name: _t("Timesheets"),
            type: 'ir.actions.act_window',
            res_model: 'account.analytic.line',
            view_mode: 'tree,form',
            view_type: 'form',
            views: [[false, 'list'], [false, 'form']],
            context: {
                'search_default_employee_id': [self.login_employee.id],
                'search_default_month': true,
            },
            domain: [['project_id', '!=', false]],
            target: 'current'
        })
    },
    job_applications_to_approve: function(event){
        var self = this;
        event.stopPropagation();
        event.preventDefault();
        this.do_action({
            name: _t("Applications"),
            type: 'ir.actions.act_window',
            res_model: 'hr.applicant',
            view_mode: 'tree,kanban,form,pivot,graph,calendar',
            view_type: 'form',
            views: [[false, 'list'],[false, 'kanban'],[false, 'form'],
                    [false, 'pivot'],[false, 'graph'],[false, 'calendar']],
            context: {},
            target: 'current'
        })
    },
});

core.action_registry.add('hr_dashboard', HrDashboard);

return HrDashboard;

});
