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
from odoo import fields
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import tagged

from .common import PharmaSopCommon


@tagged('post_install', '-at_install')
class TestSop(PharmaSopCommon):
    """SOP numbering, approval, archiving and revision."""

    def test_create_numbers_and_names(self):
        """A new SOP gets a sequence code shown in its display name."""
        sop = self.create_sop()
        self.assertEqual((sop.status, sop.version, sop.author_id), ('draft', 1, self.operator))
        self.assertTrue(sop.sop_code.startswith('SOP/'))
        self.assertEqual(sop.display_name, '[%s] Granulation' % sop.sop_code)
        self.assertEqual(sop.employee_count, 1)
        self.assertEqual(sop.training_count, 0)
        unnumbered = self.env['pharma.sop'].new({'name': 'Draft', 'sop_code': 'New'})
        self.assertEqual(unnumbered.display_name, 'Draft')

    def test_constraints(self):
        """Code must be unique, employees are required, Effective needs approval."""
        sop = self.create_sop()
        with self.assertRaises(ValidationError):
            self.env['pharma.sop'].create({
                'name': 'Copy', 'sop_code': sop.sop_code, 'workcenter_id': self.workcenter.id,
                'employee_ids': [(6, 0, self.operator_employee.ids)],
            })
        with self.assertRaises(ValidationError):
            sop.employee_ids = [(5, 0, 0)]
        with self.assertRaises(ValidationError):
            sop.status = 'effective'

    def test_approve_generates_training(self):
        """QA approval makes the SOP Effective and trains each assigned employee."""
        sop = self.create_sop(employees=self.operator_employee | self.qa_employee)
        sop.action_submit_review()
        self.assertEqual(sop.status, 'review')
        with self.assertRaises(AccessError):
            sop.with_user(self.operator).action_approve()
        sop.with_user(self.qa_user).action_approve()
        self.assertEqual((sop.status, sop.approved_by), ('effective', self.qa_user))
        self.assertTrue(sop.effective_date)
        trainings = sop.training_ids
        self.assertEqual(trainings.employee_id, self.operator_employee | self.qa_employee)
        self.assertEqual(set(trainings.mapped('status')), {'pending'})
        self.assertEqual(sop.training_count, 2)
        sop._generate_training_records()
        self.assertEqual(len(sop.training_ids), 2)
        action = sop.action_view_trainings()
        self.assertEqual(action['domain'], [('sop_id', '=', sop.id)])

    def test_author_cannot_approve(self):
        """The author of an SOP cannot approve it."""
        # A QA reviewer who also writes SOPs (QA and User roles).
        qa_and_user = self.qa_user.copy({'login': 'pharma_sop_qa_and_user'})
        qa_and_user.group_ids = [(4, self.env.ref('pharmaceutical_base.group_pharma_role_user').id)]
        sop = self.env['pharma.sop'].with_user(qa_and_user).create({
            'name': 'Cleaning', 'workcenter_id': self.workcenter.id,
            'employee_ids': [(6, 0, self.operator_employee.ids)],
        })
        sop.action_submit_review()
        with self.assertRaises(ValidationError):
            sop.action_approve()

    def test_approval_only_through_workflow(self):
        """A User cannot approve, reopen or edit an SOP by writing to it."""
        approval = {'status': 'effective', 'approved_by': self.qa_user.id,
                    'effective_date': fields.Date.today()}
        with self.assertRaises(UserError):
            self.env['pharma.sop'].with_user(self.operator).create(dict(
                approval, name='Born Effective', workcenter_id=self.workcenter.id,
                employee_ids=[(6, 0, self.operator_employee.ids)]))
        sop = self.create_sop().with_user(self.operator)
        for vals in (approval, {'version': 7}):
            with self.assertRaises(UserError):
                sop.write(vals)
        with self.assertRaises(UserError):
            sop.with_user(self.qa_user).action_approve()
        sop.action_submit_review()
        with self.assertRaises(UserError):
            sop.action_submit_review()
        sop.with_user(self.qa_user).action_approve()
        for vals in ({'name': 'Changed after approval'}, {'status': 'draft'}):
            with self.assertRaises(UserError):
                sop.write(vals)
        sop.with_user(self.qa_user).action_archive_sop()
        with self.assertRaises(UserError):
            sop.with_user(self.qa_user).action_approve()
        self.assertEqual((sop.status, sop.name, sop.approved_by),
                         ('archived', 'Granulation', self.qa_user))

    def test_archive(self):
        """Only QA archives an Effective SOP."""
        sop = self.effective_sop()
        with self.assertRaises(AccessError):
            sop.with_user(self.operator).action_archive_sop()
        sop.with_user(self.qa_user).action_archive_sop()
        self.assertEqual((sop.status, sop.active), ('archived', False))

    def test_revise(self):
        """A revision archives the SOP and its training and opens a new draft version."""
        sop = self.effective_sop()
        training = self.training_of(sop)
        with self.assertRaises(AccessError):
            sop.with_user(self.operator).action_revise()
        action = sop.with_user(self.qa_user).action_revise()
        revision = self.env['pharma.sop'].browse(action['res_id'])
        self.assertEqual((sop.active, sop.status), (False, 'archived'))
        self.assertFalse(training.active)
        self.assertEqual((revision.sop_code, revision.version, revision.status),
                         (sop.sop_code, 2, 'draft'))
        self.assertFalse(revision.approved_by)
        revision.action_submit_review()
        revision.with_user(self.qa_user).action_approve()
        self.assertEqual(self.training_of(revision).status, 'pending')

    def test_revise_several_and_reset(self):
        """Revising several SOPs lists the new drafts; Return to Draft revises too."""
        sops = self.effective_sop('Granulation') | self.effective_sop('Compression')
        action = sops.with_user(self.qa_user).action_revise()
        self.assertEqual(len(action['domain'][0][2]), 2)
        review = self.create_sop('Coating')
        review.action_submit_review()
        action = review.with_user(self.qa_user).action_reset_draft()
        self.assertEqual(self.env['pharma.sop'].browse(action['res_id']).status, 'draft')

    def test_new_version_retires_prior_training(self):
        """Approving another SOP with the same code archives the prior version's training."""
        sop = self.effective_sop()
        training = self.training_of(sop)
        same_code = self.env['pharma.sop'].create({
            'name': 'Granulation v2', 'sop_code': sop.sop_code + '-B',
            'workcenter_id': self.workcenter.id,
            'employee_ids': [(6, 0, self.operator_employee.ids)],
        })
        sop.with_user(self.qa_user).action_archive_sop()
        same_code.sop_code = sop.sop_code
        same_code.action_submit_review()
        same_code.with_user(self.qa_user).action_approve()
        self.assertFalse(training.active)
        self.assertTrue(self.training_of(same_code))
