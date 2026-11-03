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


class PosConfig(models.Model):
    """Inherit pos.config to configure multi-currency support in POS."""
    _inherit = 'pos.config'

    currency_ids = fields.Many2many(
        'res.currency',
        string='Currencies',
        help='Currencies supported for multi-currency payments in POS.',
    )
    enable_multicurrency = fields.Boolean(
        string='Enable Multi-Currency',
        default=False,
        help='Enable multi-currency payment support in POS.',
    )

    @api.model
    def get_config_settings(self, config_id):
        """Retrieve multi-currency configuration settings for the specified POS config.

        :param int or str config_id: ID of the pos.config record.
        :return: List of dictionaries containing currency details (id, name, symbol, rate).
        :rtype: list[dict]
        """
        if not config_id:
            return []
        try:
            config = self.browse(int(config_id))
        except (ValueError, TypeError):
            return []
        if not config.exists():
            return []
        result = []
        for currency in config.currency_ids:
            result.append({
                'id': currency.id,
                'name': currency.name,
                'symbol': currency.symbol,
                'rate': currency.rate,
            })
        return result

    @api.model
    def get_selected_currency(self, selected_id):
        """Retrieve details and exchange rate for the selected foreign currency.

        :param int or str selected_id: ID of the res.currency record.
        :return: List containing dictionary with currency details (id, name, symbol, rate, usd_val).
        :rtype: list[dict]
        """
        if not selected_id:
            return []
        try:
            currency = self.env['res.currency'].browse(int(selected_id))
        except (ValueError, TypeError):
            return []
        if not currency.exists():
            return []
        rate_val = round(currency.rate, 4) if currency.rate else 0
        return [{
            'id': currency.id,
            'name': currency.name,
            'symbol': currency.symbol,
            'rate': currency.rate,
            'usd_val': rate_val,
            'rate_val': rate_val,
        }]

