# -*- coding: utf-8 -*-
#############################################################################
#    A part of Open HRMS Project <https://www.openhrms.com>
#
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


class ResConfigSettings(models.TransientModel):
    """Inherits the resconfig settings for adding new fields"""
    _inherit = 'res.config.settings'

    leave_reminder = fields.Boolean(string='Leave Reminder Email',
                                    config_parameter='hr_vacation_mngmt.leave_reminder',
                                    help="Enable this field send leave "
                                         "remainder emails to hr managers")
    reminder_day_before = fields.Integer(string='Reminder Day Before',
                                         config_parameter='hr_vacation_mngmt.reminder_day_before',
                                         help='Set the day to send  reminder .')
    expense_id = fields.Many2one('account.account',
                                 string='Travel Expense Account',
                                 help='Set the default expense account',
                                 config_parameter='hr_vacation_mngmt.expense_id')
    default_leave_salary = fields.Selection([('0', 'Basic'),
                                             ('1', 'Gross')],
                                            string='Leave Salary',
                                            default_model='hr.leave',
                                            config_parameter='hr_vacation_mngmt.default_leave_salary',
                                            help='Set the default leave salary'
                                                 ' of employee.')
