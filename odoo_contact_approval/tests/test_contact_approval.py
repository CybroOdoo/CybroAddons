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
from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import TransactionCase, tagged
from odoo.addons.odoo_contact_approval import _post_init_hook


@tagged('post_install', '-at_install')
class TestContactApproval(TransactionCase):
    """Test suite for Contact Approval workflow, permissions, and constraints."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.approval_group = cls.env.ref(
            'odoo_contact_approval.group_contacts_approval'
        )
        cls.user_group = cls.env.ref('base.group_user')

        # Create a regular internal user without approval rights
        cls.regular_user = cls.env['res.users'].create({
            'name': 'Regular Contact User',
            'login': 'regular_contact_user',
            'email': 'regular_contact_user@test.example.com',
            'group_ids': [(6, 0, [cls.user_group.id])],
        })

        cls.partner_manager_group = cls.env.ref('base.group_partner_manager')
        cls.approval_manager = cls.env['res.users'].create({
            'name': 'Approval Manager User',
            'login': 'approval_manager_user',
            'email': 'approval_manager_user@test.example.com',
            'group_ids': [(6, 0, [cls.user_group.id, cls.partner_manager_group.id, cls.approval_group.id])],
        })

        # Create partners in various states
        cls.partner_draft = cls.env['res.partner'].create({
            'name': 'Draft Test Partner',
        })

        cls.partner_approved = cls.env['res.partner'].create({
            'name': 'Approved Test Partner',
        })
        cls.partner_approved.with_user(cls.approval_manager).action_approve_contact()

        cls.partner_cancelled = cls.env['res.partner'].create({
            'name': 'Cancelled Test Partner',
        })
        cls.partner_cancelled.with_user(cls.approval_manager).action_cancel_contact()

        # Stock picking type for testing pickings
        cls.picking_type = cls.env['stock.picking.type'].search([], limit=1)

        # Ensure a sale journal exists for account.move tests
        cls.sale_journal = cls.env['account.journal'].search([
            ('type', '=', 'sale'),
            ('company_id', '=', cls.env.company.id),
        ], limit=1)
        if not cls.sale_journal:
            cls.sale_journal = cls.env['account.journal'].create({
                'name': 'Customer Invoices',
                'code': 'INV',
                'type': 'sale',
                'company_id': cls.env.company.id,
            })

        # Ensure a general journal exists for miscellaneous account.move tests
        cls.general_journal = cls.env['account.journal'].search([
            ('type', '=', 'general'),
            ('company_id', '=', cls.env.company.id),
        ], limit=1)
        if not cls.general_journal:
            cls.general_journal = cls.env['account.journal'].create({
                'name': 'Miscellaneous Operations',
                'code': 'MISC',
                'type': 'general',
                'company_id': cls.env.company.id,
            })

    def test_01_contact_approval_workflow(self):
        """Test default contact state and manager actions."""
        partner = self.env['res.partner'].create({'name': 'Workflow Partner'})
        self.assertEqual(partner.state, 'draft')
        self.assertFalse(partner.approver_id)

        # Non-manager users cannot approve, cancel, or reset
        with self.assertRaises(UserError):
            partner.with_user(self.regular_user).action_approve_contact()

        with self.assertRaises(UserError):
            partner.with_user(self.regular_user).action_cancel_contact()

        with self.assertRaises(UserError):
            partner.with_user(self.regular_user).action_reset_contact()

        # Approval manager approves
        partner.with_user(self.approval_manager).action_approve_contact()
        self.assertEqual(partner.state, 'approve')
        self.assertEqual(partner.approver_id, self.approval_manager)

        # Approval manager cancels
        partner.with_user(self.approval_manager).action_cancel_contact()
        self.assertEqual(partner.state, 'cancel')
        self.assertFalse(partner.approver_id)

        # Approval manager resets to draft
        partner.with_user(self.approval_manager).action_reset_contact()
        self.assertEqual(partner.state, 'draft')
        self.assertFalse(partner.approver_id)

    def test_02_mass_approval_and_cancel(self):
        """Test recordset batch approval and cancellation."""
        partners = self.env['res.partner'].create([
            {'name': 'Batch Partner 1'},
            {'name': 'Batch Partner 2'},
        ])
        self.assertEqual(set(partners.mapped('state')), {'draft'})

        # Batch approval
        partners.with_user(self.approval_manager).action_approve_contact()
        self.assertEqual(set(partners.mapped('state')), {'approve'})
        self.assertEqual(
            set(partners.mapped('approver_id')), {self.approval_manager}
        )

        # Batch cancel
        partners.with_user(self.approval_manager).action_cancel_contact()
        self.assertEqual(set(partners.mapped('state')), {'cancel'})
        self.assertFalse(partners.mapped('approver_id'))

    def test_03_sale_order_constraint(self):
        """Ensure Sale Orders only allow approved partners."""
        # Creating SO with draft partner must fail
        with self.assertRaises(ValidationError):
            self.env['sale.order'].create({
                'partner_id': self.partner_draft.id,
            })

        # Creating SO with cancelled partner must fail
        with self.assertRaises(ValidationError):
            self.env['sale.order'].create({
                'partner_id': self.partner_cancelled.id,
            })

        # Creating SO with approved partner must succeed
        order = self.env['sale.order'].create({
            'partner_id': self.partner_approved.id,
        })
        self.assertTrue(order.id)

        # Updating SO partner to unapproved partner must fail
        with self.assertRaises(ValidationError):
            order.write({'partner_id': self.partner_draft.id})

    def test_04_purchase_order_constraint(self):
        """Ensure Purchase Orders only allow approved vendors."""
        # Creating PO with draft partner must fail
        with self.assertRaises(ValidationError):
            self.env['purchase.order'].create({
                'partner_id': self.partner_draft.id,
            })

        # Creating PO with cancelled partner must fail
        with self.assertRaises(ValidationError):
            self.env['purchase.order'].create({
                'partner_id': self.partner_cancelled.id,
            })

        # Creating PO with approved partner must succeed
        order = self.env['purchase.order'].create({
            'partner_id': self.partner_approved.id,
        })
        self.assertTrue(order.id)

        # Updating PO partner to unapproved partner must fail
        with self.assertRaises(ValidationError):
            order.write({'partner_id': self.partner_draft.id})

    def test_05_stock_picking_constraint(self):
        """Ensure Stock Pickings only allow approved contacts."""
        if not self.picking_type:
            return

        # Creating picking with draft partner must fail
        with self.assertRaises(ValidationError):
            self.env['stock.picking'].create({
                'picking_type_id': self.picking_type.id,
                'location_id': self.picking_type.default_location_src_id.id,
                'location_dest_id': self.picking_type.default_location_dest_id.id,
                'partner_id': self.partner_draft.id,
            })

        # Creating picking with approved partner must succeed
        picking = self.env['stock.picking'].create({
            'picking_type_id': self.picking_type.id,
            'location_id': self.picking_type.default_location_src_id.id,
            'location_dest_id': self.picking_type.default_location_dest_id.id,
            'partner_id': self.partner_approved.id,
        })
        self.assertTrue(picking.id)

        # Creating picking without partner must succeed (internal transfers)
        picking_no_partner = self.env['stock.picking'].create({
            'picking_type_id': self.picking_type.id,
            'location_id': self.picking_type.default_location_src_id.id,
            'location_dest_id': self.picking_type.default_location_dest_id.id,
            'partner_id': False,
        })
        self.assertTrue(picking_no_partner.id)

    def test_06_account_move_constraint(self):
        """Ensure Account Moves only enforce approved partners on invoices, not entries/payments."""
        # Creating customer invoice with draft partner must fail
        with self.assertRaises(ValidationError):
            self.env['account.move'].create({
                'move_type': 'out_invoice',
                'partner_id': self.partner_draft.id,
            })

        # Creating customer invoice with cancelled partner must fail
        with self.assertRaises(ValidationError):
            self.env['account.move'].create({
                'move_type': 'out_invoice',
                'partner_id': self.partner_cancelled.id,
            })

        # Creating vendor bill with draft partner must fail
        with self.assertRaises(ValidationError):
            self.env['account.move'].create({
                'move_type': 'in_invoice',
                'partner_id': self.partner_draft.id,
            })

        # Creating customer invoice with approved partner must succeed
        move = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner_approved.id,
        })
        self.assertTrue(move.id)

        # Creating vendor bill with approved partner must succeed
        bill = self.env['account.move'].create({
            'move_type': 'in_invoice',
            'partner_id': self.partner_approved.id,
        })
        self.assertTrue(bill.id)

        # Creating move without partner must succeed (misc journal entry)
        misc_move = self.env['account.move'].create({
            'move_type': 'entry',
            'partner_id': False,
        })
        self.assertTrue(misc_move.id)

        # Journal entries and payments must NOT be blocked by the constraint,
        # even for draft or cancelled partners
        entry_draft = self.env['account.move'].create({
            'move_type': 'entry',
            'partner_id': self.partner_draft.id,
        })
        self.assertTrue(entry_draft.id)

        entry_cancelled = self.env['account.move'].create({
            'move_type': 'entry',
            'partner_id': self.partner_cancelled.id,
        })
        self.assertTrue(entry_cancelled.id)

    def test_07_post_init_hook(self):
        """Test that _post_init_hook migrates existing partners to approved state."""
        business_partner = self.env['res.partner'].create({
            'name': 'Pre-existing Business Customer',
        })
        self.assertEqual(business_partner.state, 'draft')

        # Execute hook to simulate data migration on installation
        _post_init_hook(self.env)
        business_partner.invalidate_recordset(['state'])

        # Pre-existing partners must be migrated to 'approve'
        self.assertEqual(business_partner.state, 'approve')

        # Existing workflows (SO, PO, picking, invoices) must now succeed without ValidationError
        so = self.env['sale.order'].create({'partner_id': business_partner.id})
        self.assertTrue(so.id)

        po = self.env['purchase.order'].create({'partner_id': business_partner.id})
        self.assertTrue(po.id)

        if self.picking_type:
            picking = self.env['stock.picking'].create({
                'picking_type_id': self.picking_type.id,
                'location_id': self.picking_type.default_location_src_id.id,
                'location_dest_id': self.picking_type.default_location_dest_id.id,
                'partner_id': business_partner.id,
            })
            self.assertTrue(picking.id)

        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': business_partner.id,
        })
        self.assertTrue(invoice.id)

        # Newly created partner after installation still defaults to 'draft'
        new_partner = self.env['res.partner'].create({
            'name': 'New Post-Install Contact',
        })
        self.assertEqual(new_partner.state, 'draft')
