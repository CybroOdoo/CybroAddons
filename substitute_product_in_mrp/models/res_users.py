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
from odoo import models


class ResUsers(models.Model):
    """Inherited res.users to push a bus notification when the substitute
    product group is granted or revoked, so the web client can immediately
    invalidate its view cache and redraw the BOM components list with the
    Substitute Product column visible — without requiring a manual hard
    reload (Ctrl + Shift + R) by the user."""

    _inherit = 'res.users'

    def write(self, vals):
        """Override write to notify affected users when the substitute group
        changes so their browser-side view cache is refreshed automatically."""
        result = super().write(vals)
        if 'group_ids' in vals:
            substitute_group = self.env.ref(
                'substitute_product_in_mrp.mrp_substitute_product_group',
                raise_if_not_found=False,
            )
            if substitute_group:
                for user in self.sudo():
                    user._bus_send(
                        'substitute_product_in_mrp/refresh_views',
                        {},
                    )
        return result
