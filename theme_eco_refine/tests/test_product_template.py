# -*- coding: utf-8 -*-
###############################################################################
#
# Cybrosys Technologies Pvt. Ltd.
#
# Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
# Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
# You can modify it under the terms of the GNU AFFERO
# GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
# You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
# (AGPL v3) along with this program.
# If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'theme_eco_refine')
class TestProductTemplate(TransactionCase):
    """Tests for the fields added on product.template."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env['product.template'].create({
            'name': 'Eco Bottle',
            'product_spec': 'Steel, 500 ml',
            'product_detail': 'Keeps drinks cold for 24 hours.',
        })

    def test_fields_are_stored(self):
        """Specification and detail are saved and read back unchanged."""
        self.assertEqual(self.product.product_spec, 'Steel, 500 ml')
        self.assertEqual(self.product.product_detail,
                         'Keeps drinks cold for 24 hours.')

    def test_fields_are_optional(self):
        """A product can be created without specification or detail."""
        product = self.env['product.template'].create({'name': 'Plain'})
        self.assertFalse(product.product_spec)
        self.assertFalse(product.product_detail)

    def test_fields_are_translatable(self):
        """Both fields are declared translatable."""
        fields_ = self.env['product.template']._fields
        self.assertTrue(fields_['product_spec'].translate)
        self.assertTrue(fields_['product_detail'].translate)

    def test_translation_is_per_language(self):
        """Writing in another language does not change the source text."""
        self.env['res.lang']._activate_lang('fr_FR')
        self.product.with_context(lang='fr_FR').product_spec = 'Acier, 500 ml'
        self.assertEqual(
            self.product.with_context(lang='fr_FR').product_spec,
            'Acier, 500 ml')
        self.assertEqual(
            self.product.with_context(lang='en_US').product_spec,
            'Steel, 500 ml')