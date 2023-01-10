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


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    price_unit_boolean = fields.Boolean(default=False,
                                        compute='_compute_price_unit_boolean')

    def _compute_price_unit_boolean(self):
        """ Compute function for price_unit_boolean.
        This function will check the boolean field  of the currently logged user is true or false.
        And it will pass the value to price_unit_boolean."""
        for rec in self:
            u_id = self.env['res.users'].search([('id', '=', self._uid)])
            if u_id.readonly_unit_price_invoicing == False:
                rec.price_unit_boolean = False
            else:
                rec.price_unit_boolean = True
