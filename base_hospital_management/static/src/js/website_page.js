/** @odoo-module **/
import publicWidget from "@web/legacy/js/public/public_widget";
import { jsonrpc } from "@web/core/network/rpc_service";

publicWidget.registry.doctorWidget = publicWidget.Widget.extend({
//  Extends the publicWidget.Widget class to add doctor widget
    selector: '#booking_form',
    events: {
        'change #booking_date': 'changeBookingDate',
        'change #doctor-department': 'updateDoctorOptions',
    },
    init: function () {
        this.changeBookingDate();
    },
//  Update the doctor selection field
    async changeBookingDate () {
        var self = this;
        var selectedDate = $('#booking_date').val();
        await jsonrpc('/patient_booking/get_doctors',  {
            selected_date: selectedDate, department:false
        }).then(function (data) {
            $('#doctor-name').empty();
            // Add the fetched doctors to the dropdown
            $.each(data['doctors'], function (index,doctor) {
                self.$('#doctor-name').append($('<option>', {
                    value: doctor.id,
                    text: doctor.name,
                }));
            });
            self.$('#doctor-department').empty();
            // Add the fetched departments to the dropdown
            self.$('#doctor-department').append($('<option>'));
            $.each(data['departments'], function (index,dep) {
                self.$('#doctor-department').append($('<option>', {
                    value: dep.id,
                    text: dep.name,
                }));
            });
        });
    },
//  Update the doctor selection field
    async updateDoctorOptions () {
        var self = this;
        var selectedDate = this.$('#booking_date').val();
        var department = this.$('#doctor-department').val();
        await jsonrpc('/patient_booking/get_doctors', {
            selected_date: selectedDate, department:department
        }).then(function (data) {
            self.$('#doctor-name').empty();
            // Add the fetched doctors to the dropdown
             $.each(data['doctors'], function (index,doctor) {
                self.$('#doctor-name').append($('<option>', {
                    value: doctor.id,
                    text: doctor.name,
                }));
            });
        });
    },
});
export default publicWidget.registry.doctorWidget;
