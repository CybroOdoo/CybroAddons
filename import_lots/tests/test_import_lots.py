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
import io

import openpyxl

from odoo import Command
from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase, new_test_user
from odoo.tools.binary import BinaryBytes


def make_xlsx(rows):
    """Return an Excel file with the sample header and the given rows."""
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.append(['Lots', 'Product', 'Quantity'])
    for row in rows:
        sheet.append(row)
    buffer = io.BytesIO()
    workbook.save(buffer)
    return BinaryBytes(buffer.getvalue())


@tagged('post_install', '-at_install')
class TestImportLots(TransactionCase):
    """Test suite for importing lots from an Excel sheet,

    covering the import wizard, the checks on the sheet content, the
    replacement of the move lines, the use of existing lots, the import
    from the stock move and the access of inventory users.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.warehouse = cls.env['stock.warehouse'].search(
            [('company_id', '=', cls.env.company.id)], limit=1)
        cls.supplier_location = cls.env.ref('stock.stock_location_suppliers')
        cls.product = cls.env['product.product'].create({
            'name': 'Test Import Lot Product',
            'default_code': 'TILP',
            'is_storable': True,
            'tracking': 'lot',
        })
        cls.other_product = cls.env['product.product'].create({
            'name': 'Test Import Lot Other',
            'is_storable': True,
            'tracking': 'lot',
        })
        cls.product_name = cls.product.display_name

    def _create_receipt(self, qty=5.0):
        """Create a confirmed receipt of the lot tracked product."""
        picking = self.env['stock.picking'].create({
            'picking_type_id': self.warehouse.in_type_id.id,
            'location_id': self.supplier_location.id,
            'location_dest_id': self.warehouse.lot_stock_id.id,
            'move_ids': [Command.create({
                'product_id': self.product.id,
                'product_uom_qty': qty,
                'location_id': self.supplier_location.id,
                'location_dest_id': self.warehouse.lot_stock_id.id,
            })],
        })
        picking.action_confirm()
        return picking

    def _import(self, move, rows, env=None):
        """Import the rows through the wizard for the given move."""
        env = env or self.env
        wizard = env['lot.attachment'].create({
            'move_id': move.id,
            'attachment': make_xlsx(rows),
        })
        return wizard.action_import_lot()

    def _get_lines(self, move):
        """Return (lot name, quantity) of the move lines."""
        return sorted(
            (line.lot_id.name or line.lot_name, line.quantity)
            for line in move.move_line_ids)

    def test_01_import_creates_move_lines(self):
        """Verify the sheet rows of the product become move lines, and rows
        of other products are ignored.
        """
        move = self._create_receipt().move_ids
        action = self._import(move, [
            ('LOT-001', self.product_name, 2),
            ('LOT-002', self.product_name, 3),
            ('LOT-OTHER', self.other_product.display_name, 4),
        ])
        self.assertEqual(action['tag'], 'reload')
        self.assertEqual(self._get_lines(move),
                         [('LOT-001', 2.0), ('LOT-002', 3.0)])

    def test_02_numeric_lot_names(self):
        """Verify numeric lot cells are imported as text."""
        move = self._create_receipt().move_ids
        self._import(move, [(1001, self.product_name, 5)])
        self.assertEqual(self._get_lines(move), [('1001', 5.0)])

    def test_03_empty_quantity_defaults_to_one(self):
        """Verify a row without quantity is imported with quantity one."""
        move = self._create_receipt().move_ids
        self._import(move, [('LOT-ONE', self.product_name, None)])
        self.assertEqual(self._get_lines(move), [('LOT-ONE', 1.0)])

    def test_04_reimport_replaces_lines(self):
        """Verify importing again replaces the previous move lines."""
        move = self._create_receipt().move_ids
        rows = [('LOT-A', self.product_name, 2)]
        self._import(move, rows)
        self._import(move, rows + [('LOT-B', self.product_name, 3)])
        self.assertEqual(self._get_lines(move),
                         [('LOT-A', 2.0), ('LOT-B', 3.0)])

    def test_05_existing_lot_is_reused(self):
        """Verify an existing lot of the product is linked to the line."""
        lot = self.env['stock.lot'].create({
            'name': 'LOT-EXISTING',
            'product_id': self.product.id,
            'company_id': self.env.company.id,
        })
        move = self._create_receipt().move_ids
        self._import(move, [('LOT-EXISTING', self.product_name, 2)])
        self.assertEqual(move.move_line_ids.lot_id, lot)
        self.assertFalse(move.move_line_ids.lot_name)

    def test_06_imported_receipt_can_be_validated(self):
        """Verify the receipt can be validated and creates the lots."""
        picking = self._create_receipt()
        self._import(picking.move_ids, [
            ('LOT-V1', self.product_name, 2),
            ('LOT-V2', self.product_name, 3),
        ])
        picking.move_ids.picked = True
        picking.button_validate()
        self.assertEqual(picking.state, 'done')
        lots = self.env['stock.lot'].search(
            [('product_id', '=', self.product.id)])
        self.assertEqual(sorted(lots.mapped('name')), ['LOT-V1', 'LOT-V2'])
        self.assertEqual(self.product.qty_available, 5.0)

    def test_07_missing_file(self):
        """Verify importing without a file is refused."""
        move = self._create_receipt().move_ids
        wizard = self.env['lot.attachment'].create({'move_id': move.id})
        with self.assertRaises(ValidationError):
            wizard.action_import_lot()

    def test_08_missing_move(self):
        """Verify importing without a stock move is refused."""
        wizard = self.env['lot.attachment'].create({
            'attachment': make_xlsx([('LOT', self.product_name, 1)]),
        })
        with self.assertRaises(UserError):
            wizard.action_import_lot()

    def test_09_invalid_file(self):
        """Verify a file which is not an Excel file is refused."""
        move = self._create_receipt().move_ids
        wizard = self.env['lot.attachment'].create({
            'move_id': move.id,
            'attachment': BinaryBytes(b'not an excel file'),
        })
        with self.assertRaises(UserError):
            wizard.action_import_lot()

    def test_10_product_not_in_sheet(self):
        """Verify a sheet without the product is refused."""
        move = self._create_receipt().move_ids
        with self.assertRaises(UserError):
            self._import(move, [
                ('LOT', self.other_product.display_name, 1)])

    def test_11_missing_lot_name(self):
        """Verify a row of the product without lot name is refused."""
        move = self._create_receipt().move_ids
        with self.assertRaises(UserError):
            self._import(move, [(None, self.product_name, 2)])
        self.assertFalse(move.move_line_ids.lot_name)

    def test_12_quantity_not_a_number(self):
        """Verify a quantity which is not a number is refused."""
        move = self._create_receipt().move_ids
        with self.assertRaises(UserError):
            self._import(move, [('LOT', self.product_name, 'two')])

    def test_13_duplicate_lot_in_sheet(self):
        """Verify a lot name repeated in the sheet is refused."""
        move = self._create_receipt().move_ids
        with self.assertRaises(UserError):
            self._import(move, [
                ('LOT-DUP', self.product_name, 1),
                ('LOT-DUP', self.product_name, 2),
            ])

    def test_14_quantity_exceeds_demand(self):
        """Verify the sheet total can not exceed the demand, including
        rows without quantity counted as one.
        """
        move = self._create_receipt(qty=2.0).move_ids
        with self.assertRaises(UserError):
            self._import(move, [('LOT-BIG', self.product_name, 3)])
        with self.assertRaises(UserError):
            self._import(move, [
                ('LOT-1', self.product_name, 2),
                ('LOT-2', self.product_name, None),
            ])

    def test_15_import_from_stock_move(self):
        """Verify the stock move import uses the wizard and its checks."""
        move = self._create_receipt().move_ids
        self.assertIsNone(move.action_import_lot())
        move.attachment = make_xlsx([('LOT-MOVE', self.product_name, 4)])
        move.action_import_lot()
        self.assertEqual(self._get_lines(move), [('LOT-MOVE', 4.0)])
        move.attachment = make_xlsx([('LOT-MOVE', self.product_name, 9)])
        with self.assertRaises(UserError):
            move.action_import_lot()

    def test_16_download_sample_action(self):
        """Verify the wizard opens the sample file download."""
        action = self.env['lot.attachment'].create(
            {}).action_download_sample()
        self.assertEqual(action['type'], 'ir.actions.act_url')
        self.assertEqual(action['url'], '/download/excel')

    def test_17_wizard_and_move_views(self):
        """Verify the wizard view and the detailed operations view load
        with the import elements.
        """
        arch = self.env['lot.attachment'].get_view(view_id=self.env.ref(
            'import_lots.lot_attachment_view_form').id)['arch']
        self.assertIn('action_import_lot', arch)
        self.assertIn('action_download_sample', arch)
        arch = self.env['stock.move'].get_view(view_id=self.env.ref(
            'stock.view_stock_move_operations').id)['arch']
        self.assertIn('import_lot', arch)

    def test_18_stock_user_can_import(self):
        """Verify an inventory user can import lots."""
        user = new_test_user(
            self.env, login='import_lots_stock_user',
            groups='base.group_user,stock.group_stock_user')
        move = self._create_receipt().move_ids
        self._import(move.with_user(user), [
            ('LOT-USER', self.product_name, 1)], env=self.env(user=user))
        self.assertEqual(self._get_lines(move), [('LOT-USER', 1.0)])
