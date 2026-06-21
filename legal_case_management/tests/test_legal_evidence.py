# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, tagged
from odoo.exceptions import UserError


@tagged('post_install', '-at_install')
class TestLegalEvidence(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.client = cls.env['res.partner'].create({
            'name': 'Evidence Client',
            'email': 'evidence@example.com',
            'phone': '0987654321'
        })
        cls.category = cls.env['case.category'].create({
            'name': 'Evidence Category'
        })
        cls.case = cls.env['case.registration'].create({
            'client_id': cls.client.id,
            'case_category_id': cls.category.id,
            'description': 'Evidence Case Description'
        })
        cls.in_favor = cls.env['res.partner'].create({
            'name': 'In Favor Client'
        })

    def test_create(self):
        """Test sequence generation on create"""
        evidence = self.env['legal.evidence'].create({
            'case_id': self.case.id,
            'in_favor_id': self.in_favor.id,
        })
        self.assertNotEqual(evidence.name, 'New')
        
        # Test creation of multiple records
        evidences = self.env['legal.evidence'].create([{
            'case_id': self.case.id,
            'in_favor_id': self.in_favor.id,
        }, {
            'case_id': self.case.id,
            'in_favor_id': self.in_favor.id,
        }])
        for e in evidences:
            self.assertNotEqual(e.name, 'New')

    def test_unlink_except_draft_or_cancel(self):
        """Test that evidence records cannot be deleted"""
        evidence = self.env['legal.evidence'].create({
            'case_id': self.case.id,
            'in_favor_id': self.in_favor.id,
        })
        with self.assertRaises(UserError):
            evidence.unlink()

    def test_compute_attachment_count(self):
        """Test the computation of attachment_count"""
        evidence = self.env['legal.evidence'].create({
            'case_id': self.case.id,
            'in_favor_id': self.in_favor.id,
        })
        self.assertEqual(evidence.attachment_count, 0)
        
        # Create an attachment
        self.env['ir.attachment'].create({
            'name': 'Test Attachment',
            'type': 'binary',
            'datas': b'dGVzdA==',
            'res_model': 'legal.evidence',
            'res_id': evidence.id,
        })
        
        # The field is computed
        evidence.invalidate_model(['attachment_count'])
        self.assertEqual(evidence.attachment_count, 1)

    def test_action_get_evidence_attachments(self):
        """Test the action to get evidence attachments"""
        evidence = self.env['legal.evidence'].create({
            'case_id': self.case.id,
            'in_favor_id': self.in_favor.id,
        })
        action = evidence.action_get_evidence_attachments()
        self.assertEqual(action['type'], 'ir.actions.act_window')
        self.assertEqual(action['res_model'], 'ir.attachment')
        self.assertEqual(action['domain'], [('res_id', '=', evidence.id), ('res_model', '=', 'legal.evidence')])
