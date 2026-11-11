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
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestPipInstaller(TransactionCase):
    """Test suite for Pip Installer wizard operations and validation."""

    def setUp(self):
        super().setUp()
        self.pip_install_model = self.env['pip.install']
        self.import_message_model = self.env['import.message']

    def test_action_done_success(self):
        """Test successful execution of a valid pip command."""
        wizard = self.pip_install_model.create({
            'name': 'pip --version',
        })
        action = wizard.action_done()
        self.assertIsInstance(action, dict)
        self.assertEqual(action.get('type'), 'ir.actions.act_window')
        self.assertEqual(action.get('res_model'), 'import.message')
        message_record = self.import_message_model.browse(action.get('res_id'))
        self.assertTrue(message_record.exists())
        self.assertIn('pip', (message_record.message or '').lower())

    def test_action_done_invalid_command_prefix(self):
        """Test validation error when command does not start with pip."""
        wizard = self.pip_install_model.create({
            'name': 'python --version',
        })
        with self.assertRaises(ValidationError):
            wizard.action_done()

    def test_action_done_failed_pip_command(self):
        """Test validation error when pip execution encounters an error."""
        wizard = self.pip_install_model.create({
            'name': 'pip --nonexistent-option-xyz-123',
        })
        with self.assertRaises(ValidationError):
            wizard.action_done()

    def test_action_done_empty_command(self):
        """Test validation error when command is empty."""
        wizard = self.pip_install_model.create({
            'name': '   ',
        })
        with self.assertRaises(ValidationError):
            wizard.action_done()

    def test_action_import_message_close(self):
        """Test import.message action returns window close action."""
        message = self.import_message_model.create({
            'message': 'Test output details',
        })
        action = message.action_import_message()
        self.assertEqual(action, {'type': 'ir.actions.act_window_close'})

