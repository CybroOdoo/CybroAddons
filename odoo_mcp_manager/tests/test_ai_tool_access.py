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
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestAiToolAccess(TransactionCase):
    """Regression tests for the model+operation allow-list (A2)."""

    def setUp(self):
        super().setUp()
        self.Access = self.env['ai.tool.access']
        self.model_id = self.env['ir.model']._get_id('res.groups')
        self.rule = self.Access.search([('model_id', '=', self.model_id)], limit=1)
        if not self.rule:
            self.rule = self.Access.create({'model_id': self.model_id})
        self.rule.write({
            'active': True, 'allow_read': True, 'allow_create': False,
            'allow_update': False, 'allow_delete': False, 'allow_unlink': False,
        })
        self.create_tool = self.env['ai.tool'].create({
            'name': 'create_record',
            'description': 'Create record tool',
            'implementation': 'builtin',
        })
        self.search_tool = self.env['ai.tool'].create({
            'name': 'search_records',
            'description': 'Search records tool',
            'implementation': 'builtin',
        })

    def test_01_is_allowed_read_true_create_false(self):
        """Seeded/read rule allows read but not create."""
        self.assertTrue(self.Access.is_allowed('res.groups', 'read'))
        self.assertFalse(self.Access.is_allowed('res.groups', 'create'))

    def test_02_create_blocked_by_default(self):
        """create_record is blocked when the model rule disallows create."""
        with self.assertRaises(UserError):
            self.create_tool.execute({'model': 'res.groups', 'values': {'name': 'X'}})

    def test_03_create_allowed_after_grant(self):
        """Enabling allow_create lets create_record succeed."""
        self.rule.allow_create = True
        result = self.create_tool.execute(
            {'model': 'res.groups', 'values': {'name': 'Granted Group'}}
        )
        self.assertIn('id', result)

    def test_04_unlisted_model_denied(self):
        """A model with no rule is denied for reads."""
        self.assertFalse(self.Access.is_allowed('ir.config_parameter', 'read'))
        with self.assertRaises(UserError):
            self.search_tool.execute({'model': 'ir.config_parameter'})

    def test_05_inactive_rule_denies(self):
        """An inactive rule denies everything."""
        self.rule.active = False
        self.assertFalse(self.Access.is_allowed('res.groups', 'read'))

    def test_06_enforcement_toggle_off_bypasses(self):
        """Disabling enforcement allows any model/operation."""
        self.env['ir.config_parameter'].sudo().set_param(
            'mcp_gateway.enforce_allowlist', 'False'
        )
        # No rule for ir.config_parameter, but enforcement is off → allowed.
        result = self.search_tool.execute({'model': 'ir.config_parameter', 'limit': 1})
        self.assertIsInstance(result, list)
