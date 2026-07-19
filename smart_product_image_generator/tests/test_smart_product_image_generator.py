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

from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestProductAIImageGenerator(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.category = cls.env['product.category'].create({
            'name': 'Test Category',
        })

        cls.product = cls.env['product.template'].create({
            'name': 'Demo Product',
            'list_price': 100.0,
            'categ_id': cls.category.id,
            'description_sale': 'Demo description',
        })

    # ---------------------------------------------------------
    # Product Actions
    # ---------------------------------------------------------

    def test_open_ai_image_wizard(self):
        action = self.product.action_open_ai_image_wizard()

        self.assertEqual(
            action['res_model'],
            'smart.product.image.generator'
        )
        self.assertEqual(
            action['context']['default_product_id'],
            self.product.id
        )

    def test_bulk_generate_action(self):
        products = self.env['product.template'].create([
            {
                'name': 'Product A',
                'categ_id': self.category.id,
            },
            {
                'name': 'Product B',
                'categ_id': self.category.id,
            },
        ])

        action = products.with_context(
            active_ids=products.ids
        ).action_bulk_generate_ai_images()

        self.assertEqual(
            action['res_model'],
            'smart.product.image.generator'
        )

    # ---------------------------------------------------------
    # Wizard
    # ---------------------------------------------------------

    def test_wizard_creation(self):
        wizard = self.env[
            'smart.product.image.generator'
        ].create({
            'product_id': self.product.id,
            'ai_provider': 'stability',
            'image_style': 'professional',
        })

        self.assertEqual(
            wizard.product_id,
            self.product
        )

        self.assertEqual(
            wizard.ai_provider,
            'stability'
        )

    def test_prompt_generation(self):
        self.env['ir.config_parameter'].sudo().set_param(
            'smart_product_image_generator.brand_dna',
            'Luxury Premium Brand'
        )

        wizard = self.env[
            'smart.product.image.generator'
        ].create({
            'product_id': self.product.id,
            'ai_provider': 'stability',
            'image_style': 'professional',
        })

        wizard._compute_ai_prompt()

        self.assertTrue(wizard.prompt)

    # ---------------------------------------------------------
    # AI Generation Log
    # ---------------------------------------------------------

    def test_ai_image_log_creation(self):
        log = self.env[
            'ai.image.generation.log'
        ].create({
            'product_id': self.product.id,
            'prompt': 'Generate image',
            'ai_provider': 'openai',
            'image_style': 'professional',
            'status': 'success',
            'num_variants_requested': 2,
        })

        self.assertEqual(
            log.product_id,
            self.product
        )

        self.assertEqual(
            log.ai_provider,
            'openai'
        )

        self.assertEqual(
            log.status,
            'success'
        )

    # ---------------------------------------------------------
    # Config Settings
    # ---------------------------------------------------------

    def test_config_parameters(self):
        settings = self.env[
            'res.config.settings'
        ].create({
            'ai_brand_dna': 'Premium Brand',
            'openai_api_key': 'openai-key',
            'stability_api_key': 'stability-key',
            'gemini_api_key': 'gemini-key',
            'ai_approval_required': True,
            'ai_max_variants': 3,
        })

        settings.execute()

        params = self.env[
            'ir.config_parameter'
        ].sudo()

        self.assertEqual(
            params.get_param(
                'smart_product_image_generator.brand_dna'
            ),
            'Premium Brand'
        )

    # ---------------------------------------------------------
    # Image Line
    # ---------------------------------------------------------

    def test_ai_image_line_creation(self):
        wizard = self.env[
            'smart.product.image.generator'
        ].create({
            'product_id': self.product.id,
        })

        line = self.env[
            'product.ai.image.line'
        ].create({
            'wizard_id': wizard.id,
            'image_name': 'generated.png',
            'provider_used': 'openai',
            'style_used': 'professional',
        })

        self.assertEqual(
            line.wizard_id,
            wizard
        )

        self.assertEqual(
            line.provider_used,
            'openai'
        )
