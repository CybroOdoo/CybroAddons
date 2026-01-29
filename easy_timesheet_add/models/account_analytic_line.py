# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Mruthul Raj (odoo@cybrosys.com)
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
from odoo import fields, models


class AccountAnalyticLine(models.Model):
    """Inherits account_analytic_line to store timesheet adding via systray"""
    _inherit = 'account.analytic.line'

    start_time = fields.Datetime(string="Start Time",
                                 help="To store start time of timesheet")
    end_time = fields.Datetime(string="End Time",
                               help="To store end time of timesheet")
    current_state = fields.Selection([('play', 'play'), ('pause', 'pause')],
                                     string="Current State",
                                     help="To manage the timesheet adding via "
                                          "systray")
    pausing_time = fields.Char(help="To store time on pausing",
                               string="Pause Time")
    is_current = fields.Boolean(help="Check is timesheet completed or not",
                                string="Timesheet Completion")
