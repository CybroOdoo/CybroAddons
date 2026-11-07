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
from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError, ValidationError
from odoo import fields


class TestCaseRegistration(TransactionCase):
    """Test suite for Legal Case Management module"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        # Create Client
        cls.client = cls.env['res.partner'].create({
            'name': 'Test Client',
            'email': 'client@example.com',
            'phone': '1234567890',
        })

        # Create Other Client for security tests
        cls.other_client = cls.env['res.partner'].create({
            'name': 'Other Client',
            'email': 'other@example.com',
            'phone': '0987654321',
        })

        # Create Lawyer
        cls.lawyer = cls.env['hr.employee'].create({
            'name': 'Test Lawyer',
            'is_lawyer': True,
            'wage_per_case': '1500',
            'wage_per_trial': '300',
        })

        # Create Judge
        cls.judge = cls.env['res.partner'].create({
            'name': 'Honorable Judge Smith',
        })

        # Create Court
        cls.court = cls.env['legal.court'].create({
            'name': 'District Court',
            'judge_id': cls.judge.id,
        })

        # Create Case Category
        cls.category = cls.env['case.category'].create({
            'name': 'Corporate Law',
        })

    def test_01_case_lifecycle(self):
        """Test full case lifecycle and state transitions"""
        case = self.env['case.registration'].create({
            'client_id': self.client.id,
            'lawyer_id': self.lawyer.id,
            'court_id': self.court.id,
            'case_category_id': self.category.id,
            'description': '<p>Corporate breach of contract dispute.</p>',
            'payment_method': 'case',
        })
        self.assertNotEqual(case.name, 'New')
        self.assertTrue(case.name.startswith('CASE'))
        self.assertEqual(case.state, 'draft')
        self.assertEqual(case.judge_id, self.judge)

        # Confirm case
        case.action_confirm()
        self.assertEqual(case.state, 'in_progress')

        # Win case
        case.action_won()
        self.assertEqual(case.state, 'won')
        self.assertEqual(case.end_date, fields.Date.today())

        # Reset to draft
        case.action_reset_to_draft()
        self.assertEqual(case.state, 'draft')

        # Reject case
        case.action_reject()
        self.assertEqual(case.state, 'reject')

        # Reset and cancel
        case.action_reset_to_draft()
        case.action_confirm()
        case.action_cancel()
        self.assertEqual(case.state, 'cancel')

        # Check state labels
        case_states = dict(case._fields['state'].selection)
        self.assertEqual(case_states['reject'], 'Rejected')
        self.assertEqual(case_states['cancel'], 'Cancelled')

    def test_02_evidence_and_trial_multi_create(self):
        """Test multi-creation of evidences and trials, sequences, and compute counts"""
        case = self.env['case.registration'].create({
            'client_id': self.client.id,
            'lawyer_id': self.lawyer.id,
            'court_id': self.court.id,
            'case_category_id': self.category.id,
            'description': '<p>Dispute over property.</p>',
        })

        # Multi-create Evidences with required in_favor_id
        evidences = self.env['legal.evidence'].create([
            {
                'case_id': case.id,
                'in_favor_id': self.client.id,
                'client_id': self.client.id,
                'description': 'Signed agreement copy',
            },
            {
                'case_id': case.id,
                'in_favor_id': self.client.id,
                'client_id': self.client.id,
                'description': 'Bank transfer receipts',
            }
        ])
        self.assertEqual(len(evidences), 2)
        for ev in evidences:
            self.assertNotEqual(ev.name, 'New')

        # Multi-create Trials
        trials = self.env['legal.trial'].create([
            {
                'case_id': case.id,
                'client_id': self.client.id,
                'trial_date': fields.Datetime.now(),
                'description': '<p>Preliminary hearing</p>',
            },
            {
                'case_id': case.id,
                'client_id': self.client.id,
                'trial_date': fields.Datetime.now(),
                'description': '<p>Evidence presentation</p>',
            }
        ])
        self.assertEqual(len(trials), 2)
        for tr in trials:
            self.assertNotEqual(tr.name, 'New')

        # Check compute counts on case
        case._compute_evidence_count()
        case._compute_trial_count()
        self.assertEqual(case.evidence_count, 2)
        self.assertEqual(case.trial_count, 2)

        # Smart action returns valid window action
        ev_action = case.action_get_evidence()
        self.assertEqual(ev_action['res_model'], 'legal.evidence')
        tr_action = case.action_get_trial()
        self.assertEqual(tr_action['res_model'], 'legal.trial')

    def test_03_invoicing_wizards(self):
        """Test invoice.payment and full.settlement wizards"""
        case = self.env['case.registration'].create({
            'client_id': self.client.id,
            'lawyer_id': self.lawyer.id,
            'court_id': self.court.id,
            'case_category_id': self.category.id,
            'description': '<p>Settlement case</p>',
            'payment_method': 'case',
        })
        case.action_confirm()

        # Invoice Payment Wizard
        inv_wizard = self.env['invoice.payment'].create({
            'case_id': case.id,
            'cost': 1500.0,
            'date': fields.Date.context_today(case),
        })
        inv_wizard.create_invoice(price_unit=1500.0, label='Case fee')

        case._compute_invoice_count()
        self.assertEqual(case.invoice_count, 1)

        # Full Settlement Wizard
        settlement_wizard = self.env['full.settlement'].create({
            'case_id': case.id,
            'cost': '5000',
            'date': fields.Date.context_today(case),
        })
        settlement_wizard.action_print_invoice()

        case._compute_invoice_count()
        self.assertEqual(case.invoice_count, 2)

    def test_04_legal_case_report_wizard_and_report_values(self):
        """Test legal.case.report wizard and report generation without SQL injection"""
        case1 = self.env['case.registration'].create({
            'client_id': self.client.id,
            'lawyer_id': self.lawyer.id,
            'court_id': self.court.id,
            'case_category_id': self.category.id,
            'description': '<p>Case 1 for report</p>',
            'payment_method': 'case',
            'start_date': fields.Date.today(),
        })
        case1.action_confirm()

        # Create wizard and print report
        report_wizard = self.env['legal.case.report'].create({
            'lawyer_id': self.lawyer.id,
            'client_id': self.client.id,
            'court_id': self.court.id,
            'state': 'in_progress',
        })
        action = report_wizard.action_print_report()
        self.assertIn(action.get('type'), ('ir.actions.report', 'ir.actions.act_window'))

        # Test report model _get_report_values directly
        report_model = self.env['report.legal_case_management.report_legal_case_details']
        report_data = {
            'lawyer_id': self.lawyer.name,
            'client_id': self.client.name,
            'court_id': self.court.name,
            'judge_id': False,
            'start_date': False,
            'end_date': False,
            'payment_method': False,
            'state': 'in_progress',
        }
        res = report_model._get_report_values(docids=[], data=report_data)
        self.assertIn('docs', res)
        self.assertIn('data', res)
        self.assertTrue(len(res['docs']) >= 1)
        self.assertEqual(res['docs'][0]['case_name'], case1.name)

        # Test with no filters from wizard action (regression test for wizard docids bug)
        report_wizard_no_filter = self.env['legal.case.report'].create({})
        no_filter_action = report_wizard_no_filter.action_print_report()
        no_filter_res = report_model._get_report_values(
            docids=no_filter_action.get('context', {}).get('active_ids', []),
            data=no_filter_action.get('data')
        )
        self.assertIn('docs', no_filter_res)
        self.assertTrue(len(no_filter_res['docs']) >= 1)

        # Verify wizard state selection includes 'invoiced'
        wizard_states = dict(self.env['legal.case.report']._fields['state'].selection)
        self.assertIn('invoiced', wizard_states)
        self.assertEqual(wizard_states['reject'], 'Rejected')
        self.assertEqual(wizard_states['cancel'], 'Cancelled')

    def test_05_unlink_protection(self):
        """Test deletion prevention for in_progress cases and evidence"""
        case = self.env['case.registration'].create({
            'client_id': self.client.id,
            'lawyer_id': self.lawyer.id,
            'court_id': self.court.id,
            'case_category_id': self.category.id,
            'description': '<p>Protected case</p>',
        })
        case.action_confirm()
        with self.assertRaises(UserError):
            case.unlink()

        evidence = self.env['legal.evidence'].create({
            'case_id': case.id,
            'in_favor_id': self.client.id,
            'client_id': self.client.id,
            'description': 'Important contract',
        })
        with self.assertRaises(UserError):
            evidence.unlink()

    def test_06_portal_record_rules(self):
        """Test portal record access rules"""
        from odoo import Command
        portal_group = self.env.ref('base.group_portal')
        user_client = self.env['res.users'].create({
            'name': 'Portal User Client',
            'login': 'client_portal_test@example.com',
            'partner_id': self.client.id,
            'group_ids': [Command.link(portal_group.id)],
        })
        user_other = self.env['res.users'].create({
            'name': 'Other Portal User',
            'login': 'other_portal_test@example.com',
            'partner_id': self.other_client.id,
            'group_ids': [Command.link(portal_group.id)],
        })

        case = self.env['case.registration'].create({
            'client_id': self.client.id,
            'lawyer_id': self.lawyer.id,
            'court_id': self.court.id,
            'case_category_id': self.category.id,
            'description': '<p>Portal access test case</p>',
        })

        # Client can see own case
        cases_client = self.env['case.registration'].with_user(user_client).search([('id', '=', case.id)])
        self.assertEqual(len(cases_client), 1)

        # Other client cannot see this case
        cases_other = self.env['case.registration'].with_user(user_other).search([('id', '=', case.id)])
        self.assertEqual(len(cases_other), 0)

