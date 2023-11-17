# -*- coding: utf-8 -*-
###############################################################################
#
#  Cybrosys Technologies Pvt. Ltd.
#
#  Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#  Author: Anusha C (odoo@cybrosys.com)
#
#  You can modify it under the terms of the GNU LESSER
#  GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#  You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#  (LGPL v3) along with this program.
#  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import fields, models


class OverlappingDate(models.TransientModel):
    """This transient model is to display as a warning in the model
    hr_holiday_generator"""
    _name = 'overlapping.date'
    _description = 'Wizard to Display Warning'

    warning = fields.Text(string='Warning', readonly=True,
                          help="For showing the warning messages.")

    def action_continue(self):
        """Function for redirecting into calendar leave generator wizard"""
        generator = self.env['hr.holiday.generator'].browse(
            self.env.context.get('active_id'))
        calendar_leaves = self.env['calendar.leave'].search([
            ('holiday_generator_id', '=', generator.id)])
        existing_public_holidays = self.env['resource.calendar.leaves'].search([
            ('resource_id', '=', False)])
        filtered_calendar_leaves = calendar_leaves.filtered(
            lambda cl: cl.start_date.date() not in [holiday.date_from.date() for
                                                    holiday in
                                                    existing_public_holidays])
        if 'active_calendar_leave_ids' in self.env.context:
            filtered_calendar_leaves_ids = self.env.context[
                'active_calendar_leave_ids']
            return {
                'type': 'ir.actions.act_window',
                'name': 'Calendar Leaves',
                'res_model': 'calendar.leave.generator',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'default_calendar_leave_ids': filtered_calendar_leaves_ids}
            }
        elif filtered_calendar_leaves:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Calendar Leaves',
                'res_model': 'calendar.leave.generator',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'default_calendar_leave_ids': filtered_calendar_leaves.ids}
            }
