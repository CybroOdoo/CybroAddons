# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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


class PropertySaleReport(models.TransientModel):
    """A class for the transient model property.sale.report"""
    _name = 'property.sale.report'
    _description = 'Property Sale Report'

    from_date = fields.Date(string="From Date",
                            help='Records from the date will be selected')
    to_date = fields.Date(string="To Date",
                          help='Records till the date will be selected')
    property_id = fields.Many2one('property.property', string="Property Name",
                                  help='The property will be selected')
    partner_id = fields.Many2one('res.partner', string="Customer",
                                 help='The Customer will be selected')

    def action_create_report(self):
        """The function fetches records based on the wizard's criteria
        and returns a PDF report."""
        domain = []
        if self.partner_id:
            domain.append(('partner_id', '=', self.partner_id.id))
        if self.property_id:
            domain.append(('property_id', '=', self.property_id.id))
        if self.from_date:
            domain.append(('create_date', '>=', self.from_date))
        if self.to_date:
            domain.append(('create_date', '<=', self.to_date))

        sales = self.env['property.sale'].search(domain)
        datas = []
        for sale in sales:
            datas.append({
                'customer': sale.partner_id.name,
                'name': sale.property_id.name,
                'create_date': sale.create_date,
                'state': sale.state,
            })

        data = {
            'datas': datas,
            'to_date': self.to_date,
            'from_date': self.from_date,
            'partner_name': self.partner_id.name,
            'property_name': self.property_id.name,
        }
        return self.env.ref(
            'advanced_property_management.property_sale_report_action_report').report_action(
            self, data=data)
