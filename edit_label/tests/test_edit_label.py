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

from xml.etree import ElementTree

from odoo.exceptions import AccessError
from odoo.tests.common import TransactionCase


class TestEditLabel(TransactionCase):
    """Exercise label editing, its audit trail, and user permission lookup."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.view = cls.env['ir.ui.view'].create({
            'name': 'edit_label.test.partner.form',
            'model': 'res.partner',
            'type': 'form',
            'arch': '''<form string="Partner">
                <group>
                    <label for="email" string="Email"/>
                    <field name="email" string="Email"/>
                </group>
            </form>''',
        })

    def setUp(self):
        super().setUp()
        self.env.user.is_edit_field_label = True

    def test_edit_xml_field_label_updates_view_field_and_history(self):
        """A label update changes the XML, model field, and one audit row."""
        result = self.env['ir.ui.view'].edit_xml_field_label(
            'res.partner', 'form', 'Email', 'email', 'Contact Email', 'email'
        )

        self.assertTrue(result)

        root = ElementTree.fromstring(self.view.arch)
        self.assertEqual(
            root.find(".//label[@for='email']").get('string'),
            'Contact Email',
        )
        self.assertEqual(
            root.find(".//field[@name='email']").get('string'),
            'Contact Email',
        )

        field = self.env['ir.model.fields'].search([
            ('model', '=', 'res.partner'), ('name', '=', 'email'),
        ])
        self.assertEqual(field.field_description, 'Contact Email')

        model_name = self.env['ir.model'].search([
            ('model', '=', 'res.partner'),
        ]).name
        history = self.env['label.history'].search([
            ('model', '=', model_name),
            ('old_label', '=', 'Email'),
            ('new_label', '=', 'Contact Email'),
        ])
        self.assertEqual(len(history), 1)
        self.assertEqual(history.user_id, self.env.user)
        self.assertTrue(history.date)

    def test_edit_xml_field_label_removes_trailing_escape(self):
        """A trailing escape is stripped before the label is persisted."""
        result = self.env['ir.ui.view'].edit_xml_field_label(
            'res.partner', 'form', 'Email', 'email', 'Email Address\\', 'email'
        )

        self.assertTrue(result)
        root = ElementTree.fromstring(self.view.arch)
        self.assertEqual(
            root.find(".//field[@name='email']").get('string'),
            'Email Address',
        )
        self.assertEqual(
            self.env['label.history'].search_count([
                ('old_label', '=', 'Email'),
                ('new_label', '=', 'Email Address'),
            ]),
            1,
        )

    def test_login_user_returns_label_edit_permission(self):
        """The frontend permission endpoint reflects the current user flag."""
        self.env.user.is_edit_field_label = False
        self.assertFalse(self.env['res.users'].login_user())

        self.env.user.is_edit_field_label = True
        self.assertTrue(self.env['res.users'].login_user())

    def test_edit_xml_field_label_requires_permission(self):
        """The RPC cannot bypass the Edit Field Label user preference."""
        self.env.user.is_edit_field_label = False

        with self.assertRaises(AccessError):
            self.env['ir.ui.view'].edit_xml_field_label(
                'res.partner', 'form', 'Email', 'email', 'Contact Email', 'email'
            )
