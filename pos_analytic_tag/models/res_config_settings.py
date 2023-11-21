# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Ajith V (<https://www.cybrosys.com>)
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
###############################################################################
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    """To add a field in pos configuration settings"""
    _inherit = 'res.config.settings'

    pos_analytic_account_id = fields.Many2one(
        'account.analytic.account',
        string='Analytic Account(PoS)', readonly=False,
        help="Add analytic account for the pos session")

    @api.model
    def get_values(self):
        """Get the values use to config parameter"""
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        pos_analytic_account_id = params.get_param('pos_analytic_account_id',
                                                   default=False)
        res.update(pos_analytic_account_id=int(pos_analytic_account_id), )
        return res

    @api.model
    def set_values(self):
        """Set the value"""
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param(
            "pos_analytic_account_id",
            self.pos_analytic_account_id.id)
