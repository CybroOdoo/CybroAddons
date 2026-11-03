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
from odoo import fields, models


class ResUsers(models.Model):
    """Inherits the res.users model to add functionality for managing
        user-specific pricelist restrictions."""
    _inherit = 'res.users'

    pricelist_ids = fields.Many2many('product.pricelist',
                                     'rel_user_pricelist',
                                     help='Choose the allowed pricelists for '
                                          'the user', string="Pricelists")
    is_restricted = fields.Boolean(help='Restrict pricelists for the user',
                                   string="Restricted",
                                   compute="_compute_is_restricted")

    def _compute_is_restricted(self):
        """Compute method of the is_restricted field. It sets the field
            according to the setting in res.config.settings."""
        pricelist_restricted = self.env['ir.config_parameter'].sudo(). \
            get_bool('restrict_pricelist_user.is_restricted')
        for rec in self:
            rec.is_restricted = pricelist_restricted
