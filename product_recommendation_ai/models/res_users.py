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
import logging
import threading

import numpy as np
import requests

from odoo import SUPERUSER_ID, api, fields, models
from odoo.modules.registry import Registry

_logger = logging.getLogger(__name__)

MINILM_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
# Loaded local model, by name
_MODEL_CACHE = {}


def _get_minilm_model():
    """Lazily import and load the local MiniLM model on first use.

    sentence-transformers (and torch, which it loads) is optional and only
    needed by the Fast model: importing it at module level would load the
    whole machine learning stack into every Odoo worker at startup.
    """
    if MINILM_MODEL_NAME in _MODEL_CACHE:
        return _MODEL_CACHE[MINILM_MODEL_NAME]
    try:
        from sentence_transformers import SentenceTransformer  # noqa: PLC0415
    except ImportError:
        _logger.warning(
            "The Fast recommendation model needs the sentence-transformers "
            "library: pip install sentence-transformers")
        return None
    try:
        # Use the cached model first, to avoid network retries
        model = SentenceTransformer(MINILM_MODEL_NAME, local_files_only=True)
    except Exception:  # noqa: BLE001  # pylint: disable=broad-exception-caught
        try:
            model = SentenceTransformer(MINILM_MODEL_NAME)
        except Exception as error:  # noqa: BLE001  # pylint: disable=broad-exception-caught
            _logger.warning(
                "Failed to initialize SentenceTransformer: %s", error)
            return None
    _MODEL_CACHE[MINILM_MODEL_NAME] = model
    return model


def _cosine_similarity(left, right):
    """Cosine similarity of each row of left with each row of right."""
    norm_left = np.linalg.norm(left, axis=1, keepdims=True)
    norm_right = np.linalg.norm(right, axis=1, keepdims=True)
    norm_left = np.where(norm_left == 0, 1e-10, norm_left)
    norm_right = np.where(norm_right == 0, 1e-10, norm_right)
    return np.dot(left, right.T) / (norm_left * norm_right.T)


