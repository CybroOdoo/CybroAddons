/** @odoo-module */
import publicWidget from '@web/legacy/js/public/public_widget';
import { rpc } from "@web/core/network/rpc";

publicWidget.registry.DentalClinic = publicWidget.Widget.extend({
    selector: '#appointment_form',
    events: {
        'change #specialised_id': '_onSpecialisedChange',
        'change #doctor_id': '_onDoctorChange',
        'change #patient_id': '_onPatientChange',
    },

    /**
     * @constructor
     */
    init: function (parent, options) {
        this._super.apply(this, arguments);
    },

    /**
     * Populate doctor dropdown when specialisation changes.
     */
    _onSpecialisedChange: async function () {
        const specialised_id = this.$el.find('#specialised_id').val();

        // Reset dependent dropdowns
        this.$el.find('#doctor_id').empty().prepend('<option value="">Select Doctor</option>');
        this.$el.find('#time_shift').empty().prepend('<option value="">Select Appointment Time</option>');

        if (!specialised_id) return;

        try {
            const records = await rpc("/specialised_doctors", {
                specialised_id: specialised_id,
            });
            records.forEach((record) => {
                this.$el.find('#doctor_id').append(
                    `<option value="${record.id}">${record.name}</option>`
                );
            });
        } catch (error) {
            console.error("Error fetching doctors:", error);
        }
    },

    /**
     * Populate time-shift dropdown when doctor changes.
     */
    _onDoctorChange: async function () {
        const doctor_id = this.$el.find('#doctor_id').val();

        // Reset time shift dropdown
        this.$el.find('#time_shift').empty().prepend('<option value="">Select Appointment Time</option>');

        if (!doctor_id) return;

        try {
            const records = await rpc("/doctors_shifts", {
                doctor_id: doctor_id,
            });
            records.forEach((record) => {
                this.$el.find('#time_shift').append(
                    `<option value="${record.id}">${record.name}</option>`
                );
            });
        } catch (error) {
            console.error("Error fetching shifts:", error);
        }
    },

    /**
     * Auto-fill phone and age when patient selection changes.
     */
    _onPatientChange: async function () {
        const patient_id = this.$el.find('#patient_id').val();

        if (!patient_id) return;

        try {
            const result = await rpc("/patient_details", {
                patient_id: patient_id,
            });
            if (result && result.length) {
                this.$el.find('#phone').val(result[0].phone || '');
                this.$el.find('#age').val(result[0].patient_age || '');
            }
        } catch (error) {
            console.error("Error fetching patient details:", error);
        }
    },
});