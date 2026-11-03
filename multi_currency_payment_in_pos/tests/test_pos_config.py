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
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', 'at_install')
class TestPosConfig(TransactionCase):
    """Test multi-currency configuration on pos.config."""

    def setUp(self):
        super().setUp()
        self.pos_config_model = self.env['pos.config']
        self.currency_model = self.env['res.currency']

        # Setup test currencies
        self.currency_eur = self.env.ref('base.EUR', raise_if_not_found=False)
        if not self.currency_eur:
            self.currency_eur = self.currency_model.create({
                'name': 'EUR',
                'symbol': '€',
                'active': True,
            })
        else:
            self.currency_eur.write({'active': True})

        rate_eur = self.env['res.currency.rate'].search([
            ('currency_id', '=', self.currency_eur.id),
            ('company_id', '=', self.env.company.id),
        ], limit=1)
        if rate_eur:
            rate_eur.write({'rate': 1.1})
        else:
            self.env['res.currency.rate'].create({
                'currency_id': self.currency_eur.id,
                'rate': 1.1,
                'company_id': self.env.company.id,
            })
        self.currency_eur.invalidate_recordset(['rate'])


        self.currency_usd = self.env.ref('base.USD', raise_if_not_found=False)
        if not self.currency_usd:
            self.currency_usd = self.currency_model.create({
                'name': 'USD',
                'symbol': '$',
                'rate': 1.0,
                'active': True,
            })
        else:
            self.currency_usd.write({'active': True, 'rate': 1.0})

        # Setup POS configuration
        self.pos_config = self.pos_config_model.create({
            'name': 'Multi Currency Test POS',
            'enable_multicurrency': True,
            'payment_method_ids': [(6, 0, [])],
        })
        self.pos_config.currency_ids = [(6, 0, [self.currency_eur.id, self.currency_usd.id])]

    def test_pos_config_fields(self):
        """Test default values and assignment of multi-currency fields on pos.config."""
        self.assertTrue(self.pos_config.enable_multicurrency)
        self.assertIn(self.currency_eur, self.pos_config.currency_ids)
        self.assertIn(self.currency_usd, self.pos_config.currency_ids)

        # Test toggling enable_multicurrency
        self.pos_config.enable_multicurrency = False
        self.assertFalse(self.pos_config.enable_multicurrency)

    def test_get_config_settings_valid(self):
        """Test get_config_settings returns correct currency configurations for
        a valid pos.config.
        """
        settings = self.pos_config_model.get_config_settings(self.pos_config.id)
        self.assertIsInstance(settings, list)
        self.assertEqual(len(settings), 2)

        currency_ids = [item['id'] for item in settings]
        self.assertIn(self.currency_eur.id, currency_ids)
        self.assertIn(self.currency_usd.id, currency_ids)

        eur_entry = next(item for item in settings if item['id'] == self.currency_eur.id)
        self.assertEqual(eur_entry['name'], self.currency_eur.name)
        self.assertEqual(eur_entry['symbol'], self.currency_eur.symbol)
        self.assertEqual(eur_entry['rate'], self.currency_eur.rate)

    def test_get_config_settings_invalid_id(self):
        """Test get_config_settings gracefully returns empty list on invalid or
        missing config IDs.
        """
        self.assertEqual(self.pos_config_model.get_config_settings(False), [])
        self.assertEqual(self.pos_config_model.get_config_settings(0), [])
        self.assertEqual(self.pos_config_model.get_config_settings(99999999), [])
        self.assertEqual(self.pos_config_model.get_config_settings('invalid_id'), [])

    def test_get_selected_currency_valid(self):
        """Test get_selected_currency returns exchange rates and details for a selected currency."""
        currency_info = self.pos_config_model.get_selected_currency(self.currency_eur.id)
        self.assertIsInstance(currency_info, list)
        self.assertEqual(len(currency_info), 1)

        info = currency_info[0]
        self.assertEqual(info['id'], self.currency_eur.id)
        self.assertEqual(info['name'], self.currency_eur.name)
        self.assertEqual(info['symbol'], self.currency_eur.symbol)
        self.assertEqual(info['rate'], self.currency_eur.rate)
        expected_rate_val = round(self.currency_eur.rate, 4)
        self.assertEqual(info['usd_val'], expected_rate_val)
        self.assertEqual(info['rate_val'], expected_rate_val)


    def test_get_selected_currency_invalid_id(self):
        """Test get_selected_currency gracefully returns empty list on invalid or
        missing currency IDs.
        """
        self.assertEqual(self.pos_config_model.get_selected_currency(False), [])
        self.assertEqual(self.pos_config_model.get_selected_currency(0), [])
        self.assertEqual(self.pos_config_model.get_selected_currency(99999999), [])
        self.assertEqual(self.pos_config_model.get_selected_currency('invalid_id'), [])
