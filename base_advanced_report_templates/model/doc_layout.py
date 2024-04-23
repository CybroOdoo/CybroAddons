# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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

from odoo import models, fields


class DocLayout(models.Model):
    """Adding the fields for customization"""
    _name = "doc.layout"
    _description = 'Adding the fields for customization'

    name = fields.Char("Name")

    base_color = fields.Char("Base Color",
                             help="Background color for the invoice")

    heading_text_color = fields.Char("Heading text Color",
                                     help="Heading Text color")

    text_color = fields.Char("Text Color", help="Text color of items")

    customer_text_color = fields.Char("Customer Text Color",
                                      help="Customer address text color")

    company_text_color = fields.Char("Company Text Color",
                                     help="Company address Text color")

    logo_position = fields.Selection([('left', 'Left'), ('right', 'Right')],
                                     string="Logo Position",
                                     help="Company logo position")

    customer_position = fields.Selection(
        [('left', 'Left'), ('right', 'Right')], string="Customer position",
        help="Customer address position")

    company_position = fields.Selection([('left', 'Left'), ('right', 'Right')],
                                        string="Company Address Position",
                                        help="Company address position")

    company_id = fields.Many2one('res.company', string='Company', index=True,
                                 default=lambda self: self.env.company,
                                 help="Company name")
