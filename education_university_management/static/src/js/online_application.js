/** @odoo-module **/
// This file is used for adding filtration for online application form fields
import publicWidget from "@web/legacy/js/public/public_widget";
import { jsonrpc } from "@web/core/network/rpc_service";
publicWidget.registry.OnlineApplication = publicWidget.Widget.extend({
    selector: '#online_appl_form',
    events: {
        'change select[name="course"]': '_onCourseChange',
        'change select[name="semester"]': '_onSemesterChange',
        'submit form': '_onFormSubmit',
    },
     init() {
        this._super(...arguments);
        this.orm = this.bindService("orm");
    },
    async _onCourseChange(ev) {
        ev.preventDefault();
        var self = this
        var course = ev.currentTarget.value;
        self.$el.find('select[name="semester"]').find('option').remove()
        self.$el.find('select[name="semester"]').append("<option value=0></option>");
         self.$el.find('select[name="department"]').append("<option value=0></option>");
          const result = await this.orm.searchRead(
            'university.semester',
            [['department_id.course_id', '=', parseInt(course)]],['name']
        )
         result.forEach(function(item){
                    self.$el.find('select[name="semester"]').append("<option value=" + item['id'] + ">" +item['name'] + "</option>");
                })
        },
    async _onSemesterChange(ev){
        var self = this
        var semester = ev.currentTarget.value;
        self.$el.find('select[name="department"]').find('option').remove()
        self.$el.find('select[name="department"]').append("<option value=0></option>");
         const result = await this.orm.searchRead(
            'university.department',
            [['semester_ids', 'in', [parseInt(semester)]]],['name']
        )
        result.forEach(function(item){
                    self.$el.find('select[name="department"]').append("<option value=" + item['id'] + ">" +item['name'] + "</option>");
                })
      },
    _onFormSubmit(ev) {
        ev.preventDefault();
        // Validate fields
        const course = this.$('select[name="course"]').val();
        const semester = this.$('select[name="semester"]').val();
        const department = this.$('select[name="department"]').val();
        if (!course || !semester || department==0) {
            // If any required field is empty, show validation error
            this._displayErrorMessage('Some Fields are Empty!');
            return;
        }
        ev.currentTarget.submit();
    },
    _displayErrorMessage(message) {
        // Display error message near the submit button or form
        const errorMessage = `<div class="alert alert-danger" role="alert">${message}</div>`;
        this.$('.form-error-message').html(errorMessage);
    },
})
