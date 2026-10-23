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
from psycopg2 import IntegrityError
from odoo.tests.common import TransactionCase, tagged
from odoo.tools import mute_logger


@tagged('post_install', '-at_install')
class TestSuccessMessage(TransactionCase):
    """Test suite for the success.message wizard model and its functions."""

    def test_01_create_success_message(self):
        """Verify creation of success message record with text."""
        msg = self.env['success.message'].create({
            'message': '5 Records imported successfully',
        })
        self.assertTrue(msg.id)
        self.assertEqual(msg.message, '5 Records imported successfully')

    def test_02_action_close(self):
        """Verify action_close returns window close action dictionary."""
        msg = self.env['success.message'].create({
            'message': 'Operation completed',
        })
        res = msg.action_close()
        self.assertIsInstance(res, dict)
        self.assertEqual(res.get('type'), 'ir.actions.act_window_close')

    def test_03_required_message_constraint(self):
        """Verify creating success.message without message raises error."""
        with mute_logger('odoo.sql_db'):
            with self.assertRaises(IntegrityError):
                self.env['success.message'].create({
                    'message': None,
                })
