# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (Contact : odoo@cybrosys.com)
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
#############################################################################
from odoo import api, fields, models


class SaleOrder(models.Model):
    """ Inherit sale order and add adult person id"""
    _inherit = 'sale.order'

    adult_person_id = fields.Many2one('res.partner',
                                      string='Adult Person',
                                      domain="[('is_adult_member', '=', True)]",
                                      help='To add is adult person or not')

    @api.onchange('adult_person_id')
    def _onchange_adult_person_id(self):
        """
            When adult_person_id is chosen corresponding activities loads
            to the order lines
        """
        product = []
        for rec in self.adult_person_id.daycare_activities_ids:
            product_id = self.env['product.product'].search([
                ('product_tmpl_id', '=', rec.product_id.id)])
            product.append(product_id)
        self.write({'order_line': [(5, 0)]})
        self.update({
            'order_line': [(0, 0, {
                'product_id': rec.id,
                'product_uom': rec.uom_id.id,
                'product_uom_qty': 1,
                'name': rec.name,
                'price_unit': rec.list_price,
            }) for rec in product],
        })
