# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Yadhu Shankar E (odoo@cybrosys.com)
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
from odoo import fields, models, api


class PosConfig(models.Model):
    _inherit = 'pos.config'

    currency_ids = fields.Many2many(
        'res.currency',
        string='Currency',
        help='Currencies supported in POS.'
    )

    enable_multicurrency = fields.Boolean(
        string='Enable Multi Currency',
        help='Enable multi currency in POS.'
    )

    # ---------------------------------------------------------
    # Returns full multicurrency configuration for POS
    # ---------------------------------------------------------
    @api.model
    def get_config_settings(self, config_id):
        config = self.browse(int(config_id))
        result = []
        for currency in config.currency_ids:
            result.append({
                'id': currency.id,
                'name': currency.name,
                'symbol': currency.symbol,
                'rate': currency.rate,
            })
        return result

    # ---------------------------------------------------------
    # Return details of one selected currency
    # ---------------------------------------------------------
    @api.model
    def get_selected_currency(self, selected_id):
        currency = self.env['res.currency'].browse(int(selected_id))
        usd_val = round(1 / currency.rate, 2) if currency.rate else 0
        return [{
            'id': currency.id,
            'name': currency.name,
            'symbol': currency.symbol,
            'rate': currency.rate,
            'usd_val': usd_val,
        }]
