# -*- coding: utf-8 -*-
#############################################################################
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
#############################################################################
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestPosConfig(TransactionCase):
    """Tests for the show_mass_edit_button flag that controls whether the
    'Edit Order Line' button is displayed in the POS control buttons."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.pos_config = cls.env['pos.config'].create({
            'name': 'Test POS Shop Config',
        })
        cls.pos_config_2 = cls.env['pos.config'].create({
            'name': 'Test POS Shop Config 2',
        })

    def test_pos_config_default_mass_edit_button(self):
        """show_mass_edit_button is enabled by default on pos.config."""
        self.assertTrue(
            self.pos_config.show_mass_edit_button,
            "The default value of show_mass_edit_button should be True")

    def test_pos_config_create_with_button_disabled(self):
        """The flag can be disabled directly at creation."""
        config = self.env['pos.config'].create({
            'name': 'Test POS No Mass Edit',
            'show_mass_edit_button': False,
        })
        self.assertFalse(
            config.show_mass_edit_button,
            "A config created with the flag False must keep it False")

    def test_pos_config_write_mass_edit_button(self):
        """The flag can be switched off and on again."""
        self.pos_config.write({'show_mass_edit_button': False})
        self.assertFalse(
            self.pos_config.show_mass_edit_button,
            "The show_mass_edit_button should be set to False")
        self.pos_config.write({'show_mass_edit_button': True})
        self.assertTrue(
            self.pos_config.show_mass_edit_button,
            "The show_mass_edit_button should be set back to True")

    def test_pos_config_flag_is_per_config(self):
        """Disabling the button on one POS must not affect another POS."""
        self.pos_config.write({'show_mass_edit_button': False})
        self.assertFalse(self.pos_config.show_mass_edit_button)
        self.assertTrue(
            self.pos_config_2.show_mass_edit_button,
            "Other POS configs must keep their own value")

    def test_pos_config_write_multiple_configs(self):
        """Writing on a recordset updates every config in it."""
        configs = self.pos_config | self.pos_config_2
        configs.write({'show_mass_edit_button': False})
        self.assertFalse(any(configs.mapped('show_mass_edit_button')))

    def test_pos_config_copy_keeps_flag(self):
        """Duplicating a POS config keeps the chosen value."""
        self.pos_config.write({'show_mass_edit_button': False})
        copied = self.pos_config.copy({'name': 'Copied POS Config'})
        self.assertFalse(
            copied.show_mass_edit_button,
            "A copied config should keep the original flag value")

    def test_pos_config_field_definition(self):
        """The field is a boolean with the expected label."""
        field = self.env['pos.config'].fields_get(
            ['show_mass_edit_button'])['show_mass_edit_button']
        self.assertEqual(field['type'], 'boolean')
        self.assertEqual(field['string'], 'Show Mass Edit Button')

    def test_pos_config_flag_available_in_pos_data(self):
        """The POS frontend reads `pos.config.show_mass_edit_button`
        (t-if in the control buttons template), so the field must be part
        of the data loaded into the POS session. An empty field list means
        'load every field'."""
        fields_list = self.env['pos.config']._load_pos_data_fields(
            self.pos_config.id)
        self.assertTrue(
            not fields_list or 'show_mass_edit_button' in fields_list,
            "show_mass_edit_button must be loaded in the POS session, "
            "otherwise the Edit Order Line button will never be shown")

    def test_pos_config_form_view_shows_flag(self):
        """The POS config form exposes the flag so it can be changed."""
        arch = self.env['pos.config'].get_view(view_type='form')['arch']
        self.assertIn('show_mass_edit_button', arch)
