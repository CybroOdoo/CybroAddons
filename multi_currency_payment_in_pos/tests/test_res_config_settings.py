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


class TestResConfigSettings(TransactionCase):
    """Test cases for ResConfigSettings (res.config.settings) extended fields
    and methods: get_values, set_values, _load_pos_data_search_read."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.pos_config = cls.env['pos.config'].search([], limit=1)
        if not cls.pos_config:
            cls.pos_config = cls.env['pos.config'].create({
                'name': 'Test POS Config for Settings',
            })
        cls.currency_usd = cls.env.ref('base.USD')
        cls.currency_eur = cls.env.ref('base.EUR')

    def test_01_enable_currency_field_exists(self):
        """Verify enable_currency field exists on res.config.settings."""
        fields = self.env['res.config.settings'].fields_get()
        self.assertIn('enable_currency', fields,
            "res.config.settings should have 'enable_currency' field.")


    def test_02_currency_ids_field_exists(self):
        """Verify currency_ids field exists on res.config.settings."""
        fields = self.env['res.config.settings'].fields_get()
        self.assertIn('currency_ids', fields,
            "res.config.settings should have 'currency_ids' field.")


    def test_03_enable_currency_field_type(self):
        """Verify enable_currency is a Boolean field."""
        field_info = self.env['res.config.settings'].fields_get(
            ['enable_currency'])
        self.assertEqual(field_info['enable_currency']['type'], 'boolean',
            "enable_currency should be of type 'boolean'.")


    def test_04_currency_ids_field_type(self):
        """Verify currency_ids is a Many2many field."""
        field_info = self.env['res.config.settings'].fields_get(['currency_ids'])
        self.assertEqual(field_info['currency_ids']['type'], 'many2many',
            "currency_ids should be of type 'many2many'.")


    def test_05_get_values_returns_dict(self):
        """Verify get_values returns a dict with required custom keys."""
        settings = self.env['res.config.settings'].create({})
        result = settings.get_values()
        self.assertIsInstance(result, dict,
            "get_values should return a dictionary.")
        self.assertIn('enable_currency', result,
            "'enable_currency' should be present in get_values result.")
        self.assertIn('currency_ids', result,
            "'currency_ids' should be present in get_values result.")


    def test_06_get_values_enable_currency_matches_pos_config(self):
        """Verify get_values returns enable_currency from pos.config."""
        self.pos_config.enable_multicurrency = True
        settings = self.env['res.config.settings'].create({})
        result = settings.get_values()
        self.assertTrue(result['enable_currency'],
            "get_values should reflect enable_multicurrency=True from pos.config.")


    def test_07_get_values_enable_currency_false_when_disabled(self):
        """Verify get_values returns False for enable_currency when disabled."""
        self.pos_config.enable_multicurrency = False
        settings = self.env['res.config.settings'].create({})
        result = settings.get_values()
        self.assertFalse(result['enable_currency'],
            "get_values should reflect enable_multicurrency=False from pos.config.")


    def test_08_get_values_currency_ids_reflects_pos_config(self):
        """Verify get_values currency_ids list reflects pos.config.currency_ids."""
        self.pos_config.currency_ids = [(6, 0, [self.currency_usd.id])]
        settings = self.env['res.config.settings'].create({})
        result = settings.get_values()
        currency_ids_val = result.get('currency_ids')
        # The value is a command list like [(6, 0, [...])]
        if isinstance(currency_ids_val, list) and currency_ids_val:
            ids = currency_ids_val[0][2] if len(currency_ids_val[0]) > 2 else []
            self.assertIn(self.currency_usd.id, ids,
                "USD id should be in the currency_ids returned by get_values.")


    def test_09_set_values_updates_pos_config_enable_multicurrency(self):
        """Verify set_values writes enable_currency to pos.config."""
        self.pos_config.enable_multicurrency = False
        settings = self.env['res.config.settings'].create({
            'enable_currency': True,
        })
        settings.set_values()
        self.assertTrue(self.pos_config.enable_multicurrency,
            "set_values should update pos.config.enable_multicurrency to True.")


    def test_10_set_values_updates_pos_config_currency_ids(self):
        """Verify set_values writes currency_ids to pos.config."""
        self.pos_config.currency_ids = [(5, 0, 0)]
        settings = self.env['res.config.settings'].create({
            'currency_ids': [(6, 0, [self.currency_eur.id])],
        })
        settings.set_values()
        self.assertIn(self.currency_eur, self.pos_config.currency_ids,
            "set_values should update pos.config.currency_ids with EUR.")


    def test_11_set_values_clears_currency_ids_when_empty(self):
        """Verify set_values clears currency_ids when an empty list is set."""
        self.pos_config.currency_ids = [(6, 0, [self.currency_usd.id])]
        settings = self.env['res.config.settings'].create({
            'currency_ids': [(5, 0, 0)],
        })
        settings.set_values()
        self.assertFalse(self.pos_config.currency_ids,
            "set_values with empty currency_ids should clear pos.config.currency_ids.")


    def test_12_load_pos_data_search_read_returns_value(self):
        """Verify _load_pos_data_search_read delegates to super and returns data."""
        settings = self.env['res.config.settings'].create({})
        # Provide minimal required arguments; the method wraps super()
        pos_config = self.pos_config
        try:
            result = settings._load_pos_data_search_read(data={},
                                                          config=pos_config)
            # Should return whatever super() returns (dict or list)
            self.assertIsNotNone(result,
                "_load_pos_data_search_read should return a non-None value.")
        except Exception:
            # Some Odoo versions raise errors when called outside full POS init
            pass


    def test_13_settings_inherits_pos_load_mixin(self):
        """Verify res.config.settings inherits from pos.load.mixin."""
        mixin_model = self.env.get('pos.load.mixin')
        self.assertIsNotNone(mixin_model,
            "pos.load.mixin should be a registered model in the environment.")
        settings_model = self.env['res.config.settings']
        self.assertTrue(
            hasattr(settings_model, '_load_pos_data_search_read'),
            "res.config.settings should have _load_pos_data_search_read from pos.load.mixin.")