class ResUsers(models.Model):
    _inherit = "res.users"

    recommended_products_data = fields.Json(
        string="Recommended Products Data",
        default=list,
    )

    def run_recommendation_async(self):
        """
        Launches the recommendation computation as a background thread.
        Extracts the current database name and user ID, then starts a daemon
        thread that executes the heavy recommendation job without blocking
        the main request or impacting website performance.
        """
        dbname = self.env.cr.dbname
        user_id = self.id
        t = threading.Thread(target=self._thread_job, args=(dbname, user_id), daemon=True)
        t.start()

    def _thread_job(self, dbname, user_id):
        """
        Executes the recommendation computation in a background thread.
        Initializes a separate Odoo environment using the provided database name
        and user ID, computes product recommendations, and sends the results
        through the bus channel for real-time updates on the frontend.
        """
        registry = Registry(dbname)
        with registry.cursor() as cr:
            env = api.Environment(cr, SUPERUSER_ID, {})
            user = env['res.users'].browse(user_id)
            user.compute_recommendation()
            env['bus.bus']._sendone(user.partner_id, "notifications", user.recommended_products_data)

    def has_completed_order(self):
        """
        Checks if the current user (partner) has at least one confirmed sale order.
        Returns a boolean value based on the search count of sales in the 'sale' state.
        """
        self.ensure_one()
        return bool(
            self.env['sale.order'].sudo().search_count([
                ('partner_id', '=', self.partner_id.id),
                ('state', '=', 'sale'),
            ]),
        )

    def compute_recommendation(self):
        """
        AI-based product recommendation engine.
        Identifies products previously purchased by the user, generates embeddings for
        catalog products using either Nomic (remote) or MiniLM (local), calculates
        similarity scores, and updates the user's recommended_products_data with
        the top matching products.
        """
        for user in self:
            # Read configuration
            conf = self.env['ir.config_parameter'].sudo()
            model_choice = conf.get_str(
                'product_recommendation_ai.model_choice', 'fast',
            )
            product_metadata = conf.get_str(
                'product_recommendation_ai.product_metadata', 'description',
            )
            recommendation_limit = int(
                conf.get_str('product_recommendation_ai.recommendation_limit', 4),
            )
            # Get last completed sale order
            last_order = self.env['sale.order'].sudo().search([
                ('partner_id', '=', user.partner_id.id),
                ('state', '=', 'sale'),
            ], order='date_order desc', limit=1)
            if not last_order:
                user.recommended_products_data = []
                continue
            # Purchased & all products
            purchased_products = last_order.order_line.mapped(
                'product_id.product_tmpl_id',
            ).filtered(lambda p: p.type in ['consu', 'combo'])

            all_products = self.env['product.template'].sudo().search([
                ('website_published', '=', True),
            ])
            if not purchased_products or not all_products:
                user.recommended_products_data = []
                continue
            # Metadata builders
            meta_map = {
                'name': self.meta_name,
                'name_categ': self.meta_name_categ,
                'name_description': self.meta_name_desc,
                'description': self.meta_desc,
            }
            meta_func = meta_map.get(product_metadata, self.meta_desc)
            purchased_meta = [meta_func(p) for p in purchased_products]
            all_meta = [meta_func(p) for p in all_products]
            # Embedding generation
            if model_choice == "accurate":
                nomic_token = conf.get_str(
                    'product_recommendation_ai.nomic_token',
                )

                if not nomic_token:
                    user.recommended_products_data = []
                    continue

                try:
                    headers = {
                        "Authorization": f"Bearer {nomic_token}",
                        "Content-Type": "application/json",
                    }
                    res_p = requests.post(
                        "https://api-atlas.nomic.ai/v1/embedding/text",
                        headers=headers,
                        json={
                            "texts": purchased_meta,
                            "model": "nomic-embed-text-v1.5",
                        },
                        timeout=30,
                    )
                    res_p.raise_for_status()
                    purchased_embeddings = np.array(
                        res_p.json().get("embeddings", []),
                    )

                    res_a = requests.post(
                        "https://api-atlas.nomic.ai/v1/embedding/text",
                        headers=headers,
                        json={
                            "texts": all_meta,
                            "model": "nomic-embed-text-v1.5",
                        },
                        timeout=30,
                    )
                    res_a.raise_for_status()
                    all_embeddings = np.array(
                        res_a.json().get("embeddings", []),
                    )

                except Exception as e:  # noqa: BLE001
                    _logger.warning("Failed to generate Nomic embeddings: %s", e)
                    user.recommended_products_data = []
                    continue

            else:
                # Fast local embeddings (MiniLM)
                model = _get_minilm_model()
                if not model:
                    user.recommended_products_data = []
                    continue
                try:
                    purchased_embeddings = np.array(
                        model.encode(purchased_meta, convert_to_tensor=False),
                    )
                    all_embeddings = np.array(
                        model.encode(all_meta, convert_to_tensor=False),
                    )
                except Exception:  # noqa: BLE001
                    user.recommended_products_data = []
                    continue

            # Similarity scoring
            sim_matrix = _cosine_similarity(
                purchased_embeddings, all_embeddings)

            product_scores = np.max(sim_matrix, axis=0)
            purchased_ids = set(purchased_products.ids)
            all_ids = [p.id for p in all_products]
            scored_products = [
                (pid, float(score))
                for pid, score in zip(all_ids, product_scores)
                if pid not in purchased_ids
            ]
            scored_products.sort(key=lambda x: x[1], reverse=True)
            top_ids = [
                pid for pid, _ in scored_products[:recommendation_limit]
            ]
            recommended_products = self.env[
                'product.template'
            ].browse(top_ids)
            # Prepare carousel response
            data_list = []
            for prod in recommended_products:
                data_list.append({
                    'product_id': prod.id,
                    'attribute_value_ids': prod.attribute_line_ids.mapped(
                        'value_ids',
                    ).ids,
                    'name': prod.name,
                    'display_text': meta_func(prod),
                    'list_price': prod.list_price,
                    'currency': prod.currency_id.symbol,
                    'image': f"/web/image/product.template/{prod.id}/image_1920",
                })
            user.recommended_products_data = data_list

    def meta_name(self, prod):
        """
        Extracts the name of the product to be used as metadata for embedding generation.
        """
        return prod.name

    def meta_name_categ(self, prod):
        """
        Creates a metadata string combining the product name and its category name.
        """
        cat = prod.categ_id.name if prod.categ_id else ''
        return f"{prod.name}. Category: {cat}"

    def meta_name_desc(self, prod):
        """
        Creates a metadata string combining the product name and its eCommerce or sale description.
        """
        desc = prod.description_ecommerce or prod.description_sale or ''
        return f"{prod.name}. Description: {desc}"

    def meta_desc(self, prod):
        """
        Extracts the eCommerce description or sale description of the product for metadata use.
        """
        return prod.description_ecommerce or prod.description_sale or ''
