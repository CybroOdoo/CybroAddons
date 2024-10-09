# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
from odoo import exceptions
from odoo import api, fields, models
from ast import literal_eval


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

    @api.model
    def get_values(self):
        """Fetch configuration values from ir.config_parameter."""
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()

        # Retrieve and decode the values
        pos_membership_product_id = params.get_param('pos_membership_product_id')
        is_pos_module_pos_membership = params.get_param('membership_in_pos.is_pos_module_pos_membership')

        # Update result dictionary with the fetched values
        res.update(
            pos_membership_product_id=int(pos_membership_product_id) if pos_membership_product_id else False,
            is_pos_module_pos_membership=literal_eval(
                is_pos_module_pos_membership) if is_pos_module_pos_membership else False
        )
        return res

    @api.model
    def set_values(self):
        """Save configuration values to ir.config_parameter."""
        super(ResConfigSettings, self).set_values()

        # Access ir.config_parameter and set the values
        params = self.env['ir.config_parameter'].sudo()
        params.set_param(
            'pos_membership_product_id',
            self.pos_membership_product_id.id if self.pos_membership_product_id else False
        )
        params.set_param(
            'membership_in_pos.is_pos_module_pos_membership',
            str(self.is_pos_module_pos_membership)
        )

        # Validation: Ensure the product is available in POS
        if self.pos_membership_product_id:
            product = self.pos_membership_product_id
            if not product.available_in_pos:
                raise exceptions.UserError(
                    "The discount product seems misconfigured. Make sure it is "
                    "flagged as 'Can be Sold' and 'Available in Point of Sale'."
                )
