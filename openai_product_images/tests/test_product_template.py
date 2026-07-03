# -*- coding: utf-8 -*-
################################################################################
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
################################################################################
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


class TestProductTemplate(TransactionCase):
    """Test cases for the product.template inherit logic."""

    def setUp(self):
        super(TestProductTemplate, self).setUp()
        self.product_tmpl = self.env['product.template'].create({
            'name': 'Test Product A',
            'list_price': 100.0,
        })
        self.product_tmpl_b = self.env['product.template'].create({
            'name': 'Test Product B',
            'list_price': 200.0,
        })

    def test_action_open_image_prompt_wizard_single(self):
        """Test opening the wizard for a single product template."""
        action = self.product_tmpl.action_open_image_prompt_wizard()
        self.assertEqual(action['res_model'], 'image.suggestion')
        self.assertEqual(action['type'], 'ir.actions.act_window')
        self.assertEqual(action['target'], 'new')
        self.assertEqual(action['context']['default_product_tmpl_id'], self.product_tmpl.id)

    def test_action_open_image_prompt_wizard_multi(self):
        """Test opening the wizard for multiple product templates raises ValidationError."""
        products = self.product_tmpl | self.product_tmpl_b
        with self.assertRaises(ValidationError):
            products.action_open_image_prompt_wizard()

    def test_action_dall_e_image(self):
        """Test action_dall_e_image returns the correct action details."""
        action = self.product_tmpl.action_dall_e_image()
        self.assertEqual(action['res_model'], 'dalle.image.suggestion')
        self.assertEqual(action['type'], 'ir.actions.act_window')
        self.assertEqual(action['domain'], [('product_tmpl_id', '=', self.product_tmpl.id)])
