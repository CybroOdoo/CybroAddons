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
"""Extend purchase.order to add document layout theme."""
from odoo import fields, models


class PurchaseOrder(models.Model):
    """Extend purchase.order model to include document layout theme."""

    _inherit = 'purchase.order'

    theme_id = fields.Many2one(
        comodel_name='doc.layout',
        related='company_id.purchase_document_layout_id',
        string='Document Layout Theme',
        help="Document layout theme associated with the company's purchase orders.",
    )
