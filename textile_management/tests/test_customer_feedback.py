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
from odoo.tests import TransactionCase, tagged

from odoo.addons.textile_management.controllers.textile_management import (
    TextileManagement,
)
from odoo.addons.website_sale.tests.common import MockRequest


@tagged('post_install', '-at_install')
class TestCustomerFeedback(TransactionCase):
    """Test saving the checkout feedback on the cart."""

    @classmethod
    def setUpClass(cls):
        """Create a website cart."""
        super().setUpClass()
        cls.website = cls.env.ref('base.default_website')
        cls.cart = cls.env['sale.order'].create({
            'partner_id': cls.env['res.partner'].create({'name': 'Buyer'}).id,
            'website_id': cls.website.id,
        })
        cls.controller = TextileManagement()

    def _save_review(self, cart, **params):
        """Call the feedback route with ``cart`` as the visitor's cart."""
        with MockRequest(self.env, website=self.website,
                         sale_order_id=cart.id if cart else None):
            return self.controller.save_review(**params)

    def test_01_rating_and_comment(self):
        """The star rating and the comment are saved on the cart."""
        self.assertTrue(self._save_review(self.cart, rating=3,
                                          comment=' Great fabrics '))
        self.assertEqual(self.cart.rating, '3')
        self.assertEqual(self.cart.comment, 'Great fabrics')

    def test_02_comment_only(self):
        """A comment without stars does not set a rating."""
        self.assertTrue(self._save_review(self.cart, comment='Fast delivery'))
        self.assertEqual(self.cart.comment, 'Fast delivery')
        self.assertFalse(self.cart.rating)

    def test_03_invalid_rating(self):
        """Ratings outside the stars are ignored."""
        self.assertFalse(self._save_review(self.cart, rating=9))
        self.assertFalse(self._save_review(self.cart, rating=0))
        self.assertFalse(self.cart.rating)

    def test_04_no_cart(self):
        """Without cart, nothing is saved."""
        self.assertFalse(self._save_review(None, rating=4))

    def test_05_confirmed_order(self):
        """A confirmed order is no longer the visitor's cart."""
        self.cart.action_confirm()
        self.assertFalse(self._save_review(self.cart, rating=4))
        self.assertFalse(self.cart.rating)
