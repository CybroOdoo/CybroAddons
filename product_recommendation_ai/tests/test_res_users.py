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
import re
import sys
from unittest.mock import MagicMock, patch

import numpy as np

from odoo.tests.common import TransactionCase, tagged

from odoo.addons.product_recommendation_ai.models import res_users

FAKE_DIMENSIONS = 64
# The real loader, before the tests replace it with the fake encoder
REAL_MODEL_LOADER = res_users._get_minilm_model


class FakeEncoder:
    """Stand-in for MiniLM: hashed word counts, so that texts sharing words
    are similar, without torch or a model download."""

    def encode(self, texts, convert_to_tensor=False):  # pylint: disable=unused-argument
        vectors = np.zeros((len(texts), FAKE_DIMENSIONS))
        for row, text in enumerate(texts):
            for word in re.findall(r'[a-z]{5,}', (text or '').lower()):
                vectors[row, sum(map(ord, word)) % FAKE_DIMENSIONS] += 1
        return vectors


@tagged('post_install', '-at_install')
class TestResUsersRecommendation(TransactionCase):
    """Test suite for AI product recommendation functionality on res.users."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.config_param = cls.env['ir.config_parameter'].sudo()

        # Create category
        cls.category = cls.env['product.category'].create({
            'name': 'Electronics',
        })

        # Create test customer partner and user
        cls.partner = cls.env['res.partner'].create({
            'name': 'Recommendation Customer',
            'email': 'customer@example.com',
        })
        cls.user = cls.env['res.users'].create({
            'name': 'Recommendation User',
            'login': 'reco_user',
            'partner_id': cls.partner.id,
        })

        # Create test products (product.template)
        cls.prod_tmpl_phone = cls.env['product.template'].create({
            'name': 'Smartphone Pro',
            'type': 'consu',
            'categ_id': cls.category.id,
            'description_ecommerce': 'High performance smartphone with OLED screen',
            'description_sale': 'Smartphone sale desc',
            'list_price': 899.0,
            'website_published': True,
        })
        cls.prod_phone = cls.prod_tmpl_phone.product_variant_id

        cls.prod_tmpl_case = cls.env['product.template'].create({
            'name': 'Smartphone Protective Case',
            'type': 'consu',
            'categ_id': cls.category.id,
            'description_ecommerce': 'Durable protective case for smartphone',
            'description_sale': 'Protective case sale desc',
            'list_price': 29.0,
            'website_published': True,
        })

        cls.prod_tmpl_laptop = cls.env['product.template'].create({
            'name': 'Gaming Laptop Ultra',
            'type': 'consu',
            'categ_id': cls.category.id,
            'description_ecommerce': 'Powerful laptop with dedicated GPU',
            'description_sale': 'Gaming laptop sale desc',
            'list_price': 1499.0,
            'website_published': True,
        })

        cls.prod_tmpl_service = cls.env['product.template'].create({
            'name': 'Extended Warranty Service',
            'type': 'service',
            'categ_id': cls.category.id,
            'description_ecommerce': 'Two year hardware warranty service',
            'list_price': 99.0,
            'website_published': True,
        })
        cls.prod_service = cls.prod_tmpl_service.product_variant_id

    def setUp(self):
        super().setUp()
        # The local model is replaced by a fake encoder in every test
        self.patch(res_users, '_get_minilm_model', FakeEncoder)

    def _confirmed_order(self, partner=None, product=None):
        return self.env['sale.order'].create({
            'partner_id': (partner or self.partner).id,
            'state': 'sale',
            'order_line': [(0, 0, {
                'product_id': (product or self.prod_phone).id,
                'product_uom_qty': 1,
            })],
        })

    # -------------------------------------------------------------------------
    # Metadata Helper Methods Tests
    # -------------------------------------------------------------------------
    def test_meta_name(self):
        """Test product metadata extraction for name."""
        self.assertEqual(
            self.user.meta_name(self.prod_tmpl_phone),
            'Smartphone Pro',
        )

    def test_meta_name_categ(self):
        """Test product metadata extraction for name and category."""
        result = self.user.meta_name_categ(self.prod_tmpl_phone)
        self.assertEqual(result, 'Smartphone Pro. Category: Electronics')

        # Test when category is empty
        prod_no_cat = self.env['product.template'].create({
            'name': 'Uncategorized Product',
            'categ_id': False,
        })
        result_no_cat = self.user.meta_name_categ(prod_no_cat)
        self.assertEqual(result_no_cat, 'Uncategorized Product. Category: ')

    def test_meta_name_desc(self):
        """Test product metadata extraction for name and description."""
        # When ecommerce description is present
        result = self.user.meta_name_desc(self.prod_tmpl_phone)
        self.assertEqual(
            result,
            'Smartphone Pro. Description: High performance smartphone with OLED screen',
        )

        # When ecommerce description is empty but sale description is present
        prod_sale_only = self.env['product.template'].create({
            'name': 'Sale Only Product',
            'description_ecommerce': False,
            'description_sale': 'Only sale description available',
        })
        result_sale = self.user.meta_name_desc(prod_sale_only)
        self.assertEqual(
            result_sale,
            'Sale Only Product. Description: Only sale description available',
        )

        # When neither description is present
        prod_no_desc = self.env['product.template'].create({
            'name': 'No Desc Product',
            'description_ecommerce': False,
            'description_sale': False,
        })
        result_empty = self.user.meta_name_desc(prod_no_desc)
        self.assertEqual(result_empty, 'No Desc Product. Description: ')

    def test_meta_desc(self):
        """Test product metadata extraction for description only."""
        # Ecommerce description prioritized
        result = self.user.meta_desc(self.prod_tmpl_phone)
        self.assertEqual(result, 'High performance smartphone with OLED screen')

        # Fallback to description_sale
        prod_sale_only = self.env['product.template'].create({
            'name': 'Sale Only Product',
            'description_ecommerce': False,
            'description_sale': 'Fallback sale description',
        })
        self.assertEqual(self.user.meta_desc(prod_sale_only), 'Fallback sale description')

        # Fallback to empty string
        prod_no_desc = self.env['product.template'].create({
            'name': 'Empty Product',
            'description_ecommerce': False,
            'description_sale': False,
        })
        self.assertEqual(self.user.meta_desc(prod_no_desc), '')

    # -------------------------------------------------------------------------
    # has_completed_order Tests
    # -------------------------------------------------------------------------
    def test_has_completed_order_no_orders(self):
        """Test has_completed_order returns False when user has no sale orders."""
        self.assertFalse(self.user.has_completed_order())

    def test_has_completed_order_draft_or_cancelled(self):
        """Test has_completed_order returns False when orders are draft or cancelled."""
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'state': 'draft',
        })
        self.assertFalse(self.user.has_completed_order())

        order.action_cancel()
        self.assertEqual(order.state, 'cancel')
        self.assertFalse(self.user.has_completed_order())

    def test_has_completed_order_confirmed(self):
        """Test has_completed_order returns True when user has at least one confirmed sale order."""
        self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'state': 'sale',
            'order_line': [(0, 0, {
                'product_id': self.prod_phone.id,
                'product_uom_qty': 1,
            })],
        })
        self.assertTrue(self.user.has_completed_order())

    # -------------------------------------------------------------------------
    # compute_recommendation Tests
    # -------------------------------------------------------------------------
    def test_compute_recommendation_no_orders(self):
        """Test compute_recommendation sets empty data when user has no orders."""
        self.user.recommended_products_data = [{'some': 'data'}]
        self.user.compute_recommendation()
        self.assertFalse(self.user.recommended_products_data)

    def test_compute_recommendation_only_service_products_purchased(self):
        """Test compute_recommendation sets empty data when purchased products are not consu/combo."""
        self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'state': 'sale',
            'order_line': [(0, 0, {
                'product_id': self.prod_service.id,
                'product_uom_qty': 1,
            })],
        })
        self.user.compute_recommendation()
        self.assertFalse(self.user.recommended_products_data)

    def test_compute_recommendation_no_published_products(self):
        """Test compute_recommendation sets empty data when no products are website_published."""
        self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'state': 'sale',
            'order_line': [(0, 0, {
                'product_id': self.prod_phone.id,
                'product_uom_qty': 1,
            })],
        })
        # Unpublish all products
        self.env['product.template'].search([]).write({'website_published': False})
        self.user.compute_recommendation()
        self.assertFalse(self.user.recommended_products_data)

    def test_compute_recommendation_fast_model(self):
        """Test recommendation generation with default fast MiniLM model."""
        self.config_param.set_str('product_recommendation_ai.model_choice', 'fast')
        self.config_param.set_str('product_recommendation_ai.product_metadata', 'description')
        self.config_param.set_str('product_recommendation_ai.recommendation_limit', '2')

        # Create confirmed order with Smartphone
        self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'state': 'sale',
            'order_line': [(0, 0, {
                'product_id': self.prod_phone.id,
                'product_uom_qty': 1,
            })],
        })

        self.user.compute_recommendation()
        reco_data = self.user.recommended_products_data

        self.assertIsInstance(reco_data, list)
        self.assertTrue(len(reco_data) > 0)
        self.assertLessEqual(len(reco_data), 2)

        # Purchased product (Smartphone Pro) must NOT be in the recommendations
        recommended_tmpl_ids = [item['product_id'] for item in reco_data]
        self.assertNotIn(self.prod_tmpl_phone.id, recommended_tmpl_ids)

        # Verify recommended product structure
        first_item = reco_data[0]
        self.assertIn('product_id', first_item)
        self.assertIn('attribute_value_ids', first_item)
        self.assertIn('name', first_item)
        self.assertIn('display_text', first_item)
        self.assertIn('list_price', first_item)
        self.assertIn('currency', first_item)
        self.assertIn('image', first_item)
        self.assertTrue(first_item['image'].startswith('/web/image/product.template/'))

    def test_compute_recommendation_metadata_modes(self):
        """Test recommendation computation works across all metadata options."""
        self.config_param.set_str('product_recommendation_ai.model_choice', 'fast')
        self.config_param.set_str('product_recommendation_ai.recommendation_limit', '3')

        self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'state': 'sale',
            'order_line': [(0, 0, {
                'product_id': self.prod_phone.id,
                'product_uom_qty': 1,
            })],
        })

        modes = ['name', 'name_categ', 'name_description', 'description']
        for mode in modes:
            self.config_param.set_str('product_recommendation_ai.product_metadata', mode)
            self.user.compute_recommendation()
            data = self.user.recommended_products_data
            self.assertTrue(len(data) > 0, f"Recommendation should produce results for mode '{mode}'")

    def test_compute_recommendation_accurate_model_without_token(self):
        """Test accurate model returns empty list when nomic_token is not configured."""
        self.config_param.set_str('product_recommendation_ai.model_choice', 'accurate')
        self.config_param.set_str('product_recommendation_ai.nomic_token', '')

        self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'state': 'sale',
            'order_line': [(0, 0, {
                'product_id': self.prod_phone.id,
                'product_uom_qty': 1,
            })],
        })

        self.user.compute_recommendation()
        self.assertFalse(self.user.recommended_products_data)

    def test_compute_recommendation_accurate_model_with_token(self):
        """Test accurate model generates recommendations when nomic embedding succeeds."""
        self.config_param.set_str('product_recommendation_ai.model_choice', 'accurate')
        self.config_param.set_str('product_recommendation_ai.nomic_token', 'valid_token_xyz')
        self.config_param.set_str('product_recommendation_ai.recommendation_limit', '2')

        self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'state': 'sale',
            'order_line': [(0, 0, {
                'product_id': self.prod_phone.id,
                'product_uom_qty': 1,
            })],
        })

        # Mock requests.post response for Nomic embedding endpoint
        def fake_post(url, headers=None, json=None, timeout=None):
            mock_res = MagicMock()
            texts = (json or {}).get('texts', [])
            mock_res.json.return_value = {"embeddings": [[0.5, 0.5, 0.5, 0.5] for _ in texts]}
            mock_res.raise_for_status.return_value = None
            return mock_res

        with patch('requests.post', side_effect=fake_post):
            self.user.compute_recommendation()

        reco_data = self.user.recommended_products_data
        self.assertTrue(len(reco_data) > 0)
        self.assertLessEqual(len(reco_data), 2)
        recommended_tmpl_ids = [item['product_id'] for item in reco_data]
        self.assertNotIn(self.prod_tmpl_phone.id, recommended_tmpl_ids)

    def test_compute_recommendation_accurate_model_handles_exception(self):
        """Test accurate model handles nomic embedding exception gracefully."""
        self.config_param.set_str('product_recommendation_ai.model_choice', 'accurate')
        self.config_param.set_str('product_recommendation_ai.nomic_token', 'token_with_api_error')

        self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'state': 'sale',
            'order_line': [(0, 0, {
                'product_id': self.prod_phone.id,
                'product_uom_qty': 1,
            })],
        })

        with patch('requests.post', side_effect=RuntimeError("Nomic API Rate Limit Exceeded")):
            # Should not raise exception
            self.user.compute_recommendation()
        self.assertFalse(self.user.recommended_products_data)

    # -------------------------------------------------------------------------
    # Async and Thread Job Tests
    # -------------------------------------------------------------------------
    def test_run_recommendation_async(self):
        """Test run_recommendation_async starts a daemon thread with _thread_job target."""
        with patch('threading.Thread') as mock_thread_cls:
            mock_thread_instance = MagicMock()
            mock_thread_cls.return_value = mock_thread_instance

            self.user.run_recommendation_async()

            mock_thread_cls.assert_called_once_with(
                target=self.user._thread_job,
                args=(self.env.cr.dbname, self.user.id),
                daemon=True,
            )
            mock_thread_instance.start.assert_called_once()

    def test_thread_job_execution(self):
        """Test _thread_job runs compute_recommendation and sends bus notification."""
        with patch('odoo.addons.product_recommendation_ai.models.res_users.Registry') as mock_registry_cls:
            mock_registry = MagicMock()
            mock_registry_cls.return_value = mock_registry
            mock_cr = MagicMock()
            mock_registry.cursor.return_value.__enter__.return_value = mock_cr

            with patch('odoo.api.Environment') as mock_env_cls:
                mock_env = MagicMock()
                mock_env_cls.return_value = mock_env
                mock_env_user = MagicMock()
                mock_env['res.users'].browse.return_value = mock_env_user
                sample_data = [{
                    'product_id': self.prod_tmpl_phone.id,
                    'name': self.prod_tmpl_phone.name,
                }]
                mock_env_user.recommended_products_data = sample_data

                self.user._thread_job(self.env.cr.dbname, self.user.id)

                mock_env['res.users'].browse.assert_called_once_with(self.user.id)
                mock_env_user.compute_recommendation.assert_called_once()
                mock_env['bus.bus']._sendone.assert_called_once_with(
                    mock_env_user.partner_id, "notifications", sample_data,
                )

    # -------------------------------------------------------------------------
    # Optional local model
    # -------------------------------------------------------------------------
    def test_fast_model_ranks_similar_products_first(self):
        """The product sharing the most words with the purchase comes
        first."""
        self.config_param.set_str('product_recommendation_ai.model_choice', 'fast')
        self.config_param.set_str('product_recommendation_ai.product_metadata', 'name')
        self.config_param.set_str('product_recommendation_ai.recommendation_limit', '2')
        self._confirmed_order()
        self.user.compute_recommendation()
        data = self.user.recommended_products_data
        self.assertEqual(data[0]['product_id'], self.prod_tmpl_case.id)

    def test_fast_model_unavailable(self):
        """Without the local model, there is no recommendation and no
        error."""
        self.patch(res_users, '_get_minilm_model', lambda: None)
        self.config_param.set_str('product_recommendation_ai.model_choice', 'fast')
        self._confirmed_order()
        self.user.compute_recommendation()
        self.assertFalse(self.user.recommended_products_data)

    def test_fast_model_encoding_error(self):
        """An error of the local model gives no recommendation."""
        broken = MagicMock()
        broken.encode.side_effect = RuntimeError('model error')
        self.patch(res_users, '_get_minilm_model', lambda: broken)
        self.config_param.set_str('product_recommendation_ai.model_choice', 'fast')
        self._confirmed_order()
        self.user.compute_recommendation()
        self.assertFalse(self.user.recommended_products_data)

    def test_get_minilm_model_without_library(self):
        """sentence-transformers is optional: without it the model loader
        returns nothing instead of failing."""
        self.patch(res_users, '_MODEL_CACHE', {})
        loader = REAL_MODEL_LOADER
        with patch.dict(sys.modules, {'sentence_transformers': None}), \
                self.assertLogs(res_users.__name__, 'WARNING'):
            self.assertIsNone(loader())

    def test_get_minilm_model_loads_once(self):
        """The model is loaded once, from the local cache first, then from
        the network."""
        self.patch(res_users, '_MODEL_CACHE', {})
        loader = REAL_MODEL_LOADER
        fake_library = MagicMock()
        fake_library.SentenceTransformer.side_effect = [OSError('not cached'), 'model']
        with patch.dict(sys.modules, {'sentence_transformers': fake_library}):
            self.assertEqual(loader(), 'model')
            self.assertEqual(loader(), 'model')
        self.assertEqual(fake_library.SentenceTransformer.call_count, 2)
        fake_library.SentenceTransformer.side_effect = OSError('offline')
        self.patch(res_users, '_MODEL_CACHE', {})
        with patch.dict(sys.modules, {'sentence_transformers': fake_library}), \
                self.assertLogs(res_users.__name__, 'WARNING'):
            self.assertIsNone(loader())

    def test_several_users(self):
        """A user without orders does not stop the recommendations of the
        next users."""
        other_partner = self.env['res.partner'].create({'name': 'Second'})
        other_user = self.env['res.users'].create({
            'name': 'Second User', 'login': 'reco_user_2',
            'partner_id': other_partner.id})
        self._confirmed_order(partner=self.partner)
        (other_user | self.user).compute_recommendation()
        self.assertFalse(other_user.recommended_products_data)
        self.assertTrue(self.user.recommended_products_data)
