# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Mohammed Dilshad TK (odoo@cybrosys.com)
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
#############################################################################
from odoo import fields, models


class CleaningShift(models.Model):
    """Creating a new model to acquire cleaning shifts for all employees,
    it includes type, start time, and end time details."""
    _name = "cleaning.shift"
    _description = "Cleaning Shift"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'shift_type'

    shift_type = fields.Char(string='Shift Type',
                             help="Shift type for an employee", required=True,
                             readonly=True)
    shift_time_from = fields.Float(string='Shift Time From',
                                   help="Enter the start time for shift",
                                   required=True)
    shift_time_to = fields.Float(string='Shift Time To',
                                 help="Enter the End time for shift",
                                 required=True)
