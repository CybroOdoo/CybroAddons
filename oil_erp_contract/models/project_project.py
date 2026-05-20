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

class ProjectProject(models.Model):
    _inherit = 'project.project'

    contract_count = fields.Integer(string='Contract Count', compute='_compute_contract_count',
                                     help="Total number of oil contracts linked to this project.")

    def _compute_contract_count(self):
        """Count the oil contracts associated with this project."""
        for project in self:
            project.contract_count = self.env['oil.contract'].search_count([('project_id', '=', project.id)])

    def action_view_contracts(self):
        """Open the list of oil contracts linked to this project."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Contracts',
            'view_mode': 'list,form',
            'res_model': 'oil.contract',
            'domain': [('project_id', '=', self.id)],
            'context': {
                'default_project_id': self.id,
                'default_select_type': 'project',
                'default_vendor_id': self.partner_id.id if self.partner_id else False,
            },
        }
