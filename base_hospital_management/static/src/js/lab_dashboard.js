/** @odoo-module */
import { registry } from '@web/core/registry';
import { useService } from "@web/core/utils/hooks";
import { Component, onMounted, useState, useRef } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";
import { user } from "@web/core/user";

export class LabDashBoard extends Component {
    setup() {
        super.setup(...arguments);
        this.orm = useService('orm');
        this.user = user;
        this.ref = useRef("root");
        this.actionService = useService("action");
        this.form_view = useRef("form_view");
        this.form_view_copy = useRef("form_view_copy");
        this.published_data = useRef("published_data");
        this.main_view = useRef("main_view");
        this.process_test_view = useRef('process_test_view');

        this.state = useState({
            tests_confirm: [],
            tests_confirm_data: [],
            test_data: [],
            all_test_data: [],
            process_data: [],
            process_test_data: [],
            published_data: [],
            activeView: 'main', // Track which view is currently active
            currentRecordId: null,
        });

        onMounted(async () => {
            await this._loadTestData();
        });
    }

    async _loadTestData() {
        this._setActiveView('main');
        const domain = [['state', '=', 'draft']];
        const result = await this.orm.call('lab.test.line', 'search_read', [domain]);
        this.state.tests_confirm = result;
    }

    async _fetchTestData(ev) {
        // Get the index from the data attribute
        const record_id = parseInt(ev.currentTarget.dataset.index);
        this.state.currentRecordId = this.state.tests_confirm[record_id].id;

        const result = await this.orm.call(
            'lab.test.line',
            'action_get_patient_data',
            [this.state.currentRecordId]
        );

        this.state.tests_confirm_data = result;
        this.state.test_data = result['test_data'];
        this._setActiveView('form');
    }

    async confirmLabTest() {
        try {
            await this.orm.call(
                'lab.test.line',
                'create_lab_tests',
                [this.state.currentRecordId]
            );
            // Use proper notification system instead of alert
            this.env.services.notification.add(_t('The test has been confirmed'), {
                type: 'success',
            });
            await this._loadTestData(); // Reload the list
        } catch (error) {
            this.env.services.notification.add(_t('Failed to confirm test'), {
                type: 'danger',
            });
        }
    }

    async _allLabTest() {
        this._setActiveView('process');
        const result = await this.orm.call('patient.lab.test', 'search_read', []);
        this.state.all_test_data = result;
    }

    async fetch_all_test_data(ev) {
        // Get the index directly from the dataset
        const record_id = parseInt(ev.currentTarget.dataset.index);
        await this._openTestForm(record_id);
    }

    async _openTestForm(record_id) {
        return this.actionService.doAction({
            name: _t('Inpatient details'),
            type: 'ir.actions.act_window',
            res_model: 'patient.lab.test',
            res_id: record_id,
            views: [[false, "form"]],
        });
    }

    async _loadPublished() {
        this._setActiveView('published');
        const result = await this.orm.call('lab.test.result', 'print_test_results');
        this.state.published_data = result;
    }

    _setActiveView(view) {
        this.state.activeView = view;
    }

    static template = "LabDashboard";
}
registry.category("actions").add('lab_dashboard_tags', LabDashBoard);
