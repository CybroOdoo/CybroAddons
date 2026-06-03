odoo.define('hierarchical_chart_widget.OrgChart', function (require) {
"use strict";
var AbstractField = require('web.AbstractField');
var core = require('web.core');
var fieldRegistry = require('web.field_registry');
var QWeb = core.qweb;
const { Component, tags, useState } = owl;
var _t = core._t;


var OrgChart = AbstractField.extend({
    supportedFieldTypes: ['one2many'],
    events: _.extend({}, AbstractField.prototype.events, {
        'click .org-node': 'onChildClick',
    }),
    init: function () {
        this._super.apply(this, arguments);
    },
    _render: async function () {
        var model = this.model
        await this.DepartmentDetails(this.res_id,model)
        this.$el.html(QWeb.render('CustomerChartWidget',{'values': this.OrgStateData,}));
    },
    onChildClick(ev){
//        on clicking the nodes it will be redirected to their page
        let id = ev.target.getAttribute('value')
        const action = {
                type: 'ir.actions.act_window',
                res_model:this.model,
                res_id:parseInt(id),
                domain: [],
                views: [ [false, "form"],[false, "list"],],
                name: "Schedule Log",
                target: 'current',
            };
        this.do_action(action)
    },
    async DepartmentDetails(department_id,model){
        //----fetching the details for template
        this.OrgStateData = await this._rpc({
               model: 'hr.department',
               method: 'get_child_dept',
               args: [department_id,model]
            });
    },
});
    fieldRegistry.add("org_chart", OrgChart);
    return OrgChart;
});
