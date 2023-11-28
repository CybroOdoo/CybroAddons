# -- coding: utf-8 --
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """This class extends the `res.config.settings` model to add configuration
     settings for the HR Attendance Dashboard's default present and absent
      marks.  """
    _inherit = 'res.config.settings'

    present = fields.Selection([('present', 'Present'),
                                ('\u2714', '✔'), ('\u2705', '✅ '), ('p', 'P')],
                               string='Default Present Mark',
                               config_parameter='advance_hr_attendance_'
                                                'dashboard.present',
                               help='Select the default mark for present '
                                    'attendance.')
    absent = fields.Selection([('absent', 'Absent'),
                               ('\u2716', '✘'), ('\u274C', '❌'),
                               ('\u2B55', '⭕'), ('a', 'A')
                               ], string='Default Absent Mark',
                              config_parameter='advance_hr_attendance_'
                                               'dashboard.absent',
                              help='Select the default mark for absent '
                                   'attendance.')
