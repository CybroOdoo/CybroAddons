# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo.tests.common import TransactionCase
from odoo.exceptions import AccessError

class TestAiConsent(TransactionCase):

    def setUp(self):
        super(TestAiConsent, self).setUp()
        self.tool = self.env['ai.tool'].create({
            'name': 'consensus_tool',
            'description': 'Tool used for consent tests',
            'implementation': 'builtin',
            'requires_user_consent': True,
        })
        self.consent = self.env['ai.consent'].create({
            'tool_id': self.tool.id,
            'state': 'pending',
        })
        self.approver_group = self.env.ref('odoo_mcp_manager.group_mcp_consent_approver')

    def test_01_grant_denied_access(self):
        """Test that non-approvers cannot grant/deny."""
        # Non-approver
        self.env.user.group_ids = [(3, self.approver_group.id)]
        with self.assertRaises(AccessError):
            self.consent.action_grant()
        with self.assertRaises(AccessError):
            self.consent.action_deny()

    def test_02_grant_success(self):
        """Test successful grant by approver."""
        self.env.user.group_ids = [(4, self.approver_group.id)]
        self.consent.action_grant()
        self.assertEqual(self.consent.state, 'granted')

    def test_03_deny_success(self):
        """Test successful deny by approver."""
        self.env.user.group_ids = [(4, self.approver_group.id)]
        self.consent.action_deny()
        self.assertEqual(self.consent.state, 'denied')
