# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Technologies(<https://www.cybrosys.com>)
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
################################################################################
from odoo import models


class MrpWorkorder(models.Model):
    """Inherited model mrp_workorder to add  functions related to
       manufacturing timesheet.

        Methods:
            button_finish(self):
                Supering the function of done button to calculate total
                time in timesheet.
    """
    _inherit = 'mrp.workorder'

    def button_finish(self):
        """ Supering the function of done button to calculate total time in
                  timesheet.

         Boolean: Returns true
        """
        res = super(MrpWorkorder, self).button_finish()
        for workorder in self:
            project = self.env['project.project'].search(
                [('name', '=', f"MO: {workorder.production_id.name}")],
                limit=1
            )
            if not project:
                project = self.env['project.project'].create({
                    'name': f"MO: {workorder.production_id.name}",
                    'is_manufacturing': True,
                })
            task_name = f"{workorder.name} in {workorder.workcenter_id.name} for " \
                        f"{workorder.product_id.display_name} on {workorder.date_start}"
            task = self.env['project.task'].search(
                [('name', '=', task_name), ('project_id', '=', project.id)],
                limit=1
            )
            if not task:
                task = self.env['project.task'].create({
                    'name': task_name,
                    'project_id': project.id,
                    'date_assign': workorder.date_start,
                    'date_deadline': workorder.date_finished,
                    'allocated_hours': workorder.duration_expected,
                })
            for time_entry in workorder.time_ids:
                self.env['account.analytic.line'].create({
                    'task_id': task.id,
                    'date': time_entry.date_start.date(),
                    'name': f"{workorder.name} in {workorder.workcenter_id.name} for {workorder.product_id.display_name}",
                    'employee_id': time_entry.employee_id.id,
                    'unit_amount': time_entry.duration / 60,
                    'is_manufacturing': True,
                })
        return res
