###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
# pylint: disable=missing-module-docstring,unknown-option-value,too-few-public-methods,protected-access
"""PoS Order Receipt Model Extension for Product Bundles."""
import json
import logging

from odoo import models

_logger = logging.getLogger(__name__)


class PosOrderReceipt(models.AbstractModel):
    """Inherit pos.order.receipt to include bundle component details on receipt."""
    _inherit = 'pos.order.receipt'

    def _order_receipt_generate_line_data(self):
        """Include bundle contents information in receipt line data."""
        line_data = super()._order_receipt_generate_line_data()

        for data, line in zip(line_data, self.lines):
            data['bundle_details'] = False
            if line.product_id.is_bundle and line.product_id.bundle_contents_info:
                try:
                    raw_info = line.product_id.bundle_contents_info
                    details = (
                        json.loads(raw_info)
                        if isinstance(raw_info, str) else raw_info
                    )
                    bundle_list = []
                    for item in details:
                        qty = item.get('qty', 0)
                        if isinstance(qty, (int, float)) and float(qty).is_integer():
                            qty = int(qty)
                        formatted_price = self._order_receipt_format_currency(
                            item.get('price', 0),
                        )
                        bundle_list.append({
                            'name': item.get('name'),
                            'qty': qty,
                            'uom': item.get('uom') or self.env._('Units'),
                            'formattedPrice': formatted_price,
                        })
                    if bundle_list:
                        data['bundle_details'] = bundle_list
                except (ValueError, TypeError, KeyError) as err:
                    _logger.debug("Failed to parse bundle contents info: %s", err)

        return line_data
