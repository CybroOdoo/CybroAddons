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
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestPosSessionRestrictions(TransactionCase):
    """Test suite for pos.session.get_pos_restriction_data() method."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.POS_FIELDS = [
            'pos_allow_numpad',
            'pos_allow_payments',
            'pos_allow_discount',
            'pos_allow_qty',
            'pos_allow_price_edit',
            'pos_allow_remove_order_line',
            'pos_allow_customer_selection',
            'pos_allow_plus_minus',
        ]

        # Test user
        cls.test_user = cls.env['res.users'].create({
            'name': 'POS Session Test User',
            'login': 'pos_session_test_user',
            'email': 'pos_session_user@test.com',
            'pos_allow_payments': False,
            'pos_allow_qty': False,
        })

        # Test employee linked to user
        cls.test_employee_linked = cls.env['hr.employee'].create({
            'name': 'POS Session Test Employee Linked',
            'user_id': cls.test_user.id,
            'pos_allow_discount': False,
            'pos_allow_price_edit': False,
        })

        # Test employee without user
        cls.test_employee_unlinked = cls.env['hr.employee'].create({
            'name': 'POS Session Test Employee Unlinked',
            'user_id': False,
            'pos_allow_numpad': False,
        })

    def test_get_pos_restriction_data_structure(self):
        """Verify that get_pos_restriction_data returns a dictionary with the required top-level keys."""
        data = self.env['pos.session'].get_pos_restriction_data()

        self.assertIsInstance(data, dict, "Result should be a dictionary.")
        self.assertIn('employees', data, "Result must contain 'employees' key.")
        self.assertIn('users', data, "Result must contain 'users' key.")
        self.assertIn('emp_to_user_map', data, "Result must contain 'emp_to_user_map' key.")
        self.assertIn('advanced_ids', data, "Result must contain 'advanced_ids' key.")

    def test_get_pos_restriction_data_employee_values(self):
        """Verify that employee restrictions are correctly extracted."""
        data = self.env['pos.session'].get_pos_restriction_data()
        emp_key = str(self.test_employee_linked.id)

        self.assertIn(emp_key, data['employees'], "Linked employee should be in employees data.")
        emp_data = data['employees'][emp_key]

        # Check customized boolean values
        self.assertFalse(emp_data['pos_allow_discount'], "pos_allow_discount should be False.")
        self.assertFalse(emp_data['pos_allow_price_edit'], "pos_allow_price_edit should be False.")
        # Check default boolean values
        self.assertTrue(emp_data['pos_allow_payments'], "pos_allow_payments should be True.")
        self.assertTrue(emp_data['pos_allow_numpad'], "pos_allow_numpad should be True.")

    def test_get_pos_restriction_data_user_values(self):
        """Verify that user restrictions are correctly extracted."""
        data = self.env['pos.session'].get_pos_restriction_data()
        user_key = str(self.test_user.id)

        self.assertIn(user_key, data['users'], "Test user should be in users data.")
        user_data = data['users'][user_key]

        # Check customized boolean values
        self.assertFalse(user_data['pos_allow_payments'], "pos_allow_payments should be False.")
        self.assertFalse(user_data['pos_allow_qty'], "pos_allow_qty should be False.")
        # Check default boolean values
        self.assertTrue(user_data['pos_allow_numpad'], "pos_allow_numpad should be True.")
        self.assertTrue(user_data['pos_allow_discount'], "pos_allow_discount should be True.")

    def test_emp_to_user_map_linked_and_unlinked(self):
        """Verify that emp_to_user_map correctly maps linked employees and ignores unlinked employees."""
        data = self.env['pos.session'].get_pos_restriction_data()
        linked_emp_key = str(self.test_employee_linked.id)
        unlinked_emp_key = str(self.test_employee_unlinked.id)

        # Linked employee mapping
        self.assertIn(linked_emp_key, data['emp_to_user_map'])
        self.assertEqual(data['emp_to_user_map'][linked_emp_key], str(self.test_user.id))
        self.assertEqual(data['employees'][linked_emp_key]['user_id_int'], self.test_user.id)

        # Unlinked employee mapping
        self.assertNotIn(unlinked_emp_key, data['emp_to_user_map'])
        self.assertFalse(data['employees'][unlinked_emp_key]['user_id_int'])

    def test_no_name_field_leakage(self):
        """Verify that user/employee names are not included in get_pos_restriction_data."""
        data = self.env['pos.session'].get_pos_restriction_data()
        linked_emp_key = str(self.test_employee_linked.id)
        user_key = str(self.test_user.id)

        self.assertNotIn(
            'name',
            data['employees'][linked_emp_key],
            "Employee name must not be exposed in restriction data."
        )
        self.assertNotIn(
            'name',
            data['users'][user_key],
            "User name must not be exposed in restriction data."
        )

    def test_inactive_records_excluded(self):
        """Verify that archived employees and users are excluded from the restriction data."""
        inactive_user = self.env['res.users'].create({
            'name': 'Archived User',
            'login': 'archived_user_test',
        })
        inactive_user.write({'active': False})

        inactive_emp = self.env['hr.employee'].create({
            'name': 'Archived Employee',
        })
        inactive_emp.write({'active': False})

        data = self.env['pos.session'].get_pos_restriction_data()
        self.assertNotIn(str(inactive_user.id), data['users'])
        self.assertNotIn(str(inactive_emp.id), data['employees'])

    def test_advanced_ids_bypass_collection(self):
        """Verify that advanced employee IDs are collected from pos.config when present."""
        pos_config = self.env['pos.config'].create({'name': 'Test Config Advanced Rights'})
        if hasattr(pos_config, 'manager_employee_ids'):
            pos_config.write({
                'manager_employee_ids': [(4, self.test_employee_linked.id)],
            })
            data = self.env['pos.session'].get_pos_restriction_data()
            self.assertIn(str(self.test_employee_linked.id), data['advanced_ids'])
        elif hasattr(pos_config, 'advanced_employee_ids'):
            pos_config.write({
                'advanced_employee_ids': [(4, self.test_employee_linked.id)],
            })
            data = self.env['pos.session'].get_pos_restriction_data()
            self.assertIn(str(self.test_employee_linked.id), data['advanced_ids'])

    def test_get_pos_restriction_data_called_on_session_record(self):
        """Verify that get_pos_restriction_data can be called directly on an instantiated pos.session record."""
        pos_config = self.env['pos.config'].create({'name': 'Session Direct Config'})
        session = self.env['pos.session'].create({
            'name': 'Direct Test Session',
            'config_id': pos_config.id,
        })
        data = session.get_pos_restriction_data()
        self.assertIsInstance(data, dict)
        self.assertIn('employees', data)
        self.assertIn('users', data)
        self.assertIn('emp_to_user_map', data)
        self.assertIn('advanced_ids', data)

    def test_get_pos_restriction_data_rpc_signature_arguments(self):
        """Verify that get_pos_restriction_data accepts arbitrary args/kwargs from RPC callers without error."""
        # Test with empty list (standard RPC model call format)
        data_empty_args = self.env['pos.session'].get_pos_restriction_data([])
        self.assertIsInstance(data_empty_args, dict)

        # Test with nested list and dummy kwargs
        data_with_kwargs = self.env['pos.session'].get_pos_restriction_data([123], debug=True, context={'test': 1})
        self.assertIsInstance(data_with_kwargs, dict)

    def test_all_pos_fields_present_in_output(self):
        """Verify that all 8 POS feature permission fields exist as booleans for both employee and user."""
        data = self.env['pos.session'].get_pos_restriction_data()
        emp_key = str(self.test_employee_linked.id)
        user_key = str(self.test_user.id)

        emp_record = data['employees'][emp_key]
        user_record = data['users'][user_key]

        for field_name in self.POS_FIELDS:
            self.assertIn(field_name, emp_record, f"Field '{field_name}' must be present in employee data.")
            self.assertIsInstance(emp_record[field_name], bool, f"Field '{field_name}' in employee must be a boolean.")
            self.assertIn(field_name, user_record, f"Field '{field_name}' must be present in user data.")
            self.assertIsInstance(user_record[field_name], bool, f"Field '{field_name}' in user must be a boolean.")

    def test_user_id_parsing_formats(self):
        """Verify that get_pos_restriction_data handles various formats of user_id in employee records."""
        # 1. Normal linked employee (user_id tuple/list or int)
        data = self.env['pos.session'].get_pos_restriction_data()
        linked_key = str(self.test_employee_linked.id)
        self.assertEqual(data['employees'][linked_key]['user_id_int'], self.test_user.id)
        self.assertEqual(data['emp_to_user_map'][linked_key], str(self.test_user.id))

        # 2. Unlinked employee (user_id is False)
        unlinked_key = str(self.test_employee_unlinked.id)
        self.assertFalse(data['employees'][unlinked_key]['user_id_int'])
        self.assertNotIn(unlinked_key, data['emp_to_user_map'])
