# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Mohammed Dilshad Tk  (odoo@cybrosys.com)
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


class RentalBill(models.Model):
    """A class for the model rental bills to represent
    the related bills for a property rental"""
    _name = 'rental.bill'
    _description = 'Rental Bill'

    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.company)
    bill_no = fields.Char(string='Bill Number', required=True,
                          help='The bill number of the bill')
    name = fields.Char(string='Name', required=True,
                       help='The name of the bill')
    amount = fields.Float(string='Amount',
                          help='The amount listed in the bill')
    rental_id = fields.Many2one('property.rental', string='Property Rental',
                                help='The corresponding Property Rental')
