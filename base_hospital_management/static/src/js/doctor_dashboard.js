/** @odoo-module */
import { registry } from '@web/core/registry';
import { useService } from "@web/core/utils/hooks";
import { Component, proxy } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";

export class DoctorDashboard extends Component {
    static template = "DoctorDashboard";

    setup() {
        super.setup();
        this.orm = useService('orm');
        this.actionService = useService("action");
        this.state = proxy({
            patients: [],
            search_button: false,
            patients_search: [],
            activeSection: '',
        });
    }

    //Function for feting patient data
    async list_patient_data() {
        const patients = await this.orm.call('res.partner', 'fetch_patient_data', []);
        this.state.patients = patients;
        this.state.activeSection = 'patient_data';
        await this.actionService.doAction({
            name: _t('Patient details'),
            type: 'ir.actions.act_window',
            res_model: 'res.partner',
            view_mode: 'list,form',
            views: [[false, 'list'], [false, 'form']],
            domain: [['patient_seq', 'not in', ['New', 'Employee', 'User']]],
        });
    }

    //  Method for generating list of inpatients
    async action_list_inpatient() {
        await this.actionService.doAction({
            name: _t('Inpatient details'),
            type: 'ir.actions.act_window',
            res_model: 'hospital.inpatient',
            view_mode: 'list,form',
            views: [[false, 'list'], [false, 'form']],
        });
        this.state.activeSection = 'inpatient';
    }

    // Fetch surgery details
    async fetch_doctors_schedule() {
        await this.actionService.doAction({
            name: _t('Surgery details'),
            type: 'ir.actions.act_window',
            res_model: 'inpatient.surgery',
            view_mode: 'list,form',
            views: [[false, 'list'], [false, 'form']],
        });
        this.state.activeSection = 'surgery';
    }

    // Fetch op details
    async fetch_consultation() {
        await this.actionService.doAction({
            name: _t('Outpatient Details'),
            type: 'ir.actions.act_window',
            res_model: 'hospital.outpatient',
            view_mode: 'list,form',
            views: [[false, 'list']],
        });
        this.state.activeSection = 'outpatient';
    }

    // Fetch allocation details
    async fetch_allocation_lines() {
        await this.actionService.doAction({
            name: _t('Doctor Allocation'),
            type: 'ir.actions.act_window',
            res_model: 'doctor.allocation',
            view_mode: 'list,form',
            views: [[false, 'list'], [false, 'form']],
        });
        this.state.activeSection = 'allocation';
    }
}

registry.category("actions").add('doctor_dashboard_tags', DoctorDashboard);

