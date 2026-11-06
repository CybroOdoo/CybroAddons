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
#############################################################################
from odoo import api, fields, models


class PurchaseOrderLine(models.Model):
    """Inherits purchase.order.line to add multi-attachment support."""

    _inherit = 'purchase.order.line'

    attachment_ids = fields.Many2many(
        'ir.attachment',
        string='Attachments',
        compute='_compute_attachment_ids',
        store=True,
        readonly=False,
        help='Attachments associated with this purchase order line.',
    )

    @api.depends(
        'product_id',
        'product_id.attachment_ids',
        'product_id.product_tmpl_id.attachment_ids',
    )
    def _compute_attachment_ids(self):
        """Compute attachments from product variant first, then product
        template if no variant-level attachments exist."""
        for line in self:
            if line.product_id.attachment_ids:
                line.attachment_ids = line.product_id.attachment_ids
            elif line.product_id.product_tmpl_id.attachment_ids:
                line.attachment_ids = (
                    line.product_id.product_tmpl_id.attachment_ids
                )
            else:
                line.attachment_ids = False
