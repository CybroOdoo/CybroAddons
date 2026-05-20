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

from odoo import api, fields, models
from odoo.tools.translate import _
from odoo.exceptions import ValidationError


class OilHseRisk(models.Model):
    """
    Model for recording Health, Safety, and Environment (HSE) risk assessments.
    Supports hazard identification, risk level assessment, and mitigation planning.
    """
    _name = 'oil.hse.risk'
    _description = 'HSE Risk Assessment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(
        string='Risk Title',
        required=True,
        tracking=True,
        help='Short title that identifies the hazard or risk.')
    description = fields.Text(
        string='Description',
        required=True,
        help='Describe the hazard, exposure, and possible consequence.')
    risk_level = fields.Selection(
        [
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High'),
        ],
        string='Risk Level',
        required=True,
        tracking=True,
        help='Overall assessed level of the risk.')
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True,
        help="Company responsible for this risk assessment.")
    mitigation_plan = fields.Text(
        string='Mitigation Plan',
        help='Controls or actions planned to reduce the risk.')

    project_id = fields.Many2one(
        'project.project',
        string='Project',
        domain=[('is_oil_gas_project', '=', True)],
        help='Project where the risk applies.')
    task_id = fields.Many2one(
        'project.task',
        string='Well / Task',
        domain=[('project_id.is_oil_gas_project', '=', True)],
        help='Specific well or task where the risk applies.')

    @api.constrains('project_id', 'task_id')
    def _check_task_project(self):
        """
        Ensures that the selected well/task belongs to the assigned project.
        """
        for rec in self:
            if rec.project_id and rec.task_id and rec.task_id.project_id != rec.project_id:
                raise ValidationError(
                    _('Selected well/task must belong to the chosen project.'))

    @api.constrains('risk_level', 'mitigation_plan')
    def _check_high_risk_mitigation(self):
        """
        Validates that a mitigation plan is provided for high-risk assessments.
        """
        for rec in self:
            if rec.risk_level == 'high' and not rec.mitigation_plan:
                raise ValidationError(
                    _('Mitigation plan is required for high-risk assessments.'))
