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


class HrLeaveType(models.Model):
    """This module inherits from the 'hr.leave.type' model of the Odoo Time Off
    Module. It adds a new field called 'leave_code', which is a selection field
    that allows users to choose from a list of predefined leave codes."""
    _inherit = 'hr.leave.type'

    leave_code = fields.Selection(
        [('UL', 'UL'),
         ('SL', 'SL'),
         ('RL', 'RL'),
         ('NL', 'NL'),
         ('ML', 'ML'),
         ('FL', 'FL'),
         ('CL', 'CL'),
         ('PL', 'PL'),
         ('OL', 'OL')],
        required=True,
        string="Leave Code",
        default="NL",
        help="UL = Unpaid Leave\n"
             " SL = Sick Leave\n"
             " RL = Regular Leave\n"
             " NL = Normal Leave\n"
             " ML = Maternity Leave\n"
             " FL = Festival Leave\n"
             " CL = Compensatory Leave\n"
             " PL = Paid Leave\n"
             " OL = Other Leave")
