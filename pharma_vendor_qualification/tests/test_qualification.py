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
from datetime import timedelta

from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import tagged

from .common import PharmaVendorCommon


@tagged('post_install', '-at_install')
class TestQualification(PharmaVendorCommon):
    """Vendor qualification workflow, scoring and AVL generation."""

    def test_create_and_constraints(self):
        """A qualification is numbered; the total score is 1-100 and caps the audit score."""
        qualification = self.create_qualification()
        self.assertTrue(qualification.name.startswith('VQ'))
        self.assertEqual(qualification.display_name, '%s - Acme Pharma Supplies' % qualification.name)
        Qualification = self.env['pharma.vendor.qualification']
        self.assertIn(qualification, Qualification.search([('display_name', 'ilike', 'Acme')]))
        self.assertIn(qualification, Qualification.search([('display_name', 'ilike', qualification.name)]))
        for total in (0.0, 120.0):
            with self.assertRaises(ValidationError):
                self.create_qualification(total_score=total)
        draft = self.env['pharma.vendor.qualification'].new({'template_id': self.template.id})
        draft._onchange_template_id()
        self.assertEqual(len(draft.response_ids), 4)

    def test_send_questionnaire(self):
        """Sending needs a template and a vendor email; it creates the responses and a token."""
        qualification = self.create_qualification()
        qualification.template_id = False
        with self.assertRaises(UserError):
            qualification.action_send_questionnaire()
        qualification.template_id = self.template
        self.vendor.email = False
        with self.assertRaises(UserError):
            qualification.action_send_questionnaire()
        self.vendor.email = 'qa@acme.example'
        qualification.action_send_questionnaire()
        self.assertEqual(qualification.status, 'questionnaire_sent')
        self.assertTrue(qualification.access_token)
        self.assertEqual(len(qualification.response_ids), 4)

    def test_schedule_audit(self):
        """The audit needs a date that is not in the past."""
        qualification = self.create_qualification()
        qualification.action_send_questionnaire()
        qualification.action_receive_documents()
        self.assertEqual(qualification.status, 'documents_received')
        with self.assertRaises(UserError):
            qualification.action_schedule_audit()
        qualification.audit_date = self.env.cr.now().date() - timedelta(days=1)
        with self.assertRaises(UserError):
            qualification.action_schedule_audit()
        with self.assertRaises(UserError):
            qualification.audit_score = 50.0
        qualification.audit_date = self.env.cr.now().date()
        qualification.action_schedule_audit()
        self.assertEqual(qualification.status, 'audit_scheduled')
        with self.assertRaises(UserError):
            qualification.total_score = 90.0

    def test_approve_creates_avl(self):
        """A passing score lets QA approve; the vendor goes on the AVL for each product."""
        qualification = self.scheduled_qualification()
        qualification.audit_score = 90.0
        with self.assertRaises(AccessError):
            qualification.with_user(self.operator).action_approve()
        qualification.with_user(self.qa_user).action_approve()
        self.assertEqual((qualification.status, qualification.approved_by), ('approved', self.qa_user))
        avl = qualification.avl_ids
        self.assertEqual((avl.vendor_id, avl.product_id, avl.status),
                         (self.vendor, self.product_tmpl, 'approved'))
        other = self.env['product.template'].create({'name': 'Lactose', 'tracking': 'lot'})
        qualification.product_ids = [(4, other.id)]
        self.assertEqual(len(qualification.avl_ids), 2)
        self.assertEqual(self.product_tmpl.avl_count, 1)
        with self.assertRaises(UserError):
            qualification.audit_score = 95.0
        with self.assertRaises(ValidationError):
            self.scheduled_qualification().audit_score = 150.0

    def test_low_score_not_qualified(self):
        """A score below the pass mark marks the vendor Not Qualified."""
        qualification = self.scheduled_qualification()
        qualification._onchange_audit_score()
        self.assertEqual(qualification.status, 'not_qualified')
        qualification = self.scheduled_qualification()
        qualification.audit_score = 40.0
        self.assertEqual(qualification.status, 'not_qualified')

    def test_approve_without_score_asks_confirmation(self):
        """Approving with no score asks QA to confirm Not Qualified."""
        qualification = self.scheduled_qualification()
        action = qualification.with_user(self.qa_user).action_approve()
        self.assertEqual(action['res_model'], 'pharma.vendor.qualification.confirm.wizard')
        wizard = self.env[action['res_model']].with_user(self.qa_user).with_context(
            **action['context']).create({})
        wizard.action_confirm_disqualify()
        self.assertEqual(qualification.status, 'not_qualified')

    def test_approve_batch(self):
        """Approving several records approves the passing ones and asks once about the rest."""
        passing, failing = self.scheduled_qualification(), self.scheduled_qualification()
        passing.audit_score = 90.0
        action = (passing | failing).with_user(self.qa_user).action_approve()
        self.assertEqual(passing.status, 'approved')
        self.assertEqual(action['context']['default_qualification_ids'], failing.ids)

    def test_reject_and_reset(self):
        """QA rejects a scheduled audit and resets it to a new draft version."""
        qualification = self.scheduled_qualification()
        with self.assertRaises(AccessError):
            qualification.with_user(self.operator).action_reject()
        qualification.with_user(self.qa_user).action_reject()
        self.assertEqual(qualification.status, 'rejected')
        with self.assertRaises(AccessError):
            qualification.with_user(self.operator).action_reset_draft()
        action = qualification.with_user(self.qa_user).action_reset_draft()
        revision = self.env['pharma.vendor.qualification'].browse(action['res_id'])
        self.assertFalse(qualification.active)
        self.assertEqual((revision.name, revision.version, revision.status),
                         (qualification.name, 2, 'draft'))
        self.assertEqual(len(revision.response_ids), 4)
        both = revision | self.create_qualification()
        action = both.with_user(self.qa_user).action_reset_draft()
        self.assertEqual(len(action['domain'][0][2]), 2)

    def test_approval_only_through_workflow(self):
        """A User cannot approve a vendor, or widen an approval, by writing to it."""
        Avl = self.env['pharma.avl']
        with self.assertRaises(UserError):
            self.env['pharma.vendor.qualification'].with_user(self.operator).create({
                'vendor_id': self.vendor.id, 'product_ids': [(6, 0, self.product_tmpl.ids)],
                'total_score': 100.0, 'status': 'approved',
            })
        with self.assertRaises(UserError):
            self.create_qualification().write(
                {'status': 'approved', 'approved_by': self.qa_user.id})
        self.assertFalse(Avl.search([('vendor_id', '=', self.vendor.id)]))
        qualification = self.approved_qualification().with_user(self.operator)
        lactose = self.env['product.template'].create({'name': 'Lactose', 'tracking': 'lot'})
        other = self.env['res.partner'].create({'name': 'Other Vendor', 'supplier_rank': 1})
        for vals in ({'product_ids': [(4, lactose.id)]}, {'vendor_id': other.id}):
            with self.assertRaises(UserError):
                qualification.write(vals)
        self.assertEqual(Avl.search([('status', '=', 'approved')]).mapped(
            lambda a: (a.vendor_id, a.product_id)), [(self.vendor, self.product_tmpl)])

    def test_create_approved(self):
        """A qualification imported as approved creates its AVL entries."""
        qualification = self.env['pharma.vendor.qualification'].create({
            'vendor_id': self.vendor.id, 'product_ids': [(6, 0, self.product_tmpl.ids)],
            'total_score': 100.0, 'status': 'approved',
        })
        self.assertEqual(qualification.avl_ids.status, 'approved')
