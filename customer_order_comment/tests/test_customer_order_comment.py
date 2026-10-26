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
from werkzeug.utils import redirect as werkzeug_redirect

from odoo.tests.common import TransactionCase, tagged
from odoo.addons.customer_order_comment.controllers import customer_order_comment
from odoo.addons.customer_order_comment.controllers.customer_order_comment import CustomerRatingAndReview


@tagged('post_install', '-at_install')
class TestCustomerOrderComment(TransactionCase):
    """ Test suite for customer order rating and comment features """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Customer',
            'email': 'customer@example.com',
        })
        cls.order = cls.env['sale.order'].create({
            'partner_id': cls.partner.id,
        })
        cls.controller = CustomerRatingAndReview()

    def test_01_rating_selection_values(self):
        """ Ensure rating selection contains options 0 through 5 matching frontend """
        field_selection = dict(self.order._fields['rating'].selection)
        self.assertEqual(field_selection.get('0'), 'Not Rated')
        self.assertEqual(field_selection.get('1'), 'Very Bad')
        self.assertEqual(field_selection.get('2'), 'Poor')
        self.assertEqual(field_selection.get('3'), 'Average Quality')
        self.assertEqual(field_selection.get('4'), 'Good')
        self.assertEqual(field_selection.get('5'), 'Very Good Quality')

    def test_02_sale_order_fields_and_defaults(self):
        """ Check default values and model writing for rating and comment """
        self.assertEqual(self.order.rating, '0')
        self.assertFalse(self.order.comment)
        self.order.write({
            'rating': '5',
            'comment': 'Outstanding experience and fast shipping!',
        })
        self.assertEqual(self.order.rating, '5')
        self.assertEqual(self.order.comment, 'Outstanding experience and fast shipping!')

    def test_03_res_config_settings_toggle(self):
        """ Test enabling and disabling customer comment setting """
        settings = self.env['res.config.settings'].create({
            'comment_configuration': True,
        })
        settings.execute()
        is_enabled = self.env['ir.config_parameter'].sudo().get_bool(
            'customer_order_comment.comment_configuration'
        )
        self.assertTrue(is_enabled)

        settings = self.env['res.config.settings'].create({
            'comment_configuration': False,
        })
        settings.execute()
        is_enabled = self.env['ir.config_parameter'].sudo().get_bool(
            'customer_order_comment.comment_configuration'
        )
        self.assertFalse(is_enabled)

    def test_04_controller_disabled_setting(self):
        """ Verify controller rejects submissions when feature is disabled """
        self.env['ir.config_parameter'].sudo().set_bool(
            'customer_order_comment.comment_configuration', False
        )
        mock_request = MagicMock()
        mock_request.env = self.env
        mock_request.session = {'sale_last_order_id': self.order.id}
        mock_request.redirect.side_effect = lambda url, code=303: werkzeug_redirect(url, code)
        with patch.object(customer_order_comment, 'request', mock_request):
            res = self.controller.customer_order_rating(
                order_id=self.order.id,
                rate_value='5',
                comment='Should not be saved',
            )
            self.assertEqual(res.status_code, 303)
            self.assertEqual(res.location, '/shop/confirmation')
            mock_request.redirect.assert_called_once_with('/shop/confirmation')
            self.assertEqual(self.order.rating, '0')
            self.assertFalse(self.order.comment)

    def test_05_controller_unauthorized_order_id(self):
        """ Verify controller blocks arbitrary order_id not in session or owned """
        self.env['ir.config_parameter'].sudo().set_bool(
            'customer_order_comment.comment_configuration', True
        )
        target_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
        })
        mock_request = MagicMock()
        mock_request.env = self.env
        mock_request.session = {'sale_last_order_id': self.order.id}
        mock_request.redirect.side_effect = lambda url, code=303: werkzeug_redirect(url, code)
        with patch.object(customer_order_comment, 'request', mock_request):
            # Attempt to modify target_order which is not the session order
            res = self.controller.customer_order_rating(
                order_id=target_order.id,
                rate_value='5',
                comment='Unauthorized write',
            )
            self.assertEqual(res.status_code, 303)
            self.assertEqual(res.location, '/shop/confirmation')
            mock_request.redirect.assert_called_once_with('/shop/confirmation')
            self.assertEqual(target_order.rating, '0')
            self.assertFalse(target_order.comment)

    def test_06_controller_authorized_session_submission(self):
        """ Verify controller accepts valid submission for session order """
        self.env['ir.config_parameter'].sudo().set_bool(
            'customer_order_comment.comment_configuration', True
        )
        mock_request = MagicMock()
        mock_request.env = self.env
        mock_request.session = {'sale_last_order_id': self.order.id}
        mock_request.redirect.side_effect = lambda url, code=303: werkzeug_redirect(url, code)
        with patch.object(customer_order_comment, 'request', mock_request):
            res = self.controller.customer_order_rating(
                order_id=self.order.id,
                rate_value='5',
                comment='Great product quality!',
            )
            self.assertEqual(res.status_code, 303)
            self.assertEqual(res.location, '/shop/confirmation')
            mock_request.redirect.assert_called_once_with('/shop/confirmation')
            self.assertEqual(self.order.rating, '5')
            self.assertEqual(self.order.comment, 'Great product quality!')

    def test_07_controller_authorized_token_submission(self):
        """ Verify controller accepts valid submission when matching access token is provided """
        self.env['ir.config_parameter'].sudo().set_bool(
            'customer_order_comment.comment_configuration', True
        )
        token_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
        })
        token_order._portal_ensure_token()
        mock_request = MagicMock()
        mock_request.env = self.env
        mock_request.session = {}  # Empty session
        mock_request.redirect.side_effect = lambda url, code=303: werkzeug_redirect(url, code)
        with patch.object(customer_order_comment, 'request', mock_request):
            res = self.controller.customer_order_rating(
                order_id=token_order.id,
                access_token=token_order.access_token,
                rate_value='4',
                comment='Good service and communication!',
            )
            self.assertEqual(res.status_code, 303)
            self.assertEqual(res.location, '/shop/confirmation')
            mock_request.redirect.assert_called_once_with('/shop/confirmation')
            self.assertEqual(token_order.rating, '4')
            self.assertEqual(token_order.comment, 'Good service and communication!')

