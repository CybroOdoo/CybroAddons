# -*- coding: utf-8 -*-
#############################################################################
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


from odoo import fields, models
from datetime import timedelta
from odoo.tools.translate import _


class ProjectTask(models.Model):
    """
    Extends 'project.task' to include HSE tracking at the well/task level,
    including hydrogen sulfide (H2S) presence, HSE risk classification,
    emergency planning, and work permit workflow integration.
    """
    _inherit = 'project.task'

    # ── HSE-Specific fields ──
    h2s_present = fields.Boolean(
        string='H\u2082S Present',
        help='Indicates the presence of hydrogen sulfide — critical HSE hazard.')
    hse_classification = fields.Selection(
        [
            ('low_risk', 'Low Risk'),
            ('medium_risk', 'Medium Risk'),
            ('high_risk', 'High Risk'),
        ],
        string='HSE Classification',
        tracking=True,
        help='Overall HSE risk classification for this well / task.')
    emergency_contact_id = fields.Many2one(
        'res.partner',
        string='Emergency Contact',
        help='On-site emergency contact person.')
    nearest_hospital = fields.Char(
        string='Nearest Hospital',
        help='Hospital name and approximate distance from the site.')
    muster_point = fields.Char(
        string='Muster Point',
        help='Emergency assembly point description.')
    prev_stage_id = fields.Many2one(
        'project.task.type',
        string='Previous Stage',
        copy=False,
        help="Stage the task was in before entering the permit waiting stage.")
    requested_stage_id = fields.Many2one(
        'project.task.type',
        string='Requested Stage',
        copy=False,
        help="Target stage that requires a work permit before the task can proceed.")

    hse_incident_count = fields.Integer(
        string='Incidents',
        compute='_compute_hse_counts',
        help="Total HSE incidents linked to this task.")
    hse_inspection_count = fields.Integer(
        string='Inspections',
        compute='_compute_hse_counts',
        help="Total HSE inspections linked to this task.")
    hse_permit_count = fields.Integer(
        string='Work Permits',
        compute='_compute_hse_counts',
        help="Total work permits linked to this task.")
    hse_risk_count = fields.Integer(
        string='Risk Assessments',
        compute='_compute_hse_counts',
        help="Total risk assessments linked to this task.")
    is_waiting_stage = fields.Boolean(
        compute="_compute_is_waiting_stage",
        store=False,
        help="Indicates whether this task is currently in a permit waiting stage.")

    def _compute_is_waiting_stage(self):
        """
        Determines if the task is currently in a 'Waiting' stage.
        """
        for rec in self:
            rec.is_waiting_stage = bool(rec.stage_id and rec.stage_id.is_waiting_stage)

    def _compute_hse_counts(self):
        """
        Computes the count of HSE records (incidents, inspections, permits, risks)
        directly linked to this specific task.
        """
        incident_model = self.env['oil.hse.incident']
        inspection_model = self.env['oil.hse.inspection']
        permit_model = self.env['oil.hse.permit']
        risk_model = self.env['oil.hse.risk']
        for rec in self:
            task_domain = [('task_id', '=', rec.id)]
            rec.hse_incident_count = incident_model.search_count(task_domain)
            rec.hse_inspection_count = inspection_model.search_count(task_domain)
            rec.hse_permit_count = permit_model.search_count(task_domain)
            rec.hse_risk_count = risk_model.search_count(task_domain)

    def _get_hse_action(self, xmlid):
        """
        Helper method to return an action for viewing specific HSE records
        filtered for the current task.
        """
        self.ensure_one()
        action = self.env.ref(xmlid).read()[0]
        action['domain'] = [('task_id', '=', self.id)]
        action['context'] = dict(
            self.env.context,
            default_task_id=self.id,
            default_project_id=self.project_id.id,
        )
        return action

    def action_view_hse_incidents(self):
        """Open HSE incidents linked to this task."""
        return self._get_hse_action('oil_erp_hse.action_oil_hse_incident')

    def action_view_hse_inspections(self):
        """Open HSE inspections linked to this task."""
        return self._get_hse_action('oil_erp_hse.action_oil_hse_inspection')

    def action_view_hse_permits(self):
        """Open work permits linked to this task."""
        return self._get_hse_action('oil_erp_hse.action_oil_hse_permit')

    def action_view_hse_risks(self):
        """Open HSE risks linked to this task."""
        return self._get_hse_action('oil_erp_hse.action_oil_hse_risk')

    def action_report_incident(self) -> dict:
        """Open a blank oil.hse.incident form pre-linked to this well/task."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Report Incident'),
            'res_model': 'oil.hse.incident',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_task_id': self.id,
                'default_project_id': self.project_id.id,
                'default_company_id': self.company_id.id,
            },
        }

    def write(self, vals):
        """Route stage changes through the waiting stage when permits are required."""
        if self.env.context.get('skip_work_permit_stage_check'):
            return super(ProjectTask, self).write(vals)

        if 'stage_id' in vals:
            new_stage = self.env['project.task.type'].browse(vals['stage_id'])
            waiting_stage = self.env['project.task.type'].search(
                [('is_waiting_stage', '=', True)], limit=1
            )

            if not waiting_stage:
                return super(ProjectTask, self).write(vals)

            if new_stage.is_work_permit_required:
                for rec in self:
                    if rec.stage_id != waiting_stage:
                        super(ProjectTask, rec).write({
                            'prev_stage_id': rec.stage_id.id,
                            'requested_stage_id': new_stage.id,
                            'stage_id': waiting_stage.id,
                        })
                return True

        return super(ProjectTask, self).write(vals)

    def action_create_permit(self):
        """Open a new work permit form for the current task."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Create Work Permit'),
            'res_model': 'oil.hse.permit',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_task_id': self.id,
                'default_project_id': self.project_id.id,
                'default_from_stage_id': self.prev_stage_id.id,
                'default_to_stage_id': self.requested_stage_id.id,
                'default_start_date': fields.Datetime.now(),
                'default_end_date': fields.Datetime.now() + timedelta(days=1),
                'default_permit_type': 'cold_work',
            },
        }
