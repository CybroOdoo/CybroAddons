# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Anfas Faisal K (odoo@cybrosys.info)
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


class EquipmentDetail(models.Model):
    """Model to manage equipment details associated with request items."""
    _name = "equipment.detail"
    _description = "Details of equipment associated with request items."
    _rec_name = 'product_id'

    product_id = fields.Many2one('product.product', string='Product',
                                 help='A reference to the specific product '
                                      'associated with this item.')
    description = fields.Char(string='Description',
                              help='A brief description of the item.')
    quantity = fields.Float(string='Quantity', default=1,
                            help='The number of units of the associated product'
                                 'that were requested or used.')
    product_uom_id = fields.Many2one('uom.uom',
                                     string='Product Unit of Measure',
                                     help='The unit of measure for the '
                                          'associated'
                                          'product.')
    equipment_detail_id = fields.Many2one('equipment.request',
                                          string='Request Equipments',
                                          help='A reference to the equipment '
                                               'request that led to this item '
                                               '(if'
                                               'applicable).')

    @api.onchange('product_id')
    def _onchange_product_id(self):
        """Changing the Product Field will reset the Quantity to 1"""
        self.quantity = 1
        self.product_uom_id = self.product_id.uom_id
