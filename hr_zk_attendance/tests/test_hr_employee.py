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
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestHrEmployeeBiometric(TransactionCase):
    """Tests for biometric fields and actions added to hr.employee."""

    def setUp(self):
        super().setUp()
        self.employee = self.env['hr.employee'].create({
            'name': 'Biometric Test Employee',
        })
        self.device = self.env['biometric.device.details'].create({
            'name': 'Test Biometric Device',
            'device_ip': '192.0.2.10',
            'port_number': 4370,
        })

    def test_biometric_fields_can_be_assigned(self):
        """An employee can store its device ID and associated device."""
        self.employee.write({
            'device_id_num': 'EMP-100',
            'device_id': self.device.id,
        })

        self.assertEqual(self.employee.device_id_num, 'EMP-100')
        self.assertEqual(self.employee.device_id, self.device)
        self.assertFalse(self.employee.fingerprint_ids)

    def test_fingerprint_templates_are_linked_to_employee(self):
        """Fingerprint template records appear in the employee relation."""
        fingerprint = self.env['fingerprint.templates'].create({
            'employee_id': self.employee.id,
            'finger_id': '2',
            'filename': 'biometric-test-employee-finger-2',
        })

        self.assertIn(fingerprint, self.employee.fingerprint_ids)
        self.assertEqual(fingerprint.employee_id, self.employee)

    def test_action_biometric_device_opens_employee_wizard(self):
        """The employee action opens the biometric management wizard."""
        action = self.employee.action_biometric_device()

        self.assertEqual(action['type'], 'ir.actions.act_window')
        self.assertEqual(action['target'], 'new')
        self.assertEqual(action['res_model'], 'employee.biometric')
        self.assertEqual(action['view_mode'], 'form')
        self.assertEqual(
            action['context'],
            {'default_employee_id': self.employee.id},
        )
