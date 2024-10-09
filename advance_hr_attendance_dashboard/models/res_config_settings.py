# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gayathri V(odoo@cybrosys.com)
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
