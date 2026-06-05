# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestSlackUser(TransactionCase):

    def test_slack_user_creation(self):
        """Test creating a slack.user record successfully"""
        company = self.env['res.company'].create({
            'name': 'Test Company',
            'bot_token': 'xoxb-test-token',
        })
        user = self.env['slack.user'].create({
            'name': 'Test User',
            'email': 'test@example.com',
            'user': 'U12345',
            'res_company_id': company.id,
            'user_token': 'xoxp-test-token',
        })
        self.assertTrue(user.exists())
        self.assertEqual(user.name, 'Test User')
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.user, 'U12345')
        self.assertEqual(user.res_company_id, company)
        self.assertEqual(user.user_token, 'xoxp-test-token')
