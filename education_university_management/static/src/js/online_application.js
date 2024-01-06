/** @odoo-module **/

// This file is used for adding filtration for online application form fields

import publicWidget from "web.public.widget";
import rpc from 'web.rpc';

publicWidget.registry.OnlineApplication = publicWidget.Widget.extend({
    selector: '#online_appl_form',
    events: {
        'change select[name="course"]': '_onCourseChange',
        'change select[name="department"]': '_onDepartmentChange',
    },
    _onCourseChange: function (ev) {
        var self = this
        var course = ev.currentTarget.value;
        self.$el.find('select[name="department"]').find('option').remove()
        self.$el.find('select[name="department"]').append("<option value=0></option>");
        rpc.query({
            model:'university.department',
            method: 'search_read',
            args: [[['course_id', '=', parseInt(course)]]],
            fields: ['name'],
            }).then(function(result){
                result.forEach(function(item){
                    self.$el.find('select[name="department"]').append("<option value=" + item['id'] + ">" +item['name'] + "</option>");
                })
            });
    },
    _onDepartmentChange: function (ev) {
        var self = this
        var department = ev.currentTarget.value;
        self.$el.find('select[name="semester"]').find('option').remove()
        self.$el.find('select[name="semester"]').append("<option value=0></option>");
        rpc.query({
            model:'university.semester',
            method: 'search_read',
            args: [[['department_id', '=', parseInt(department)]]],
            fields: ['name'],
            }).then(function(result){
                result.forEach(function(item){
                    self.$el.find('select[name="semester"]').append("<option value=" + item['id'] + ">" +item['name'] + "</option>");
                })
            });
    }
})
