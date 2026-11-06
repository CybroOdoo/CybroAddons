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
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from collections import defaultdict

from odoo import models


class PosOrder(models.Model):
    """Inherits pos.order to provide category-wise grouping for POS receipts."""

    _inherit = 'pos.order'

    def order_receipt_generate_data(self, basic_receipt=False):
        """Generate receipt data grouped by product POS categories."""
        data = super().order_receipt_generate_data(basic_receipt=basic_receipt)
        lines_data = data.get('lines', [])
        line_data_by_id = {ld['id']: ld for ld in lines_data if 'id' in ld}

        grouped = defaultdict(lambda: {
            'category_id': None,
            'category_name': '',
            'subtotal': 0.0,
            'lines': [],
        })

        for order_line in self.lines:
            pos_categ = order_line.product_id.pos_categ_ids[:1]
            cat_id = pos_categ.id if pos_categ else None
            cat_name = pos_categ.name if pos_categ else ''

            group = grouped[cat_id]
            group['category_id'] = cat_id
            group['category_name'] = cat_name
            group['subtotal'] += order_line.price_subtotal_incl

            line_data = line_data_by_id.get(order_line.id)
            if line_data:
                group['lines'].append(line_data)

        category_data = list(grouped.values())
        for cat in category_data:
            cat['subtotal_formatted'] = self._order_receipt_format_currency(cat['subtotal'])

        data['category_data'] = category_data
        return data
