# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gayathri V(<https://www.cybrosys.com>)
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


class DealerSalesReport(models.TransientModel):
    """Transient model for a wizard to generate sales report."""
    _name = 'dealer.sale.report'
    _description = 'Dealer Sale Report'

    from_date = fields.Date(string='From Date',
                            help='Date on which report taken')
    to_date = fields.Date(string='To Date', help='Date to which report taken')
    type = fields.Selection(string='Report Type', help='Report Type',
                            selection=[('agreement_based', 'Agreement Based'),
                                       ('dealer_based', 'Dealer Based')])
    dealer_id = fields.Many2one('franchise.dealer',
                                string='Franchise Dealer',
                                help='Franchise dealer record')
    agreement_id = fields.Many2one('franchise.agreement',
                                   string='Franchise Agreement',
                                   help='Franchise Agreement record')

    def create_report(self):
        """Method to generate the Dealer Sales Report"""
        query = """ select dealer_sale.dealer_id,
                franchise_dealer.dealer_name,
                franchise_agreement.agreement_type,
                dealer_sale.dealer_agreement_id,
                dealer_sale.scrap_quantity, 
                dealer_sale.total_sale_amount,
                dealer_sale.sale_quantity,
                dealer_sale.monthly_target_gained,
                dealer_sale.dealership_signed_on,
                dealer_sale.monthly_target_amount from dealer_sale
                inner join franchise_dealer on franchise_dealer.id = 
                dealer_sale.dealer_id inner join franchise_agreement on 
                franchise_agreement.id = dealer_sale.dealer_agreement_id"""
        if self.from_date:
            query += """ where dealer_sale.create_date >= '%s'""" % \
                     self.from_date
        if self.to_date:
            query += """ and dealer_sale.create_date <= '%s'""" % \
                     self.to_date
        if self.dealer_id:
            query += """ and franchise_dealer.id = %d""" % self.dealer_id
            self.env.cr.execute(query)

            fetch_dealer_details = self.env.cr.dictfetchall()
            data = {
                'form_data': self.read()[0],
                'fetch_dealer_details': fetch_dealer_details
            }
            return self.env.ref(
                'franchise_management.action_dealer_sale_on_dealer_report_pdf'
            ).report_action(self, data=data)
        if self.agreement_id:
            query += """ and dealer_agreement_id = %d""" % self.agreement_id
            self.env.cr.execute(query)
            fetch_agreement_details = self.env.cr.dictfetchall()
            data = {
                'form_data': self.read()[0],
                'fetch_agreement_details': fetch_agreement_details
            }
            return self.env.ref(
                'franchise_management.'
                'action_dealer_sale_on_agreement_report_pdf').report_action(
                self, data=data)
        self.env.cr.execute(query)
        fetch_all_details = self.env.cr.dictfetchall()
        data = {
            'form_data': self.read()[0],
            'fetch_all_details': fetch_all_details
        }
        return self.env.ref(
            'franchise_management.action_dealer_sale_based_report_pdf') \
            .report_action(self, data=data)
