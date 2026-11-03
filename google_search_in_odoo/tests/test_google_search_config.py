# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Yadhu Shankar E (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from unittest.mock import MagicMock, patch

from odoo.tests import tagged
from odoo.tests.common import TransactionCase

EXA_PATCH_TARGET = 'odoo.addons.google_search_in_odoo.models.res_users.Exa'


@tagged('post_install', '-at_install')
class TestGoogleSearchConfig(TransactionCase):
    """Test the Exa-backed google_search_config server action used by the
    systray search widget for both admin and non-admin users."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.icp = cls.env['ir.config_parameter'].sudo()
        cls.non_admin_user = cls.env['res.users'].create({
            'name': 'Standard Employee User',
            'login': 'standard_user',
            'email': 'standard_user@example.com',
            'group_ids': [(6, 0, [cls.env.ref('base.group_user').id])],
        })

    @staticmethod
    def _make_remote_result(title=None, url=None, highlights=None,
                             summary=None, text=None):
        result = MagicMock()
        result.title = title
        result.url = url
        result.highlights = highlights
        result.summary = summary
        result.text = text
        return result

    def test_empty_or_whitespace_input_returns_empty_list(self):
        self.assertEqual(self.env['res.users'].google_search_config(''), [])
        self.assertEqual(self.env['res.users'].google_search_config('   '), [])
        self.assertEqual(self.env['res.users'].google_search_config(None), [])

    def test_returns_error_when_search_is_disabled(self):
        self.icp.set_param('google_search_in_odoo.google_search', False)
        result = self.env['res.users'].google_search_config('odoo')
        self.assertEqual(result, {'error': 'Please enable Google Search.'})

        # Also verify res.config.settings proxy
        res_settings_result = self.env['res.config.settings'].google_search_config('odoo')
        self.assertEqual(res_settings_result, {'error': 'Please enable Google Search.'})

    def test_returns_error_when_api_key_is_missing(self):
        self.icp.set_param('google_search_in_odoo.google_search', 'True')
        self.icp.set_param('google_search_in_odoo.ser_client_api', '')

        result = self.env['res.users'].google_search_config('odoo')
        self.assertEqual(result, {'error': 'Please provide API key.'})

    def test_returns_error_when_exa_library_is_missing(self):
        self.icp.set_param('google_search_in_odoo.google_search', 'True')
        self.icp.set_param('google_search_in_odoo.ser_client_api', 'test-key')

        with patch(EXA_PATCH_TARGET, None):
            result = self.env['res.users'].google_search_config('odoo')
        self.assertEqual(result, {'error': 'Exa library is not installed on the server.'})

    def test_search_status_can_be_checked_by_non_admin_user(self):
        self.icp.set_param('google_search_in_odoo.google_search', 'True')
        is_enabled = self.env['res.users'].with_user(
            self.non_admin_user
        ).get_google_search_status()
        self.assertTrue(is_enabled)

        self.icp.set_param('google_search_in_odoo.google_search', '')
        is_enabled_false = self.env['res.users'].with_user(
            self.non_admin_user
        ).get_google_search_status()
        self.assertFalse(is_enabled_false)

    def test_search_results_are_mapped_to_title_link_snippet(self):
        self.icp.set_param('google_search_in_odoo.google_search', 'True')
        self.icp.set_param(
            'google_search_in_odoo.ser_client_api', 'test-api-key')
        remote_result = self._make_remote_result(
            title='Odoo Official Site',
            url='https://www.odoo.com',
            highlights=['First highlight', 'Second highlight'],
        )
        response = MagicMock(results=[remote_result])

        with patch(EXA_PATCH_TARGET) as exa_cls:
            exa_cls.return_value.search.return_value = response
            items = self.env['res.users'].with_user(
                self.non_admin_user
            ).google_search_config('odoo')

        exa_cls.assert_called_once_with('test-api-key')
        exa_cls.return_value.search.assert_called_once_with(
            'odoo', num_results=10, type='auto',
            contents={'highlights': True},
        )
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]['title'], 'Odoo Official Site')
        self.assertEqual(items[0]['link'], 'https://www.odoo.com')
        self.assertEqual(
            items[0]['snippet'], 'First highlight ... Second highlight')

    def test_falls_back_to_summary_when_no_highlights(self):
        self.icp.set_param('google_search_in_odoo.google_search', 'True')
        self.icp.set_param(
            'google_search_in_odoo.ser_client_api', 'test-api-key')
        remote_result = self._make_remote_result(
            title='Odoo', url='https://www.odoo.com',
            highlights=None, summary='A short summary',
        )
        response = MagicMock(results=[remote_result])

        with patch(EXA_PATCH_TARGET) as exa_cls:
            exa_cls.return_value.search.return_value = response
            items = self.env['res.users'].google_search_config('odoo')

        self.assertEqual(items[0]['snippet'], 'A short summary')

    def test_falls_back_to_truncated_text_when_no_highlights_or_summary(self):
        self.icp.set_param('google_search_in_odoo.google_search', 'True')
        self.icp.set_param(
            'google_search_in_odoo.ser_client_api', 'test-api-key')
        long_text = 'x' * 400
        remote_result = self._make_remote_result(
            title='Odoo', url='https://www.odoo.com',
            highlights=None, summary=None, text=long_text,
        )
        response = MagicMock(results=[remote_result])

        with patch(EXA_PATCH_TARGET) as exa_cls:
            exa_cls.return_value.search.return_value = response
            items = self.env['res.users'].google_search_config('odoo')

        self.assertEqual(items[0]['snippet'], long_text[:300] + '...')

    def test_short_text_is_not_truncated(self):
        self.icp.set_param('google_search_in_odoo.google_search', 'True')
        self.icp.set_param(
            'google_search_in_odoo.ser_client_api', 'test-api-key')
        short_text = 'a short body of text'
        remote_result = self._make_remote_result(
            title='Odoo', url='https://www.odoo.com',
            highlights=None, summary=None, text=short_text,
        )
        response = MagicMock(results=[remote_result])

        with patch(EXA_PATCH_TARGET) as exa_cls:
            exa_cls.return_value.search.return_value = response
            items = self.env['res.users'].google_search_config('odoo')

        self.assertEqual(items[0]['snippet'], short_text)

    def test_missing_title_and_link_default_to_empty_string(self):
        self.icp.set_param('google_search_in_odoo.google_search', 'True')
        self.icp.set_param(
            'google_search_in_odoo.ser_client_api', 'test-api-key')
        remote_result = self._make_remote_result(
            title=None, url=None, highlights=['A highlight'],
        )
        response = MagicMock(results=[remote_result])

        with patch(EXA_PATCH_TARGET) as exa_cls:
            exa_cls.return_value.search.return_value = response
            items = self.env['res.users'].google_search_config('odoo')

        self.assertEqual(items[0]['title'], '')
        self.assertEqual(items[0]['link'], '')

    def test_returns_empty_list_when_no_results(self):
        self.icp.set_param('google_search_in_odoo.google_search', 'True')
        self.icp.set_param(
            'google_search_in_odoo.ser_client_api', 'test-api-key')
        response = MagicMock(results=[])

        with patch(EXA_PATCH_TARGET) as exa_cls:
            exa_cls.return_value.search.return_value = response
            items = self.env['res.users'].google_search_config('odoo')

        self.assertEqual(items, [])

    def test_search_exception_is_caught_logged_and_returns_clean_error(self):
        self.icp.set_param('google_search_in_odoo.google_search', 'True')
        self.icp.set_param(
            'google_search_in_odoo.ser_client_api', 'test-api-key')

        with patch(EXA_PATCH_TARGET) as exa_cls:
            exa_cls.return_value.search.side_effect = Exception('Internal API Error')
            result = self.env['res.users'].google_search_config('odoo')

        self.assertEqual(
            result,
            {'error': 'Unable to complete search. Please verify the API key and try again.'}
        )
