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
    """
    Extends 'project.project' to provide visibility into equipment deployed across
    all tasks within the project.
    """
    _inherit = 'project.project'

    equipment_count = fields.Integer(
        string='Equipment Count',
        compute='_compute_equipment_count',
        help="Enter the equipment Count."
    )

    def _compute_equipment_count(self):
        """
        Calculates the total number of unique equipment items linked to all tasks
        in this project.
        """
        for rec in self:
            equipment = self.env['project.task'].search([
                ('project_id', '=', rec.id),
            ]).mapped('equipment_ids')
            rec.equipment_count = len(equipment)

    def action_view_equipment(self):
        """
        Returns an action to view all equipment linked to any task in this project.
        """
        self.ensure_one()
        action = self.env['ir.actions.actions']._for_xml_id(
            'oil_erp_equipment.action_oil_equipment')
        action['domain'] = [('well_site_ids.project_id', '=', self.id)]
        action['context'] = dict(
            self.env.context,
            default_is_oil_equipment=True,
        )
        return action
