# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
from odoo import api, fields, models


class DamageDetail(models.Model):
    """Model to manage damage details associated with expense items."""
    _name = "damage.detail"
    _description = "Details of expenses related to equipment damage."
    _rec_name = 'product_id'

    product_id = fields.Many2one('product.product', string='Product',
                                 help='A reference to the specific product '
                                      'associated with this expense item.')
    unit_price = fields.Float(string='Unit Price',
                              help='The cost per unit of the associated '
                                   'product.')
    quantity = fields.Float(string='Quantity', default=1,
                            help='The number of units of the associated product'
                                 'that were purchased.')
    expense_note = fields.Char(string='Description',
                               help='A brief description or'
                                    'note about the expense item.')
    equipment_damage_id = fields.Many2one('equipment.request', string='Damage',
                                          help='A reference to the equipment '
                                               'request that led to this '
                                               'expense'
                                               'item (if applicable).')

    @api.onchange('product_id')
    def _onchange_product_id(self):
        """Changing the Product Field will give Product's Unit Price and also
        resets to Quantity to 1"""
        self.unit_price = self.product_id.lst_price
        self.quantity = 1

    @api.onchange('quantity')
    def _onchange_quantity(self):
        """Changing  Quantity causes the Unit Price of Product to Change"""
        self.unit_price = self.product_id.lst_price * self.quantity
