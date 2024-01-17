# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Jumana Haseen (<https://www.cybrosys.com>)
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
from odoo import fields, models


class ProductTemplate(models.Model):
    """Inherits the model product.template and add extra functionality"""
    _inherit = 'product.template'

    def action_transfer_stock(self):
        """Open a pop-up to make the stock transfer"""
        stock_quant = self.env['stock.quant'].search(
            [('product_id', '=', self.product_variant_id.id),
             ('on_hand', '=', True)])
        location = stock_quant.mapped('location_id')
        return {
            'type': 'ir.actions.act_window',
            'target': 'new',
            'name': "Stock Transfer",
            'view_mode': 'form',
            'res_model': 'stock.transfer',
            'context': {'default_product_id': self.id,
                        'default_location_ids':
                            [[fields.Command.link(loc)] for loc in
                             location.ids]},
        }
