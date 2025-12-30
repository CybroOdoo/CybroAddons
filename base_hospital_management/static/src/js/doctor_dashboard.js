/** @odoo-module */
import { registry} from '@web/core/registry';
import { useService } from "@web/core/utils/hooks";
import { useRef } from "@odoo/owl";
import { Component, useState } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";
import { user } from "@web/core/user";

// Doctor dashboard component initialization
export class DoctorDashboard extends Component {
    setup() {
        super.setup(...arguments);
        this.ref = useRef('root')
        this.orm = useService('orm')
        this.user = user;
        this.actionService = useService("action");
        this.welcome = useRef("welcome");
        this.state = useState({
            patients : [],
            search_button : false,
            patients_search :[],
            activeSection: null,
        });
    }
    //Function for feting patient data
    async list_patient_data(){
        this.actionService.doAction({
            name: _t('Patient details'),
            type: 'ir.actions.act_window',
            res_model: 'res.partner',
            view_mode: 'list,form',
            views: [[false, 'list'],[false, 'form']],
            domain: [['patient_seq', 'not in', ['New', 'Employee', 'User']]]
        });
        const patients = await this.orm.call('res.partner', 'fetch_patient_data', [],);
        this.state.patients = patients;
        this.state.activeSection = 'patient';
    }
//  Method for generating list of inpatients
    action_list_inpatient() {
        this.actionService.doAction({
            name: _t('Inpatient details'),
            type: 'ir.actions.act_window',
            res_model: 'hospital.inpatient',
            view_mode: 'list,form', // Specify both tree and form view modes
            views: [[false, 'list'],[false, 'form']],
        });
        this.state.activeSection = 'inpatient';

    }
//  Fetch surgery details
    fetch_doctors_schedule() {
         this.actionService.doAction({
            name: _t('Surgery details'),
            type: 'ir.actions.act_window',
            res_model: 'inpatient.surgery',
            view_mode: 'list,form', // Specify both tree and form view modes
            views: [[false, 'list'],[false, 'form']],
        });
        this.state.activeSection = 'surgery';
    }
//  Fetch op details
    fetch_consultation(){
        this.actionService.doAction({
            name: _t('Outpatient Details'),
            type: 'ir.actions.act_window',
            res_model: 'hospital.outpatient',
            view_mode: 'list,form',
            views: [[false, 'list']],
        });
        this.state.activeSection = 'consultation';
    }
//  Fetch allocation details
    fetch_allocation_lines() {
        this.actionService.doAction({
            name: _t('Doctor Allocation'),
            type: 'ir.actions.act_window',
            res_model: 'doctor.allocation',
            view_mode: 'list,form',
            views: [[false, 'list'],[false, 'form']]
        });
        this.state.activeSection = 'shift';
    }
}
DoctorDashboard.template = "DoctorDashboard"
registry.category("actions").add('doctor_dashboard_tags', DoctorDashboard);
