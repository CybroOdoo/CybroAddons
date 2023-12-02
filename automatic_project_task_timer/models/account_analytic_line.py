# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Prathyunnan R(odoo@cybrosys.com)
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
    """inherited the 'account.analytic.line' for showing the time records."""
    _inherit = 'account.analytic.line'

    date_start = fields.Datetime(string='Start Date', help='Shows the '
                                                           'starting time of '
                                                           'the timer')
    date_end = fields.Datetime(string='End Date', readonly=1, help='Shows '
                                                                   'the ending'
                                                                   ' time of '
                                                                   'the timer')
    timer_duration = fields.Float(invisible=1, string='Time Duration(Minutes)',
                                  help='Shows the real time ')
