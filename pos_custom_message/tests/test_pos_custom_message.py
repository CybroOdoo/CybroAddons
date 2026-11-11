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
from odoo import Command
from odoo.exceptions import AccessError
from odoo.tests import tagged
from odoo.tests.common import new_test_user

from odoo.addons.point_of_sale.tests.common import TestPoSCommon

PARAM_KEY = 'pos_custom_message.message_ids'


@tagged('post_install', '-at_install')
class TestPosCustomMessage(TestPoSCommon):
    """Test suite for POS custom messages, covering message creation,

    per-POS loading, the message selection in settings and access rights.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.message_model = cls.env['pos.custom.message']
        cls.basic_message = cls.message_model.create({
            'message_type': 'warn',
            'title': 'Test Basic Shop Message',
            'message_text': 'Count the cash drawer.',
            'execution_time': 13.5,
            'pos_config_ids': [Command.set(cls.basic_config.ids)],
        })
        cls.second_basic_message = cls.message_model.create({
            'message_type': 'info',
            'title': 'Test Second Basic Shop Message',
            'message_text': 'Restock the shelves.',
            'execution_time': 17.0,
            'pos_config_ids': [Command.set(cls.basic_config.ids)],
        })
        cls.other_message = cls.message_model.create({
            'title': 'Test Other Shop Message',
            'message_text': 'Only for the other shop.',
            'execution_time': 9.0,
            'pos_config_ids': [Command.set(cls.other_currency_config.ids)],
        })

    def setUp(self):
        super().setUp()
        # Start every test without a saved message selection
        self.env['ir.config_parameter'].sudo().set_str(PARAM_KEY, '')

    def _get_loaded_messages(self, config):
        """Return the messages the POS would load for the given config."""
        domain = self.message_model._load_pos_data_domain(
            {'pos.config': config})
        return self.message_model.search(domain)

    def test_01_message_defaults(self):
        """Verify a new message is an alert by default."""
        message = self.message_model.create({'title': 'Test Default Message'})
        self.assertEqual(message.message_type, 'alert')
        self.assertEqual(message.display_name, 'Test Default Message')
        self.assertFalse(message.pos_config_ids)

    def test_02_session_loads_custom_message_model(self):
        """Verify the POS session loads the custom message model."""
        models_to_load = self.env['pos.session']._load_pos_data_models(
            self.basic_config)
        self.assertIn('pos.custom.message', models_to_load)

    def test_03_load_fields(self):
        """Verify the fields needed by the POS popup are exposed."""
        fields_to_load = self.message_model._load_pos_data_fields(
            self.basic_config)
        for field_name in ('message_type', 'title', 'message_text',
                           'execution_time', 'pos_config_ids'):
            self.assertIn(field_name, fields_to_load)

    def test_04_messages_filtered_by_pos_config(self):
        """Verify each POS only loads the messages linked to it."""
        basic_messages = self._get_loaded_messages(self.basic_config)
        self.assertIn(self.basic_message, basic_messages)
        self.assertIn(self.second_basic_message, basic_messages)
        self.assertNotIn(self.other_message, basic_messages)

        other_messages = self._get_loaded_messages(self.other_currency_config)
        self.assertIn(self.other_message, other_messages)
        self.assertNotIn(self.basic_message, other_messages)

    def test_05_settings_selection_limits_messages(self):
        """Verify only the messages selected in settings are loaded."""
        settings = self.env['res.config.settings'].create({
            'pos_config_id': self.basic_config.id,
            'message_ids': [Command.set(self.basic_message.ids)],
        })
        settings.set_values()
        self.assertEqual(
            self.env['ir.config_parameter'].sudo().get_str(PARAM_KEY),
            str(self.basic_message.ids))

        basic_messages = self._get_loaded_messages(self.basic_config)
        self.assertIn(self.basic_message, basic_messages)
        self.assertNotIn(self.second_basic_message, basic_messages)

        # The selection is shown again when the settings are reopened
        values = self.env['res.config.settings'].get_values()
        self.assertEqual(values['message_ids'],
                         [Command.set(self.basic_message.ids)])

    def test_06_empty_selection_hides_all_messages(self):
        """Verify saving an empty selection disables every message."""
        settings = self.env['res.config.settings'].create({
            'pos_config_id': self.basic_config.id,
            'message_ids': [Command.clear()],
        })
        settings.set_values()
        self.assertFalse(self._get_loaded_messages(self.basic_config))
        self.assertFalse(
            self.env['res.config.settings'].get_values()['message_ids'])

    def test_07_deleted_message_is_ignored(self):
        """Verify a deleted message left in the selection does not break."""
        deleted_message = self.message_model.create({
            'title': 'Test Deleted Message',
            'pos_config_ids': [Command.set(self.basic_config.ids)],
        })
        deleted_id = deleted_message.id
        self.env['ir.config_parameter'].sudo().set_str(
            PARAM_KEY, str([self.basic_message.id, deleted_id]))
        deleted_message.unlink()

        self.assertEqual(self.message_model._get_selected_message_ids(),
                         self.basic_message.ids)
        values = self.env['res.config.settings'].get_values()
        self.assertEqual(values['message_ids'],
                         [Command.set(self.basic_message.ids)])

    def test_08_invalid_parameter_is_ignored(self):
        """Verify a malformed saved selection falls back to all messages."""
        self.env['ir.config_parameter'].sudo().set_str(PARAM_KEY, 'not a list')
        self.assertIsNone(self.message_model._get_selected_message_ids())
        basic_messages = self._get_loaded_messages(self.basic_config)
        self.assertIn(self.basic_message, basic_messages)
        self.assertIn(self.second_basic_message, basic_messages)

    def test_09_messages_loaded_in_pos_session(self):
        """Verify an open POS session receives its custom messages."""
        self.config = self.basic_config
        self.open_new_session()
        data = self.pos_session.load_data({'only_records': True})

        loaded = {message['id']: message
                  for message in data['pos.custom.message']}
        self.assertIn(self.basic_message.id, loaded)
        self.assertNotIn(self.other_message.id, loaded)

        message = loaded[self.basic_message.id]
        self.assertEqual(message['message_type'], 'warn')
        self.assertEqual(message['title'], 'Test Basic Shop Message')
        self.assertEqual(message['message_text'], 'Count the cash drawer.')
        self.assertEqual(message['execution_time'], 13.5)
        self.assertEqual(message['pos_config_ids'], self.basic_config.ids)

    def test_10_access_rights(self):
        """Verify POS users can only read messages and managers can edit."""
        pos_user = new_test_user(
            self.env, login='custom_message_pos_user',
            groups='base.group_user,point_of_sale.group_pos_user')
        pos_manager = new_test_user(
            self.env, login='custom_message_pos_manager',
            groups='base.group_user,point_of_sale.group_pos_manager')

        message = self.basic_message.with_user(pos_user)
        self.assertEqual(message.title, 'Test Basic Shop Message')
        with self.assertRaises(AccessError):
            message.write({'title': 'Changed by POS user'})
        with self.assertRaises(AccessError):
            self.message_model.with_user(pos_user).create({'title': 'New'})

        self.basic_message.with_user(pos_manager).write(
            {'title': 'Changed by POS manager'})
        self.assertEqual(self.basic_message.title, 'Changed by POS manager')
