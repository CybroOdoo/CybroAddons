# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#
###############################################################################from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestProductApproval(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestProductApproval, cls).setUpClass()
        cls.product_tmpl_obj = cls.env['product.template']
        cls.product_obj = cls.env['product.product']

        # Creating a test product template
        cls.test_product_tmpl = cls.product_tmpl_obj.create({
            'name': 'Test Draft Product Template',
            'type': 'consu',
        })

        # Creating a test product variant
        cls.test_product = cls.product_obj.create({
            'name': 'Test Draft Product Variant',
            'type': 'consu',
        })

    def test_01_default_approve_state(self):
        """Test if the default approval state is draft."""
        self.assertEqual(
            self.test_product_tmpl.approve_state, 'draft',
            "The default approval state for a new product template should be 'draft'."
        )
        self.assertEqual(
            self.test_product.approve_state, 'draft',
            "The default approval state for a new product variant should be 'draft'."
        )

    def test_02_action_confirm_product_approval(self):
        """Test the confirm action for product template and variant."""
        self.test_product_tmpl.action_confirm_product_approval()
        self.assertEqual(
            self.test_product_tmpl.approve_state, 'confirmed',
            "The product template state should be 'confirmed' after calling the confirm action."
        )

        self.test_product.action_confirm_product_approval()
        self.assertEqual(
            self.test_product.approve_state, 'confirmed',
            "The product variant state should be 'confirmed' after calling the confirm action."
        )

    def test_03_action_reset_product_approval(self):
        """Test the reset to draft action."""
        # First set them to confirmed
        self.test_product_tmpl.action_confirm_product_approval()
        self.test_product.action_confirm_product_approval()

        # Reset them
        self.test_product_tmpl.action_reset_product_approval()
        self.assertEqual(
            self.test_product_tmpl.approve_state, 'draft',
            "The product template state should be 'draft' after calling the reset action."
        )

        self.test_product.action_reset_product_approval()
        self.assertEqual(
            self.test_product.approve_state, 'draft',
            "The product variant state should be 'draft' after calling the reset action."
        )

    def test_04_action_confirm_products(self):
        """Test bulk confirmation action for product templates."""
        self.test_product_tmpl.with_context(active_ids=self.test_product_tmpl.ids).action_confirm_products()
        self.assertEqual(
            self.test_product_tmpl.approve_state, 'confirmed',
            "The product template state should be 'confirmed' after bulk confirmation."
        )

    def test_05_action_confirm_product_variants(self):
        """Test bulk confirmation action for product variants."""
        self.test_product.with_context(active_ids=self.test_product.ids).action_confirm_products()
        self.assertEqual(
            self.test_product.approve_state, 'confirmed',
            "The product variant state should be 'confirmed' after bulk confirmation."
        )
