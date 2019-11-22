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

# -*- coding: utf-8 -*-
from odoo import models, api


class AllInOneAccountReport(models.TransientModel):

    """In this class the values are fetched from the wizard
    and the required values from the database and passed to
    the report template"""

    _name = "report.pos_waiter.performance_analysis"

    @api.model
    def _get_report_values(self, docids, data=None):
        start_date = data['start_date']
        end_date = data['end_date']
        query = """select sum(po.amount_total) as total_amount,po.date_order::date as order_date,
                he.name as waiter_name
                from pos_order po
                join hr_employee he
                on he.id = po.employee_id
                where po.date_order::date >= '%s' AND po.date_order::date <= '%s'
                group by he.name,po.date_order::date
                order by po.date_order::date """ % (start_date, end_date)
        self._cr.execute(query)
        performance_details = self._cr.dictfetchall()
        return {
            'start_date': start_date,
            'end_date': end_date,
            'performance_details': performance_details
        }
