/** @odoo-module **/
// This file is used for adding filtration for online application form fields
import publicWidget from "@web/legacy/js/public/public_widget";
import { jsonrpc } from "@web/core/network/rpc_service";
publicWidget.registry.OnlineApplication = publicWidget.Widget.extend({
    selector: '#online_appl_form',
    events: {
        'change select[name="course"]': '_onCourseChange',
        'change select[name="department"]': '_onDepartmentChange',
    },
     init() {
        this._super(...arguments);
        this.orm = this.bindService("orm");
    },
    async _onCourseChange(ev) {
        ev.preventDefault();
        var self = this
        var course = ev.currentTarget.value;
        self.$el.find('select[name="department"]').find('option').remove()
        self.$el.find('select[name="department"]').append("<option value=0></option>");
          const result = await this.orm.searchRead(
            'university.department',
            [['course_id', '=', parseInt(course)]],['name']
        )
         result.forEach(function(item){
                    self.$el.find('select[name="department"]').append("<option value=" + item['id'] + ">" +item['name'] + "</option>");
                })
        },
      async _onDepartmentChange(ev){
        var self = this
        var department = ev.currentTarget.value;
        self.$el.find('select[name="semester"]').find('option').remove()
        self.$el.find('select[name="semester"]').append("<option value=0></option>");
         const result = await this.orm.searchRead(
            'university.semester',
            [['department_id', '=', parseInt(department)]],['name']
        )
        result.forEach(function(item){
                    self.$el.find('select[name="semester"]').append("<option value=" + item['id'] + ">" +item['name'] + "</option>");
                })
      }
})
