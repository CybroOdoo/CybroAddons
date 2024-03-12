# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Technologies (<https://www.cybrosys.com>)
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
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class SelectProductPack(models.TransientModel):
    """A new model is created select.product.pack to add product pack to
     sale order."""
    _name = 'select.product.pack'
    _rec_name = 'product_id'
    _description = 'Add product pack to sale order'

    product_id = fields.Many2one(
        'product.product', string='Select Pack', help='Select Product Pack',
        domain=[('is_pack', '=', True)], required=True)
    quantity = fields.Integer(string='Quantity', help='Quantity', default=1,
                              required=True)

    def action_add_pack_order(self):
        """
        When a pack is added, pack information are added under
        the sale order line.
        """
        active_id = self._context.get('active_id')
        if active_id:
            sale_id = self.env['sale.order'].browse(active_id)
            name = self.product_id.display_name
            if self.product_id.description_sale:
                name += '\n' + self.product_id.description_sale
            self.env['sale.order.line'].create({
                'product_id': self.product_id.id,
                'product_uom': self.product_id.uom_id.id,
                'product_uom_qty': self.quantity,
                'order_id': sale_id.id,
                'name': name,
                'tax_id': self.product_id.taxes_id.ids
            })

    @api.constrains('quantity')
    def _check_positive_qty(self):
        """ Check if the 'quantity' field of the record is positive."""
        if any([ml.quantity < 0 for ml in self]):
            raise ValidationError(_('You can not enter negative quantities.'))
