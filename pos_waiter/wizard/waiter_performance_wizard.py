# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2019-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Sayooj A O(<https://www.cybrosys.com>)
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

from odoo import fields, api, models


class ReportWizard(models.TransientModel):

    """In this class we are defining a new model for
    printing the wizard"""

    _name = 'waiter.performance.wizard'

    report_start_date = fields.Date(string='Start Date', required=True)
    report_end_date = fields.Date(string='End Date', required=True)

    @api.multi
    def print_performance_report(self):

        """In this function we are passing the wizard values
        to the report file"""

        data = {'start_date': self.report_start_date, 'end_date': self.report_end_date}
        res = self.env.ref('pos_waiter.waiter_performance_report').report_action(self, data=data)
        return res
