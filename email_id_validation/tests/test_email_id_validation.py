###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL-3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL-3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC
#    LICENSE (LGPL-3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
"""Unit tests for email_id_validation module."""
from unittest.mock import patch

from email_validator import EmailNotValidError

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install', 'email_id_validation')
class TestEmailIdValidation(TransactionCase):
    """Test suite for partner and employee email validation."""

    def test_partner_valid_email(self):
        """Verify partner creation and update with valid email."""
        partner = self.env['res.partner'].create({
            'name': 'Valid Partner',
            'email': 'valid.test@gmail.com',
        })
        self.assertEqual(partner.email, 'valid.test@gmail.com')

        # Test updating to another valid email
        partner.write({'email': 'updated.test@gmail.com'})
        self.assertEqual(partner.email, 'updated.test@gmail.com')

    def test_partner_empty_email(self):
        """Verify partner creation with empty/False email succeeds."""
        partner = self.env['res.partner'].create({
            'name': 'Partner Without Email',
            'email': False,
        })
        self.assertFalse(partner.email)

    def test_partner_invalid_email_syntax(self):
        """Verify partner creation with malformed email raises validation."""
        with self.assertRaises(ValidationError):
            self.env['res.partner'].create({
                'name': 'Invalid Partner',
                'email': 'not-an-email',
            })

    def test_partner_invalid_email_update(self):
        """Verify updating existing partner with invalid email raises error."""
        partner = self.env['res.partner'].create({
            'name': 'Valid Partner Initially',
            'email': 'valid.init@gmail.com',
        })
        with self.assertRaises(ValidationError):
            partner.write({'email': 'bad_email@'})

    def test_partner_mocked_deliverability_error(self):
        """Verify deliverability error handling for res.partner."""
        with patch(
            'odoo.addons.email_id_validation.models.res_partner.validate_email',
            side_effect=EmailNotValidError('Domain does not accept email'),
        ):
            with self.assertRaises(ValidationError) as exc:
                self.env['res.partner'].create({
                    'name': 'Deliverability Fail',
                    'email': 'user@undeliverable.org',
                })
            self.assertIn('Domain does not accept email', str(exc.exception))

    def test_employee_valid_work_email(self):
        """Verify employee creation and update with valid work email."""
        employee = self.env['hr.employee'].create({
            'name': 'Valid Employee',
            'work_email': 'valid.emp@gmail.com',
        })
        self.assertEqual(employee.work_email, 'valid.emp@gmail.com')

        # Test updating to another valid work email
        employee.write({'work_email': 'updated.emp@gmail.com'})
        self.assertEqual(employee.work_email, 'updated.emp@gmail.com')

    def test_employee_empty_work_email(self):
        """Verify employee creation with empty/False work email succeeds."""
        employee = self.env['hr.employee'].create({
            'name': 'Employee Without Email',
            'work_email': False,
        })
        self.assertFalse(employee.work_email)

    def test_employee_invalid_work_email_syntax(self):
        """Verify employee creation with malformed email raises validation."""
        with self.assertRaises(ValidationError):
            self.env['hr.employee'].create({
                'name': 'Invalid Employee',
                'work_email': 'malformed-email',
            })

    def test_employee_invalid_work_email_update(self):
        """Verify updating employee with invalid email raises error."""
        employee = self.env['hr.employee'].create({
            'name': 'Valid Employee Initially',
            'work_email': 'valid.initial@gmail.com',
        })
        with self.assertRaises(ValidationError):
            employee.write({'work_email': '@broken-domain.com'})

    def test_employee_mocked_deliverability_error(self):
        """Verify deliverability error handling for hr.employee."""
        with patch(
            'odoo.addons.email_id_validation.models.hr_employee.validate_email',
            side_effect=EmailNotValidError('MX record not found'),
        ):
            with self.assertRaises(ValidationError) as exc:
                self.env['hr.employee'].create({
                    'name': 'Deliverability Fail Employee',
                    'work_email': 'user@no-mx.org',
                })
            self.assertIn('MX record not found', str(exc.exception))
