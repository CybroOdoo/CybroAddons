# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, tagged
from odoo.exceptions import UserError


@tagged('post_install', '-at_install')
class TestLegalCourt(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.judge = cls.env['res.partner'].create({
            'name': 'Judge Judy',
        })
        cls.court = cls.env['legal.court'].create({
            'name': 'Supreme Court',
            'judge_id': cls.judge.id,
        })
        cls.client = cls.env['res.partner'].create({
            'name': 'Court Client',
            'email': 'client@court.com',
            'phone': '1112223333'
        })
        cls.category = cls.env['case.category'].create({
            'name': 'Court Category'
        })

    def test_onchange_judge_id(self):
        """Test onchange method updates judge partner fields"""
        court = self.env['legal.court'].new({
            'name': 'High Court',
        })
        court.judge_id = self.judge.id
        court._onchange_judge_id()
        self.assertTrue(self.judge.is_judge)
        self.assertTrue(self.judge.is_judge_unavailable)

    def test_unlink_except_draft_or_cancel(self):
        """Test that court cannot be deleted if linked to a non-draft case"""
        case = self.env['case.registration'].create({
            'client_id': self.client.id,
            'case_category_id': self.category.id,
            'court_id': self.court.id,
            'description': 'Test Court Case',
        })

        self.court.unlink()
        self.assertFalse(self.court.exists())

        court_2 = self.env['legal.court'].create({'name': 'District Court'})
        case_2 = self.env['case.registration'].create({
            'client_id': self.client.id,
            'case_category_id': self.category.id,
            'court_id': court_2.id,
            'description': 'Test Court Case 2',
            'state': 'in_progress'
        })

        with self.assertRaises(UserError):
            court_2.unlink()
