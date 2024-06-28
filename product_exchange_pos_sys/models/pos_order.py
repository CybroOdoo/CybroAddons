# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Ayana KP (Contact : odoo@cybrosys.com)
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


class PosOrderLine(models.Model):
    """Inheriting pos order line model to get product details"""
    _inherit = "pos.order.line"

    @api.model
    def get_product_details(self, ids):
        """Function for get the product details"""
        return [{
            'product_id': rec.product_id.id,
            'name': rec.product_id.name,
            'qty': rec.qty
        } for rec in self.browse(ids)]


class PosOrder(models.Model):
    """ Inheriting pos order model for setting pos exchange order """
    _inherit = 'pos.order'

    exchange = fields.Boolean(string="Exchange",
                              help="Indicates if this order line contains"
                                   " exchanged products.")

    @api.model
    def get_pos_orders(self):
        return [{
            'id': rec.id,
            'pos_reference': rec.pos_reference,
            'name': rec.name,
            'partner_id': rec.partner_id.name if rec.partner_id else '',
            'date_order': rec.date_order,
            'lines': rec.lines.ids,
        } for rec in self.sudo().search([('exchange', '=', False)])]

