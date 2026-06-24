# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Syamili K (odoo@cybrosys.com)
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
#############################################################################

from odoo.tests.common import HttpCase, tagged

@tagged('post_install', '-at_install')
class TestReferralControllers(HttpCase):
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Referral Test Partner',
            'referral_code': 'TESTCODE123',
            'points': 500,
            'sign_up': 5,
        })
        cls.user = cls.env['res.users'].create({
            'name': 'Referral Test User',
            'login': 'test_referral_user',
            'password': 'testpassword',
            'partner_id': cls.partner.id,
        })
        cls.env['ir.config_parameter'].sudo().set_param('refer_friend_and_earn.sign_up_points', '50')
        
        # Setup Discount rule
        cls.discount_rule = cls.env['apply.discounts'].create({
            'starting_points': 50,
            'end_points': 1000,
            'discount': 10.0,
        })

    def test_01_refer_earn_route(self):
        """Test the /refer/earn route to ensure a code is generated and correct info is returned"""
        self.authenticate('test_referral_user', 'testpassword')
        response = self.url_open('/refer/earn')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'TESTCODE123', response.content, "The partner's referral code should be present in the page")
        self.assertIn(b'500', response.content, "The partner's points should be visible in the template")

    def test_02_refer_and_earn_submit(self):
        """Test the form submission for referring a friend"""
        self.authenticate('test_referral_user', 'testpassword')
        
        from unittest.mock import patch
        with patch('odoo.http.Request.validate_csrf', return_value=True):
            response = self.url_open('/refer_and_earn/form/submit', data={
                'referral_code': 'TESTCODE123',
                'email': 'friend@example.com',
            })
        self.assertEqual(response.status_code, 200, "Form submission should be successful")
        
    def test_03_shop_pricelist_points(self):
        """Test applying points to the cart"""
        self.authenticate('test_referral_user', 'testpassword')
        
        # Apply 100 points
        response = self.url_open('/shop/pricelist/points?points=100')
        self.assertEqual(response.status_code, 200)

        # Test with points exceeding available
        response = self.url_open('/shop/pricelist/points?points=1000')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Please enter valid points', response.content)

    def test_04_signup_with_referral(self):
        """Test the signup process with a referral code"""
        # Instead of full HTTP test, test the logic in AuthSignupHome if
        # possible, or at least open the signup page
        response = self.url_open('/web/signup?referral_code=TESTCODE123')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'TESTCODE123', response.content)

