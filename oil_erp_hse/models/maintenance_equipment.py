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

from odoo import models


class MaintenanceEquipment(models.Model):
    """Extends equipment with HSE inspection actions."""
    _inherit = 'maintenance.equipment'

    def action_create_inspection(self):
        """Create or open a draft HSE inspection for this equipment."""
        self.ensure_one()
        task_id = False
        project_id = False

        # Check if an active inspection already exists for this equipment
        existing_inspection = self.env['oil.hse.inspection'].search([
            ('equipment_id', '=', self.id),
            ('inspection_type', '=', 'equipment'),
            ('state', '=', 'draft'),
        ], limit=1)

        if existing_inspection:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Inspection Already Exists',
                    'message': f'An active inspection already exists for this equipment (Ref: {existing_inspection.name}).',
                    'type': 'warning',
                    'sticky': False,
                },
            }

        if self._context.get('active_model') == 'project.task':
            task = self.env['project.task'].browse(
                self._context.get('active_id'))
            if task.exists():
                task_id = task.id
                project_id = task.project_id.id

        if not task_id and hasattr(self, 'well_site_ids') and self.well_site_ids:
            active_tasks = self.well_site_ids.filtered(
                lambda t: not t.stage_id.is_closed)
            if active_tasks:
                task_id = active_tasks[0].id
                project_id = active_tasks[0].project_id.id

        inspection = self.env['oil.hse.inspection'].create({
            'equipment_id': self.id,
            'task_id': task_id,
            'project_id': project_id,
            'inspection_type': 'equipment',
            'state': 'draft',
        })

        return {
            'name': 'Inspection',
            'type': 'ir.actions.act_window',
            'res_model': 'oil.hse.inspection',
            'res_id': inspection.id,
            'view_mode': 'form',
            'target': 'current',
        }
