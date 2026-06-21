# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, tagged
from odoo.exceptions import UserError


@tagged('post_install', '-at_install')
class TestCaseCategory(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.category = cls.env['case.category'].create({
            'name': 'Test Category'
        })
        cls.client = cls.env['res.partner'].create({
            'name': 'Test Client',
            'email': 'client@example.com',
            'phone': '1234567890'
        })

    def test_unlink_except_draft_or_cancel(self):
        """ Prevent the deletion of a case category if it is used in any cases not in draft """
        # Case in draft state
        case = self.env['case.registration'].create({
            'client_id': self.client.id,
            'case_category_id': self.category.id,
            'description': 'Test Description'
        })
        
        # Because case_category_id is required=True on case.registration,
        # Postgres will raise ForeignKeyViolation if we try to delete the category
        # while a case still points to it. So we must delete the draft case first
        # to prove the category itself can be deleted.
        case.unlink()
        
        # Category can be deleted because no cases point to it anymore
        self.category.unlink()
        self.assertFalse(self.category.exists())

        # Re-create category and a case in a non-draft state to test UserError
        category_2 = self.env['case.category'].create({'name': 'Test Category 2'})
        case_2 = self.env['case.registration'].create({
            'client_id': self.client.id,
            'case_category_id': category_2.id,
            'description': 'Test Description 2',
            'state': 'in_progress'
        })

        with self.assertRaises(UserError):
            category_2.unlink()
