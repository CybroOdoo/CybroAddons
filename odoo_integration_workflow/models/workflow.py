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
from odoo import models, fields, api
import logging
import json
import time

_logger = logging.getLogger(__name__)


class APIWorkflow(models.Model):
    _name = 'api.workflow'
    _inherit = ['api.workflow.testing']
    _description = 'API Workflow'

    # ======================================================
    # 1. BASIC FIELDS
    # ======================================================
    name = fields.Char(string='Workflow Name', required=True,help="Workflow Name")
    description = fields.Text(string='Description',help="Description")
    workflow_data = fields.Text(string='Workflow Data',help="Workflow Data")
    active = fields.Boolean(string='Active', default=True,help="Active")
    created_date = fields.Datetime(string='Created Date', default=fields.Datetime.now,help="Created Date")

    # Trigger Status (For List View visibility)
    trigger_type = fields.Selection([
        ('manual', 'Manual'),
        ('cron', 'Scheduled'),
        ('model', 'Record Event')
    ], string="Trigger Type", default='manual')

    # Links to background records
    cron_id = fields.Many2one('ir.cron', string="Cron Job", ondelete='set null')
    automation_id = fields.Many2one('base.automation', string="Automated Action", ondelete='set null')


    test_result_ids = fields.One2many('api.workflow.test.result', 'workflow_id', string='History')
    last_test_result = fields.Many2one('api.workflow.test.result', string='Last Result',
                                       compute='_compute_last_test_result')

    def _compute_last_test_result(self):
        for record in self:
            record.last_test_result = record.test_result_ids[:1]

    @api.model
    def get_existing_models(self):
        """ Used by Frontend to populate Model Selector """
        try:
            models = self.env['ir.model'].sudo().search_read(
                [('transient', '=', False)],
                ['model', 'name'],
                limit=5000,
                order='model asc'
            )
            return models
        except Exception as e:
            return []

    @api.model
    def get_model_fields(self, model_name):
        """ Used by Frontend to populate Field Selectors """
        if not model_name or model_name not in self.env: return []
        fields_data = self.env[model_name].fields_get(attributes=['string', 'type', 'readonly'])
        # Return list sorted by name
        return sorted([
            {'name': k, 'string': v['string'], 'type': v['type']}
            for k, v in fields_data.items()
        ], key=lambda x: x['name'])

    def open_workflow_builder(self):
        self.ensure_one()

        params = {
            'workflow_id': self.id,
            'workflow_name': self.name,
        }

        if self.workflow_data:
            try:
                parsed = json.loads(self.workflow_data)
                if parsed and isinstance(parsed, dict):
                    params['workflow_data'] = parsed
            except (json.JSONDecodeError, TypeError) as e:
                _logger.error(f"🔧 JSON parse error: {e}")

        return {
            'type': 'ir.actions.client',
            'tag': 'workflow_builder',
            'name': f'Workflow Builder - {self.name}',
            'params': params,
        }

    def action_view_test_history(self):
        """ Fixes 'action_view_test_history not valid' error """
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Test History - {self.name}',
            'res_model': 'api.workflow.test.result',
            'view_mode': 'tree,form',
            'domain': [('workflow_id', '=', self.id)],
        }

    def run_workflow_from_record(self):
        """ Execute workflow with real database writes """
        self.ensure_one()

        import json
        try:
            data = json.loads(self.workflow_data) if self.workflow_data else {}

            exec_payload = {
                'nodes': data.get('nodes', []),
                'connections': data.get('connections', []),
                'initial_data': {},
                'dry_run': False,
                'workflowId': self.id
            }

            res = self.test_workflow(exec_payload)

        except Exception as e:
            _logger.error(f"Workflow execution error: {e}")
            res = {'success': False, 'message': str(e)}

        msg_type = 'success' if res and res.get('success') else 'danger'
        msg = res.get('message', 'Execution Finished') if res else 'Execution Failed'

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Workflow Execution',
                'message': msg,
                'type': msg_type,
                'sticky': False,
            }
        }

    # ======================================================
    # 5. SAVE LOGIC (Handles saving JSON & syncing Automation)
    # ======================================================
    @api.model
    def save_or_update_workflow(self, vals):
        """ Main Save Entry Point """

        record_id = vals.get('id')
        if record_id:
            record = self.browse(record_id)
            record.write(vals)
        else:
            record = self.create(vals)


        if 'workflow_data' in vals:
            try:
                import json
                data = json.loads(vals['workflow_data'])
                nodes_list = data.get('nodes', [])

                auto_node = next((n for n in nodes_list if n.get('type') == 'automation'), None)

                if auto_node:

                    t_type = auto_node.get('config', {}).get('trigger_type', 'manual')
                    record.write({'trigger_type': t_type})

                    record._sync_odoo_cron(auto_node)
                    record._sync_odoo_automation(auto_node)
                else:
                    record.write({'trigger_type': 'manual'})

            except Exception as e:
                import traceback
                traceback.print_exc()

        return record.id

    # ======================================================
    # 6. TRIGGER SYNCHRONIZATION (Cron & Automation)
    # ======================================================
    def _sync_odoo_cron(self, auto_node):
        """
        Creates/Updates an ir.cron record based on Automation Node settings.
        Args: auto_node (dict): The specific JSON configuration object for the automation node.
        """
        cron_name = f"Workflow Cron: {self.name} ({self.id})"
        existing_cron = self.env['ir.cron'].search([('name', '=', cron_name)], limit=1)

        config = auto_node.get('config', {}) if auto_node else {}
        trigger_type = config.get('trigger_type')

        if trigger_type != 'cron':
            if existing_cron:
                existing_cron.active = False
                self.cron_id = False
            return

        try:
            interval_num = int(config.get('interval_number', 1))
            interval_type = config.get('interval_type', 'hours')
            is_active = config.get('cron_active', False)
        except:
            interval_num = 1
            interval_type = 'hours'
            is_active = False

        python_code = f"env['api.workflow'].browse({self.id}).execute_workflow(initial_context={{'trigger_source': 'cron'}})"

        vals = {
            'name': cron_name,
            'model_id': self.env['ir.model'].search([('model', '=', 'api.workflow')], limit=1).id,
            'state': 'code',
            'code': python_code,
            'interval_number': interval_num,
            'interval_type': interval_type,
            'active': is_active
        }

        if existing_cron:
            existing_cron.write(vals)
            self.cron_id = existing_cron.id
        else:
            new_cron = self.env['ir.cron'].create(vals)
            self.cron_id = new_cron.id

    def _sync_odoo_automation(self, auto_node):

        config = auto_node.get('config', {}) if auto_node else {}
        trigger_type = config.get('trigger_type')

        automation_name = f"Workflow Hook: {self.name} ({self.id})"
        existing_auto = self.env['base.automation'].search([('name', '=', automation_name)], limit=1)
        if trigger_type != 'model':
            if existing_auto:
                existing_auto.active = False
                self.automation_id = False
            return

        target_model = config.get('trigger_model')
        trigger_event = config.get('trigger_on') or 'on_create'

        if not target_model: return

        model_ref = self.env['ir.model'].search([('model', '=', target_model)], limit=1)
        if not model_ref:
            return

        import textwrap
        code_to_execute = textwrap.dedent(f"""
            # Triggered by Workflow Builder
            action = env['api.workflow'].browse({self.id})
            action.execute_workflow(initial_context={{'record': record, 'trigger_source': 'automation'}})
        """)

        # 4. SERVER ACTION
        action_name = f"Action: {automation_name}"
        server_action = self.env['ir.actions.server'].search([('name', '=', action_name)], limit=1)

        action_vals = {
            'name': action_name,
            'model_id': model_ref.id,
            'state': 'code',
            'code': code_to_execute,
        }

        if server_action:
            server_action.write(action_vals)
        else:
            server_action = self.env['ir.actions.server'].create(action_vals)

        auto_vals = {
            'name': automation_name,
            'model_id': model_ref.id,
            'trigger': trigger_event,
            'active': True,
            'action_server_ids': [(6, 0, [server_action.id])]
        }

        if existing_auto:
            existing_auto.write(auto_vals)
            self.automation_id = existing_auto.id
        else:
            new_auto = self.env['base.automation'].create(auto_vals)
            self.automation_id = new_auto.id


    # ======================================================
    # 7. EXECUTION ENGINE (Server Side)
    # ======================================================
    def execute_workflow(self, initial_context=None):
        """ Called by Cron or Automation. """
        if not self.workflow_data:
            return

        import json
        try:
            data = json.loads(self.workflow_data)

            exec_payload = {
                'nodes': data.get('nodes', []),
                'connections': data.get('connections', []),
                'initial_data': {},
                'dry_run': False,
                'workflowId': self.id
            }

            # Handle Event Trigger Data
            if initial_context and 'record' in initial_context:
                record = initial_context['record']
                try:
                    read_data = record.read([], load=False)
                    if read_data:
                        exec_payload['initial_data'] = {
                            'trigger': {
                                'id': record.id,
                                'name': record.display_name,
                                'data': read_data[0]
                            }
                        }
                except Exception as e:
                    return

            res = self.test_workflow(exec_payload)
            return res

        except Exception as e:
            import traceback
            traceback.print_exc()
            return {'success': False, 'message': str(e)}

    def run_automated_workflow(self, initial_data=None):
        return self.execute_workflow()

    # ======================================================
    # 8. FRONTEND TEST WRAPPER (Handling Dry Run)
    # ======================================================
    @api.model
    def test_workflow(self, workflow_data):
        dry_run = workflow_data.get('dry_run', False)
        start_time = time.time()

        if dry_run:
            self.env.cr.execute('SAVEPOINT workflow_dry_run')
            try:
                res = super(APIWorkflow, self).test_workflow(workflow_data)
            finally:
                self.env.cr.execute('ROLLBACK TO SAVEPOINT workflow_dry_run')
            res['message'] += " (Dry Run)"
            return res
        else:
            res = super(APIWorkflow, self).test_workflow(workflow_data)
            self._create_history_log(workflow_data, res, start_time)
            return res

    def _create_history_log(self, input_data, result, start_time):
        """ Helper to create history logs """
        w_id = input_data.get('workflowId') or self.id
        if not w_id: return

        try:
            node_results = result.get('results', [])
            success_count = len([n for n in node_results if n.get('success')])

            self.env['api.workflow.test.result'].create({
                'workflow_id': int(w_id),
                'test_date': fields.Datetime.now(),
                'success': result.get('success', False),
                'total_nodes': len(node_results),
                'successful_nodes': success_count,
                'failed_nodes': len(node_results) - success_count,
                'total_response_time': round(time.time() - start_time, 3),
                'node_structure': json.dumps(input_data),
                'test_responses': json.dumps(node_results)
            })
        except Exception as e:
            _logger.error(f"Failed to create history log: {e}")
