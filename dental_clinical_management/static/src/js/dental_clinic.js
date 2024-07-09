/** @odoo-module */
import publicWidget from '@web/legacy/js/public/public_widget';
import { jsonrpc } from "@web/core/network/rpc_service";


publicWidget.registry.DentalClinic = publicWidget.Widget.extend({
    selector: '#appointment_form',
    events: {
        'change #specialised_id': '_onSpecialisedChange',
        'change #doctor_id': '_onDoctorChange',
    },
    /**
     * @constructor
     */
    init: function (parent, options) {
        this._super.apply(this, arguments);
        this.rpc = this.bindService("rpc");
    },
    _onSpecialisedChange: async function () {
        var self = this
        var specialised_id = this.$el.find('#specialised_id').val();
        await jsonrpc("/specialised_doctors", {
            specialised_id: specialised_id
        }).then(function (records) {
            self.$el.find('#doctor_id').empty();
            self.$el.find('#doctor_id').prepend('<option value="">Select Doctor</option>');
            records.forEach(function (record) {
                self.$('#doctor_id').append(
                    `<option value="${record.id}">${record.name}</option>`
                );
            });
        });
    },
    _onDoctorChange: async function () {
        var self = this
        var doctor_id = this.$el.find('#doctor_id').val();
        await jsonrpc("/doctors_shifts", {
            doctor_id: doctor_id
        }).then(function (records) {
            self.$el.find('#time_shift').empty();
            self.$el.find('#time_shift').prepend('<option value="">Select Appointment Time</option>');
            records.forEach(function (record) {
                self.$('#time_shift').append(
                    `<option value="${record.id}">${record.name}</option>`
                );
            });
        });
    },
});