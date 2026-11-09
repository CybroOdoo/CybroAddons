# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
################################################################################

"""Model for custom document layout themes."""
from odoo import fields, models


class DocLayout(models.Model):
    """Document layout theme model for report design customization."""

    _name = "doc.layout"
    _description = 'Document Layout Theme'

    name = fields.Char(
        string="Name",
        required=True,
        help="Name of the document layout theme.",
    )
    theme_style = fields.Selection(
        selection=[
            ('traditional', 'Traditional'),
            ('standard', 'Standard'),
            ('modern', 'Modern'),
            ('attractive', 'Attractive'),
        ],
        string="Theme Style",
        default='traditional',
        required=True,
        help="Visual style structure to use for reports.",
    )
    base_color = fields.Char(
        string="Base Color",
        help="Primary theme accent color applied to report banners and headers.",
    )
    heading_text_color = fields.Char(
        string="Heading Text Color",
        help="Text color applied to table headers and section titles.",
    )
    text_color = fields.Char(
        string="Text Color",
        help="Text color for line item details and primary table content.",
    )
    customer_text_color = fields.Char(
        string="Customer Text Color",
        help="Text color applied to customer address and contact details.",
    )
    company_text_color = fields.Char(
        string="Company Text Color",
        help="Text color applied to company address and header contact details.",
    )
    logo_position = fields.Selection(
        selection=[('left', 'Left'), ('right', 'Right')],
        default='left',
        string="Logo Position",
        help="Alignment position for company logo in document headers.",
    )
    customer_position = fields.Selection(
        selection=[('left', 'Left'), ('right', 'Right')],
        default='left',
        string="Customer Position",
        help="Alignment position for customer address details on reports.",
    )
    company_position = fields.Selection(
        selection=[('left', 'Left'), ('right', 'Right')],
        default='right',
        string="Company Address Position",
        help="Alignment position for company address details on reports.",
    )
    company_id = fields.Many2one(
        'res.company',
        string="Company",
        index=True,
        default=lambda self: self.env.company,
        help="Company associated with this document layout theme.",
    )
