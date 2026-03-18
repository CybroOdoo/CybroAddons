# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Shahil Rasheed (odoo@cybrosys.com)
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
#############################################################################
import logging
from odoo import api, models

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.model
    def create(self, vals):
        """To pass the Bus notification when a new product is created"""
        record = super().create(vals)
        pos_sessions = self.env['pos.session'].search([('state', '=', 'opened')])
        if pos_sessions:
            for variant in record.product_variant_ids.filtered(lambda v: v.available_in_pos):
                self._notify_pos_product_change(variant, pos_sessions)
        return record

    def write(self, vals):
        """To pass the bus notification when the existing products are updated"""
        res = super(ProductTemplate, self).write(vals)
        pos_sessions = self.env['pos.session'].search([('state', '=', 'opened')])
        if pos_sessions:
            variants = self.mapped("product_variant_ids").filtered(lambda v: v.available_in_pos)
            for variant in variants:
                self._notify_pos_product_change(variant, pos_sessions)
        return res

    def _notify_pos_product_change(self, product, pos_sessions):
        """Send bus notification to all active POS sessions"""
        notification_data = {
            'product_id': int(product.id),
            'name': str(product.display_name),
            'list_price': float(product.lst_price),
            'standard_price': float(product.standard_price),
            'qty_available': float(product.qty_available),
            'barcode': str(product.barcode or ""),
            'categ_id': int(product.categ_id.id) if product.categ_id else False,
            'taxes_id': [int(t) for t in product.taxes_id.ids],
        }
        for session in pos_sessions:
            channel = str(session.id)
            try:
                self.env['bus.bus']._sendone(
                    channel,
                    'product_update',
                    notification_data
                )
            except Exception:
                _logger.exception(
                    "pos_update_realtime: failed to send product_update "
                    "notification to POS session %s", session.id
                )
