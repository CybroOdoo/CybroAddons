# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, tagged
from odoo.exceptions import UserError, ValidationError
from odoo.fields import Date
from datetime import timedelta


@tagged('post_install', '-at_install')
class TestCaseRegistration(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.client = cls.env['res.partner'].create({
            'name': 'Case Client',
            'email': 'caseclient@example.com',
            'phone': '1231231234'
        })
        cls.category = cls.env['case.category'].create({
            'name': 'Criminal Case'
        })
        cls.lawyer = cls.env['hr.employee'].create({
            'name': 'Senior Lawyer',
            'is_lawyer': True,
            'wage_per_case': 5000,
            'wage_per_trial': 500,
        })
        cls.junior_lawyer = cls.env['hr.employee'].create({
            'name': 'Junior Lawyer',
            'is_lawyer': True,
            'parent_id': cls.lawyer.id,
        })
        cls.case = cls.env['case.registration'].create({
            'client_id': cls.client.id,
            'case_category_id': cls.category.id,
            'description': 'Main Test Case',
            'lawyer_id': cls.lawyer.id,
        })

    def test_onchange_payment_method(self):
        """Test that court_no_required changes based on payment method"""
        case = self.env['case.registration'].new({
            'payment_method': 'out_of_court'
        })
        case._onchange_payment_method()
        self.assertFalse(case.court_no_required)

        case.payment_method = 'trial'
        case._onchange_payment_method()
        self.assertTrue(case.court_no_required)

    def test_onchange_lawyer_id(self):
        """Test lawyer availability validation"""
        # Make the main case end date in the future to make lawyer busy
        self.case.state = 'in_progress'
        self.case.end_date = Date.today() + timedelta(days=10)

        # Create a new case in memory and set lawyer to the busy one
        new_case = self.env['case.registration'].new({
            'lawyer_id': self.lawyer.id
        })
        res = new_case._onchange_lawyer_id()
        
        # Check that warning is triggered and junior lawyer domain is returned
        self.assertTrue(new_case.lawyer_unavailable)
        self.assertTrue(self.lawyer.not_available)
        self.assertIn('warning', res)
        self.assertEqual(res['warning']['title'], 'Lawyer Unavailable')
        self.assertIn('domain', res)
        self.assertEqual(res['domain']['junior_lawyer_id'][0][2], self.lawyer.id)

    def test_unlink_except_draft_or_cancel(self):
        """Test constraints on deleting cases"""
        # In progress case cannot be deleted
        self.case.state = 'in_progress'
        with self.assertRaises(UserError):
            self.case.unlink()

        # Cancelled case can be deleted
        case_to_delete = self.env['case.registration'].create({
            'client_id': self.client.id,
            'case_category_id': self.category.id,
            'description': 'To Delete',
            'state': 'cancel'
        })
        case_to_delete.unlink()
        self.assertFalse(case_to_delete.exists())

    def test_action_full_settlement(self):
        """Test action returning full settlement wizard"""
        action = self.case.action_full_settlement()
        self.assertFalse(self.case.court_no_required)
        self.assertEqual(action['res_model'], 'full.settlement')
        self.assertEqual(action['context']['default_case_id'], self.case.id)

    def test_action_cancel_and_reset(self):
        """Test state transitions for cancel and reset"""
        self.lawyer.not_available = True
        self.case.action_cancel()
        self.assertEqual(self.case.state, 'cancel')
        self.assertEqual(self.case.end_date, Date.today())
        self.assertFalse(self.lawyer.not_available)

        self.case.action_reset_to_draft()
        self.assertEqual(self.case.state, 'draft')

    def test_action_confirm_and_reject(self):
        """Test confirm sequence generation and reject"""
        self.case.action_confirm()
        self.assertEqual(self.case.state, 'in_progress')
        self.assertNotEqual(self.case.name, 'New')

        self.case.action_reject()
        self.assertEqual(self.case.state, 'reject')

    def test_validation_case_registration(self):
        """Test lawyer presence validation"""
        case_no_lawyer = self.env['case.registration'].create({
            'client_id': self.client.id,
            'case_category_id': self.category.id,
            'description': 'No lawyer',
        })
        with self.assertRaises(ValidationError):
            case_no_lawyer.validation_case_registration()

    def test_action_invoice(self):
        """Test action_invoice wizard opening and wage logic"""
        # Test validation
        with self.assertRaises(ValidationError):
            self.case.action_invoice()

        # Test case wage
        self.case.payment_method = 'case'
        action = self.case.action_invoice()
        self.assertEqual(action['res_model'], 'invoice.payment')
        self.assertEqual(action['context']['default_cost'], str(self.lawyer.wage_per_case))

        # Test trial wage
        self.case.payment_method = 'trial'
        action = self.case.action_invoice()
        self.assertEqual(action['context']['default_cost'], str(self.lawyer.wage_per_trial))

    def test_action_evidence_and_trial(self):
        """Test window actions for adding evidence and trials"""
        action_ev = self.case.action_evidence()
        self.assertEqual(action_ev['res_model'], 'legal.evidence')
        self.assertEqual(action_ev['context']['default_case_id'], self.case.id)

        action_tr = self.case.action_trial()
        self.assertEqual(action_tr['res_model'], 'legal.trial')
        self.assertEqual(action_tr['context']['default_case_id'], self.case.id)

    def test_action_get_attachments_and_compute(self):
        """Test retrieving attachments and computing count"""
        self.env['ir.attachment'].create({
            'name': 'Case Doc',
            'type': 'binary',
            'datas': b'dGVzdA==',
            'res_model': 'case.registration',
            'res_id': self.case.id,
        })
        self.case._compute_case_attachment_count()
        self.assertEqual(self.case.case_attachment_count, 1)

        action = self.case.action_get_attachments()
        self.assertEqual(action['res_model'], 'ir.attachment')
        self.assertEqual(action['domain'], [('res_id', '=', self.case.id), ('res_model', '=', 'case.registration')])

    def test_action_won_and_lost(self):
        """Test won and lost states"""
        self.case.action_won()
        self.assertEqual(self.case.state, 'won')
        self.assertEqual(self.case.end_date, Date.today())

        self.case.action_lost()
        self.assertEqual(self.case.state, 'lost')
        self.assertEqual(self.case.end_date, Date.today())

    def test_compute_evidence_and_get(self):
        """Test evidence count and get action"""
        in_favor = self.env['res.partner'].create({'name': 'Favor'})
        self.env['legal.evidence'].create({
            'case_id': self.case.id,
            'in_favor_id': in_favor.id,
        })
        self.case._compute_evidence_count()
        self.assertEqual(self.case.evidence_count, 1)

        action = self.case.action_get_evidence()
        self.assertEqual(action['res_model'], 'legal.evidence')
        self.assertIn('domain', action)

    def test_compute_trial_and_get(self):
        """Test trial count and get action"""
        self.env['legal.trial'].create({
            'case_id': self.case.id,
            'trial_date': Date.today(),
        })
        self.case._compute_trial_count()
        self.assertEqual(self.case.trial_count, 1)

        action = self.case.action_get_trial()
        self.assertEqual(action['res_model'], 'legal.trial')
        self.assertIn('domain', action)

    def test_compute_invoice_and_get(self):
        """Test invoice count and get action"""
        self.case.action_confirm() # Generate sequence name
        self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.client.id,
            'case_ref': self.case.name,
        })
        self.case._compute_invoice_count()
        self.assertEqual(self.case.invoice_count, 1)

        action = self.case.action_get_invoice()
        self.assertEqual(action['res_model'], 'account.move')
        self.assertEqual(action['domain'], [('case_ref', '=', self.case.name)])
