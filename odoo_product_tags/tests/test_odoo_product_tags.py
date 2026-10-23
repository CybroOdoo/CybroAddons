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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import Command
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestOdooProductTags(TransactionCase):
    """Test cases for Odoo Product Tags module."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.tag_a = cls.env['product.tag'].create({'name': 'Tag Alpha'})
        cls.tag_b = cls.env['product.tag'].create({'name': 'Tag Beta'})
        cls.tag_c = cls.env['product.tag'].create({'name': 'Tag Gamma'})

    def test_01_res_config_settings_set_and_get(self):
        """Test setting and getting default product tags in Settings."""
        settings = self.env['res.config.settings'].create({
            'product_tag_ids': [Command.set([self.tag_a.id, self.tag_b.id])],
        })
        settings.set_values()

        param_val = self.env['ir.config_parameter'].sudo().get_str(
            'odoo_product_tags.product_tag_ids')
        self.assertIn(str(self.tag_a.id), param_val)
        self.assertIn(str(self.tag_b.id), param_val)

        values = self.env['res.config.settings'].get_values()
        tag_commands = values.get('product_tag_ids')
        self.assertTrue(tag_commands)
        self.assertEqual(set(tag_commands[0][2]), {self.tag_a.id, self.tag_b.id})

    def test_02_product_template_creation_with_default_tags(self):
        """Test product template creation automatically populating default tags."""
        self.env['ir.config_parameter'].sudo().set_str(
            'odoo_product_tags.product_tag_ids',
            str([self.tag_a.id, self.tag_b.id]))

        template_with_defaults = self.env['product.template'].create({
            'name': 'Template Auto Tags',
        })
        self.assertEqual(set(template_with_defaults.product_tag_ids.ids), {self.tag_a.id, self.tag_b.id})

        template_with_custom = self.env['product.template'].create({
            'name': 'Template Custom Tags',
            'product_tag_ids': [Command.set([self.tag_c.id])],
        })
        self.assertEqual(set(template_with_custom.product_tag_ids.ids), {self.tag_c.id})

        self.env['ir.config_parameter'].sudo().set_str(
            'odoo_product_tags.product_tag_ids', '')
        template_without_defaults = self.env['product.template'].create({
            'name': 'Template No Default Tags',
        })
        self.assertFalse(template_without_defaults.product_tag_ids)

    def test_03_product_product_creation_with_default_tags(self):
        """Test product variant creation automatically populating default tags."""
        self.env['ir.config_parameter'].sudo().set_str(
            'odoo_product_tags.product_tag_ids',
            str([self.tag_b.id, self.tag_c.id]))

        product_with_defaults = self.env['product.product'].create({
            'name': 'Product Auto Tags',
        })
        self.assertEqual(set(product_with_defaults.product_tag_ids.ids), {self.tag_b.id, self.tag_c.id})

        product_with_custom = self.env['product.product'].create({
            'name': 'Product Custom Tags',
            'product_tag_ids': [Command.set([self.tag_a.id])],
        })
        self.assertEqual(set(product_with_custom.product_tag_ids.ids), {self.tag_a.id})

        self.env['ir.config_parameter'].sudo().set_str(
            'odoo_product_tags.product_tag_ids', '')
        product_without_defaults = self.env['product.product'].create({
            'name': 'Product No Default Tags',
        })
        self.assertFalse(product_without_defaults.product_tag_ids)

    def test_04_action_apply_tags_returns_action_dict(self):
        """Test action_apply_template_tags and action_apply_product_tags return valid actions."""
        template = self.env['product.template'].create({'name': 'Template Action Test'})
        tmpl_action = template.action_apply_template_tags()
        self.assertEqual(tmpl_action.get('type'), 'ir.actions.act_window')
        self.assertEqual(tmpl_action.get('res_model'), 'product.multiple.tag')
        self.assertEqual(tmpl_action.get('view_mode'), 'form')
        self.assertEqual(tmpl_action.get('target'), 'new')
        self.assertEqual(tmpl_action.get('context', {}).get('default_product_tmp_ids'), template.ids)
        self.assertTrue(tmpl_action.get('context', {}).get('default_is_product_template'))

        product = self.env['product.product'].create({'name': 'Product Action Test'})
        prod_action = product.action_apply_product_tags()
        self.assertEqual(prod_action.get('type'), 'ir.actions.act_window')
        self.assertEqual(prod_action.get('res_model'), 'product.multiple.tag')
        self.assertEqual(prod_action.get('view_mode'), 'form')
        self.assertEqual(prod_action.get('target'), 'new')
        self.assertEqual(prod_action.get('context', {}).get('default_product_ids'), product.ids)
        self.assertTrue(prod_action.get('context', {}).get('default_is_product'))

    def test_05_wizard_apply_tags_to_templates(self):
        """Test applying tags via product.multiple.tag wizard to templates."""
        tmpl_1 = self.env['product.template'].create({'name': 'Tmpl Batch 1'})
        tmpl_2 = self.env['product.template'].create({'name': 'Tmpl Batch 2'})

        # Context active_ids approach
        wizard = self.env['product.multiple.tag'].with_context(
            active_ids=[tmpl_1.id, tmpl_2.id],
            default_is_product_template=True,
        ).create({
            'product_tag_ids': [Command.set([self.tag_a.id, self.tag_c.id])],
        })
        wizard.action_apply_template_tags()

        self.assertEqual(set(tmpl_1.product_tag_ids.ids), {self.tag_a.id, self.tag_c.id})
        self.assertEqual(set(tmpl_2.product_tag_ids.ids), {self.tag_a.id, self.tag_c.id})

        # Field product_tmp_ids approach (no active_ids in context)
        wizard_field = self.env['product.multiple.tag'].with_context(active_ids=False).create({
            'product_tmp_ids': [Command.set([tmpl_1.id])],
            'product_tag_ids': [Command.set([self.tag_b.id])],
        })
        wizard_field.action_apply_template_tags()
        self.assertEqual(set(tmpl_1.product_tag_ids.ids), {self.tag_b.id})

    def test_06_wizard_apply_tags_to_products(self):
        """Test applying tags via product.multiple.tag wizard to products."""
        prod_1 = self.env['product.product'].create({'name': 'Prod Batch 1'})
        prod_2 = self.env['product.product'].create({'name': 'Prod Batch 2'})

        # Context active_ids approach
        wizard = self.env['product.multiple.tag'].with_context(
            active_ids=[prod_1.id, prod_2.id],
            default_is_product=True,
        ).create({
            'product_tag_ids': [Command.set([self.tag_b.id, self.tag_c.id])],
        })
        wizard.action_apply_product_tags()

        self.assertEqual(set(prod_1.product_tag_ids.ids), {self.tag_b.id, self.tag_c.id})
        self.assertEqual(set(prod_2.product_tag_ids.ids), {self.tag_b.id, self.tag_c.id})

        # Field product_ids approach (no active_ids in context)
        wizard_field = self.env['product.multiple.tag'].with_context(active_ids=False).create({
            'product_ids': [Command.set([prod_1.id])],
            'product_tag_ids': [Command.set([self.tag_a.id])],
        })
        wizard_field.action_apply_product_tags()
        self.assertEqual(set(prod_1.product_tag_ids.ids), {self.tag_a.id})

    def test_07_invalid_config_parameter_resilience(self):
        """Test that invalid config parameter values do not crash creation or settings."""
        self.env['ir.config_parameter'].sudo().set_str(
            'odoo_product_tags.product_tag_ids', 'invalid_syntax[[')

        tmpl = self.env['product.template'].create({'name': 'Resilience Template'})
        self.assertFalse(tmpl.product_tag_ids)

        prod = self.env['product.product'].create({'name': 'Resilience Product'})
        self.assertFalse(prod.product_tag_ids)

        values = self.env['res.config.settings'].get_values()
        self.assertFalse(values.get('product_tag_ids'))
