# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
################################################################################
from odoo import fields, models


class ProductTemplate(models.Model):
    """To inherit location and stock selection fields to product template"""
    _inherit = 'product.template'

    def _get_location_type_selection(self):
        return [('all', 'All'), ('specific', 'Specific')]

    def _get_stock_type_selection(self):
        return [('on_hand', 'On Hand Quantity'), ('forecast', 'Forecasted Quantity')]

    location_type = fields.Selection(selection='_get_location_type_selection',
                                     string="Location Type",
                                     help="Choose stock for a specific location or all locations.",
                                     default=lambda self: self.env['ir.default']._get('product.template',
                                                                                      'location_type') or 'all')
    stock_location_id = fields.Many2one('stock.location',
                                        string='Stock Location',
                                        help='Choose a specific location',
                                        default=lambda self: self.env['ir.default']._get('product.template',
                                                                                         'stock_location_id') or self.env.ref(
                                            'stock.stock_location_stock').id)
    stock_type = fields.Selection(string="Stock Type",
                                  selection='_get_stock_type_selection',
                                  help='Choose Stock type',
                                  default=lambda self: self.env['ir.default']._get('product.template',
                                                                                   'stock_type') or 'on_hand')

    def _get_combination_info(self, combination=False, product_id=False,
                              add_qty=1, parent_combination=False,
                              only_template=False, uom_id=False):
        """Retrieve product combination information and update stock availability
           based on the selected stock type and location for the website product page."""
        combination_info = super()._get_combination_info(product_id=product_id,
                                                         combination=combination, add_qty=add_qty,
                                                         only_template=only_template)
        loc_type = self.location_type or self.env['ir.default']._get('product.template',
                                                                     'custom_location_type') or 'all'
        stock_type = self.stock_type or self.env['ir.default']._get('product.template', 'stock_type') or 'on_hand'
        stock_location = self.stock_location_id or self.env['ir.default']._get('product.template', 'stock_location_id')
        if not stock_location:
            stock_location = self.env.ref('stock.stock_location_stock')

        # Fallback to global website settings if product doesn't explicitly show availability
        if not combination_info.get('show_availability'):
            IrDefault = self.env['ir.default'].sudo()
            global_show = IrDefault._get('product.template', 'show_availability')
            if global_show:
                combination_info['show_availability'] = True
                global_threshold = IrDefault._get('product.template', 'available_threshold')
                if global_threshold is not None:
                    combination_info['available_threshold'] = global_threshold

        if loc_type == 'specific':
            incoming_domain = [
                ('product_tmpl_id', '=', self.id),
                ('location_dest_id', '=', stock_location.id)]
            outgoing_domain = [
                ('product_tmpl_id', '=', self.id),
                ('location_id', '=', stock_location.id)]
            if stock_type == 'on_hand':
                incoming_domain.append(('state', '=', 'done'))
                outgoing_domain.append(('state', '=', 'done'))

            incoming_stock = self.env['stock.move'].sudo().search(incoming_domain)
            outgoing_stock = self.env['stock.move'].sudo().search(outgoing_domain)
            incoming_quant = sum(incoming.product_uom_qty for incoming in incoming_stock)
            outgoing_quant = sum(outgoing.product_uom_qty for outgoing in outgoing_stock)
            combination_info['free_qty'] = incoming_quant - outgoing_quant
        else:
            combination_info[
                'free_qty'] = self.sudo().virtual_available if stock_type == 'forecast' else self.sudo().qty_available

        combination_info['stock'] = 'out_of_stock' if combination_info.get('free_qty', 0) <= 0 else 'in_stock'
        return combination_info
