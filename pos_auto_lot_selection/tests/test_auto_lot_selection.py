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
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from datetime import datetime, timedelta
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestAutoLotSelection(TransactionCase):
    """Test suite for POS Auto Lot Selection (FEFO logic and draft lot tracking)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.warehouse = cls.env['stock.warehouse'].search([('company_id', '=', cls.company.id)], limit=1)
        cls.stock_location = cls.warehouse.lot_stock_id

        # Tracked product by lot/serial
        cls.product = cls.env['product.product'].create({
            'name': 'Tracked Product FEFO',
            'type': 'consu',
            'is_storable': True,
            'tracking': 'lot',
        })

        now = datetime.now()
        # Lot 1: Expiring in 10 days
        cls.lot_1 = cls.env['stock.lot'].create({
            'name': 'LOT-EXP-10D',
            'product_id': cls.product.id,
            'company_id': cls.company.id,
            'expiration_date': now + timedelta(days=10),
        })
        # Lot 2: Expiring in 3 days (earlier expiry)
        cls.lot_2 = cls.env['stock.lot'].create({
            'name': 'LOT-EXP-03D',
            'product_id': cls.product.id,
            'company_id': cls.company.id,
            'expiration_date': now + timedelta(days=3),
        })
        # Lot 3: Expiring in 20 days
        cls.lot_3 = cls.env['stock.lot'].create({
            'name': 'LOT-EXP-20D',
            'product_id': cls.product.id,
            'company_id': cls.company.id,
            'expiration_date': now + timedelta(days=20),
        })

        # Add initial quant inventory
        cls.env['stock.quant']._update_available_quantity(cls.product, cls.stock_location, 5.0, lot_id=cls.lot_1)
        cls.env['stock.quant']._update_available_quantity(cls.product, cls.stock_location, 5.0, lot_id=cls.lot_2)
        cls.env['stock.quant']._update_available_quantity(cls.product, cls.stock_location, 5.0, lot_id=cls.lot_3)

        # POS configuration
        cls.pos_config = cls.env['pos.config'].search([('company_id', '=', cls.company.id)], limit=1)
        if not cls.pos_config:
            cls.pos_config = cls.env['pos.config'].create({
                'name': 'Test POS Auto Lot',
                'company_id': cls.company.id,
            })

    def test_fefo_priority(self):
        """Verify that the lot expiring earliest (FEFO) is automatically returned first."""
        lots = self.env['stock.lot'].get_available_lots_for_pos(
            product_id=self.product.id,
            company_id=self.company.id,
            config_id=self.pos_config.id,
        )
        self.assertEqual(lots, [self.lot_2.name], "FEFO must prioritize LOT-EXP-03D over LOT-EXP-10D and LOT-EXP-20D")

    def test_used_lots_exclusion_serial_sequential(self):
        """Verify that excluded/used lots are skipped, preventing duplicate serial/lot assignment."""
        # When lot_2 is already used in a draft order
        lots = self.env['stock.lot'].get_available_lots_for_pos(
            product_id=self.product.id,
            company_id=self.company.id,
            config_id=self.pos_config.id,
            used_lots=[self.lot_2.name],
        )
        self.assertEqual(lots, [self.lot_1.name], "When lot_2 is used, lot_1 (next earliest expiry) must be picked")

        # When lot_2 and lot_1 are both used
        lots_remaining = self.env['stock.lot'].get_available_lots_for_pos(
            product_id=self.product.id,
            company_id=self.company.id,
            config_id=self.pos_config.id,
            used_lots=[self.lot_2.name, self.lot_1.name],
        )
        self.assertEqual(lots_remaining, [self.lot_3.name], "When lot_2 and lot_1 are used, lot_3 must be picked")

        # When all lots are used
        lots_none = self.env['stock.lot'].get_available_lots_for_pos(
            product_id=self.product.id,
            company_id=self.company.id,
            config_id=self.pos_config.id,
            used_lots=[self.lot_2.name, self.lot_1.name, self.lot_3.name],
        )
        self.assertEqual(lots_none, [], "When all lots are used, an empty list must be returned for fallback handling")

    def test_location_and_zero_qty_filtering(self):
        """Verify that lots with 0 quantity or in non-POS locations are not selected."""
        zero_qty_lot = self.env['stock.lot'].create({
            'name': 'LOT-ZERO-QTY',
            'product_id': self.product.id,
            'company_id': self.company.id,
            'expiration_date': datetime.now() + timedelta(days=1),
        })
        # Not creating any stock.quant for zero_qty_lot
        lots = self.env['stock.lot'].get_available_lots_for_pos(
            product_id=self.product.id,
            company_id=self.company.id,
            config_id=self.pos_config.id,
            used_lots=[self.lot_2.name, self.lot_1.name, self.lot_3.name],
        )
        self.assertNotIn(zero_qty_lot.name, lots, "Lots with zero available quantity must not be returned")
