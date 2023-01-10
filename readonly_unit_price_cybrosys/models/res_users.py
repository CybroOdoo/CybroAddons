# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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

from odoo import api, fields, models, _


class ResUsers(models.Model):
    _inherit = 'res.users'

    readonly_unit_price_sales = fields.Boolean('Readonly Unit Price for Sales',
                                               help='If enabled, the Unit Price in the Sale Order Line will be readonly for this user.')
    readonly_unit_price_invoicing = fields.Boolean(
        'Readonly Unit Price for Invoice',
        help='If enabled, the Unit Price in the Invoice Lines will be readonly for this user.')
    is_admin_boolean = fields.Boolean(compute='_compute_is_admin_boolean')

    def _compute_is_admin_boolean(self):
        """ checks if the currently logged user is admin or not"""
        u_id = self.search([('id','=',self._uid)])
        if u_id._is_admin() == True:
            self.is_admin_boolean = True
        else:
            self.is_admin_boolean = False
