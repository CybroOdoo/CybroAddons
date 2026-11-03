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
class TestResConfigSettings(TransactionCase):
    """Test multi-currency related configuration fields in res.config.settings."""

    def setUp(self):
        super().setUp()
        self.currency_eur = self.env.ref('base.EUR', raise_if_not_found=False)
        if not self.currency_eur:
            self.currency_eur = self.env['res.currency'].create({
                'name': 'EUR',
                'symbol': '€',
                'rate': 1.1,
                'active': True,
            })
        else:
            self.currency_eur.write({'active': True, 'rate': 1.1})

        self.currency_usd = self.env.ref('base.USD', raise_if_not_found=False)
        if not self.currency_usd:
            self.currency_usd = self.env['res.currency'].create({
                'name': 'USD',
                'symbol': '$',
                'rate': 1.0,
                'active': True,
            })
        else:
            self.currency_usd.write({'active': True, 'rate': 1.0})

        self.pos_config = self.env['pos.config'].create({
            'name': 'Settings Test POS',
            'enable_multicurrency': False,
            'payment_method_ids': [(6, 0, [])],
        })

    def test_settings_read_related_fields(self):
        """Test related fields on res.config.settings read from pos.config."""
        self.pos_config.enable_multicurrency = True
        self.pos_config.currency_ids = [(6, 0, [self.currency_eur.id])]

        settings = self.env['res.config.settings'].create({
            'pos_config_id': self.pos_config.id,
        })
        self.assertTrue(settings.enable_currency)
        self.assertIn(self.currency_eur, settings.currency_ids)

    def test_settings_write_related_fields(self):
        """Test writing to related fields on settings updates pos.config."""
        settings = self.env['res.config.settings'].create({
            'pos_config_id': self.pos_config.id,
            'enable_currency': True,
            'currency_ids': [(6, 0, [self.currency_eur.id, self.currency_usd.id])],
        })

        self.assertTrue(self.pos_config.enable_multicurrency)
        self.assertIn(self.currency_eur, self.pos_config.currency_ids)
        self.assertIn(self.currency_usd, self.pos_config.currency_ids)

        settings.write({
            'enable_currency': False,
            'currency_ids': [(6, 0, [self.currency_usd.id])],
        })
        self.assertFalse(self.pos_config.enable_multicurrency)
        self.assertEqual(self.pos_config.currency_ids.ids, [self.currency_usd.id])
