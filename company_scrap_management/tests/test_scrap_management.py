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
"""Automated unit test suite for Scrap Management."""
from datetime import date, timedelta
from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestScrapManagement(TransactionCase):
    """Test suite for Scrap Management models, wizards, and reports."""

    @classmethod
    def setUpClass(cls):
        """Set up test environment and master data for scrap management tests."""
        super().setUpClass()
        cls.company = cls.env.company

        # Setup stock locations
        cls.internal_loc = cls.env['stock.location'].search([
            ('usage', '=', 'internal'),
            ('company_id', 'in', [cls.company.id, False])
        ], limit=1)
        if not cls.internal_loc:
            cls.internal_loc = cls.env['stock.location'].create({
                'name': 'Test Internal Location',
                'usage': 'internal',
                'company_id': cls.company.id,
            })

        cls.scrap_loc = cls.company.scrap_location_id
        if not cls.scrap_loc:
            cls.scrap_loc = cls.env['stock.location'].search([
                ('usage', '=', 'inventory'),
                ('company_id', 'in', [cls.company.id, False])
            ], limit=1)
        if not cls.scrap_loc:
            cls.scrap_loc = cls.env['stock.location'].create({
                'name': 'Test Scrap Location',
                'usage': 'inventory',
                'company_id': cls.company.id,
            })

        # Create products
        cls.product_finished = cls.env['product.product'].create({
            'name': 'Test Scrapped Machine',
            'is_storable': True,
        })
        cls.component_motor = cls.env['product.product'].create({
            'name': 'Test Component Motor',
            'is_storable': True,
        })
        cls.component_gear = cls.env['product.product'].create({
            'name': 'Test Component Gear',
            'is_storable': True,
        })
        cls.component_service = cls.env['product.product'].create({
            'name': 'Test Labor Service',
            'type': 'service',
        })

        # Create Bill of Materials (BOM)
        cls.bom = cls.env['mrp.bom'].create({
            'product_tmpl_id': cls.product_finished.product_tmpl_id.id,
            'product_qty': 1.0,
            'type': 'normal',
            'bom_line_ids': [
                (0, 0, {
                    'product_id': cls.component_motor.id,
                    'product_qty': 2.0,
                }),
                (0, 0, {
                    'product_id': cls.component_gear.id,
                    'product_qty': 5.0,
                }),
                (0, 0, {
                    'product_id': cls.component_service.id,
                    'product_qty': 1.0,
                }),
            ],
        })

    def _create_scrap_move(self, product=None, qty=2.0, reference='SCRAP/MOVE/01'):
        """Helper to create a stock move configured as a scrap order."""
        product = product or self.product_finished
        move = self.env['stock.move'].create({
            'product_id': product.id,
            'product_uom_qty': qty,
            'quantity': qty,
            'uom_id': product.uom_id.id,
            'location_id': self.internal_loc.id,
            'location_dest_id': self.scrap_loc.id,
            'is_scrap': True,
            'typ_of_reuse': 'dismantle',
            'state_management': 'none',
            'bill_of_material_id': self.bom.id,
            'reference': reference,
            'company_id': self.company.id,
        })
        move.state = 'done'
        return move

    def _create_scrap_management(self, scrap_move=None, custom_number=None):
        """Helper to create a scrap.management record."""
        scrap_move = scrap_move or self._create_scrap_move()
        vals = {
            'scrap_order_id': scrap_move.id,
            'location_id': self.internal_loc.id,
        }
        if custom_number:
            vals['scrap_management_number'] = custom_number
        return self.env['scrap.management'].create(vals)

    def test_01_scrap_management_creation_and_sequence(self):
        """Test default sequence generation, initial states and related fields."""
        scrap_move = self._create_scrap_move(qty=3.0)
        scrap_mgmt = self._create_scrap_management(scrap_move=scrap_move)

        # Sequence should be auto-assigned from ir.sequence (not 'New')
        self.assertNotEqual(scrap_mgmt.scrap_management_number, 'New')
        self.assertEqual(scrap_mgmt.state, 'draft')
        self.assertEqual(scrap_mgmt.product_id, self.product_finished)
        self.assertEqual(scrap_mgmt.bill_of_material_id, self.bom)
        self.assertEqual(scrap_mgmt.qty, 3.0)
        self.assertEqual(scrap_mgmt.display_name, scrap_mgmt.scrap_management_number)

        # Test custom sequence creation (overriding default 'New')
        custom_mgmt = self._create_scrap_management(
            scrap_move=self._create_scrap_move(reference='SCRAP/CUSTOM'),
            custom_number='CUSTOM-SCRAP-001'
        )
        self.assertEqual(custom_mgmt.scrap_management_number, 'CUSTOM-SCRAP-001')

        # Test batch creation
        move_1 = self._create_scrap_move(reference='SCRAP/BATCH/1')
        move_2 = self._create_scrap_move(reference='SCRAP/BATCH/2')
        batch_records = self.env['scrap.management'].create([
            {'scrap_order_id': move_1.id, 'location_id': self.internal_loc.id},
            {'scrap_order_id': move_2.id, 'location_id': self.internal_loc.id},
        ])
        self.assertEqual(len(batch_records), 2)
        self.assertNotEqual(batch_records[0].scrap_management_number, 'New')
        self.assertNotEqual(batch_records[1].scrap_management_number, 'New')

    def test_02_action_confirm_bom_calculation(self):
        """Test action_confirm populates lines correctly and ignores service products."""
        # Scrap order with qty 2.0
        # BOM: 2 motors (qty=2), 5 gears (qty=5), 1 service (qty=1) per 1.0 finished product
        # Expected dismantle qty: 2.0 * 2.0 = 4.0 motors, 2.0 * 5.0 = 10.0 gears
        scrap_move = self._create_scrap_move(qty=2.0)
        scrap_mgmt = self._create_scrap_management(scrap_move=scrap_move)

        scrap_mgmt.action_confirm()

        self.assertEqual(scrap_mgmt.state, 'confirm')
        self.assertEqual(len(scrap_mgmt.scrap_management_line_ids), 2)

        motor_line = scrap_mgmt.scrap_management_line_ids.filtered(
            lambda l: l.product_id == self.component_motor
        )
        gear_line = scrap_mgmt.scrap_management_line_ids.filtered(
            lambda l: l.product_id == self.component_gear
        )

        self.assertTrue(motor_line)
        self.assertEqual(motor_line.dismantle_qty, 4.0)
        self.assertTrue(gear_line)
        self.assertEqual(gear_line.dismantle_qty, 10.0)

        # Service line should not be included
        service_line = scrap_mgmt.scrap_management_line_ids.filtered(
            lambda l: l.product_id == self.component_service
        )
        self.assertFalse(service_line)

    def test_03_action_done_partial_and_full_useful(self):
        """Test action_done handles both useful and scrap components appropriately."""
        # Use a non-storable/consumable product setup to isolate move flow
        prod_parent = self.env['product.product'].create({
            'name': 'Parent Machine Consu',
            'type': 'consu',
        })
        comp_useful = self.env['product.product'].create({
            'name': 'Comp Useful Consu',
            'type': 'consu',
        })
        comp_partial = self.env['product.product'].create({
            'name': 'Comp Partial Consu',
            'type': 'consu',
        })
        bom = self.env['mrp.bom'].create({
            'product_tmpl_id': prod_parent.product_tmpl_id.id,
            'product_qty': 1.0,
            'bom_line_ids': [
                (0, 0, {'product_id': comp_useful.id, 'product_qty': 2.0}),
                (0, 0, {'product_id': comp_partial.id, 'product_qty': 4.0}),
            ],
        })

        scrap_move = self.env['stock.move'].create({
            'product_id': prod_parent.id,
            'product_uom_qty': 2.0,
            'quantity': 2.0,
            'uom_id': prod_parent.uom_id.id,
            'location_id': self.internal_loc.id,
            'location_dest_id': self.scrap_loc.id,
            'is_scrap': True,
            'typ_of_reuse': 'dismantle',
            'state_management': 'none',
            'bill_of_material_id': bom.id,
            'reference': 'SCRAP/PARTIAL/TEST',
            'company_id': self.company.id,
        })
        scrap_move.state = 'done'

        scrap_mgmt = self.env['scrap.management'].create({
            'scrap_order_id': scrap_move.id,
            'location_id': self.internal_loc.id,
        })
        scrap_mgmt.action_confirm()

        # Dismantle qty: useful=4.0, partial=8.0
        line_useful = scrap_mgmt.scrap_management_line_ids.filtered(
            lambda l: l.product_id == comp_useful
        )
        line_partial = scrap_mgmt.scrap_management_line_ids.filtered(
            lambda l: l.product_id == comp_partial
        )

        # Set 100% useful for line 1 (scrap_qty = 0)
        line_useful.useful_qty = 4.0
        # Set partial useful for line 2 (useful = 5.0, scrap_qty = 3.0)
        line_partial.useful_qty = 5.0

        scrap_mgmt.action_done()

        self.assertEqual(scrap_mgmt.state, 'done')
        self.assertEqual(scrap_move.state_management, 'dismantled')
        self.assertEqual(scrap_mgmt.date, date.today())

        # Verify moves created with scrap management origin
        moves = self.env['stock.move'].search([
            ('origin', '=', scrap_mgmt.scrap_management_number)
        ])
        self.assertTrue(moves)

    def test_04_action_done_zero_useful(self):
        """Test action_done when zero components are recoverable (100% scrap)."""
        prod_parent = self.env['product.product'].create({
            'name': 'All Scrap Parent',
            'type': 'consu',
        })
        comp = self.env['product.product'].create({
            'name': 'All Scrap Component',
            'type': 'consu',
        })
        bom = self.env['mrp.bom'].create({
            'product_tmpl_id': prod_parent.product_tmpl_id.id,
            'product_qty': 1.0,
            'bom_line_ids': [
                (0, 0, {'product_id': comp.id, 'product_qty': 3.0}),
            ],
        })

        scrap_move = self.env['stock.move'].create({
            'product_id': prod_parent.id,
            'product_uom_qty': 1.0,
            'quantity': 1.0,
            'uom_id': prod_parent.uom_id.id,
            'location_id': self.internal_loc.id,
            'location_dest_id': self.scrap_loc.id,
            'is_scrap': True,
            'typ_of_reuse': 'dismantle',
            'state_management': 'none',
            'bill_of_material_id': bom.id,
            'reference': 'SCRAP/ZERO/TEST',
            'company_id': self.company.id,
        })
        scrap_move.state = 'done'

        scrap_mgmt = self.env['scrap.management'].create({
            'scrap_order_id': scrap_move.id,
            'location_id': self.internal_loc.id,
        })
        scrap_mgmt.action_confirm()

        # useful_qty defaults to 0.0, so all 3.0 units will be scrapped
        scrap_mgmt.action_done()

        self.assertEqual(scrap_mgmt.state, 'done')
        self.assertEqual(scrap_move.state_management, 'dismantled')

    def test_05_multi_recordset_execution(self):
        """Test multi-recordset execution across action_confirm and action_done."""
        prod1 = self.env['product.product'].create({'name': 'Multi Prod 1', 'type': 'consu'})
        prod2 = self.env['product.product'].create({'name': 'Multi Prod 2', 'type': 'consu'})
        comp1 = self.env['product.product'].create({'name': 'Multi Comp 1', 'type': 'consu'})
        comp2 = self.env['product.product'].create({'name': 'Multi Comp 2', 'type': 'consu'})

        bom1 = self.env['mrp.bom'].create({
            'product_tmpl_id': prod1.product_tmpl_id.id,
            'product_qty': 1.0,
            'bom_line_ids': [(0, 0, {'product_id': comp1.id, 'product_qty': 1.0})],
        })
        bom2 = self.env['mrp.bom'].create({
            'product_tmpl_id': prod2.product_tmpl_id.id,
            'product_qty': 1.0,
            'bom_line_ids': [(0, 0, {'product_id': comp2.id, 'product_qty': 1.0})],
        })

        move1 = self.env['stock.move'].create({
            'product_id': prod1.id,
            'quantity': 1.0,
            'uom_id': prod1.uom_id.id,
            'location_id': self.internal_loc.id,
            'location_dest_id': self.scrap_loc.id,
            'is_scrap': True,
            'typ_of_reuse': 'dismantle',
            'state_management': 'none',
            'bill_of_material_id': bom1.id,
            'company_id': self.company.id,
        })
        move1.state = 'done'

        move2 = self.env['stock.move'].create({
            'product_id': prod2.id,
            'quantity': 1.0,
            'uom_id': prod2.uom_id.id,
            'location_id': self.internal_loc.id,
            'location_dest_id': self.scrap_loc.id,
            'is_scrap': True,
            'typ_of_reuse': 'dismantle',
            'state_management': 'none',
            'bill_of_material_id': bom2.id,
            'company_id': self.company.id,
        })
        move2.state = 'done'

        records = self.env['scrap.management'].create([
            {'scrap_order_id': move1.id, 'location_id': self.internal_loc.id},
            {'scrap_order_id': move2.id, 'location_id': self.internal_loc.id},
        ])

        # Multi-record confirm
        records.action_confirm()
        for rec in records:
            self.assertEqual(rec.state, 'confirm')
            self.assertEqual(len(rec.scrap_management_line_ids), 1)

        # Multi-record done
        records.action_done()
        for rec in records:
            self.assertEqual(rec.state, 'done')
            self.assertEqual(rec.scrap_order_id.state_management, 'dismantled')

    def test_06_action_product_moves(self):
        """Test action_product_moves returns proper act_window dictionary."""
        scrap_move = self._create_scrap_move()
        scrap_mgmt = self._create_scrap_management(scrap_move=scrap_move)

        action = scrap_mgmt.action_product_moves()
        self.assertEqual(action.get('type'), 'ir.actions.act_window')
        self.assertEqual(action.get('res_model'), 'stock.move.line')
        self.assertIn(('move_id.origin', '=', scrap_mgmt.scrap_management_number), action.get('domain'))

    def test_07_stock_move_scrap_fields_and_display_name(self):
        """Test stock.move display name compute and scrap helper methods."""
        # Scrap move with reference
        scrap_move = self._create_scrap_move(reference='REF-SCRAP-999')
        self.assertEqual(scrap_move.display_name, 'REF-SCRAP-999')
        self.assertEqual(scrap_move.scrap_qty, scrap_move.quantity)
        self.assertEqual(scrap_move.scrap_location_id, self.scrap_loc)

        # Standard non-scrap move
        normal_move = self.env['stock.move'].create({
            'product_id': self.product_finished.id,
            'product_uom_qty': 1.0,
            'quantity': 1.0,
            'uom_id': self.product_finished.uom_id.id,
            'location_id': self.internal_loc.id,
            'location_dest_id': self.internal_loc.id,
            'is_scrap': False,
            'company_id': self.company.id,
        })
        normal_move._compute_display_name()
        self.assertNotEqual(normal_move.display_name, 'REF-SCRAP-999')

        # Test do_scrap delegation
        res = scrap_move.do_scrap()
        self.assertTrue(res)

    def test_08_scrap_management_line_model(self):
        """Test scrap.management.line fields and relations."""
        scrap_move = self._create_scrap_move()
        scrap_mgmt = self._create_scrap_management(scrap_move=scrap_move)

        line = self.env['scrap.management.line'].create({
            'product_id': self.component_motor.id,
            'scrap_management_id': scrap_mgmt.id,
            'dismantle_qty': 10.0,
            'useful_qty': 6.0,
        })

        self.assertEqual(line.product_id, self.component_motor)
        self.assertEqual(line.scrap_management_id, scrap_mgmt)
        self.assertEqual(line.dismantle_qty, 10.0)
        self.assertEqual(line.useful_qty, 6.0)

    def test_09_wizard_report_product_wise(self):
        """Test wizard action_print_pdf with product_wise filter."""
        scrap_move = self._create_scrap_move()
        scrap_mgmt = self._create_scrap_management(scrap_move=scrap_move)
        scrap_mgmt.date = fields.Date.today()

        today = fields.Date.today()
        wizard_filtered = self.env['scrap.management.report'].create({
            'filter': 'product_wise',
            'product_ids': [(6, 0, [self.product_finished.id])],
            'from_date': today - timedelta(days=5),
            'to_date': today + timedelta(days=5),
        })
        action = wizard_filtered.action_print_pdf()
        report_name = action.get('report_name') or (
            action.get('context', {}).get('report_action', {}).get('report_name')
            if isinstance(action.get('context'), dict) else None
        )
        self.assertEqual(
            report_name,
            'company_scrap_management.report_scrap_management_product_wise'
        )

        # Test without product filter and dates
        wizard_unfiltered = self.env['scrap.management.report'].create({
            'filter': 'product_wise',
        })
        action_unfiltered = wizard_unfiltered.action_print_pdf()
        report_name_unfiltered = action_unfiltered.get('report_name') or (
            action_unfiltered.get('context', {}).get('report_action', {}).get('report_name')
            if isinstance(action_unfiltered.get('context'), dict) else None
        )
        self.assertEqual(
            report_name_unfiltered,
            'company_scrap_management.report_scrap_management_product_wise'
        )

    def test_10_wizard_report_state_wise(self):
        """Test wizard action_print_pdf with state_wise filter."""
        today = fields.Date.today()
        wizard_filtered = self.env['scrap.management.report'].create({
            'filter': 'state_wise',
            'state': 'done',
            'from_date': today - timedelta(days=5),
            'to_date': today + timedelta(days=5),
        })
        action = wizard_filtered.action_print_pdf()
        report_name = action.get('report_name') or (
            action.get('context', {}).get('report_action', {}).get('report_name')
            if isinstance(action.get('context'), dict) else None
        )
        self.assertEqual(
            report_name,
            'company_scrap_management.report_scrap_management_state_wise'
        )

        # Test without dates
        wizard_unfiltered = self.env['scrap.management.report'].create({
            'filter': 'state_wise',
            'state': 'draft',
        })
        action_unfiltered = wizard_unfiltered.action_print_pdf()
        report_name_unfiltered = action_unfiltered.get('report_name') or (
            action_unfiltered.get('context', {}).get('report_action', {}).get('report_name')
            if isinstance(action_unfiltered.get('context'), dict) else None
        )
        self.assertEqual(
            report_name_unfiltered,
            'company_scrap_management.report_scrap_management_state_wise'
        )

    def test_11_report_scrap_management_abstract_model(self):
        """Test the report.company_scrap_management.report_scrap_management _get_report_values."""
        scrap_move = self._create_scrap_move()
        scrap_mgmt = self._create_scrap_management(scrap_move=scrap_move)

        report_model = self.env['report.company_scrap_management.report_scrap_management']
        vals = report_model._get_report_values(docids=[scrap_mgmt.id])

        self.assertIn('scrap_management', vals)
        self.assertEqual(vals['scrap_management'], scrap_mgmt)

    def test_12_useful_qty_constraints(self):
        """Test validation constraints on scrap.management.line useful_qty."""
        scrap_move = self._create_scrap_move()
        scrap_mgmt = self._create_scrap_management(scrap_move=scrap_move)

        line = self.env['scrap.management.line'].create({
            'product_id': self.component_motor.id,
            'scrap_management_id': scrap_mgmt.id,
            'dismantle_qty': 5.0,
            'useful_qty': 3.0,
        })

        # Test negative useful quantity raises ValidationError
        with self.assertRaises(ValidationError):
            line.useful_qty = -1.0

        # Test useful quantity exceeding dismantle quantity raises ValidationError
        with self.assertRaises(ValidationError):
            line.useful_qty = 6.0


