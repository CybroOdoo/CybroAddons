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
from odoo.fields import Command
from odoo.tests import common, new_test_user, tagged


@tagged('post_install', '-at_install')
class TestMrpProduction(common.TransactionCase):
    """ Test suite for mrp.production model extensions in serial_no_from_mo. """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company

        # Raw material component
        cls.raw_material = cls.env['product.product'].create({
            'name': 'Component Material',
            'is_storable': True,
        })

        # Product tracked by serial
        cls.product_serial = cls.env['product.product'].create({
            'name': 'Serial Tracked Finished Good',
            'is_storable': True,
            'tracking': 'serial',
            'mo_serial_digit': 4,
            'mo_serial_prefix': 'SN-PROD-',
        })

        # Product tracked by lot
        cls.product_lot = cls.env['product.product'].create({
            'name': 'Lot Tracked Finished Good',
            'is_storable': True,
            'tracking': 'lot',
            'mo_serial_digit': 3,
            'mo_serial_prefix': 'LOT-PROD-',
        })

        # Untracked product
        cls.product_untracked = cls.env['product.product'].create({
            'name': 'Untracked Finished Good',
            'is_storable': True,
            'tracking': False,
        })

        # Bills of Materials
        cls.bom_serial = cls.env['mrp.bom'].create({
            'product_tmpl_id': cls.product_serial.product_tmpl_id.id,
            'product_qty': 1.0,
            'type': 'normal',
            'bom_line_ids': [
                Command.create({'product_id': cls.raw_material.id, 'product_qty': 1.0}),
            ],
        })

        cls.bom_lot = cls.env['mrp.bom'].create({
            'product_tmpl_id': cls.product_lot.product_tmpl_id.id,
            'product_qty': 1.0,
            'type': 'normal',
            'bom_line_ids': [
                Command.create({'product_id': cls.raw_material.id, 'product_qty': 1.0}),
            ],
        })

        cls.bom_untracked = cls.env['mrp.bom'].create({
            'product_tmpl_id': cls.product_untracked.product_tmpl_id.id,
            'product_qty': 1.0,
            'type': 'normal',
            'bom_line_ids': [
                Command.create({'product_id': cls.raw_material.id, 'product_qty': 1.0}),
            ],
        })

        # Standard non-admin MRP user to ensure operations run without AccessError
        cls.user_mrp = new_test_user(
            cls.env,
            login='test_mrp_operator',
            groups='base.group_user,mrp.group_mrp_user,stock.group_stock_user',
        )

        cls.picking_type = cls.env['stock.picking.type'].search([
            ('code', '=', 'mrp_operation'),
            ('company_id', '=', cls.company.id),
        ], limit=1)

    def _create_mo(self, product, bom, qty=1.0, user=None):
        """ Helper to create a manufacturing order. """
        env = self.env(user=user) if user else self.env
        vals = {
            'product_id': product.id,
            'bom_id': bom.id,
            'product_qty': qty,
            'uom_id': product.uom_id.id,
            'company_id': self.company.id,
        }
        if self.picking_type:
            vals['picking_type_id'] = self.picking_type.id
        return env['mrp.production'].create(vals)

    def test__get_or_create_serial_sequence(self):
        """ Test _get_or_create_serial_sequence function:
        Verifies sequence creation, sudo usage, idempotency, and prefix/digit updates. """
        mo = self.env['mrp.production']
        params = self.env['ir.config_parameter'].sudo()
        # 1. Global sequence creation
        params.set_int('serial_no_from_mo.mo_serial_digit', 5)
        params.set_str('serial_no_from_mo.mo_serial_prefix', 'GLOB-')
        seq_global = mo._get_or_create_serial_sequence(
            self.product_serial, 'global', self.company
        )
        self.assertTrue(seq_global, "Global sequence should be created.")
        self.assertEqual(seq_global.code, 'mrp.production.sequence')
        self.assertEqual(seq_global.prefix, 'GLOB-')
        self.assertEqual(seq_global.padding, 5)
        # 2. Re-fetching without config change should not alter write_date unnecessarily
        seq_reloaded = mo._get_or_create_serial_sequence(
            self.product_serial, 'global', self.company
        )
        self.assertEqual(seq_global.id, seq_reloaded.id)
        # 3. Updating config alters prefix/padding on the sequence
        params.set_str('serial_no_from_mo.mo_serial_prefix', 'NEWGLOB-')
        params.set_int('serial_no_from_mo.mo_serial_digit', 6)
        seq_updated = mo._get_or_create_serial_sequence(
            self.product_serial, 'global', self.company
        )
        self.assertEqual(seq_updated.prefix, 'NEWGLOB-')
        self.assertEqual(seq_updated.padding, 6)
        # 4. Product-wise sequence creation with unique language-agnostic code
        seq_prod = mo._get_or_create_serial_sequence(
            self.product_serial, 'product_wise', self.company
        )
        expected_code = f'mrp.production.product.{self.product_serial.id}'
        self.assertEqual(seq_prod.code, expected_code)
        self.assertEqual(seq_prod.prefix, 'SN-PROD-')
        self.assertEqual(seq_prod.padding, 4)

    def test_action_confirm(self):
        """ Test action_confirm function:
        Covers global mode, product-wise mode, lot vs serial counts, preserving
        existing user-set lots, disabled config, untracked products, and execution
        by non-admin MRP user. """
        params = self.env['ir.config_parameter'].sudo()
        # 1. Global serial number generation for serial tracking with qty > 1
        params.set_bool('serial_no_from_mo.is_serial_selection', True)
        params.set_str('serial_no_from_mo.serial_selection', 'global')
        params.set_int('serial_no_from_mo.mo_serial_digit', 3)
        params.set_str('serial_no_from_mo.mo_serial_prefix', 'TEST-SN-')
        mo_global = self._create_mo(self.product_serial, self.bom_serial, qty=3.0)
        mo_global.action_confirm()
        self.assertEqual(
            len(mo_global.lot_producing_ids),
            3,
            "For serial-tracked products, 3 distinct serial numbers must be created for qty=3.",
        )
        for lot in mo_global.lot_producing_ids:
            self.assertTrue(
                lot.name.startswith('TEST-SN-'),
                f"Generated lot {lot.name} should match global prefix 'TEST-SN-'.",
            )
            self.assertEqual(lot.product_id, self.product_serial)
            self.assertEqual(lot.company_id, self.company)
        # 2. Product-wise serial generation
        params.set_str('serial_no_from_mo.serial_selection', 'product_wise')
        mo_prod = self._create_mo(self.product_serial, self.bom_serial, qty=2.0)
        mo_prod.action_confirm()
        self.assertEqual(
            len(mo_prod.lot_producing_ids),
            2,
            "2 serial numbers should be generated for qty=2 in product-wise mode.",
        )
        for lot in mo_prod.lot_producing_ids:
            self.assertTrue(
                lot.name.startswith('SN-PROD-'),
                f"Generated lot {lot.name} should match product prefix 'SN-PROD-'.",
            )
        # 3. Lot-tracked product creates exactly 1 lot regardless of quantity
        mo_lot = self._create_mo(self.product_lot, self.bom_lot, qty=5.0)
        mo_lot.action_confirm()
        self.assertEqual(
            len(mo_lot.lot_producing_ids),
            1,
            "Lot-tracked products should generate exactly 1 lot regardless of order quantity.",
        )
        self.assertTrue(mo_lot.lot_producing_ids.name.startswith('LOT-PROD-'))
        # 4. User-set lot/serial must NOT be silently overwritten
        mo_predefined = self._create_mo(self.product_serial, self.bom_serial, qty=1.0)
        manual_lot = self.env['stock.lot'].create({
            'name': 'MANUAL-SERIAL-001',
            'product_id': self.product_serial.id,
            'company_id': self.company.id,
        })
        mo_predefined.lot_producing_ids = manual_lot
        mo_predefined.action_confirm()
        self.assertEqual(
            mo_predefined.lot_producing_ids,
            manual_lot,
            "Pre-existing user-defined lot must not be overwritten upon confirmation.",
        )
        # 5. Disabled serial selection does not auto-generate lots
        params.set_bool('serial_no_from_mo.is_serial_selection', False)
        mo_disabled = self._create_mo(self.product_serial, self.bom_serial, qty=1.0)
        mo_disabled.action_confirm()

        self.assertFalse(
            mo_disabled.lot_producing_ids,
            "When serial selection is disabled, no lot/serial should be auto-generated.",
        )
        # 6. Untracked products confirm without error and generate no lots
        params.set_bool('serial_no_from_mo.is_serial_selection', True)
        mo_untracked = self._create_mo(self.product_untracked, self.bom_untracked, qty=2.0)
        mo_untracked.action_confirm()
        self.assertFalse(
            mo_untracked.lot_producing_ids,
            "Untracked products should have no lot_producing_ids.",
        )
        # 7. Non-admin MRP user confirming MO executes without AccessError on sequence creation
        mo_mrp_user = self._create_mo(
            self.product_serial, self.bom_serial, qty=1.0, user=self.user_mrp
        )
        mo_mrp_user.action_confirm()
        self.assertTrue(
            mo_mrp_user.lot_producing_ids,
            "Normal MRP user should successfully confirm and receive auto-generated serial.",
        )
