# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Aysha Shalin (odoo@cybrosys.com)
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
from odoo import fields, models


class ProductTemplate(models.Model):
    """ To inherit location and stock selection fields to product template """
    _inherit = 'product.template'

    location_type = fields.Selection(selection=[('all', 'All'),
                                                ('specific', 'Specific')],
                                     help="Choose stock for a specific location"
                                          " or all locations.", default='all')
    stock_location_id = fields.Many2one('stock.location',
                                        string='Stock Location',
                                        help='Choose a specific location')
    stock_type = fields.Selection(selection=[('on_hand', 'On Hand Quantity'),
                                             ('forecast', 'Forecasted Quantity')
                                             ], help='Choose Stock type',
                                  default='on_hand')

    def _get_combination_info(self, combination=False, product_id=False,
                              add_qty=1, pricelist=False,
                              parent_combination=False, only_template=False):
        """ To add stock details and displays stock details to product page """
        combination_info = super()._get_combination_info(product_id=product_id,
                            combination=combination, add_qty=add_qty,
                            pricelist=pricelist, only_template=only_template,
                            parent_combination=parent_combination)
        product = self.env['product.product'].sudo().browse(
            combination_info['product_id'])
        if self.location_type == 'specific':
            if 'free_qty' in combination_info:
                incoming_domain = [
                    ('product_id', '=', combination_info['product_id']),
                    ('location_dest_id', '=', self.stock_location_id.id)]
                outgoing_domain = [
                    ('product_id', '=', combination_info['product_id']),
                    ('location_id', '=', self.stock_location_id.id)]
                if product.stock_type == 'on_hand':
                    incoming_domain.append(('state', '=', 'done'))
                    outgoing_domain.append(('state', '=', 'done'))
            else:
                incoming_domain = [
                    ('product_tmpl_id', '=',
                     combination_info['product_template_id']),
                    ('location_dest_id', '=', self.stock_location_id.id)]
                outgoing_domain = [
                    ('product_tmpl_id', '=',
                     combination_info['product_template_id']),
                    ('location_id', '=', self.stock_location_id.id)]
                if self.stock_type == 'on_hand':
                    incoming_domain.append(('state', '=', 'done'))
                    outgoing_domain.append(('state', '=', 'done'))
            incoming_stock = self.env['stock.move'].sudo().search(
                incoming_domain)
            outgoing_stock = self.env['stock.move'].sudo().search(
                outgoing_domain)
            incoming_quant = sum(incoming.product_uom_qty for incoming
                                 in incoming_stock)
            outgoing_quant = sum(outgoing.product_uom_qty for outgoing
                                 in outgoing_stock)
            combination_info['free_qty'] = incoming_quant - outgoing_quant
        else:
            if 'free_qty' in combination_info:
                combination_info['free_qty'] = product.virtual_available if \
                    product.stock_type == 'forecast' else product.qty_available
            else:
                combination_info['free_qty'] = self.sudo().virtual_available if \
                    self.stock_type == 'forecast' else self.sudo().qty_available
        combination_info['stock'] = 'out_of_stock' if not \
            combination_info['free_qty'] else 'in_stock'
        return combination_info
