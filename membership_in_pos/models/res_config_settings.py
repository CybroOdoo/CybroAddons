# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from odoo import exceptions
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    """This class used to add fields in the settings model"""
    _inherit = ['res.config.settings','pos.load.mixin']

    pos_membership_product_id = fields.Many2one('product.product',
                                                string="Membership Product",
                                                help="Membership product",
                                                config_parameter='pos_membership_product_id',
                                                compute='_compute_pos_membership_discount_product_id',
                                                store=True, readonly=False)
    is_pos_module_pos_membership = fields.Boolean(string="Pos Membership",
                                                  config_parameter='membership_in_pos.is_pos_module_pos_membership',
                                                  help="Pos module's pos membership")

    @api.depends('is_pos_module_pos_membership')
    def _compute_pos_membership_discount_product_id(self):
        """This is used to compute the default discount product of membership"""
        for rec in self:
            if rec.is_pos_module_pos_membership:
                rec.pos_membership_product_id = self.env.ref(
                    'pos_discount.product_product_consumable', raise_if_not_found=False).id if self.env.ref('pos_discount.product_product_consumable', raise_if_not_found=False) else False
            else:
                rec.pos_membership_product_id = False

    def set_values(self):
        """Save configuration values and handle side-effects."""
        super(ResConfigSettings, self).set_values()

        # Sync menu visibility with the boolean setting
        menu = self.env.ref(
            'membership_in_pos.pos_membership_menu_root',
            raise_if_not_found=False
        )
        if menu:
            menu.sudo().write({'active': self.is_pos_module_pos_membership})

        # Validate product config only when membership is enabled
        if self.is_pos_module_pos_membership and self.pos_membership_product_id:
            product = self.pos_membership_product_id
            if not product.available_in_pos:
                raise exceptions.UserError(
                    "The discount product seems misconfigured. Make sure it is "
                    "flagged as 'Can be Sold' and 'Available in Point of Sale'."
                )

    @api.model
    def _load_pos_data_fields(self, config_id):
        """Returns the list of fields to be loaded for POS data."""
        result = super()._load_pos_data_fields(config_id)
        result += ['is_pos_module_pos_membership']
        return result
