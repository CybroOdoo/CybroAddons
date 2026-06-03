# -*- coding: utf-8 -*-
from unittest.mock import Mock, patch

from odoo.tests.common import TransactionCase


class TestLoginUserLog(TransactionCase):
    """Tests for login log creation on authentication."""

    def setUp(self):
        super().setUp()
        self.user = self.env['res.users'].with_context(no_reset_password=True).create({
            'name': 'Login Log User',
            'login': 'login_log_user',
            'email': 'login_log_user@example.com',
            'password': 'login_log_password',
            'groups_id': [(6, 0, [self.env.ref('base.group_user').id])],
        })

    def test_check_credentials_creates_login_log(self):
        ipify_response = Mock()
        ipify_response.json.return_value = {'ip': '1.2.3.4'}
        geo_response = Mock()
        geo_response.json.return_value = {
            'latitude': '10.0',
            'longitude': '20.0',
            'city': 'Kochi',
            'region': 'Kerala',
            'country_name': 'India',
            'postal': '682001',
            'timezone': 'Asia/Kolkata',
        }

        with patch(
            'odoo.addons.export_delete_login_log.models.login_user_log.requests.get',
            side_effect=[ipify_response, geo_response],
        ):
            self.user.with_user(self.user)._check_credentials(
                'login_log_password',
                {'interactive': True},
            )

        log = self.env['login.log'].sudo().search(
            [('name', '=', 'Login Log User')],
            order='id desc',
            limit=1,
        )
        self.assertTrue(log)
        self.assertEqual(log.ip_address, '1.2.3.4')
        self.assertEqual(log.geo_loc, '10.0, 20.0')
        self.assertEqual(log.address, 'Kochi, Kerala, India')
        self.assertEqual(log.postal_code, '682001')
        self.assertEqual(log.time_zone, 'Asia/Kolkata')
        self.assertFalse(log.remark)

    def test_check_credentials_uses_error_reason_for_remark(self):
        ipify_response = Mock()
        ipify_response.json.return_value = {'ip': '5.6.7.8'}
        geo_response = Mock()
        geo_response.json.return_value = {
            'error': True,
            'reason': 'RateLimited',
        }

        with patch(
            'odoo.addons.export_delete_login_log.models.login_user_log.requests.get',
            side_effect=[ipify_response, geo_response],
        ):
            self.user.with_user(self.user)._check_credentials(
                'login_log_password',
                {'interactive': True},
            )

        log = self.env['login.log'].sudo().search(
            [('ip_address', '=', '5.6.7.8')],
            order='id desc',
            limit=1,
        )
        self.assertTrue(log)
        self.assertEqual(log.remark, 'Free quota exceeded')
        self.assertFalse(log.geo_loc)
        self.assertFalse(log.address)
