# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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
################################################################################
from odoo import api, models, fields, _
from odoo.exceptions import UserError


class DeletePosPaidOrder(models.TransientModel):
    _name = "delete.paid.pos.order"
    _description = "Delete Paid POS Order"

    pos_order_delete = fields.Boolean(string='Delete Paid Order', default=True,
                                      help="Enable to delete POS orders")
    code = fields.Char(string='Code', help="Setup code to enter "
                                           "while deleting the POS order")

    @api.model
    def default_get(self, fields):
        """The function used to update the default values"""
        is_delete = self.env['ir.config_parameter'].sudo().get_param(
            'pos_paid_order_delete.is_delete')
        result = super(DeletePosPaidOrder, self).default_get(fields)
        if is_delete:
            delete_paid_order = self.env[
                'ir.config_parameter'].sudo().get_param(
                'pos_paid_order_delete.delete_paid_order')
            result['pos_order_delete'] = delete_paid_order != 'order_with_code'
        return result

    def delete_pos_paid_order(self):
        """This function is used to delete the pos paid orders and the
        corresponding payments"""
        is_delete = (self.env['ir.config_parameter'].sudo().
                     get_param('pos_paid_order_delete.is_delete'))
        if is_delete:
            delete_paid_order = (self.env['ir.config_parameter'].sudo().
                                 get_param('pos_paid_order_delete.'
                                           'delete_paid_order'
                                           ))
            pos_orders = self.env['pos.order'].browse(self.env.context.get
                                                      ('active_ids'))
            code = self.env['ir.config_parameter'].sudo().get_param(
                'pos_paid_order_delete.code')
            if delete_paid_order == 'order_with_code':
                if code == self.code:
                    for order in pos_orders:
                        for payment in order.payment_ids:
                            payment.unlink()
                        order.action_pos_order_cancel()
                        order.unlink()
                else:
                    raise UserError("The code is wrong.Please enter the "
                                    "correct code")
            else:
                for order in pos_orders:
                    for payment in order.payment_ids:
                        payment.unlink()
                    order.action_pos_order_cancel()
                    order.unlink()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Delete Pos Orders'),
            'res_model': 'pos.order',
            'view_mode': 'tree',
            'view_id': self.env.ref('point_of_sale.view_pos_order_tree').id,
            'target': 'main',
        }
