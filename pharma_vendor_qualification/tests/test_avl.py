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
from odoo.tools import mute_logger

from .common import PharmaVendorCommon


@tagged('post_install', '-at_install')
class TestAvl(PharmaVendorCommon):
    """Approved Vendor List entries and their approval workflow."""

    def create_avl(self):
        """An AVL entry under review, created by the operator."""
        return self.env['pharma.avl'].with_user(self.operator).create({
            'vendor_id': self.vendor.id, 'product_id': self.product_tmpl.id,
        })

    def test_workflow(self):
        """Procurement submits, the QA Director approves, blocks and resets."""
        avl = self.create_avl()
        self.assertEqual(avl.display_name, 'Paracetamol API / Acme Pharma Supplies')
        for term in ('Acme', 'Paracetamol'):
            self.assertIn(avl, self.env['pharma.avl'].search([('display_name', 'ilike', term)]))
        with self.assertRaises(UserError):
            avl.with_user(self.qa_user).action_approve()
        avl.with_user(self.operator).action_submit()
        self.assertEqual(avl.status, 'pending_approval')
        with self.assertRaises(UserError):
            avl.with_user(self.operator).action_submit_review()
        with self.assertRaises(UserError):
            avl.with_user(self.operator).action_approve()
        avl.with_user(self.qa_user).action_approve()
        self.assertEqual((avl.status, avl.approved_by), ('approved', self.qa_user))
        with self.assertRaises(UserError):
            avl.with_user(self.operator).action_block()
        avl.with_user(self.qa_user).action_block()
        self.assertEqual((avl.status, avl.approved_by.id), ('blocked', False))
        with self.assertRaises(UserError):
            avl.with_user(self.operator).action_reset()
        avl.with_user(self.qa_user).action_reset()
        self.assertEqual(avl.status, 'under_review')

    def test_approval_only_through_workflow(self):
        """A User cannot put a vendor on the AVL by writing to it."""
        with self.assertRaises(UserError):
            self.env['pharma.avl'].with_user(self.operator).create({
                'vendor_id': self.vendor.id, 'product_id': self.product_tmpl.id,
                'status': 'approved', 'approved_by': self.qa_user.id,
            })
        avl = self.create_avl()
        with self.assertRaises(UserError):
            avl.write({'status': 'approved', 'approved_by': self.qa_user.id})
        avl.action_submit()
        avl.with_user(self.qa_user).action_approve()
        other = self.env['res.partner'].create({'name': 'Other Vendor', 'supplier_rank': 1})
        with self.assertRaises(UserError):
            avl.write({'vendor_id': other.id})
        self.assertEqual((avl.status, avl.vendor_id), ('approved', self.vendor))

    def test_unique_vendor_product(self):
        """A vendor appears once per product."""
        self.create_avl()
        with mute_logger('odoo.sql_db'), self.assertRaises(Exception):
            self.create_avl()
        self.assertEqual(self.env['pharma.avl'].new({}).display_name, 'New AVL')
