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
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from odoo.tests import common, tagged


@tagged('post_install', '-at_install')
class TestPosWeightManual(common.TransactionCase):
    """Test cases for POS manual weight configuration and behavior."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.pos_config = cls.env['pos.config'].create({
            'name': 'Test Shop Manual Weight',
        })
        cls.uom_kg = cls.env.ref('uom.product_uom_kgm')
        cls.weighable_product = cls.env['product.template'].create({
            'name': 'Test Fresh Apples',
            'type': 'consu',
            'list_price': 5.50,
            'to_weight': True,
            'uom_id': cls.uom_kg.id,
        })
        cls.regular_product = cls.env['product.template'].create({
            'name': 'Test Soft Drink',
            'type': 'consu',
            'list_price': 2.00,
            'to_weight': False,
        })

    def test_default_config_state(self):
        """Test default config has manual weight disabled."""
        self.assertFalse(self.pos_config.is_allow_manual_weight)

    def test_enable_manual_weight(self):
        """Test enabling manual weight setting on POS config."""
        self.pos_config.is_allow_manual_weight = True
        self.assertTrue(self.pos_config.is_allow_manual_weight)

    def test_res_config_settings_related_field(self):
        """Test res.config.settings writes to pos.config related field."""
        settings = self.env['res.config.settings'].create({
            'pos_config_id': self.pos_config.id,
            'pos_is_allow_manual_weight': True,
        })
        settings.execute()
        self.assertTrue(self.pos_config.is_allow_manual_weight)

        settings = self.env['res.config.settings'].create({
            'pos_config_id': self.pos_config.id,
            'pos_is_allow_manual_weight': False,
        })
        settings.execute()
        self.assertFalse(self.pos_config.is_allow_manual_weight)

    def test_weighable_product_flags(self):
        """Test that to_weight flag is set properly on products."""
        self.assertTrue(self.weighable_product.to_weight)
        self.assertFalse(self.regular_product.to_weight)
        self.assertEqual(self.weighable_product.uom_id.name, self.uom_kg.name)

    def test_pos_config_data_loading(self):
        """Test that is_allow_manual_weight is loaded into POS config data."""
        self.pos_config.is_allow_manual_weight = True
        read_records = self.env['pos.config']._load_pos_data_read(
            self.pos_config, self.pos_config,
        )
        self.assertTrue(read_records)
        self.assertTrue(read_records[0].get('is_allow_manual_weight'))
