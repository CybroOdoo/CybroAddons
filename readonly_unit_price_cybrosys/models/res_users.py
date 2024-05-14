# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import fields, models


class ResUsers(models.Model):
    """ Inherited th res users to apply the readonly feature to the
    unit price. """
    _inherit = 'res.users'

    readonly_unit_price_sales = fields.Boolean(
        string='Readonly Unit Price for Sales',
        help="This field used to enable readonly or not for sales ")
    readonly_unit_price_invoicing = fields.Boolean(
        string='Readonly Unit Price for Invoice',
        help='If enabled, the Unit Price in the Invoice Lines will be'
             ' readonly for this user.')
    is_admin_boolean = fields.Boolean(
        string='Is Admin',
        compute='_compute_is_admin_boolean',
        help='To check the readonly access for the user.')

    def _compute_is_admin_boolean(self):
        """ checks if the currently logged user is admin or not"""
        for rec in self:
            rec.is_admin_boolean = rec.env.user._is_admin()
