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

from odoo import fields, models


class StockMoveLine(models.Model):
    """Exposes storage-class metadata on move lines for GMP traceability."""
    _inherit = 'stock.move.line'

    pharma_required_storage_category_id = fields.Many2one(
        comodel_name='stock.storage.category',
        related='product_id.storage_category_id',
        string='Required Storage Class',
        help='Storage class the product requires. Shown next to the class the '
             'destination actually provides, so a move into the wrong area is '
             'visible in the traceability history.',
    )

    pharma_src_storage_category_id = fields.Many2one(
        comodel_name='stock.storage.category',
        related='location_id.storage_category_id',
        string='Storage Class (From)',
        help='Storage class provided by the source location of this move.',
    )

    # Stored so the traceability list can be grouped by storage class; the
    # related fields above are only ever displayed, never grouped.
    pharma_storage_category_id = fields.Many2one(
        comodel_name='stock.storage.category',
        related='location_dest_id.storage_category_id',
        string='Storage Class (To)',
        store=True,
        index='btree_not_null',
        help='Storage class provided by the destination location of this move. '
             'Stored so move history can be grouped by storage class.',
    )
