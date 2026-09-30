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

from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestWorkflowTestResult(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Workflow = cls.env['api.workflow']
        cls.Result = cls.env['api.workflow.test.result']
        cls.workflow = cls.Workflow.create({'name': 'Workflow Result Test'})

    def test_compute_success_rate(self):
        result = self.Result.create({
            'workflow_id': self.workflow.id,
            'total_nodes': 4,
            'successful_nodes': 3,
        })

        self.assertEqual(result.success_rate, 75.0)

        empty_result = self.Result.create({
            'workflow_id': self.workflow.id,
            'total_nodes': 0,
            'successful_nodes': 0,
        })
        self.assertEqual(empty_result.success_rate, 0.0)

    def test_action_open_node_structure(self):
        node_structure = {'nodes': [{'id': 'start', 'type': 'start'}], 'connections': []}
        result = self.Result.create({
            'workflow_id': self.workflow.id,
            'node_structure': json.dumps(node_structure),
        })

        action = result.action_open_node_structure()

        self.assertEqual(action['type'], 'ir.actions.client')
        self.assertEqual(action['tag'], 'workflow_builder')
        self.assertEqual(action['params']['workflow_name'], self.workflow.name)
        self.assertEqual(action['params']['workflow_data'], node_structure)

    def test_get_formatted_node_structure(self):
        result = self.Result.create({
            'workflow_id': self.workflow.id,
            'node_structure': '{"b": 2, "a": 1}',
        })
        self.assertEqual(result.get_formatted_node_structure(), '{\n  "b": 2,\n  "a": 1\n}')

        result.node_structure = '{invalid'
        self.assertEqual(result.get_formatted_node_structure(), '{invalid')

        result.node_structure = False
        self.assertEqual(result.get_formatted_node_structure(), 'No node structure available')

    def test_get_formatted_test_responses(self):
        result = self.Result.create({
            'workflow_id': self.workflow.id,
            'test_responses': '[{"success": true}]',
        })
        self.assertEqual(result.get_formatted_test_responses(), '[\n  {\n    "success": true\n  }\n]')

        result.test_responses = 'plain response'
        self.assertEqual(result.get_formatted_test_responses(), 'plain response')

        result.test_responses = False
        self.assertEqual(result.get_formatted_test_responses(), 'No test responses available')
