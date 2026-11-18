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
from odoo import models, fields


class PosConfig(models.Model):
    _inherit = 'pos.config'

    pos_multi_currency_enabled = fields.Boolean(
        string='Enable Multi Currency',
        default=False,
        help='Allow cashiers to accept payments in multiple currencies at the POS.'
    )
    pos_multi_currency_conversion = fields.Boolean(
        string='Enable Multi Currency Conversion',
        default=False,
        help='Show currency conversion details on the payment screen.'
    )
    pos_allowed_currency_ids = fields.Many2many(
        comodel_name='res.currency',
        relation='pos_config_allowed_currency_rel',
        column1='config_id',
        column2='currency_id',
        string='Allowed Currencies',
        help='Currencies available for payment at this Point of Sale.'
    )

    def get_limited_currencies_data(self):
        """Return currency data for POS frontend."""
        self.ensure_one()
        currencies = []
        for currency in self.pos_allowed_currency_ids.filtered('active'):
            currencies.append({
                'id': currency.id,
                'name': currency.name,
                'symbol': currency.symbol,
                'rate': currency.rate,
                'decimal_places': currency.decimal_places,
                'position': currency.position,
            })
        return currencies

    def _get_pos_ui_res_currency(self, params):
        """Override to include multi-currency config in POS session info."""
        result = super()._get_pos_ui_res_currency(params)
        return result

    def get_pos_session_info(self):
        """Return POS session information related to multi-currency configuration.
        Returns:
            dict: A dictionary containing the multi-currency status, conversion
                setting, and allowed currencies data for the POS session.
        """
        result = {}
        if self.pos_multi_currency_enabled:
            result['pos_multi_currency_enabled'] = True
            result['pos_multi_currency_conversion'] = self.pos_multi_currency_conversion
            result['pos_allowed_currencies'] = self.get_limited_currencies_data()
        else:
            result['pos_multi_currency_enabled'] = False
            result['pos_multi_currency_conversion'] = False
            result['pos_allowed_currencies'] = []
        return result
