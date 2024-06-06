/** @odoo-module */
import { registry} from '@web/core/registry';
import { useService } from "@web/core/utils/hooks";
import { Component, onMounted, useState, useRef } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";

export class LabDashBoard extends Component {
//Initialize LabDashBoard
    setup() {
        super.setup(...arguments);
        this.orm = useService('orm')
        this.user = useService("user");
        this.ref = useRef("root");
        this.actionService = useService("action");
        this.form_view = useRef("form_view");
        this.form_view_copy = useRef("form_view_copy");
        this.published_data =useRef("published_data");
        this.main_view = useRef("main_view");
        this.process_test_view = useRef('process_test_view');
        var record_id;
        this.state= useState({
            tests_confirm :[],
            tests_confirm_data :[],
            test_data :[],
            all_test_data :[],
            process_data :[],
            process_test_data :[],
            published_data :[],
        });
        onMounted(async () => {
            await this._loadTestData();
        });
    }
//  Method for getting the lab test data
    async _loadTestData (){
        this.form_view.el.classList.add("d-none")
        this.process_test_view.el.classList.add("d-none")
        this.published_data.el.classList.add("d-none")
        this.main_view.el.classList.remove("d-none")
        self.state = 'lab.test.line'
        var domain = [['state', '=', 'draft']];
        var result = await this.orm.call('lab.test.line', 'search_read',[domain],);
            this.state.tests_confirm = result,
            $('#form-view').attr('hidden', 'true');
            $('#create-button').html('<button class="btn btn-outline-info" id="create" style="margin-left:10px;">Create</button>')
    }
//   Method on clicking the tests to confirm button
    async _fetchTestData (ev){
        this.main_view.el.classList.add("d-none")
        this.form_view.el.classList.remove("d-none")
        var record_id = parseInt($(ev.target).closest('tr').data('index'));
        var record_id = this.state.tests_confirm[record_id].id
        this.record_id = record_id
        var result = await this.orm.call('lab.test.line', 'action_get_patient_data', [record_id],);
        this.state.tests_confirm_data = result,
        this.state.test_data = result['test_data']
    }
//  Method on clicking confirm button in the tests to confirm
    confirmLabTest (){
        this.orm.call('lab.test.line','create_lab_tests',[this.record_id],
        ).then(function (result){
            $('#action-button').hide();
            alert('The test has been confirmed ');
        })
    }
//  Method for fetching all lab tests on clicking second button click
    async _allLabTest () {
        this.form_view.el.classList.add("d-none")
        this.process_test_view.el.classList.remove("d-none")
        this.published_data.el.classList.add("d-none")
        this.main_view.el.classList.add("d-none")
        var result = await this.orm.call('patient.lab.test','search_read',);
        this.state.all_test_data = result
    }
//  Method for getting all test data
    fetch_all_test_data (ev){
        var self = this;
        var record_id = parseInt($(ev.target).closest('tr').data('index'));
        self.load_all_test_data(record_id)
    }
//  Method for loading all test data
    async load_all_test_data (record_id){
        const action = await this.actionService.doAction({
                            name: _t('Inpatient details'),
                            type: 'ir.actions.act_window',
                            res_model: 'patient.lab.test',
                            res_id: record_id,
                            views: [[false, "form"]],
                        });
        return action;
    }
//  Method for getting result published lab tests
    async _loadPublished (){
        this.form_view.el.classList.add("d-none")
        this.process_test_view.el.classList.add("d-none")
        this.published_data.el.classList.remove("d-none")
        this.main_view.el.classList.add("d-none")
        var result = await this.orm.call('lab.test.result','print_test_results',)
        this.state.published_data = result
    }
}
LabDashBoard.template = "LabDashboard"
registry.category("actions").add('lab_dashboard_tags', LabDashBoard);
