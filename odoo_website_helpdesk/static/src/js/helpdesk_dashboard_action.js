odoo.define('odoo_website_helpdesk.helpdesk_dashboard_action', function (require){
"use strict";
var AbstractAction = require('web.AbstractAction');
var ControlPanel = require('web.ControlPanel');
var core = require('web.core');
var QWeb = core.qweb;
var rpc = require('web.rpc');
var ajax = require('web.ajax');
var CustomDashBoard = AbstractAction.extend({
   template: 'HelpdeskDashBoard',

   start: function() {
        var self = this;
        ajax.rpc('/helpdesk_dashboard').then(function (res) {
        $("#new_state_value").text(res.new)
        $("#inprogress_value").text(res.in_progress)
        $("#canceled_value").text(res.canceled)
        $("#done_value").text(res.done)
        $("#closed_value").text(res.closed)
        $("#new_state").click(function(){
        self.do_action({
            name:'New Tickets',
            type: 'ir.actions.act_window',
            res_model: 'help.ticket',
            view_mode: 'tree,form',
            views: [[false, 'list'],[false, 'form']],
            domain: [['id', '=', res.new_id]],
        })
        })
        $("#in_progress_state").click(function(){
        self.do_action({
            name:'In progress Tickets',
            type: 'ir.actions.act_window',
            res_model: 'help.ticket',
            view_mode: 'tree,form',
            views: [[false, 'list'],[false, 'form']],
            domain: [['id', '=', res.in_progress_id]],
        })
        })
        $("#cancelled_state").click(function(){
        self.do_action({
            name:'Canceled Tickets',
            type: 'ir.actions.act_window',
            res_model: 'help.ticket',
            view_mode: 'tree,form',
            views: [[false, 'list'],[false, 'form']],
            domain: [['id', '=', res.canceled_id]],
        })
        })
        $("#done_state").click(function(){
        self.do_action({
            name:'Done Tickets',
            type: 'ir.actions.act_window',
            res_model: 'help.ticket',
            view_mode: 'tree,form',
            views: [[false, 'list'],[false, 'form']],
            domain: [['id', '=', res.done_id]],
        })
        })
        $("#closed_state").click(function(){
        self.do_action({
            name:'Closed Tickets',
            type: 'ir.actions.act_window',
            res_model: 'help.ticket',
            view_mode: 'tree,form',
            views: [[false, 'list'],[false, 'form']],
            domain: [['id', '=', res.closed_id]],
        })
        })

//        week function start
        $("#filter_selection").change(function(e){
        var target = $(e.target)
        var value = target.val()
        if (value == "this_week") {
        ajax.rpc('/helpdesk_dashboard_week').then(function (res) {
        $("#new_state_value").text(res.new)
        $("#inprogress_value").text(res.in_progress)
        $("#canceled_value").text(res.canceled)
        $("#done_value").text(res.done)
        $("#closed_value").text(res.closed)
        $("#new_state").click(function(){
        self.do_action({
            name:'New Tickets',
            type: 'ir.actions.act_window',
            res_model: 'help.ticket',
            view_mode: 'tree,form',
            views: [[false, 'list'],[false, 'form']],
            domain: [['id', '=', res.new_id]],
        })
        })
        $("#in_progress_state").click(function(){
        self.do_action({
            name:'In progress Tickets',
            type: 'ir.actions.act_window',
            res_model: 'help.ticket',
            view_mode: 'tree,form',
            views: [[false, 'list'],[false, 'form']],
            domain: [['id', '=', res.in_progress_id]],
        })
        })
        $("#cancelled_state").click(function(){
        self.do_action({
            name:'Canceled Tickets',
            type: 'ir.actions.act_window',
            res_model: 'help.ticket',
            view_mode: 'tree,form',
            views: [[false, 'list'],[false, 'form']],
            domain: [['id', '=', res.canceled_id]],
        })
        })
        $("#done_state").click(function(){
        self.do_action({
            name:'Done Tickets',
            type: 'ir.actions.act_window',
            res_model: 'help.ticket',
            view_mode: 'tree,form',
            views: [[false, 'list'],[false, 'form']],
            domain: [['id', '=', res.done_id]],
        })
        })
        $("#closed_state").click(function(){
        self.do_action({
            name:'Closed Tickets',
            type: 'ir.actions.act_window',
            res_model: 'help.ticket',
            view_mode: 'tree,form',
            views: [[false, 'list'],[false, 'form']],
            domain: [['id', '=', res.closed_id]],
             })
          })
        })
        }else if (value == "this_month") {
        ajax.rpc('/helpdesk_dashboard_month').then(function (res) {
        $("#new_state_value").text(res.new)
        $("#inprogress_value").text(res.in_progress)
        $("#canceled_value").text(res.canceled)
        $("#done_value").text(res.done)
        $("#closed_value").text(res.closed)
        $("#new_state").click(function(){
        self.do_action({
            name:'New Tickets',
            type: 'ir.actions.act_window',
            res_model: 'help.ticket',
            view_mode: 'tree,form',
            views: [[false, 'list'],[false, 'form']],
            domain: [['id', '=', res.new_id]],
        })
        })
        $("#in_progress_state").click(function(){
        self.do_action({
            name:'In progress Tickets',
            type: 'ir.actions.act_window',
            res_model: 'help.ticket',
            view_mode: 'tree,form',
            views: [[false, 'list'],[false, 'form']],
            domain: [['id', '=', res.in_progress_id]],
        })
        })
        $("#cancelled_state").click(function(){
        self.do_action({
            name:'Canceled Tickets',
            type: 'ir.actions.act_window',
            res_model: 'help.ticket',
            view_mode: 'tree,form',
            views: [[false, 'list'],[false, 'form']],
            domain: [['id', '=', res.canceled_id]],
        })
        })
        $("#done_state").click(function(){
        self.do_action({
            name:'Done Tickets',
            type: 'ir.actions.act_window',
            res_model: 'help.ticket',
            view_mode: 'tree,form',
            views: [[false, 'list'],[false, 'form']],
            domain: [['id', '=', res.done_id]],
        })
        })
        $("#closed_state").click(function(){
        self.do_action({
            name:'Closed Tickets',
            type: 'ir.actions.act_window',
            res_model: 'help.ticket',
            view_mode: 'tree,form',
            views: [[false, 'list'],[false, 'form']],
            domain: [['id', '=', res.closed_id]],
             })
          })
          })
        }else if (value == "this_year") {
        ajax.rpc('/helpdesk_dashboard_year').then(function (res) {
             $("#new_state_value").text(res.new)
        $("#inprogress_value").text(res.in_progress)
        $("#canceled_value").text(res.canceled)
        $("#done_value").text(res.done)
        $("#closed_value").text(res.closed)
        $("#new_state").click(function(){
        self.do_action({
            name:'New Tickets',
            type: 'ir.actions.act_window',
            res_model: 'help.ticket',
            view_mode: 'tree,form',
            views: [[false, 'list'],[false, 'form']],
            domain: [['id', '=', res.new_id]],
        })
        })
        $("#in_progress_state").click(function(){
        self.do_action({
            name:'In progress Tickets',
            type: 'ir.actions.act_window',
            res_model: 'help.ticket',
            view_mode: 'tree,form',
            views: [[false, 'list'],[false, 'form']],
            domain: [['id', '=', res.in_progress_id]],
        })
        })
        $("#cancelled_state").click(function(){
        self.do_action({
            name:'Canceled Tickets',
            type: 'ir.actions.act_window',
            res_model: 'help.ticket',
            view_mode: 'tree,form',
            views: [[false, 'list'],[false, 'form']],
            domain: [['id', '=', res.canceled_id]],
        })
        })
        $("#done_state").click(function(){
        self.do_action({
            name:'Done Tickets',
            type: 'ir.actions.act_window',
            res_model: 'help.ticket',
            view_mode: 'tree,form',
            views: [[false, 'list'],[false, 'form']],
            domain: [['id', '=', res.done_id]],
        })
        })
        $("#closed_state").click(function(){
        self.do_action({
            name:'Closed Tickets',
            type: 'ir.actions.act_window',
            res_model: 'help.ticket',
            view_mode: 'tree,form',
            views: [[false, 'list'],[false, 'form']],
            domain: [['id', '=', res.closed_id]],
             })
          })
          })
        }
        });
   })
  },
})




core.action_registry.add('helpdesk_dashboard_tag', CustomDashBoard);

return CustomDashBoard
})