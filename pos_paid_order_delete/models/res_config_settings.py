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
from odoo import api, models, fields


class ResConfigSettings(models.TransientModel):
    """Inheriting ResConfigSettings to add new fields"""
    _inherit = 'res.config.settings'

    is_delete = fields.Boolean(string='Delete Paid Order',
                               help='Based on this selection it shows the '
                                    'fields for deleting the paid pos order '
                                    'with code and without code')
    delete_paid_order = fields.Selection(
        [('order_with_code', 'Delete POS order with code'),
         ('order_without_code', 'Delete POS order without code')],
        default='order_with_code',
        string='Delete Paid Order',
        store=True,
        help='Delete the paid POS order with code or without providing the '
             'code')
    code = fields.Char(string='Code', help="Enter code to confirming "
                                           "record deletion")

    @api.model
    def get_values(self):
        """Get values from the fields"""
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo().get_param
        is_delete = params('pos_paid_order_delete.is_delete')
        delete_paid_order = params('pos_paid_order_delete.delete_paid_order')
        code = params('pos_paid_order_delete.code')
        res.update(
            is_delete=is_delete,
            delete_paid_order=delete_paid_order,
            code=code,
        )
        return res

    def set_values(self):
        """Set values in the fields"""
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param(
            'pos_paid_order_delete.is_delete',
            self.is_delete)
        self.env['ir.config_parameter'].sudo().set_param(
            'pos_paid_order_delete.delete_paid_order',
            self.delete_paid_order)
        self.env['ir.config_parameter'].sudo().set_param(
            'pos_paid_order_delete.code',
            self.code)
        if self.is_delete:
            self.env['ir.actions.act_window'].search([
                ('name', '=', 'Delete Paid Order')]).update(
                {'binding_model_id': self.env['ir.model.data']._xmlid_to_res_id
                ('point_of_sale.model_pos_order')
                 })
        else:
            (self.env['ir.actions.act_window'].search([
                ('name', '=', 'Delete Paid Order')]).update
             ({'binding_model_id': ''}))

    @api.onchange('is_delete')
    def _onchange_is_delete(self):
        """This function is used to st the value of code is None when we are
        disabling the pos order delete field"""
        if not self.is_delete:
            self.code = None
