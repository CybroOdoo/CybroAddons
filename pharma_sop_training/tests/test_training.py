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

from lxml import etree

from odoo import fields
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import tagged

from .common import PharmaSopCommon


@tagged('post_install', '-at_install')
class TestTraining(PharmaSopCommon):
    """Training assessment, re-take, expiry and sign-off clearance."""

    @classmethod
    def setUpClass(cls):
        """An Effective SOP with a pending training for the operator."""
        super().setUpClass()
        cls.sop = cls.effective_sop()

    def test_name_and_uniqueness(self):
        """The record is named after employee and SOP; one active record per pair."""
        training = self.training_of(self.sop)
        self.assertEqual(training.training_name, 'Pharma Operator / Granulation')
        self.assertEqual(self.env['pharma.training'].new({}).training_name, 'New Training')
        with self.assertRaises(ValidationError):
            self.env['pharma.training'].create({
                'sop_id': self.sop.id, 'employee_id': self.operator_employee.id,
            })

    def test_score_limits(self):
        """Total score is 1-100 and the score lies between 0 and the total."""
        training = self.training_of(self.sop)
        for vals in ({'total_score': 0.0}, {'total_score': 120.0},
                     {'score': -1.0}, {'score': 101.0}):
            with self.assertRaises(ValidationError):
                training.write(vals)

    def test_record_assessment(self):
        """QA records the score; the passing percentage decides the result."""
        training = self.training_of(self.sop)
        with self.assertRaises(ValidationError):
            training.with_user(self.qa_user).action_record_assessment()
        training.score = 50.0
        with self.assertRaises(AccessError):
            training.with_user(self.operator).action_record_assessment()
        training.with_user(self.qa_user).action_record_assessment()
        self.assertEqual((training.status, training.assessor_id), ('failed', self.qa_user))
        self.pass_training(training, 80.0)
        self.assertEqual(training.status, 'passed')
        self.assertEqual(training.completed_on, fields.Date.today())

    def test_result_set_by_qa_only(self):
        """A trainee cannot pass their own training or change a passed one."""
        Training = self.env['pharma.training']
        training = self.training_of(self.sop).with_user(self.operator)
        with self.assertRaises(UserError):
            training.write({'status': 'passed', 'score': 100.0})
        with self.assertRaises(ValidationError):
            Training.check_training_clearance(self.operator.id, self.sop.ids)
        # The trainee cannot grade the assessment: score and total are QA's.
        for vals in ({'score': 95.0}, {'total_score': 10.0}):
            with self.assertRaises(UserError):
                training.write(vals)
        for user, editable in ((self.operator, False), (self.qa_user, True)):
            arch = etree.fromstring(Training.with_user(user).get_views(
                [(False, 'form')])['views']['form']['arch'])
            score = arch.xpath("//field[@name='score']")
            self.assertEqual(len(score), 1)
            self.assertEqual(score[0].get('readonly') not in ('1', 'True'), editable)
        training = training.with_user(self.qa_user)
        self.pass_training(training)
        training = training.with_user(self.operator)
        for vals in ({'expiry_date': '2099-12-31'}, {'score': 1.0},
                     {'employee_id': self.qa_employee.id}, {'status': 'pending'}):
            with self.assertRaises(UserError):
                training.write(vals)
        with self.assertRaises(UserError):
            training.with_user(self.qa_user).action_record_assessment()
        self.assertEqual((training.status, training.score, training.employee_id),
                         ('passed', 90.0, self.operator_employee))

    def test_retake(self):
        """A re-take archives the record and opens a new pending attempt."""
        training = self.training_of(self.sop)
        self.pass_training(training)
        with self.assertRaises(AccessError):
            training.with_user(self.operator).action_retake()
        action = training.with_user(self.qa_user).action_retake()
        retake = self.env['pharma.training'].browse(action['res_id'])
        self.assertFalse(training.active)
        self.assertEqual((retake.status, retake.version, retake.score), ('pending', 2, 0.0))
        other = self.effective_sop('Compression')
        both = retake | self.training_of(other)
        action = both.with_user(self.qa_user).action_retake()
        self.assertEqual(len(action['domain'][0][2]), 2)

    def test_cron_expiry(self):
        """The daily cron expires passed training past its expiry date."""
        training = self.training_of(self.sop)
        self.pass_training(training)
        training.expiry_date = fields.Date.today() - timedelta(days=1)
        self.env['pharma.training']._cron_expire_trainings()
        self.assertEqual(training.status, 'expired')

    def test_clearance(self):
        """Sign-off needs passed, current training; untracked users are not checked."""
        Training = self.env['pharma.training']
        sop_ids = self.sop.ids
        self.assertTrue(Training.check_training_clearance(self.env.user.id, sop_ids))
        self.assertTrue(Training.check_training_clearance(self.operator.id))
        with self.assertRaises(ValidationError):
            Training.check_training_clearance(self.operator.id, sop_ids)
        training = self.training_of(self.sop)
        self.pass_training(training)
        self.assertTrue(Training.check_training_clearance(self.operator.id, sop_ids))
        training.expiry_date = fields.Date.today() - timedelta(days=1)
        with self.assertRaisesRegex(ValidationError, 'has expired'):
            Training.check_training_clearance(self.operator.id, sop_ids)
