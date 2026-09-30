# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions @cybrosys(odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import fields, models
import json
import logging

_logger = logging.getLogger(__name__)
class WorkflowTestResult(models.Model):
    _name = 'api.workflow.test.result'
    _description = 'API Workflow Test Results'
    _order = 'test_date desc'

    workflow_id = fields.Many2one('api.workflow', string='Workflow', required=True, ondelete='cascade',help="Workflow id")
    test_date = fields.Datetime(string='Test Date', default=fields.Datetime.now,help="Test Date")
    success = fields.Boolean(string='Success',help="Whether or not the test was successful")
    total_nodes = fields.Integer(string='Total Nodes',help="Total Nodes")
    successful_nodes = fields.Integer(string='Successful Nodes',help="Successful Nodes")
    failed_nodes = fields.Integer(string='Failed Nodes',help="Failed Nodes")
    total_response_time = fields.Float(string='Total Response Time (s)',help="Total Response Time (s)")
    node_structure = fields.Text(string='Node Structure',help="Node Structure")
    test_responses = fields.Text(string='Test Responses',help="Test Responses")
    error_message = fields.Text(string='Error Message',help="Error Message")
    success_rate = fields.Float(string='Success Rate', compute='_compute_success_rate',help="Success Rate")

    def _compute_success_rate(self):
        for record in self:
            if record.total_nodes > 0:
                record.success_rate = (record.successful_nodes / record.total_nodes) * 100
            else:
                record.success_rate = 0.0

    def action_open_node_structure(self):
        """Open a popup window to view node structure"""
        self.ensure_one()
        return {
            'type': 'ir.actions.client',
            'tag': 'workflow_builder',
            'name': f'Workflow Builder - {self.workflow_id.name}',
            'params': {

                'workflow_id': self.workflow_id.name,
                'workflow_data': json.loads(self.node_structure) if self.node_structure else {},
                'workflow_name': self.workflow_id.name,
            },
        }


    def get_formatted_node_structure(self):
        """Return formatted node structure for display"""
        self.ensure_one()
        if self.node_structure:
            try:
                data = json.loads(self.node_structure)
                return json.dumps(data, indent=2)
            except json.JSONDecodeError:
                return self.node_structure
        return "No node structure available"

    def get_formatted_test_responses(self):
        """Return formatted test responses for display"""
        self.ensure_one()
        if self.test_responses:
            try:
                data = json.loads(self.test_responses)
                return json.dumps(data, indent=2)
            except json.JSONDecodeError:
                return self.test_responses
        return "No test responses available"