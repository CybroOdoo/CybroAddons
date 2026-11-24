# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Ranjith R (odoo@cybrosys.com)
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
###############################################################################
from odoo import fields, models


class AccountAnalyticLine(models.Model):
    """Extending account analytic line for project task time tracking."""
    _inherit = 'account.analytic.line'

    date_start = fields.Datetime(string='Start Date',
                                 help="Start date and time for the task.")
    date_end = fields.Datetime(string='End Date', readonly=True,
                               help="End date and time for the task.")
    timer_duration = fields.Float(invisible=1, string='Time Duration (Minutes)',
                                  help="Duration of the timer in minutes.")
    using_timer = fields.Boolean(string='Timer Used',
                                 help="Signifies whether the the timesheet"
                                      " created using timer")
