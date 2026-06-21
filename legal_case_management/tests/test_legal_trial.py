# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, tagged
from odoo.exceptions import UserError
from odoo.fields import Datetime


@tagged('post_install', '-at_install')
class TestLegalTrial(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.client = cls.env['res.partner'].create({
            'name': 'Trial Client',
            'email': 'trial@example.com',
            'phone': '0987654321'
        })
        cls.category = cls.env['case.category'].create({
            'name': 'Trial Category'
        })
        cls.case = cls.env['case.registration'].create({
            'client_id': cls.client.id,
            'case_category_id': cls.category.id,
            'description': 'Trial Case Description'
        })

    def test_create(self):
        """Test sequence generation on create"""
        trial = self.env['legal.trial'].create({
            'case_id': self.case.id,
            'trial_date': Datetime.now(),
        })
        self.assertNotEqual(trial.name, 'New')
        
        # Test creation of multiple records
        trials = self.env['legal.trial'].create([{
            'case_id': self.case.id,
            'trial_date': Datetime.now(),
        }, {
            'case_id': self.case.id,
            'trial_date': Datetime.now(),
        }])
        for t in trials:
            self.assertNotEqual(t.name, 'New')

    def test_unlink_except_draft_or_cancel(self):
        """Test that trial records cannot be deleted"""
        trial = self.env['legal.trial'].create({
            'case_id': self.case.id,
            'trial_date': Datetime.now(),
        })
        with self.assertRaises(UserError):
            trial.unlink()
