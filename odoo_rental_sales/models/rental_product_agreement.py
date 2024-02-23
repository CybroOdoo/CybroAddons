# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Aswathi PN (odoo@cybrosys.com)
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


class RentalProductAgreement(models.Model):
    """Model for showing the rental agreement details"""
    _name = 'rental.product.agreement'
    _description = 'Rental Product Agreement'

    name = fields.Char(string='Name', required=True,
                       help='Name of rental product agreement')
    sequence = fields.Integer(string='Sequence', required=True,
                              help='Sequence of rental product Agreement')
    description = fields.Text(string='Description',
                              help='Description of rental product agreement')
    agreement_file = fields.Binary(string='Product Agreement',
                                   help='Rental product agreement file')
