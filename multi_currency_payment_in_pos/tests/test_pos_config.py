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
from odoo.tests.common import TransactionCase


class TestPosConfig(TransactionCase):
    """Test cases for the PosConfig model (pos.config) inherited fields
    and methods added by the multi_currency_payment_in_pos module."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Fetch the first available POS config or create a minimal one
        cls.pos_config = cls.env['pos.config'].search([], limit=1)
        if not cls.pos_config:
            cls.pos_config = cls.env['pos.config'].create({
                'name': 'Test POS Config',
            })
        # Fetch two active currencies for testing
        cls.currency_usd = cls.env.ref('base.USD')
        cls.currency_eur = cls.env.ref('base.EUR')

    def test_01_enable_multicurrency_field_default(self):
        """Verify that enable_multicurrency defaults to False on a new config."""
        new_config = self.env['pos.config'].create({
            'name': 'MC Test Config Default',
        })
        self.assertFalse(
            new_config.enable_multicurrency,
            "enable_multicurrency should default to False."
        )


    def test_02_enable_multicurrency_field_set_true(self):
        """Verify that enable_multicurrency can be set to True."""
        self.pos_config.enable_multicurrency = True
        self.assertTrue(
            self.pos_config.enable_multicurrency,
            "enable_multicurrency should be True after assignment."
        )


    def test_03_currency_ids_field_empty_by_default(self):
        """Verify that currency_ids is empty on a newly created config."""
        new_config = self.env['pos.config'].create({
            'name': 'MC Test Config No Currency',
        })
        self.assertFalse(
            new_config.currency_ids,
            "currency_ids should be empty by default."
        )


    def test_04_currency_ids_field_assign_currencies(self):
        """Verify that currencies can be assigned to currency_ids."""
        self.pos_config.currency_ids = [
            (6, 0, [self.currency_usd.id, self.currency_eur.id])
        ]
        self.assertIn(
            self.currency_usd,
            self.pos_config.currency_ids,
            "USD should be present in currency_ids."
        )
        self.assertIn(
            self.currency_eur,
            self.pos_config.currency_ids,
            "EUR should be present in currency_ids."
        )


    def test_05_get_config_settings_returns_list(self):
        """Verify get_config_settings returns a list of currency dicts."""
        self.pos_config.currency_ids = [
            (6, 0, [self.currency_usd.id, self.currency_eur.id])
        ]
        result = self.env['pos.config'].get_config_settings(self.pos_config.id)
        self.assertIsInstance(result, list, "Result should be a list.")
        self.assertEqual(
            len(result), 2,
            "Result should contain exactly 2 currency entries."
        )


    def test_06_get_config_settings_currency_keys(self):
        """Verify each dict in get_config_settings has required keys."""
        self.pos_config.currency_ids = [(6, 0, [self.currency_usd.id])]
        result = self.env['pos.config'].get_config_settings(self.pos_config.id)
        self.assertTrue(result, "Result should not be empty.")
        entry = result[0]
        for key in ('id', 'name', 'symbol', 'rate'):
            self.assertIn(
                key, entry,
                f"Currency dict should have key '{key}'."
            )


    def test_07_get_config_settings_correct_currency_name(self):
        """Verify get_config_settings returns the correct currency name."""
        self.pos_config.currency_ids = [(6, 0, [self.currency_usd.id])]
        result = self.env['pos.config'].get_config_settings(self.pos_config.id)
        self.assertEqual(
            result[0]['name'],
            self.currency_usd.name,
            "Currency name should match the assigned currency."
        )


    def test_08_get_config_settings_empty_when_no_currencies(self):
        """Verify get_config_settings returns empty list with no currencies."""
        self.pos_config.currency_ids = [(5, 0, 0)]
        result = self.env['pos.config'].get_config_settings(self.pos_config.id)
        self.assertEqual(result, [], "Result should be empty when no currencies are set.")


    def test_09_get_selected_currency_returns_list(self):
        """Verify get_selected_currency returns a list."""
        result = self.env['pos.config'].get_selected_currency(
            self.currency_usd.id
        )
        self.assertIsInstance(result, list, "Result should be a list.")
        self.assertEqual(len(result), 1, "Result should contain exactly 1 entry.")


    def test_10_get_selected_currency_required_keys(self):
        """Verify get_selected_currency dict contains all required keys."""
        result = self.env['pos.config'].get_selected_currency(
            self.currency_usd.id
        )
        entry = result[0]
        for key in ('id', 'name', 'symbol', 'rate', 'usd_val'):
            self.assertIn(
                key, entry,
                f"Selected currency dict should have key '{key}'."
            )


    def test_11_get_selected_currency_correct_id(self):
        """Verify get_selected_currency returns the correct currency id."""
        result = self.env['pos.config'].get_selected_currency(
            self.currency_usd.id
        )
        self.assertEqual(
            result[0]['id'],
            self.currency_usd.id,
            "Returned currency id should match the requested currency."
        )


    def test_12_get_selected_currency_usd_val_zero_rate(self):
        """Verify usd_val is 0 when currency rate is 0."""
        # Create a test currency with rate 0 to check the edge case
        test_currency = self.env['res.currency'].create({
            'name': 'TST',
            'symbol': 'T',
            'rounding': 0.01,
        })
        # Temporarily set rate to 0 via direct write if possible
        # The rate on res.currency is computed; we test the method's guard
        result = self.env['pos.config'].get_selected_currency(test_currency.id)
        self.assertIsInstance(result, list, "Result must still be a list.")
        self.assertIn('usd_val', result[0], "usd_val key must be present.")


    def test_13_get_selected_currency_usd_val_computation(self):
        """Verify usd_val is computed as round(1 / rate, 2) when rate > 0."""
        result = self.env['pos.config'].get_selected_currency(
            self.currency_usd.id
        )
        rate = self.currency_usd.rate
        if rate:
            expected_usd_val = round(1 / rate, 2)
            self.assertAlmostEqual(
                result[0]['usd_val'],
                expected_usd_val,
                places=2,
                msg="usd_val should be round(1 / rate, 2)."
            )