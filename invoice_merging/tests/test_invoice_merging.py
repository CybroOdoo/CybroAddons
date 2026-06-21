# -*- coding: utf-8 -*-
from odoo.tests import TransactionCase, tagged
from odoo.exceptions import AccessError
from odoo import fields


@tagged('-at_install', 'post_install')
class TestInvoiceMerging(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestInvoiceMerging, cls).setUpClass()

        # Create partners
        cls.partner_a = cls.env['res.partner'].create({
            'name': 'Customer A',
        })
        cls.partner_b = cls.env['res.partner'].create({
            'name': 'Customer B',
        })

        # Create product
        cls.product = cls.env['product.product'].create({
            'name': 'Service Product',
            'lst_price': 150.0,
        })

        # Create some draft invoices
        cls.invoice_1 = cls.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': cls.partner_a.id,
            'invoice_line_ids': [
                fields.Command.create({
                    'product_id': cls.product.id,
                    'price_unit': 100.0,
                    'quantity': 2,
                })
            ]
        })

        cls.invoice_2 = cls.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': cls.partner_a.id,
            'invoice_line_ids': [
                fields.Command.create({
                    'product_id': cls.product.id,
                    'price_unit': 200.0,
                    'quantity': 1,
                })
            ]
        })

    def test_01_name_search_display_invoice_with_partner(self):
        """Test the custom name_search logic under display_invoice_with_partner context."""
        # Test without context (should use standard format)
        res_standard = self.env['account.move'].name_search(name=self.invoice_1.name)
        self.assertTrue(res_standard)

        # Test with context display_invoice_with_partner
        res_custom = self.env['account.move'].with_context(
            display_invoice_with_partner=True
        ).name_search(name=self.invoice_1.name)
        
        self.assertTrue(res_custom)
        custom_dict = dict(res_custom)
        self.assertIn(self.invoice_1.id, custom_dict)
        
        expected_name_draft = f"Draft - {self.partner_a.display_name}"
        expected_name_numbered = f"{self.invoice_1.name} - {self.partner_a.display_name}"
        self.assertIn(custom_dict[self.invoice_1.id], [expected_name_draft, expected_name_numbered])

    def test_02_action_merge_invoice_wizard_creation(self):
        """Test that action_merge_invoice on moves launches the wizard with correct inputs."""
        moves = self.invoice_1 | self.invoice_2
        action = moves.action_merge_invoice()
        
        self.assertEqual(action.get('type'), 'ir.actions.act_window')
        self.assertEqual(action.get('res_model'), 'merge.invoice')
        self.assertEqual(action.get('target'), 'new')
        
        wizard_id = action.get('res_id')
        self.assertTrue(wizard_id)
        
        wizard = self.env['merge.invoice'].browse(wizard_id)
        self.assertEqual(wizard.invoice_ids, moves)

    def test_03_exceptions_single_invoice(self):
        """Test exception when merging a single invoice."""
        wizard = self.env['merge.invoice'].create({
            'invoice_ids': [fields.Command.set([self.invoice_1.id])],
        })
        with self.assertRaises(AccessError, msg="Should raise error on single invoice"):
            wizard.action_merge_invoice()

    def test_04_exceptions_non_draft_state(self):
        """Test exception when one of the invoices is not in draft state."""
        # We simulate a posted invoice by setting state to posted (avoiding complex posting logic if possible)
        self.invoice_2.state = 'posted'
        
        wizard = self.env['merge.invoice'].create({
            'invoice_ids': [fields.Command.set([self.invoice_1.id, self.invoice_2.id])],
        })
        with self.assertRaises(AccessError, msg="Should raise error on posted invoices"):
            wizard.action_merge_invoice()
        
        # Reset state back to draft for other tests
        self.invoice_2.state = 'draft'

    def test_05_exceptions_different_move_types(self):
        """Test exception when merging moves of different types (e.g. out_invoice vs in_invoice)."""
        bill = self.env['account.move'].create({
            'move_type': 'in_invoice',
            'partner_id': self.partner_a.id,
            'invoice_line_ids': [
                fields.Command.create({
                    'product_id': self.product.id,
                    'price_unit': 50.0,
                    'quantity': 1,
                })
            ]
        })
        
        wizard = self.env['merge.invoice'].create({
            'invoice_ids': [fields.Command.set([self.invoice_1.id, bill.id])],
        })
        with self.assertRaises(AccessError, msg="Should raise error on different move types"):
            wizard.action_merge_invoice()

    def test_06_merge_to_new_invoice_cancel_others(self):
        """Test merging draft invoices into a new invoice and cancelling the original ones."""
        moves = self.invoice_1 | self.invoice_2
        wizard = self.env['merge.invoice'].create({
            'invoice_ids': [fields.Command.set(moves.ids)],
            'partner_id': self.partner_a.id,
            'merge_type': 'cancel',
        })
        
        # Track moves before wizard execution
        moves_before = self.env['account.move'].search([])
        wizard.action_merge_invoice()
        moves_after = self.env['account.move'].search([])
        
        new_moves = moves_after - moves_before
        self.assertEqual(len(new_moves), 1, "A single new account.move should be created")
        
        new_invoice = new_moves[0]
        self.assertEqual(new_invoice.partner_id, self.partner_a)
        
        # Verify lines are copied correctly
        # payment_term and tax lines are excluded, product lines are copied
        new_invoice_lines = new_invoice.line_ids.filtered(
            lambda l: l.display_type not in ['payment_term', 'tax'] and l.name != 'Automatic Balancing Line'
        )
        self.assertEqual(len(new_invoice_lines), 2, "Copied lines count should be 2")
        
        # Check values of copied lines
        prices = new_invoice_lines.mapped('price_unit')
        self.assertIn(100.0, prices)
        self.assertIn(200.0, prices)
        
        # Verify original moves are cancelled
        self.assertEqual(self.invoice_1.state, 'cancel')
        self.assertEqual(self.invoice_2.state, 'cancel')
        
        # Verify payment reference on new invoice
        expected_ref = f"Merged (Draft {self.invoice_1.id}, Draft {self.invoice_2.id})"
        self.assertEqual(new_invoice.payment_reference, expected_ref)

    def test_07_merge_to_new_invoice_keep_others(self):
        """Test merging draft invoices into a new invoice and keeping the original ones."""
        moves = self.invoice_1 | self.invoice_2
        wizard = self.env['merge.invoice'].create({
            'invoice_ids': [fields.Command.set(moves.ids)],
            'partner_id': self.partner_a.id,
            'merge_type': 'keep',
        })
        
        moves_before = self.env['account.move'].search([])
        wizard.action_merge_invoice()
        moves_after = self.env['account.move'].search([])
        
        new_invoice = (moves_after - moves_before)[0]
        
        # Verify original moves remain draft
        self.assertEqual(self.invoice_1.state, 'draft')
        self.assertEqual(self.invoice_2.state, 'draft')
        
        # Verify payment reference
        expected_ref = f"Merged (Draft {self.invoice_1.id}, Draft {self.invoice_2.id})"
        self.assertEqual(new_invoice.payment_reference, expected_ref)

    def test_08_merge_to_existing_invoice_cancel_others(self):
        """Test merging into an existing invoice and cancelling the other ones."""
        moves = self.invoice_1 | self.invoice_2
        wizard = self.env['merge.invoice'].create({
            'invoice_ids': [fields.Command.set(moves.ids)],
            'target_invoice_id': self.invoice_1.id,
            'merge_type': 'cancel',
        })
        
        moves_before = self.env['account.move'].search([])
        wizard.action_merge_invoice()
        moves_after = self.env['account.move'].search([])
        
        new_moves = moves_after - moves_before
        self.assertEqual(len(new_moves), 0, "No new invoices should be created when merging to existing")
        
        # Verify lines copied to target invoice (invoice_1)
        invoice_1_lines = self.invoice_1.line_ids.filtered(
            lambda l: l.display_type not in ['payment_term', 'tax']
        )
        self.assertEqual(len(invoice_1_lines), 2, "invoice_1 should now have 2 product/invoice lines")
        
        # Verify other invoice (invoice_2) is cancelled
        self.assertEqual(self.invoice_2.state, 'cancel')
        
        # Verify target invoice is not cancelled
        self.assertEqual(self.invoice_1.state, 'draft')
        
        # Verify payment reference
        expected_ref = f"Merged (Draft {self.invoice_1.id}, Draft {self.invoice_2.id})"
        self.assertEqual(self.invoice_1.payment_reference, expected_ref)
