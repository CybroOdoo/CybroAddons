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

from odoo import api, models


class PurchaseOrder(models.Model):
    """Core pharma purchase behaviour: merge identical order lines."""
    _inherit = 'purchase.order'

    @api.model_create_multi
    def create(self, vals_list):
        """Executes the create operation."""
        records = super().create(vals_list)
        records._merge_identical_lines()
        return records

    def write(self, vals):
        """Executes the write operation."""
        res = super().write(vals)
        if 'order_line' in vals:
            self._merge_identical_lines()
        return res

    def _merge_identical_lines(self):
        """Merges identical product lines into a single line with summed quantities."""
        for order in self:
            if order.state not in ['draft', 'sent']:
                continue
            seen = {}
            lines_to_unlink = self.env['purchase.order.line']
            for line in order.order_line:
                if not line.product_id:
                    continue
                key = (line.product_id.id, line.product_uom_id.id)
                if key in seen:
                    seen[key].product_qty += line.product_qty
                    lines_to_unlink |= line
                else:
                    seen[key] = line
            if lines_to_unlink:
                lines_to_unlink.unlink()
