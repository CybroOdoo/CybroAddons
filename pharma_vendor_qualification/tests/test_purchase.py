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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import PharmaVendorCommon


@tagged('post_install', '-at_install')
class TestPurchase(PharmaVendorCommon):
    """QA approval of purchase orders and the AVL check."""

    def create_po(self, lines=True):
        """A draft purchase order for the API from the vendor, raised by the operator."""
        return self.env['purchase.order'].with_user(self.operator).create({
            'partner_id': self.vendor.id,
            'order_line': [(0, 0, {'product_id': self.product.id, 'product_qty': 10, 'price_unit': 5.0})] if lines else [],
        })

    def test_allowed_products_and_vendors(self):
        """Only qualified materials can be bought; no vendor means no product."""
        po = self.create_po(lines=False)
        self.assertFalse(po.allowed_product_ids)
        self.assertFalse(po.is_vendor_not_qualified)
        self.approved_qualification()
        po.invalidate_recordset()
        self.assertIn(self.product, po.allowed_product_ids)
        self.assertIn(self.vendor, po.approved_vendor_ids)
        other = self.env['product.product'].create({'name': 'Unqualified Excipient'})
        catalog = self.env['product.product'].search(po._get_product_catalog_domain())
        self.assertIn(self.product, catalog)
        self.assertNotIn(other, catalog)
        empty = self.env['purchase.order'].new({})
        self.assertFalse(empty.allowed_product_ids)
        self.assertFalse(empty.is_vendor_not_qualified)

    def test_not_qualified_vendor_flagged(self):
        """A Not Qualified vendor is flagged on the order."""
        qualification = self.scheduled_qualification()
        qualification.audit_score = 10.0
        po = self.create_po(lines=False)
        self.assertTrue(po.is_vendor_not_qualified)

    def test_approval_workflow(self):
        """Procurement submits, QA approves after the AVL check, then the order confirms."""
        po = self.create_po()
        self.assertEqual(po.pharma_po_state, 'rfq')
        # A context key sent by the client does not open the approval fields.
        with self.assertRaises(UserError):
            po.with_user(self.operator).with_context(pharma_po_workflow_action=True).write(
                {'pharma_approval_state': 'approved', 'pharma_approved_by': self.qa_user.id})
        self.assertEqual(po.pharma_approval_state, 'draft')
        with self.assertRaises(UserError):
            po.with_user(self.operator).button_confirm()
        with self.assertRaises(UserError):
            self.create_po(lines=False).with_user(self.operator).action_submit_pharma_approval()
        po.with_user(self.operator).action_submit_pharma_approval()
        self.assertEqual(po.pharma_po_state, 'waiting_approval')
        with self.assertRaises(UserError):
            po.with_user(self.operator).action_submit_pharma_approval()
        with self.assertRaises(UserError):
            po.with_user(self.operator).action_pharma_approve()
        with self.assertRaisesRegex(UserError, 'AVL Check Failed'):
            po.with_user(self.qa_user).action_pharma_approve()
        self.approved_qualification()
        po.with_user(self.qa_user).action_pharma_approve()
        self.assertEqual((po.pharma_approval_state, po.pharma_approved_by), ('approved', self.qa_user))
        with self.assertRaises(UserError):
            po.with_user(self.qa_user).action_pharma_approve()
        po.with_user(self.operator).button_confirm()
        self.assertEqual((po.state, po.pharma_po_state), ('purchase', 'purchase'))

    def test_reject_and_reset(self):
        """QA rejects a submitted order and procurement resets it to draft."""
        po = self.create_po()
        with self.assertRaises(UserError):
            po.with_user(self.qa_user).action_pharma_reject()
        po.with_user(self.operator).action_submit_pharma_approval()
        with self.assertRaises(UserError):
            po.with_user(self.operator).action_pharma_reject()
        with self.assertRaises(UserError):
            po.with_user(self.operator).action_pharma_reset_draft()
        po.with_user(self.qa_user).action_pharma_reject()
        self.assertEqual(po.pharma_approval_state, 'rejected')
        po.with_user(self.operator).action_pharma_reset_draft()
        self.assertEqual(po.pharma_approval_state, 'draft')
        po.action_rfq_send()
        po.write({'state': 'sent'})
        self.assertEqual(po.pharma_po_state, 'sent')
