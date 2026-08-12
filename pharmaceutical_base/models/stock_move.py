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


class StockMove(models.Model):
    """Surfaces the QC test status of the moved product."""
    _inherit = 'stock.move'

    qc_test_order_status = fields.Selection(
        selection=[
            ('pass', 'Pass'),
            ('fail', 'Fail'),
        ],
        string='QC Test Order',
        compute='_compute_qc_test_order_status',
        help='Indicates whether the component product has passed QC testing.',
    )

    @api.depends('product_id', 'product_id.has_passed_qc_test')
    def _compute_qc_test_order_status(self):
        """Computes whether the product on this move has passed a QC test order."""
        for move in self:
            if move.product_id and move.product_id.has_passed_qc_test:
                move.qc_test_order_status = 'pass'
            else:
                move.qc_test_order_status = 'fail'
