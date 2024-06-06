/** @odoo-module */
import { registry} from '@web/core/registry';
import { useService } from "@web/core/utils/hooks";
import { useRef } from "@odoo/owl";
import { Component, useState } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";

// Doctor dashboard component initialization
export class DoctorDashboard extends Component {
    setup() {
        super.setup(...arguments);
        this.ref = useRef('root')
        this.orm = useService('orm')
        this.user = useService("user");
        this.actionService = useService("action");
        this.welcome = useRef("welcome");
        this.state = useState({
            patients : [],
            search_button : false,
            patients_search :[],
        });
    }
    //Function for feting patient data
    async list_patient_data(){
        this.actionService.doAction({
            name: _t('Patient details'),
            type: 'ir.actions.act_window',
            res_model: 'res.partner',
            view_mode: 'tree,form', // Specify both tree and form view modes
            views: [[false, 'list'],[false, 'form']],
            domain: [['patient_seq', 'not in', ['New', 'Employee', 'User']]]
        });
        const patients = await this.orm.call('res.partner', 'fetch_patient_data', [],);
        if (self.$('.n_active')[0]){
            self.$('.n_active')[0].classList.remove('n_active');
        }
        self.$('.patient_data')[0].classList.add('n_active');
        self.listPatient = patients;
    }
//  Method for generating list of inpatients
    action_list_inpatient() {
        this.actionService.doAction({
            name: _t('Inpatient details'),
            type: 'ir.actions.act_window',
            res_model: 'hospital.inpatient',
            view_mode: 'tree,form', // Specify both tree and form view modes
            views: [[false, 'list'],[false, 'form']],
        });
    }
//  Fetch surgery details
    fetch_doctors_schedule() {
         this.actionService.doAction({
            name: _t('Surgery details'),
            type: 'ir.actions.act_window',
            res_model: 'inpatient.surgery',
            view_mode: 'tree,form', // Specify both tree and form view modes
            views: [[false, 'tree'],[false, 'form']],
        });
    }
//  Fetch op details
    fetch_consultation(){
        this.actionService.doAction({
            name: _t('Outpatient Details'),
            type: 'ir.actions.act_window',
            res_model: 'hospital.outpatient',
            view_mode: 'tree,form', // Specify both tree and form view modes
            views: [[false, 'tree']], // Specify the view type as 'tree'
        });
    }
//  Fetch allocation details
    fetch_allocation_lines() {
        this.actionService.doAction({
            name: _t('Doctor Allocation'),
            type: 'ir.actions.act_window',
            res_model: 'doctor.allocation',
            view_mode: 'tree,form', // Specify both tree and form view modes
            views: [[false, 'list'],[false, 'form']]
        });
    }
}
DoctorDashboard.template = "DoctorDashboard"
registry.category("actions").add('doctor_dashboard_tags', DoctorDashboard);
