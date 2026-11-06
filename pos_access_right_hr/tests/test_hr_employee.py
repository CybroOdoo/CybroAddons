# -*- coding: utf-8 -*-
#################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################

from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestHrEmployeePosAccess(TransactionCase):
    """Test suite for POS employee access rights restrictions."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.employee = cls.env['hr.employee'].create({
            'name': 'Test Cashier Employee',
        })
        cls.pos_config = cls.env['pos.config'].create({
            'name': 'Test POS Shop',
        })

    def test_01_default_access_rights(self):
        """Verify all POS disable flags are False by default."""
        self.assertFalse(self.employee.disable_payment)
        self.assertFalse(self.employee.disable_customer)
        self.assertFalse(self.employee.disable_plus_minus)
        self.assertFalse(self.employee.disable_numpad)
        self.assertFalse(self.employee.disable_qty)
        self.assertFalse(self.employee.disable_discount)
        self.assertFalse(self.employee.disable_price)
        self.assertFalse(self.employee.disable_remove_button)

    def test_02_configure_access_rights(self):
        """Verify updating POS disable flags on hr.employee."""
        self.employee.write({
            'disable_payment': True,
            'disable_customer': True,
            'disable_plus_minus': True,
            'disable_numpad': True,
            'disable_qty': True,
            'disable_discount': True,
            'disable_price': True,
            'disable_remove_button': True,
        })
        self.assertTrue(self.employee.disable_payment)
        self.assertTrue(self.employee.disable_customer)
        self.assertTrue(self.employee.disable_plus_minus)
        self.assertTrue(self.employee.disable_numpad)
        self.assertTrue(self.employee.disable_qty)
        self.assertTrue(self.employee.disable_discount)
        self.assertTrue(self.employee.disable_price)
        self.assertTrue(self.employee.disable_remove_button)

    def test_03_load_pos_data_fields(self):
        """Verify _load_pos_data_fields returns custom UI control flags."""
        fields = self.env['hr.employee']._load_pos_data_fields(self.pos_config.id)
        expected_fields = [
            'disable_payment',
            'disable_customer',
            'disable_plus_minus',
            'disable_numpad',
            'disable_qty',
            'disable_discount',
            'disable_price',
            'disable_remove_button',
        ]
        for field_name in expected_fields:
            self.assertIn(
                field_name,
                fields,
                f"Field '{field_name}' must be included in _load_pos_data_fields",
            )
        self.assertIn('name', fields)
        self.assertIn('user_id', fields)

    def test_04_load_pos_data_payload(self):
        """Verify _load_pos_data includes custom flags in employee payload."""
        self.employee.write({
            'disable_payment': True,
            'disable_discount': True,
        })
        config_data = self.pos_config.read(load=False)
        data = {'pos.config': {'data': config_data}}
        pos_data = self.env['hr.employee']._load_pos_data(data)
        self.assertIn('data', pos_data)
        self.assertIn('fields', pos_data)
        for field_name in [
            'disable_payment',
            'disable_customer',
            'disable_plus_minus',
            'disable_numpad',
            'disable_qty',
            'disable_discount',
            'disable_price',
            'disable_remove_button',
        ]:
            self.assertIn(field_name, pos_data['fields'])

        emp_record = next(
            (e for e in pos_data['data'] if e['id'] == self.employee.id),
            None,
        )
        if emp_record:
            self.assertTrue(emp_record.get('disable_payment'))
            self.assertTrue(emp_record.get('disable_discount'))
            self.assertFalse(emp_record.get('disable_price'))
