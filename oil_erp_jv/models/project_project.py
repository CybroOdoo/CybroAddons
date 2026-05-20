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
from odoo.tools.translate import _


class ProjectProject(models.Model):
    """Extends project.project to show linked JV Agreements."""
    _inherit = 'project.project'

    jv_agreement_ids = fields.One2many(
        'oil.jv.agreement',
        'project_id',
        string='JV Agreements',
        help="Joint Operating Agreements linked to this project.")
    jv_agreement_count = fields.Integer(
        string='JV Agreements',
        compute='_compute_jv_agreement_count',
        help="Number of JV agreements for this project.")

    def _compute_jv_agreement_count(self):
        """Count the JV agreements linked to this project."""
        for project in self:
            project.jv_agreement_count = self.env[
                'oil.jv.agreement'].search_count(
                [('project_id', '=', project.id)])

    def action_view_jv_agreements(self):
        """Open the list of JV agreements for this project."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('JV Agreements'),
            'res_model': 'oil.jv.agreement',
            'view_mode': 'list,form',
            'domain': [('project_id', '=', self.id)],
            'context': {'default_project_id': self.id},
        }
