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
from unittest.mock import MagicMock, patch

from odoo.tests.common import TransactionCase, tagged

from odoo.addons.login_pos_direct.controllers.login_pos_direct import PosScreen


@tagged('post_install', '-at_install')
class TestLoginPosDirect(TransactionCase):
    """Test cases for POS Direct Login models and controllers."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group_pos_user = cls.env.ref('point_of_sale.group_pos_user')

        cls.pos_config = cls.env['pos.config'].create({
            'name': 'Test Direct POS Shop',
            'company_id': cls.env.company.id,
        })

        cls.pos_user = cls.env['res.users'].create({
            'name': 'POS Direct Cashier',
            'login': 'pos_cashier_direct_test',
            'email': 'pos_cashier_direct_test@example.com',
            'group_ids': [(6, 0, [cls.group_pos_user.id])],
        })

        cls.standard_user = cls.env['res.users'].create({
            'name': 'Standard Backend User',
            'login': 'standard_direct_test_user',
            'email': 'standard_direct_test_user@example.com',
            'group_ids': [(6, 0, [cls.env.ref('base.group_user').id])],
        })

    def test_pos_config_assignment(self):
        """Test assigning POS configuration to a user with POS User group."""
        self.pos_user.write({'pos_conf_id': self.pos_config.id})
        self.assertEqual(self.pos_user.pos_conf_id, self.pos_config)

    def test_pos_config_cleared_on_group_removal(self):
        """Test that pos_conf_id is automatically cleared when POS group is removed."""
        self.pos_user.write({'pos_conf_id': self.pos_config.id})
        self.assertEqual(self.pos_user.pos_conf_id, self.pos_config)

        # Remove POS User group
        self.pos_user.write({
            'group_ids': [(3, self.group_pos_user.id)],
        })
        self.assertFalse(self.pos_user.pos_conf_id)

    def test_pos_config_cleared_on_create_without_group(self):
        """Test creating user without POS group clears pos_conf_id."""
        user = self.env['res.users'].create({
            'name': 'No POS Group User',
            'login': 'no_pos_group_user',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id])],
            'pos_conf_id': self.pos_config.id,
        })
        self.assertFalse(user.pos_conf_id)

    def test_onchange_pos_conf_id(self):
        """Test onchange warning when user does not have POS group."""
        draft_user = self.standard_user.new(
            {'pos_conf_id': self.pos_config.id},
            origin=self.standard_user,
        )
        res_warning = draft_user._onchange_pos_conf_id()
        self.assertTrue(isinstance(res_warning, dict))
        self.assertIn('warning', res_warning)

        # Test onchange when user has POS group
        draft_pos_user = self.pos_user.new(
            {'pos_conf_id': self.pos_config.id},
            origin=self.pos_user,
        )
        res_ok = draft_pos_user._onchange_pos_conf_id()
        self.assertIsNone(res_ok)

    def test_controller_login_redirect_with_pos(self):
        """Test PosScreen._login_redirect returns POS UI URL when user has pos_conf_id."""
        self.pos_user.write({'pos_conf_id': self.pos_config.id})
        controller = PosScreen()

        mock_request = MagicMock()
        mock_request.env = self.env
        mock_request.session.uid = self.pos_user.id

        with patch(
            'odoo.addons.login_pos_direct.controllers.login_pos_direct.request',
            mock_request,
        ), patch(
            'odoo.http.request',
            mock_request,
        ):
            redirect_url = controller._login_redirect(self.pos_user.id)
            expected_url = f'/pos/ui/{self.pos_config.id}'
            self.assertEqual(redirect_url, expected_url)

    def test_controller_login_redirect_without_pos(self):
        """Test PosScreen._login_redirect falls back to default redirect without pos_conf_id."""
        controller = PosScreen()
        mock_request = MagicMock()
        mock_request.env = self.env
        mock_request.session.uid = self.standard_user.id

        with patch(
            'odoo.addons.login_pos_direct.controllers.login_pos_direct.request',
            mock_request,
        ), patch(
            'odoo.http.request',
            mock_request,
        ), patch(
            'odoo.addons.web.controllers.utils.request',
            mock_request,
        ):
            redirect_url = controller._login_redirect(self.standard_user.id)
            self.assertNotEqual(redirect_url, f'/pos/ui/{self.pos_config.id}')
