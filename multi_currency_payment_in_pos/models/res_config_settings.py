# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Dhanya Babu (odoo@cybrosys.com)
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
##############################################################################
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    """Added boolean field and currency."""
    _inherit = 'res.config.settings'

    currency_ids = fields.Many2many('res.currency',
                                    string="Currencies",
                                    related="pos_config_id.currency_ids",
                                    readonly=False,
                                    help="The list of currencies supported by "
                                         "this Point of Sale configuration.")

    enable_currency = fields.Boolean(string="Enable Currency",
                                     config_parameter="multi_currency_payment_in_pos.enable_currency",
                                     help="Enable or disable currency for "
                                          "this POS configuration.")

    @api.onchange('enable_currency')
    def _onchange_value(self):
        """When enable the boolean field many2many currency field will
        display."""
        for rec in self:
            rec.pos_config_id.enable_multicurrency = rec.enable_currency
