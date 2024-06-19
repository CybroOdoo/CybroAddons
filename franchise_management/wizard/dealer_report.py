# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Jumana Jabin MK(<https://www.cybrosys.com>)
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
"""Franchise Dealer Report Wizard"""
from odoo import fields, models


class DealerReport(models.TransientModel):
    """Transient Model to Generate Dealer Report."""
    _name = 'dealer.report'
    _description = 'Dealer Report Wizard'

    from_date = fields.Date(string='From Date', help='From Date')
    to_date = fields.Date(string='To Date', help='To Date')
    type = fields.Selection(string='Report Type', help='Report Type',
                            selection=[('agreement_based', 'Agreement Based'),
                                       ('dealer_based', 'Dealer Based')])
    dealer_id = fields.Many2one('res.users',
                                string='Franchise Dealer',
                                help='Franchise Dealer',
                                domain="[('is_dealer_user', '=', True)]")
    agreement_id = fields.Many2one('franchise.agreement',
                                   string='Franchise Agreement',
                                   help='Franchise Agreement')

    def create_report(self):
        """Method to create report after fetching the values using query"""
        query = """ select franchise_dealer.id,
            franchise_dealer.serial_no, franchise_dealer.dealer_name,
            res_partner.id, res_partner.name, franchise_dealer.dealer_mail, 
            franchise_dealer.business_city, franchise_dealer.investment_from, 
            franchise_dealer.investment_to, franchise_dealer.signed_on, 
            franchise_dealer.contract_type_id,
            franchise_agreement.agreement_type from franchise_dealer
            inner join res_users on res_users.id =
            franchise_dealer.dealer_portal_user inner join res_partner on 
            res_partner.id = res_users.partner_id
            inner join franchise_agreement on franchise_agreement.id =
            franchise_dealer.contract_type_id """

        if self.from_date:
            query += """ where franchise_dealer.create_date >= '%s'""" %\
                     self.from_date
        if self.to_date:
            query += """ and franchise_dealer.create_date <= '%s'""" % \
                     self.to_date
        if self.dealer_id:
            query += """ and res_users.id = %d""" % self.dealer_id
            self.env.cr.execute(query)
            fetch_dealer_details = self.env.cr.dictfetchall()
            data = {
                'form_data': self.read()[0],
                'fetch_dealer_details': fetch_dealer_details
            }
            return self.env.ref(
                'franchise_management.action_dealer_based_report_pdf')\
                .report_action(self, data=data)
        if self.agreement_id:
            query += """ and contract_type_id = %d""" % self.agreement_id
            self.env.cr.execute(query)

            fetch_agreement_details = self.env.cr.dictfetchall()
            data = {
                'form_data': self.read()[0],
                'fetch_agreement_details': fetch_agreement_details
            }
            return self.env.ref(
                'franchise_management.action_agreement_based_report_pdf')\
                .report_action(self, data=data)
        self.env.cr.execute(query)
        fetch_all_details = self.env.cr.dictfetchall()
        data = {
            'form_data': self.read()[0],
            'fetch_all_details': fetch_all_details
        }
        return self.env.ref(
            'franchise_management.franchise_dealer_details_report_action')\
            .report_action(self, data=data)
