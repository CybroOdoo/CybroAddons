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
class TestSlackChannel(TransactionCase):

    def test_slack_channel_creation(self):
        """Test creating a slack.channel record successfully"""
        company = self.env['res.company'].create({
            'name': 'Test Company',
            'bot_token': 'xoxb-test-token',
        })
        channel = self.env['slack.channel'].create({
            'name': 'general',
            'res_company_id': company.id,
        })
        self.assertTrue(channel.exists())
        self.assertEqual(channel.name, 'general')
        self.assertEqual(channel.res_company_id, company)
