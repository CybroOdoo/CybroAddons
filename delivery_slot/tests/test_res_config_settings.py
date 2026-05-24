# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author:  Manasa T P (odoo@cybrosys.com)
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
#############################################################################
from odoo.tests.common import TransactionCase


class TestResConfigSettings(TransactionCase):
    """Test cases for the res.config.settings extension in delivery_slot."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ResConfig = cls.env['res.config.settings']
        cls.IrConfig = cls.env['ir.config_parameter'].sudo()
        cls.PARAM_KEY = 'delivery_slot.enable_delivery_date'

    def _create_config(self, enable_delivery_date):
        """Helper: create and return a res.config.settings record."""
        return self.ResConfig.create({
            'enable_delivery_date': enable_delivery_date,
        })

    # -------------------------------------------------------------------------
    # Field existence & type
    # -------------------------------------------------------------------------

    def test_field_exists_on_model(self):
        """Test that enable_delivery_date field is present on the model."""
        fields = self.ResConfig.fields_get(['enable_delivery_date'])
        self.assertIn('enable_delivery_date', fields)
        self.assertEqual(fields['enable_delivery_date']['type'], 'boolean')

    # -------------------------------------------------------------------------
    # Default value
    # -------------------------------------------------------------------------

    def test_default_enable_delivery_date_is_false(self):
        """Test that enable_delivery_date defaults to False when param is unset."""
        # Clear the system parameter to ensure clean state
        self.IrConfig.set_param(self.PARAM_KEY, False)
        config = self.ResConfig.create({})
        self.assertFalse(config.enable_delivery_date)

    # -------------------------------------------------------------------------
    # Set & execute config
    # -------------------------------------------------------------------------

    def test_set_enable_delivery_date_true(self):
        """Test that setting enable_delivery_date=True persists to ir.config_parameter."""
        config = self._create_config(True)
        config.execute()
        stored_value = self.IrConfig.get_param(self.PARAM_KEY)
        self.assertTrue(
            stored_value in (True, 'True', '1', 't', 'true'),
            f"Expected truthy value in config parameter, got: {stored_value!r}")

    def test_set_enable_delivery_date_false(self):
        """Test that setting enable_delivery_date=False persists as falsy."""
        # First enable it
        config_on = self._create_config(True)
        config_on.execute()
        # Now disable it
        config_off = self._create_config(False)
        config_off.execute()
        stored_value = self.IrConfig.get_param(self.PARAM_KEY)
        self.assertFalse(
            stored_value in (True, 'True', '1', 't', 'true'),
            f"Expected falsy value in config parameter, got: {stored_value!r}")

    # -------------------------------------------------------------------------
    # Config parameter key
    # -------------------------------------------------------------------------

    def test_config_parameter_key(self):
        """Test that the config_parameter key matches the expected value."""
        field_def = self.ResConfig._fields.get('enable_delivery_date')
        self.assertIsNotNone(field_def, "Field enable_delivery_date must exist")
        self.assertEqual(
            getattr(field_def, 'config_parameter', None),
            self.PARAM_KEY,
        )

    # -------------------------------------------------------------------------
    # Write and re-read
    # -------------------------------------------------------------------------

    def test_write_enable_delivery_date(self):
        """Test writing to enable_delivery_date after initial creation."""
        config = self._create_config(False)
        self.assertFalse(config.enable_delivery_date)
        config.write({'enable_delivery_date': True})
        self.assertTrue(config.enable_delivery_date)

    # -------------------------------------------------------------------------
    # Impact on SaleOrder default
    # -------------------------------------------------------------------------

    def test_sale_order_slot_per_product_respects_config_true(self):
        """When config param is True, new SaleOrder.slot_per_product should be True."""
        self.IrConfig.set_param(self.PARAM_KEY, 'True')
        partner = self.env['res.partner'].create({'name': 'Test Partner DS'})
        order = self.env['sale.order'].create({'partner_id': partner.id})
        self.assertTrue(order.slot_per_product,
                        "slot_per_product should default to True when config param is True")

    def test_sale_order_slot_per_product_respects_config_false(self):
        """When config param is False, new SaleOrder.slot_per_product should be False."""
        self.IrConfig.set_param(self.PARAM_KEY, False)
        partner = self.env['res.partner'].create({'name': 'Test Partner DS2'})
        order = self.env['sale.order'].create({'partner_id': partner.id})
        self.assertFalse(order.slot_per_product,
                         "slot_per_product should default to False when config param is False")
