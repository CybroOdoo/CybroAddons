# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Aleena K (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC
#    LICENSE (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestEmailValidation(TransactionCase):

    def test_valid_partner_email(self):
        """Test valid partner email."""
        partner = self.env['res.partner'].create({
            'name': 'Demo Partner',
            'email': 'demo@gmail.com',
        })
        self.assertEqual(
            partner.email,
            'demo@gmail.com'
        )

    def test_invalid_partner_email(self):
        """Test invalid partner email."""
        with self.assertRaises(ValidationError):
            self.env['res.partner'].create({
                'name': 'Invalid Partner',
                'email': 'invalid-email',
            })

    def test_employee_email_length_validation(self):
        """Test employee email length validation."""
        local_part = 'a' * 65
        with self.assertRaises(ValidationError):
            self.env['hr.employee'].create({
                'name': 'Demo Employee',
                'work_email': f'{local_part}@gmail.com',
            })
