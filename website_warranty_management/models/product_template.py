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


class ProductTemplate(models.Model):
    """Inherited product template to add fields"""
    _inherit = 'product.template'

    is_warranty_available = fields.Boolean(string="Warranty Available",
                                           help="Boolean field to check"
                                                "the warranty availability")
    warranty_duration = fields.Integer(string="Warranty Duration",
                                       help="Warranty duration value")
    warranty_period_type = fields.Selection([
        ('days', 'Days'),
        ('months', 'Months'),
        ('years', 'Years')
    ], string="Warranty Period Type", default='months', help="Warranty duration unit")
    warranty_type = fields.Selection([
        ('full', 'Full Warranty'),
        ('reparable', 'Reparable')
    ], string="Warranty Type", default='full', help="Type of warranty")
