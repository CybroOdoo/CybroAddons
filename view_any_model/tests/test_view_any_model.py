# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3), Version 3 for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo.tests import tagged
from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError


@tagged('post_install', '-at_install')
class TestViewAnyModel(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Demo Partner',
        })
        cls.model = cls.env['ir.model']._get('res.partner')

    def test_action_view_model_list(self):
        """Test opening model in list view."""
        wizard = self.env['view.any.model'].create({
            'view_type': 'list',
            'model_id': self.model.id,
        })
        action = wizard.action_view_model()
        self.assertEqual(
            action['type'],
            'ir.actions.act_window'
        )
        self.assertEqual(
            action['res_model'],
            'res.partner'
        )
        self.assertEqual(
            action['view_mode'],
            'list,form'
        )

    def test_action_view_model_form(self):
        """Test opening model in form view."""
        wizard = self.env['view.any.model'].create({
            'view_type': 'form',
            'model_id': self.model.id,
            'record_id': self.partner.id,
        })
        action = wizard.action_view_model()
        self.assertEqual(
            action['view_mode'],
            'form'
        )
        self.assertEqual(
            action['res_id'],
            self.partner.id
        )

    def test_invalid_record_id(self):
        """Test invalid record id."""
        wizard = self.env['view.any.model'].create({
            'view_type': 'form',
            'model_id': self.model.id,
            'record_id': 999999,
        })
        with self.assertRaises(UserError):
            wizard.action_view_model()

    def test_negative_record_id(self):
        """Test negative record id."""
        wizard = self.env['view.any.model'].create({
            'view_type': 'form',
            'model_id': self.model.id,
            'record_id': -1,
        })
        with self.assertRaises(UserError):
            wizard.action_view_model()

    def test_model_domain(self):
        """Test model domain returns models."""
        wizard = self.env['view.any.model']
        domain = wizard._get_domain()
        self.assertTrue(domain)
        self.assertEqual(
            domain[0][0],
            'id'
        )
        self.assertEqual(
            domain[0][1],
            'in'
        )
        self.assertTrue(
            isinstance(domain[0][2], list)
        )
        self.assertTrue(
            len(domain[0][2]) > 0
        )
        