"""Pos membership"""
# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gayathri v (odoo@cybrosys.com)
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
from odoo import exceptions
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    """This class used to add fields in the settings model"""
    _inherit = 'res.config.settings'

    pos_membership_product_id = fields.Many2one('product.product',
                                                string="Membership Product",
                                                help="Membership product",
                                                compute='_compute_pos_membership_discount_product_id',
                                                store=True, readonly=False)
    is_pos_module_pos_membership = fields.Boolean(string="Pos Membership",
                                                  help="Pos module's pos membership")

    @api.depends('is_pos_module_pos_membership')
    def _compute_pos_membership_discount_product_id(self):
        """This is used to compute the default discount product of membership"""
        for rec in self:
            if rec.is_pos_module_pos_membership:
                rec.pos_membership_product_id = self.env.ref(
                    'point_of_sale.product_product_consumable').id
            else:
                rec.pos_membership_product_id = False

    def get_values(self):
        """Getting the values from the transient model"""
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        is_pos_module_pos_membership = params.get_param('membership_in_pos.'
                                                        'is_pos_module_pos_membership')
        res.update(
            pos_membership_product_id=int(
                self.env['ir.config_parameter'].sudo().get_param(
                    'pos_membership_product_id')),
            is_pos_module_pos_membership=is_pos_module_pos_membership
        )
        return res

    @api.model
    def set_values(self):
        """ Set values for the fields """
        super().set_values()
        self.env['ir.config_parameter'].sudo().set_param(
            'pos_membership_product_id',
            self.pos_membership_product_id.id)
        self.env['ir.config_parameter'].sudo().set_param(
            'membership_in_pos.is_pos_module_pos_membership',
            self.is_pos_module_pos_membership)
        if self.pos_membership_product_id:
            if not (self.pos_membership_product_id.available_in_pos):
                raise exceptions.UserError(
                    "The discount product seems misconfigured.Make sure it is "
                    "flagged as 'Can be Sold' and 'Available in Point of Sale")

