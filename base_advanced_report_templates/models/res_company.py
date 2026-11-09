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
"""Extend res.company to add document layout configurations."""
from odoo import fields, models


class ResCompany(models.Model):
    """Extend res.company to store default document layout themes."""

    _inherit = 'res.company'

    sale_document_layout_id = fields.Many2one(
        comodel_name="doc.layout",
        string="Sale Document Layout",
        help="Document layout theme associated with sales orders for the company.",
    )
    purchase_document_layout_id = fields.Many2one(
        comodel_name="doc.layout",
        string="Purchase Document Layout",
        help="Document layout theme associated with purchase orders for the company.",
    )
    account_document_layout_id = fields.Many2one(
        comodel_name="doc.layout",
        string="Account Document Layout",
        help="Document layout theme associated with invoices for the company.",
    )
    stock_document_layout_id = fields.Many2one(
        comodel_name="doc.layout",
        string="Stock Document Layout",
        help="Document layout theme associated with delivery orders for the company.",
    )
