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
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from odoo import api, fields, models


class ResPartner(models.Model):
    """Class for inherited model res partner. Contains computed fields to track
    related users."""
    _inherit = 'res.partner'

    related_user_id = fields.Many2one(
        'res.users',
        string='Related User',
        compute='_compute_related_user',
        store=True,
        compute_sudo=True,
        readonly=True,
        help='This field contains the related user of the partner if there is any.',
    )
    is_have_user = fields.Boolean(
        string='Have User',
        compute='_compute_related_user',
        store=True,
        compute_sudo=True,
        help='This field helps to check if there is any user related to the partner.',
    )

    @api.depends('user_ids', 'user_ids.active')
    def _compute_related_user(self):
        """Compute the related user and boolean flag based on user_ids."""
        for partner in self:
            user = partner.user_ids[:1]
            partner.related_user_id = user
            partner.is_have_user = bool(user)
