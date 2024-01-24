# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
###############################################################################
from odoo import api, fields, models


class PurchaseOrderLine(models.Model):
    """inherited purchase.order.line to add field"""
    _inherit = 'purchase.order.line'

    @api.depends('product_id', 'product_id.attachment_ids',
                 'product_id.product_tmpl_id.attachment_ids')
    def _compute_attachment_ids(self):
        for line in self:
            if line.product_id.attachment_ids:
                line.attachment_ids = line.product_id.attachment_ids
            elif line.product_id.product_tmpl_id.attachment_ids:
                line.attachment_ids = line.product_id.product_tmpl_id.attachment_ids
            else:
                line.attachment_ids = False

    attachment_ids = fields.Many2many('ir.attachment', string='Attachments',
                                      compute='_compute_attachment_ids',
                                      help='Product Attachments', store=True,
                                      readonly=False)
