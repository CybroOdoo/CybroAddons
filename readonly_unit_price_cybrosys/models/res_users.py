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
from odoo import api, fields, models


class ResUsers(models.Model):
    """ Inherit the res users to apply the readonly feature
     to the unit price. """
    _inherit = 'res.users'

    readonly_unit_price_sales = fields.Boolean(
        string='Readonly Unit Price for Sales',
        help="If enabled, the Unit Price in the Sales Order Lines"
             " will be read-only for this user.")
    readonly_unit_price_invoicing = fields.Boolean(
        'Readonly Unit Price for Invoice',
        help='If enabled, the Unit Price in the Invoice Lines'
             ' will be readonly for this user.')
    is_admin_boolean = fields.Boolean(
        compute='_compute_is_admin_boolean',
        help='Whether the current user is an administrator.')

    @api.depends_context('uid')
    def _compute_is_admin_boolean(self):
        """ Check whether the current user is an administrator"""
        for rec in self:
            rec.is_admin_boolean = rec.env.user._is_admin()
