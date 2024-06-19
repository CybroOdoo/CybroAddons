# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Vishnu KP (odoo@cybrosys.com)
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


class PosOrder(models.Model):
    """Inherited pos order to add some fields"""
    _inherit = "pos.order"

    barcode = fields.Char(string="Barcode", readonly=True,
                          help='to get barcode number of this particular order')
    is_return = fields.Boolean(string='Return orders', default=False, related='is_refunded',
                               store=True,
                               helps='differentiate the pos order and return/ '
                                     'refund order')

    @api.model
    def create(self, vals):
        """Override the create function to add barcode number in order"""
        res = super().create(vals)
        res.barcode = res.pos_reference.replace("Order", "").replace(
            " ", "").replace("-", "")
        return res

    def action_barcode_return(self, barcode):
        """This fn is to search the pos order based on the barcode passed
        from the js and returns true or false"""
        order = self.env['pos.order'].search([('barcode', '=', barcode),
                                              ('is_return', '=', False)])
        if order and order.is_refunded is False:
            refund_id = order.refund()['res_id']
            refund = self.browse(refund_id)
            return {'order': refund, 'exist': True}
        return {'order': len(order), 'exist': False}

    def _prepare_refund_values(self, current_session):
        """Override this function to pass that the order is return """
        res = super()._prepare_refund_values(current_session)
        res.update({
            'is_return': True
        })
        return res

    def find_order(self, barcode):
        order = self.env['pos.order'].search([('barcode', '=', barcode),
                                              ('is_return', '=', False)])
        returned_order = self.env['pos.order'].search([('barcode', '=', barcode),
                                              ('is_return', '=', True)])
        if order:
            return order.id
        else:
            if returned_order:
                return False
            else:
                return "error"
