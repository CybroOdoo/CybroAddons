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


class OilReservoir(models.Model):
    """Extends oil.reservoir to show linked JV Agreements via the
    reservoir's auto-created project."""
    _inherit = 'oil.reservoir'

    jv_agreement_count = fields.Integer(
        string='JV Agreements',
        compute='_compute_jv_agreement_count',
        help="Number of JV agreements linked to this reservoir's project.")

    def _compute_jv_agreement_count(self):
        """Count the JV agreements linked to this reservoir project."""
        for reservoir in self:
            if reservoir.project_id:
                reservoir.jv_agreement_count = self.env[
                    'oil.jv.agreement'].search_count(
                    [('project_id', '=', reservoir.project_id.id)])
            else:
                reservoir.jv_agreement_count = 0

    def action_view_jv_agreements(self):
        """Open the list of JV agreements linked to this reservoir project."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('JV Agreements'),
            'res_model': 'oil.jv.agreement',
            'view_mode': 'list,form',
            'domain': [('project_id', '=', self.project_id.id)],
            'context': {'default_project_id': self.project_id.id},
        }
