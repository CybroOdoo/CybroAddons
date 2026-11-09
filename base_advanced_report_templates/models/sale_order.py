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
"""Extend sale.order to add customer image and theme layout."""
from odoo import fields, models


class SaleOrder(models.Model):
    """Extend sale.order model to include customer image and document layout theme."""

    _inherit = 'sale.order'

    customer_image = fields.Binary(
        string="Image",
        related="partner_id.image_1920",
        help="Image associated with the customer on the sale order.",
    )
    theme_id = fields.Many2one(
        comodel_name='doc.layout',
        related='company_id.sale_document_layout_id',
        string='Document Layout Theme',
        help="Document layout theme associated with the company's sale orders.",
    )
