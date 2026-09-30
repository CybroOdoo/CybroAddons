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
from unittest.mock import Mock, patch

from odoo.addons.odoo_integration_workflow.controllers.workflow_controller import WorkflowController
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestWorkflowController(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.workflow = cls.env['api.workflow'].create({'name': 'Controller Workflow'})

    def test_autosave_workflow_ignores_unsaved_workflow(self):
        controller = WorkflowController()

        result = controller.autosave_workflow(workflow_data={'workflow': {'nodes': []}})

        self.assertEqual(result['status'], 'ignored')

    def test_autosave_workflow_updates_existing_workflow(self):
        controller = WorkflowController()
        fake_request = Mock()
        fake_request.env = self.env
        workflow_data = {'nodes': [{'id': 'start', 'type': 'start'}], 'connections': []}

        with patch('odoo.addons.odoo_integration_workflow.controllers.workflow_controller.request', fake_request):
            result = controller.autosave_workflow(workflow_data={
                'id': self.workflow.id,
                'workflow': workflow_data,
            })

        self.assertEqual(result, {'status': 'success'})
        self.assertEqual(json.loads(self.workflow.workflow_data), workflow_data)

    def test_autosave_workflow_returns_not_found(self):
        controller = WorkflowController()
        fake_request = Mock()
        fake_request.env = self.env

        with patch('odoo.addons.odoo_integration_workflow.controllers.workflow_controller.request', fake_request):
            result = controller.autosave_workflow(workflow_data={
                'id': 999999999,
                'workflow': {'nodes': []},
            })

        self.assertEqual(result['status'], 'error')
        self.assertEqual(result['message'], 'Workflow not found')

    def test_autosave_workflow_returns_exception_message(self):
        controller = WorkflowController()

        class BrokenEnv:
            def __getitem__(self, model_name):
                raise Exception('env failure')

        fake_request = Mock()
        fake_request.env = BrokenEnv()

        with patch('odoo.addons.odoo_integration_workflow.controllers.workflow_controller.request', fake_request):
            result = controller.autosave_workflow(workflow_data={
                'id': self.workflow.id,
                'workflow': {'nodes': []},
            })

        self.assertEqual(result['status'], 'error')
        self.assertIn('env failure', result['message'])
