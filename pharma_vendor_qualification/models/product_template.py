# -*- coding: utf-8 -*-
#############################################################################
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
#    If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################

from odoo import api, fields, models


class ProductTemplate(models.Model):
    """Adds the Approved Vendor List relation to the product."""
    _inherit = 'product.template'

    avl_ids = fields.One2many(
        comodel_name='pharma.avl',
        inverse_name='product_id',
        string='Approved Vendor List',
        help='Vendors approved by QA to supply this material.',
    )

    avl_count = fields.Integer(
        string='AVL Count',
        compute='_compute_avl_count',
        help='Specifies the AVL Count for this record.',
    )

    @api.depends('avl_ids')
    def _compute_avl_count(self):
        """Count the AVL entries associated with this product."""
        for rec in self:
            rec.avl_count = len(rec.avl_ids)
