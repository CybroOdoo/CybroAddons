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
"""Invoice multi approval test suite."""
from odoo import Command, fields
from odoo.exceptions import AccessError, UserError
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestInvoiceMultiApproval(TransactionCase):
    """Test suite for Invoice Multi Level Approval workflow"""

    @classmethod
    def setUpClass(cls):
        """Set up test environment and users for approval tests."""
        super().setUpClass()
        cls.group_approver = cls.env.ref(
            'invoice_multi_approval.group_approver'
        )
        cls.group_manager = cls.env.ref(
            'invoice_multi_approval.group_approve_manager'
        )
        cls.group_billing = cls.env.ref(
            'account.group_account_invoice'
        )

        cls.user_approver_1 = cls.env['res.users'].create({
            'name': 'Approver 1',
            'login': 'approver1',
            'email': 'approver1@test.com',
            'group_ids': [Command.set([
                cls.group_billing.id,
                cls.group_approver.id,
            ])],
        })
        cls.user_approver_2 = cls.env['res.users'].create({
            'name': 'Approver 2',
            'login': 'approver2',
            'email': 'approver2@test.com',
            'group_ids': [Command.set([
                cls.group_billing.id,
                cls.group_approver.id,
            ])],
        })
        cls.user_manager = cls.env['res.users'].create({
            'name': 'Approve Manager User',
            'login': 'approve_manager_user',
            'email': 'manager@test.com',
            'group_ids': [Command.set([
                cls.group_billing.id,
                cls.group_manager.id,
            ])],
        })

        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Partner',
        })
        cls.partner_2 = cls.env['res.partner'].create({
            'name': 'Second Test Partner',
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Test Service Product',
            'type': 'service',
        })

        cls.config = cls.env.ref(
            'invoice_multi_approval.default_invoice_multi_approval_config'
        )
        # Reset configuration for clean test isolation
        cls.config.write({
            'approve_customer_invoice': False,
            'approve_vendor_bill': False,
            'approve_customer_credit': False,
            'approve_vendor_credit': False,
            'invoice_approver_ids': [Command.clear()],
            'bill_approver_ids': [Command.clear()],
            'cust_credit_approver_ids': [Command.clear()],
            'vend_credit_approver_ids': [Command.clear()],
        })

    def _create_move(self, move_type='out_invoice'):
        """Helper to create an invoice/bill with one line"""
        return self.env['account.move'].create({
            'move_type': move_type,
            'partner_id': self.partner.id,
            'invoice_date': fields.Date.today(),
            'invoice_line_ids': [Command.create({
                'product_id': self.product.id,
                'quantity': 1,
                'price_unit': 100.0,
            })],
        })

    def test_01_default_workflow_when_approval_disabled(self):
        """When approval is disabled, invoice should post directly without
        approver lines."""
        invoice = self._create_move('out_invoice')
        self.assertFalse(
            invoice.approval_ids,
            "Approval lines should be empty when approval is disabled."
        )
        self.assertTrue(
            invoice.document_fully_approved,
            "Document should be fully approved when approval is not required."
        )
        invoice.action_post()
        self.assertEqual(invoice.state, 'posted')

    def test_02_approval_required_blocks_unapproved_posting(self):
        """When approval is enabled, posting unapproved invoice raises
        UserError."""
        self.config.write({
            'approve_customer_invoice': True,
            'invoice_approver_ids': [Command.set([self.user_approver_1.id])],
        })
        invoice = self._create_move('out_invoice')
        self.assertTrue(
            bool(invoice.approval_ids),
            "Approval lines should be populated."
        )
        self.assertFalse(
            invoice.document_fully_approved,
            "Document should not be fully approved before approval."
        )
        with self.assertRaises(UserError):
            invoice.action_post()

    def test_03_approver_approval_and_posting(self):
        """When assigned approver approves, document is fully approved and
        posts successfully."""
        self.config.write({
            'approve_customer_invoice': True,
            'invoice_approver_ids': [Command.set([self.user_approver_1.id])],
        })
        invoice = self._create_move('out_invoice')

        # Approver 1 approves
        invoice.with_user(self.user_approver_1).action_invoice_approve()
        self.assertTrue(invoice.document_fully_approved)
        invoice.action_post()
        self.assertEqual(invoice.state, 'posted')

    def test_04_multiple_approvers_order_independent(self):
        """Multiple approvers approving in reverse order should satisfy
        approval."""
        self.config.write({
            'approve_customer_invoice': True,
            'invoice_approver_ids': [Command.set([
                self.user_approver_1.id,
                self.user_approver_2.id,
            ])],
        })
        invoice = self._create_move('out_invoice')

        # Approver 2 approves first, then Approver 1
        invoice.with_user(self.user_approver_2).action_invoice_approve()
        self.assertFalse(invoice.document_fully_approved)

        invoice.with_user(self.user_approver_1).action_invoice_approve()
        self.assertTrue(invoice.document_fully_approved)
        invoice.action_post()
        self.assertEqual(invoice.state, 'posted')

    def test_05_manager_override(self):
        """Approve Manager approval immediately marks document as fully
        approved."""
        self.config.write({
            'approve_customer_invoice': True,
            'invoice_approver_ids': [Command.set([
                self.user_approver_1.id,
                self.user_approver_2.id,
            ])],
        })
        invoice = self._create_move('out_invoice')

        # Manager approves directly
        invoice.with_user(self.user_manager).action_invoice_approve()
        self.assertTrue(
            invoice.document_fully_approved,
            "Manager approval should trigger manager override."
        )
        invoice.action_post()
        self.assertEqual(invoice.state, 'posted')

    def test_06_vendor_bill_approval(self):
        """Vendor bill approval workflow verification."""
        self.config.write({
            'approve_vendor_bill': True,
            'bill_approver_ids': [Command.set([self.user_approver_1.id])],
        })
        bill = self._create_move('in_invoice')
        self.assertTrue(bool(bill.approval_ids))
        self.assertFalse(bill.document_fully_approved)

        with self.assertRaises(UserError):
            bill.action_post()

        bill.with_user(self.user_approver_1).action_invoice_approve()
        self.assertTrue(bill.document_fully_approved)
        bill.action_post()
        self.assertEqual(bill.state, 'posted')

    def test_07_customer_credit_note_approval(self):
        """Customer credit note approval workflow verification."""
        self.config.write({
            'approve_customer_credit': True,
            'cust_credit_approver_ids': [
                Command.set([self.user_approver_1.id])
            ],
        })
        credit_note = self._create_move('out_refund')
        self.assertTrue(bool(credit_note.approval_ids))
        self.assertFalse(credit_note.document_fully_approved)

        with self.assertRaises(UserError):
            credit_note.action_post()

        credit_note.with_user(self.user_approver_1).action_invoice_approve()
        self.assertTrue(credit_note.document_fully_approved)
        credit_note.action_post()
        self.assertEqual(credit_note.state, 'posted')

    def test_08_vendor_credit_note_approval(self):
        """Vendor credit note (refund) approval workflow verification."""
        self.config.write({
            'approve_vendor_credit': True,
            'vend_credit_approver_ids': [
                Command.set([self.user_approver_1.id])
            ],
        })
        refund = self._create_move('in_refund')
        self.assertTrue(bool(refund.approval_ids))
        self.assertFalse(refund.document_fully_approved)

        with self.assertRaises(UserError):
            refund.action_post()

        refund.with_user(self.user_approver_1).action_invoice_approve()
        self.assertTrue(refund.document_fully_approved)
        refund.action_post()
        self.assertEqual(refund.state, 'posted')

    def test_09_partner_onchange_preserves_approvals(self):
        """Changing partner on a draft invoice must preserve approvals
        already given."""
        self.config.write({
            'approve_customer_invoice': True,
            'invoice_approver_ids': [Command.set([
                self.user_approver_1.id,
                self.user_approver_2.id,
            ])],
        })
        invoice = self._create_move('out_invoice')

        # Approver 1 approves
        invoice.with_user(self.user_approver_1).action_invoice_approve()
        appr1_line = invoice.approval_ids.filtered(
            lambda line: line.approver_id == self.user_approver_1
        )
        self.assertTrue(appr1_line.approval_status)

        # Invoicing user changes partner
        invoice.partner_id = self.partner_2
        invoice._onchange_partner_id()

        # Approval status of Approver 1 must remain True
        appr1_line_after = invoice.approval_ids.filtered(
            lambda line: line.approver_id == self.user_approver_1
        )
        self.assertTrue(
            appr1_line_after.approval_status,
            "Partner change must not clear or reset approvals already given."
        )

    def test_10_users_approved_rpc_security(self):
        """Attempting to write users_approved directly must not bypass
        approval."""
        self.config.write({
            'approve_customer_invoice': True,
            'invoice_approver_ids': [Command.set([self.user_approver_1.id])],
        })
        invoice = self._create_move('out_invoice')
        self.assertFalse(invoice.document_fully_approved)

        # Try to forge approval via write
        invoice.write({'users_approved': True})

        # Must still block posting because users_approved is computed
        with self.assertRaises(UserError):
            invoice.action_post()

    def test_11_approver_cannot_modify_other_user_line(self):
        """An approver cannot directly modify another user's approval line."""
        self.config.write({
            'approve_customer_invoice': True,
            'invoice_approver_ids': [Command.set([
                self.user_approver_1.id,
                self.user_approver_2.id,
            ])],
        })
        invoice = self._create_move('out_invoice')
        line_user_2 = invoice.approval_ids.filtered(
            lambda line: line.approver_id == self.user_approver_2
        )

        # Approver 1 tries to approve User 2's line directly
        with self.assertRaises(UserError):
            line_user_2.with_user(self.user_approver_1).write({
                'approval_status': True
            })

    def test_12_plain_user_cannot_create_or_unlink_approval_line(self):
        """A regular user cannot create or unlink approval.line records."""
        self.config.write({
            'approve_customer_invoice': True,
            'invoice_approver_ids': [Command.set([self.user_approver_1.id])],
        })
        invoice = self._create_move('out_invoice')
        approval_line = invoice.approval_ids[:1]

        # Regular user tries to unlink approval line
        with self.assertRaises((UserError, AccessError)):
            approval_line.with_user(self.user_approver_1).unlink()

        # Regular user tries to create approval line
        with self.assertRaises((UserError, AccessError)):
            self.env['approval.line'].with_user(self.user_approver_1).create({
                'move_id': invoice.id,
                'approver_id': self.user_manager.id,
                'approval_status': True,
            })

    def test_13_empty_approval_lines_when_enabled_blocks_posting(self):
        """If approval is enabled, an invoice with no approval lines cannot post."""
        self.config.write({
            'approve_customer_invoice': True,
            'invoice_approver_ids': [Command.set([self.user_approver_1.id])],
        })
        invoice = self._create_move('out_invoice')
        # Even if approval_ids is cleared or empty, it must not be considered approved
        invoice.sudo().approval_ids = [Command.clear()]
        self.assertFalse(invoice.approval_ids)
        self.assertFalse(
            invoice.document_fully_approved,
            "Invoice with empty approval lines must not be treated as fully approved."
        )
        with self.assertRaises(UserError):
            invoice.action_post()

    def test_14_manager_not_in_list_approves_preserves_audit_trail(self):
        """A manager who is not in the approval lines list approves:
        audit trail creates a line for the manager and leaves other users' lines
        intact, while triggering manager override."""
        self.config.write({
            'approve_customer_invoice': True,
            'invoice_approver_ids': [Command.set([
                self.user_approver_1.id,
                self.user_approver_2.id,
            ])],
        })
        invoice = self._create_move('out_invoice')
        # Remove manager from approval lines if present to test manager not in list
        manager_lines = invoice.approval_ids.filtered(
            lambda line: line.approver_id == self.user_manager
        )
        if manager_lines:
            manager_lines.sudo().unlink()

        self.assertNotIn(self.user_manager, invoice.approval_ids.approver_id)

        # Manager approves
        invoice.with_user(self.user_manager).action_invoice_approve()

        # Check other users' lines are not marked as approved
        user_1_line = invoice.approval_ids.filtered(
            lambda line: line.approver_id == self.user_approver_1
        )
        user_2_line = invoice.approval_ids.filtered(
            lambda line: line.approver_id == self.user_approver_2
        )
        self.assertFalse(user_1_line.approval_status)
        self.assertFalse(user_2_line.approval_status)

        # Check manager line was created with approval_status True
        manager_line = invoice.approval_ids.filtered(
            lambda line: line.approver_id == self.user_manager
        )
        self.assertTrue(bool(manager_line))
        self.assertTrue(manager_line.approval_status)

        # Manager override is triggered
        self.assertTrue(invoice.document_fully_approved)
        invoice.action_post()
        self.assertEqual(invoice.state, 'posted')

    def test_15_regular_user_can_create_invoice_and_approval_ids_sanitized(self):
        """Regular user can create and save invoice without permission error,
        and cannot forge approval lines via create or write."""
        self.config.write({
            'approve_customer_invoice': True,
            'invoice_approver_ids': [Command.set([self.user_approver_1.id])],
        })

        # Regular billing user creates an invoice (even if UI passes approval_ids)
        invoice = self.env['account.move'].with_user(self.user_approver_1).create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'invoice_date': fields.Date.today(),
            'invoice_line_ids': [Command.create({
                'product_id': self.product.id,
                'quantity': 1,
                'price_unit': 100.0,
            })],
            # Attempt to forge an already-approved line via client payload
            'approval_ids': [Command.create({
                'approver_id': self.user_manager.id,
                'approval_status': True,
            })],
        })
        self.assertTrue(invoice.id)
        # Verify forged approval_status=True was stripped and manager line is unapproved
        manager_lines = invoice.approval_ids.filtered(
            lambda line: line.approver_id == self.user_manager
        )
        self.assertTrue(bool(manager_lines))
        self.assertFalse(manager_lines.approval_status)
        self.assertIn(self.user_approver_1, invoice.approval_ids.approver_id)
        self.assertFalse(invoice.document_fully_approved)

        # Attempt to clear approval lines via write RPC as regular user
        invoice.with_user(self.user_approver_1).write({
            'approval_ids': [Command.clear()],
        })
        # Approval lines must still be present
        self.assertTrue(invoice.approval_ids)
        self.assertFalse(invoice.document_fully_approved)
