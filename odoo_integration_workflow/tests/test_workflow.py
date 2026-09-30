# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
import json
from unittest.mock import patch

from odoo import fields
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestAPIWorkflow(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Workflow = cls.env['api.workflow']
        cls.Result = cls.env['api.workflow.test.result']

    def setUp(self):
        super().setUp()
        self.workflow = self.Workflow.create({
            'name': 'Workflow Model Test',
            'workflow_data': json.dumps({'nodes': [], 'connections': []}),
        })

    def test_get_model_fields(self):
        fields_data = self.Workflow.get_model_fields('res.partner')
        field_names = {field['name'] for field in fields_data}

        self.assertIn('name', field_names)
        self.assertEqual(self.Workflow.get_model_fields('missing.model'), [])
        self.assertEqual(self.Workflow.get_model_fields(False), [])

    def test_open_workflow_builder_with_valid_and_invalid_json(self):
        workflow_data = {'nodes': [{'id': 'start', 'type': 'start'}]}
        self.workflow.workflow_data = json.dumps(workflow_data)

        action = self.workflow.open_workflow_builder()

        self.assertEqual(action['type'], 'ir.actions.client')
        self.assertEqual(action['tag'], 'workflow_builder')
        self.assertEqual(action['params']['workflow_id'], self.workflow.id)
        self.assertEqual(action['params']['workflow_data'], workflow_data)

        self.workflow.workflow_data = '{invalid'
        action = self.workflow.open_workflow_builder()
        self.assertNotIn('workflow_data', action['params'])

    def test_action_view_test_history(self):
        action = self.workflow.action_view_test_history()

        self.assertEqual(action['type'], 'ir.actions.act_window')
        self.assertEqual(action['res_model'], 'api.workflow.test.result')
        self.assertEqual(action['domain'], [('workflow_id', '=', self.workflow.id)])

    def test_compute_last_test_result_uses_result_order(self):
        older = self.Result.create({
            'workflow_id': self.workflow.id,
            'test_date': fields.Datetime.to_datetime('2026-01-01 10:00:00'),
            'success': False,
        })
        newer = self.Result.create({
            'workflow_id': self.workflow.id,
            'test_date': fields.Datetime.to_datetime('2026-01-02 10:00:00'),
            'success': True,
        })

        self.workflow.invalidate_recordset(['test_result_ids', 'last_test_result'])
        self.assertEqual(self.workflow.last_test_result, newer)
        self.assertNotEqual(self.workflow.last_test_result, older)

    def test_save_or_update_workflow_sets_manual_without_automation_node(self):
        workflow_id = self.Workflow.save_or_update_workflow({
            'name': 'Saved Workflow',
            'workflow_data': json.dumps({'nodes': [{'id': 'start', 'type': 'start'}]}),
        })

        workflow = self.Workflow.browse(workflow_id)
        self.assertTrue(workflow.exists())
        self.assertEqual(workflow.trigger_type, 'manual')

    def test_sync_odoo_cron_create_update_and_disable(self):
        auto_node = {
            'type': 'automation',
            'config': {
                'trigger_type': 'cron',
                'interval_number': '2',
                'interval_type': 'hours',
                'cron_active': True,
            },
        }

        self.workflow._sync_odoo_cron(auto_node)

        self.assertTrue(self.workflow.cron_id)
        self.assertEqual(self.workflow.cron_id.interval_number, 2)
        self.assertEqual(self.workflow.cron_id.interval_type, 'hours')
        self.assertTrue(self.workflow.cron_id.active)
        self.assertIn("execute_workflow", self.workflow.cron_id.code)

        self.workflow._sync_odoo_cron({'type': 'automation', 'config': {'trigger_type': 'manual'}})
        self.assertFalse(self.workflow.cron_id)

    def test_execute_workflow_returns_test_result_and_builds_trigger_context(self):
        self.workflow.workflow_data = json.dumps({
            'nodes': [{'id': 'start', 'type': 'start'}],
            'connections': [],
        })
        partner = self.env['res.partner'].create({'name': 'Triggered Partner'})

        with patch.object(type(self.workflow), 'test_workflow', return_value={'success': True, 'message': 'ok'}) as mocked:
            result = self.workflow.execute_workflow({'record': partner})

        self.assertEqual(result, {'success': True, 'message': 'ok'})
        payload = mocked.call_args.args[0]
        self.assertEqual(payload['workflowId'], self.workflow.id)
        self.assertEqual(payload['initial_data']['trigger']['id'], partner.id)

    def test_run_workflow_from_record_returns_notification(self):
        with patch.object(type(self.workflow), 'test_workflow', return_value={'success': True, 'message': 'ok'}):
            action = self.workflow.run_workflow_from_record()

        self.assertEqual(action['type'], 'ir.actions.client')
        self.assertEqual(action['tag'], 'display_notification')
        self.assertEqual(action['params']['type'], 'success')

    def test_test_workflow_dry_run_does_not_create_history(self):
        payload = {
            'workflowId': self.workflow.id,
            'dry_run': True,
            'nodes': [{'id': 'start', 'type': 'start'}],
            'connections': [],
        }

        result = self.Workflow.test_workflow(payload)
        history = self.Result.search([('workflow_id', '=', self.workflow.id)])

        self.assertTrue(result['success'])
        self.assertIn('(Dry Run)', result['message'])
        self.assertFalse(history)

    def test_create_history_log(self):
        self.workflow._create_history_log(
            {'workflowId': self.workflow.id, 'nodes': [{'id': 'n1'}]},
            {'success': False, 'results': [{'success': True}, {'success': False}]},
            0,
        )

        history = self.Result.search([('workflow_id', '=', self.workflow.id)], limit=1)
        self.assertTrue(history)
        self.assertFalse(history.success)
        self.assertEqual(history.total_nodes, 2)
        self.assertEqual(history.successful_nodes, 1)
        self.assertEqual(history.failed_nodes, 1)
