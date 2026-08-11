# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
#############################################################################

from odoo import fields
from odoo.tests.common import TransactionCase
from odoo.tests import tagged

# Config parameter keys backing each field
_PARAM_OPEN_API_VALUE = 'meeting_summarizer.open_api_value'
_PARAM_OPEN_API_KEY = 'meeting_summarizer.open_api_key'
_PARAM_AUTO_MAIL_SEND = 'meeting_summarizer.auto_mail_send'
_PARAM_SELECT_USER = 'meeting_summarizer.select_user'


@tagged('post_install', '-at_install')
class TestResConfigSettings(TransactionCase):
    """Test suite for the ResConfigSettings model extension.
    """

    def setUp(self):
        super().setUp()
        params = self.env['ir.config_parameter'].sudo()
        for key in (_PARAM_OPEN_API_VALUE, _PARAM_AUTO_MAIL_SEND):
            params.set_param(key, False)
        params.set_param(_PARAM_OPEN_API_KEY, '')
        params.set_param(_PARAM_SELECT_USER, 'host')
        self.config = self.env['res.config.settings'].create({})

    # -----------------------------------------------------------------------
    # Field existence & type
    # -----------------------------------------------------------------------

    def test_open_api_value_field_exists_and_is_boolean(self):
        """'open_api_value' must exist on res.config.settings and be
        a Boolean field."""
        field = self.env['res.config.settings']._fields.get('open_api_value')
        self.assertIsNotNone(field, "Field 'open_api_value' must exist")
        self.assertIsInstance(field, fields.Boolean)

    def test_open_api_key_field_exists_and_is_char(self):
        """'open_api_key' must exist on res.config.settings and be
        a Char field."""
        field = self.env['res.config.settings']._fields.get('open_api_key')
        self.assertIsNotNone(field, "Field 'open_api_key' must exist")
        self.assertIsInstance(field, fields.Char)

    def test_auto_mail_send_field_exists_and_is_boolean(self):
        """'auto_mail_send' must exist on res.config.settings and be
        a Boolean field."""
        field = self.env['res.config.settings']._fields.get('auto_mail_send')
        self.assertIsNotNone(field, "Field 'auto_mail_send' must exist")
        self.assertIsInstance(field, fields.Boolean)

    def test_select_user_field_exists_and_is_selection(self):
        """'select_user' must exist on res.config.settings and be
        a Selection field."""
        field = self.env['res.config.settings']._fields.get('select_user')
        self.assertIsNotNone(field, "Field 'select_user' must exist")
        self.assertIsInstance(field, fields.Selection)

    def test_select_user_has_two_valid_choices(self):
        """'select_user' must expose exactly choices: 'host' and
        'all_attendees'."""
        field = self.env['res.config.settings']._fields.get('select_user')
        keys = [key for key, _ in field.selection]
        self.assertEqual(len(keys), 2, "Exactly two selection choices expected")
        self.assertIn('host', keys)
        self.assertIn('all_attendees', keys)

    # -----------------------------------------------------------------------
    # config_parameter key mapping
    # -----------------------------------------------------------------------

    def test_open_api_value_config_parameter_key(self):
        """'open_api_value' must be backed by config_parameter
        'meeting_summarizer.open_api_value'."""
        field = self.env['res.config.settings']._fields.get('open_api_value')
        self.assertEqual(field.config_parameter, _PARAM_OPEN_API_VALUE)

    def test_open_api_key_config_parameter_key(self):
        """'open_api_key' must be backed by config_parameter
        'meeting_summarizer.open_api_key'."""
        field = self.env['res.config.settings']._fields.get('open_api_key')
        self.assertEqual(field.config_parameter, _PARAM_OPEN_API_KEY)

    def test_auto_mail_send_config_parameter_key(self):
        """'auto_mail_send' must be backed by config_parameter
        'meeting_summarizer.auto_mail_send'."""
        field = self.env['res.config.settings']._fields.get('auto_mail_send')
        self.assertEqual(field.config_parameter, _PARAM_AUTO_MAIL_SEND)

    def test_select_user_config_parameter_key(self):
        """'select_user' must be backed by config_parameter
        'meeting_summarizer.select_user'."""
        field = self.env['res.config.settings']._fields.get('select_user')
        self.assertEqual(field.config_parameter, _PARAM_SELECT_USER)

    # -----------------------------------------------------------------------
    # Persistence to ir.config_parameter
    # -----------------------------------------------------------------------

    def test_open_api_value_persists_on_execute(self):
        """Setting open_api_value=True and calling execute() must
        persist 'True' to ir.config_parameter."""
        self.config.open_api_value = True
        self.config.execute()
        val = self.env['ir.config_parameter'].sudo().get_param(_PARAM_OPEN_API_VALUE)
        self.assertEqual(val, 'True')

    def test_open_api_key_persists_on_execute(self):
        """Setting open_api_key to a string value and calling
        execute() must persist that exact string to ir.config_parameter."""
        test_key = 'sk-test-key-without-digits'
        self.config.open_api_key = test_key
        self.config.execute()
        val = self.env['ir.config_parameter'].sudo().get_param(_PARAM_OPEN_API_KEY)
        self.assertEqual(val, test_key)

    def test_auto_mail_send_persists_on_execute(self):
        """Setting auto_mail_send=True and calling execute() must
        persist 'True' to ir.config_parameter."""
        self.config.auto_mail_send = True
        self.config.execute()
        val = self.env['ir.config_parameter'].sudo().get_param(_PARAM_AUTO_MAIL_SEND)
        self.assertEqual(val, 'True')

    def test_select_user_persists_on_execute(self):
        """Setting select_user='all_attendees' and calling execute()
        must persist that value to ir.config_parameter."""
        self.config.select_user = 'all_attendees'
        self.config.execute()
        val = self.env['ir.config_parameter'].sudo().get_param(_PARAM_SELECT_USER)
        self.assertEqual(val, 'all_attendees')

    # -----------------------------------------------------------------------
    # Fresh record reflects persisted values
    # -----------------------------------------------------------------------

    def test_fresh_settings_record_reflects_all_persisted_values(self):
        """After persisting configuration fields, a freshly created
        settings record must read back the exact same values."""
        params = self.env['ir.config_parameter'].sudo()
        params.set_param(_PARAM_OPEN_API_VALUE, True)
        params.set_param(_PARAM_OPEN_API_KEY, 'sk-fresh-test-key')
        params.set_param(_PARAM_AUTO_MAIL_SEND, True)
        params.set_param(_PARAM_SELECT_USER, 'all_attendees')

        fresh = self.env['res.config.settings'].create({})
        self.assertTrue(fresh.open_api_value)
        self.assertEqual(fresh.open_api_key, 'sk-fresh-test-key')
        self.assertTrue(fresh.auto_mail_send)
        self.assertEqual(fresh.select_user, 'all_attendees')