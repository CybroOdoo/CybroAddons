# -*- coding: utf-8 -*-

import logging

from odoo.tests import tagged
from odoo.tests.common import TransactionCase

_logger = logging.getLogger(__name__)


@tagged('post_install', '-at_install')
class TestHRMultiCompany(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.company = cls.env.company

        cls.employee = cls.env['hr.employee'].create({
            'name': 'Test Employee',
        })

        cls.attendance = cls.env['hr.attendance'].create({
            'employee_id': cls.employee.id,
            'check_in': '2026-01-01 09:00:00',
        })

        cls.salary_rule_category = cls.env[
            'hr.salary.rule.category'
        ].create({
            'name': 'Test Category',
            'code': 'TEST_CAT',
        })

    # -------------------------------------------------------------------------
    # Attendance Tests
    # -------------------------------------------------------------------------

    def test_01_attendance_company_default(self):
        _logger.info(
            "Starting TestHRMultiCompany."
            "test_01_attendance_company_default ..."
        )
        self.assertEqual(
            self.attendance.company_id,
            self.company
        )

    def test_02_attendance_company_stored(self):
        _logger.info(
            "Starting TestHRMultiCompany."
            "test_02_attendance_company_stored ..."
        )
        self.assertTrue(self.attendance.company_id)

    def test_03_attendance_company_field_exists(self):
        _logger.info(
            "Starting TestHRMultiCompany."
            "test_03_attendance_company_field_exists ..."
        )
        self.assertIn(
            'company_id',
            self.env['hr.attendance']._fields
        )

    def test_04_attendance_company_readonly(self):
        _logger.info(
            "Starting TestHRMultiCompany."
            "test_04_attendance_company_readonly ..."
        )
        field = self.env['hr.attendance']._fields['company_id']
        self.assertTrue(field.readonly)

    def test_05_attendance_company_copy_false(self):
        _logger.info(
            "Starting TestHRMultiCompany."
            "test_05_attendance_company_copy_false ..."
        )
        field = self.env['hr.attendance']._fields['company_id']
        self.assertFalse(field.copy)

    # -------------------------------------------------------------------------
    # Salary Rule Category Tests
    # -------------------------------------------------------------------------

    def test_06_salary_rule_category_company_default(self):
        _logger.info(
            "Starting TestHRMultiCompany."
            "test_06_salary_rule_category_company_default ..."
        )
        self.assertEqual(
            self.salary_rule_category.company_id,
            self.company
        )

    def test_07_salary_rule_category_company_stored(self):
        _logger.info(
            "Starting TestHRMultiCompany."
            "test_07_salary_rule_category_company_stored ..."
        )
        self.assertTrue(
            self.salary_rule_category.company_id
        )

    def test_08_salary_rule_category_field_exists(self):
        _logger.info(
            "Starting TestHRMultiCompany."
            "test_08_salary_rule_category_field_exists ..."
        )
        self.assertIn(
            'company_id',
            self.env['hr.salary.rule.category']._fields
        )

    def test_09_salary_rule_category_readonly(self):
        _logger.info(
            "Starting TestHRMultiCompany."
            "test_09_salary_rule_category_readonly ..."
        )
        field = self.env[
            'hr.salary.rule.category'
        ]._fields['company_id']
        self.assertTrue(field.readonly)

    def test_10_salary_rule_category_copy_false(self):
        _logger.info(
            "Starting TestHRMultiCompany."
            "test_10_salary_rule_category_copy_false ..."
        )
        field = self.env[
            'hr.salary.rule.category'
        ]._fields['company_id']
        self.assertFalse(field.copy)

    # -------------------------------------------------------------------------
    # Multi-company Behaviour
    # -------------------------------------------------------------------------

    def test_11_attendance_company_matches_user_company(self):
        _logger.info(
            "Starting TestHRMultiCompany."
            "test_11_attendance_company_matches_user_company ..."
        )
        self.assertEqual(
            self.attendance.company_id,
            self.env.user.company_id
        )

    def test_12_salary_rule_category_matches_user_company(self):
        _logger.info(
            "Starting TestHRMultiCompany."
            "test_12_salary_rule_category_matches_user_company ..."
        )
        self.assertEqual(
            self.salary_rule_category.company_id,
            self.env.user.company_id
        )