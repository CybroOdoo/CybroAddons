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
from odoo import models


class PosSession(models.Model):
    _inherit = 'pos.session'

    def _loader_params_res_currency(self):
        """Include allowed currencies in the POS data load."""
        result = super()._loader_params_res_currency()
        config = self.config_id
        if config.pos_multi_currency_enabled and config.pos_allowed_currency_ids:
            allowed_ids = config.pos_allowed_currency_ids.ids
            existing_domain = result.get('search_params', {}).get('domain', [])
            if existing_domain:
                result['search_params']['domain'] = [
                    '|', ('id', 'in', allowed_ids),
                ] + existing_domain
            else:
                result['search_params']['domain'] = [('id', 'in', allowed_ids)]
        return result

    def _pos_data_process(self, loaded_data):
        """
        Odoo 19 hook called after all POS data is loaded.
        Inject multi-currency config into the pos.config record data.
        This is the correct Odoo 19 method — runs after load_pos_data().
        """
        result = super()._pos_data_process(loaded_data)
        self._inject_multi_currency_data(loaded_data)
        return result

    def _inject_multi_currency_data(self, loaded_data):
        """Add multi-currency fields to the pos.config entry in loaded_data."""
        config = self.config_id
        config_list = loaded_data.get('pos.config', [])
        for rec in config_list:
            if rec.get('id') == config.id:
                rec['pos_multi_currency_enabled'] = config.pos_multi_currency_enabled
                rec['pos_multi_currency_conversion'] = config.pos_multi_currency_conversion
                rec['pos_allowed_currency_ids'] = config.pos_allowed_currency_ids.ids
                currencies_data = []
                for cur in config.pos_allowed_currency_ids.filtered('active'):
                    currencies_data.append({
                        'id': cur.id,
                        'name': cur.name,
                        'symbol': cur.symbol,
                        'rate': cur.rate,
                        'decimal_places': cur.decimal_places,
                        'position': cur.position,
                    })
                rec['pos_allowed_currencies_data'] = currencies_data

    def get_pos_ui_pos_config(self, params):
        """
        Also override get_pos_ui_pos_config for compatibility with
        Odoo versions that call this method directly.
        """
        result = super().get_pos_ui_pos_config(params)
        config = self.config_id
        for rec in result:
            if rec.get('id') == config.id:
                rec['pos_multi_currency_enabled'] = config.pos_multi_currency_enabled
                rec['pos_multi_currency_conversion'] = config.pos_multi_currency_conversion
                rec['pos_allowed_currency_ids'] = config.pos_allowed_currency_ids.ids
                currencies_data = []
                for cur in config.pos_allowed_currency_ids.filtered('active'):
                    currencies_data.append({
                        'id': cur.id,
                        'name': cur.name,
                        'symbol': cur.symbol,
                        'rate': cur.rate,
                        'decimal_places': cur.decimal_places,
                        'position': cur.position,
                    })
                rec['pos_allowed_currencies_data'] = currencies_data
        return result

    def load_pos_data(self):
        """
        Override load_pos_data as a final fallback — this is always called
        when the POS session starts.
        """
        result = super().load_pos_data()
        config = self.config_id
        config_list = result.get('pos.config', [])
        for rec in config_list:
            if rec.get('id') == config.id:
                rec['pos_multi_currency_enabled'] = config.pos_multi_currency_enabled
                rec['pos_multi_currency_conversion'] = config.pos_multi_currency_conversion
                rec['pos_allowed_currency_ids'] = config.pos_allowed_currency_ids.ids
                currencies_data = []
                for cur in config.pos_allowed_currency_ids.filtered('active'):
                    currencies_data.append({
                        'id': cur.id,
                        'name': cur.name,
                        'symbol': cur.symbol,
                        'rate': cur.rate,
                        'decimal_places': cur.decimal_places,
                        'position': cur.position,
                    })
                rec['pos_allowed_currencies_data'] = currencies_data
        return result
