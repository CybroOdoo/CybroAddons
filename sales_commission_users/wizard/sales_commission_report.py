# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Vishnu K P(odoo@cybrosys.com)
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


class SalesCommissionReport(models.TransientModel):
    """Creating sales commission report model."""
    _name = 'sales.commission.report'
    _description = 'Sales Commission Report'

    sales_person_id = fields.Many2one('res.users', string='Sales Person',
                                      help="Sales person")
    start_date = fields.Date(string='Start Date', help="Start date")
    end_date = fields.Date(string='End Date', help="End date")

    def action_print_report(self):
        """To create a report for sale commission for a sales person"""
        data = {
            'sales_person_id': self.sales_person_id.name,
            'start_date': self.start_date,
            'end_date': self.end_date,
        }
        return self.env.ref(
            'sales_commission_users.sales_commission_report_action'
        ).report_action(self, data=data)
