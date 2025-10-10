# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Ayana KP(odoo@cybrosys.com)
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
from odoo.tools import float_compare


class StockLot(models.Model):
    _inherit = "stock.lot"

    is_taken = fields.Boolean(string='Taken lot', default=False,
                              help='If enables this lot number is taken')

    @api.model
    def check_product_stock_in_location(self, product_id, location_id):
        """Check if product has positive stock in the given location"""
        product = self.env['product.product'].browse(product_id)

        # Get on hand quantity using Odoo's built-in method
        stock_quant = self.env['stock.quant'].search([
            ('product_id', '=', product_id),
            ('location_id', '=', location_id)
        ])

        total_qty = sum(stock_quant.mapped('quantity'))

        return {
            'has_positive_stock': total_qty > 0,
            'total_quantity': total_qty
        }

    @api.model
    def get_available_lots_for_pos(self, product_id, pos_config_id=None):
        """Get available lots for a product in POS location"""

        # Get POS location
        if pos_config_id:
            pos_config = self.env['pos.config'].browse(pos_config_id)
            location_id = pos_config.picking_type_id.default_location_src_id.id
        else:
            pos_session = self.env['pos.session'].search([
                ('state', '=', 'opened'),
                ('user_id', '=', self.env.uid)
            ], limit=1)
            if pos_session:
                location_id = pos_session.config_id.picking_type_id.default_location_src_id.id
            else:
                return {'has_positive_stock': False, 'lots': []}

        # Check total stock in location
        stock_check = self.check_product_stock_in_location(product_id, location_id)

        # If no positive stock, return immediately
        if not stock_check['has_positive_stock']:
            return {
                'has_positive_stock': False,
                'total_quantity': stock_check['total_quantity'],
                'lots': []
            }

        # Stock is positive, get lots with FEFO/FIFO
        product = self.env['product.product'].browse(product_id)
        company_id = self.env.company.id
        removal_strategy = product.product_tmpl_id.categ_id.removal_strategy_id.method or 'fifo'

        # Get all lots for this product
        lot_domain = [
            ('product_id', '=', product_id),
            '|', ('company_id', '=', company_id), ('company_id', '=', False)
        ]

        if removal_strategy == 'fefo':
            lots = self.sudo().search(lot_domain, order='expiration_date asc')
        else:
            lots = self.sudo().search(lot_domain, order='create_date asc')

        # Get lots with positive quantity in the location
        available_lots = []
        for lot in lots:
            quants = self.env['stock.quant'].sudo().search([
                ('lot_id', '=', lot.id),
                ('location_id', '=', location_id),
                ('product_id', '=', product_id)
            ])

            lot_qty = sum(quants.mapped('quantity'))

            if lot_qty > 0:
                available_lots.append({
                    'lot_name': lot.name,
                    'lot_id': lot.id,
                    'available_qty': lot_qty,
                    'expiration_date': str(lot.expiration_date) if lot.expiration_date else False,
                })

        return {
            'has_positive_stock': True,
            'total_quantity': stock_check['total_quantity'],
            'lots': available_lots
        }
