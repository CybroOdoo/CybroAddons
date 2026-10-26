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
from odoo import api, fields, models


class ResUsers(models.Model):
    """Class added for adding field to select the allowed POS for users."""
    _inherit = 'res.users'

    allowed_pos_ids = fields.Many2many(
        comodel_name='pos.config',
        string='Allowed POS',
        help='Point of Sale configurations allowed for this user.',
    )
    show_users = fields.Boolean(
        string='Show Users of POS',
        default=True,
        help='Show allowed users on the Point of Sale dashboard for administrators.',
    )
    allowed_pos_category_ids = fields.Many2many(
        'pos.category', compute='_compute_allowed_pos_categories'
    )
    has_unlimited_pos = fields.Boolean(compute='_compute_allowed_pos_categories')

    @api.depends('allowed_pos_ids', 'allowed_pos_ids.limit_categories', 'allowed_pos_ids.iface_available_categ_ids')
    def _compute_allowed_pos_categories(self):
        for user in self:
            categories = self.env['pos.category']
            has_unlimited = False
            if not user.allowed_pos_ids:
                has_unlimited = True
            else:
                for pos in user.allowed_pos_ids:
                    if not pos.limit_categories:
                        has_unlimited = True
                        break
                    categories |= pos.iface_available_categ_ids
            user.allowed_pos_category_ids = categories
            user.has_unlimited_pos = has_unlimited
