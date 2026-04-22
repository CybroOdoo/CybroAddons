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
from odoo.exceptions import ValidationError


class ProjectTask(models.Model):
    """
    Extends 'project.task' to allow equipment assignment and enforce that
    equipment is not double-booked on active tasks.
    """
    _inherit = 'project.task'

    equipment_ids = fields.Many2many(
        'maintenance.equipment',
        'project_task_maintenance_equipment_rel',
        'task_id', 'equipment_id',
        string='Equipment',
        domain="[('id', 'in', available_equipment_ids)]",
        context={'default_is_oil_equipment': True},
        help='Oil & gas equipment deployed at this well / task.',
    )
    equipment_count = fields.Integer(
        string='Equipment Count',
        compute='_compute_equipment_count',
        help="Enter the equipment Count."
    )
    available_equipment_ids = fields.Many2many(
        'maintenance.equipment',
        string='Available Equipment',
        compute='_compute_available_equipment_ids',
        help='Oil & gas equipment not currently assigned to any other open/active task.',
    )

    def _compute_equipment_count(self):
        """
        Calculates the total number of unique equipment items linked to all tasks
        in this project.
        """
        for rec in self:
            rec.equipment_count = len(rec.equipment_ids)

    def _compute_available_equipment_ids(self):
        """
        Identifies equipment that is NOT currently assigned to any other open task.
        Used to filter the selection in the UI.
        """
        # Find all equipment IDs that are busy (linked to at least one open task)
        busy_equipment_ids = set(
            self.env['project.task'].sudo().search([
                ('stage_id.is_closed', '=', False),
            ]).filtered(lambda t: t.id not in self.ids).mapped('equipment_ids').ids)

        # All oil equipment
        all_oil_equipment = self.env['maintenance.equipment'].search([
            ('is_oil_equipment', '=', True),
        ])

        available = all_oil_equipment.filtered(
            lambda e: e.id not in busy_equipment_ids
        )

        for rec in self:
            rec.available_equipment_ids = available

    @api.constrains('equipment_ids', 'stage_id')
    def _check_equipment_assignment(self):
        """
        Backend constraint to prevent assigning equipment that is already in use
        on another uncompleted task.
        """
        for task in self:
            if not task.stage_id.is_closed:
                for equipment in task.equipment_ids:
                    active_tasks = equipment.well_site_ids.filtered(
                        lambda t: t.id != task.id and not t.stage_id.is_closed
                    )
                    if active_tasks:
                        raise ValidationError(
                            "Equipment '%s' is already linked to an uncompleted task: '%s'. "
                            "You cannot add it to another task until the previous task is completed."
                            % (equipment.name, active_tasks[0].name)
                        )

    def action_view_equipment(self):
        """
        Returns an action to view all equipment linked to any task in this project.
        """
        self.ensure_one()
        action = self.env['ir.actions.actions']._for_xml_id(
            'oil_erp_equipment.action_oil_equipment')
        action['domain'] = [('well_site_ids', 'in', self.id)]
        action['context'] = dict(
            self.env.context,
            default_is_oil_equipment=True,
        )
        return action
