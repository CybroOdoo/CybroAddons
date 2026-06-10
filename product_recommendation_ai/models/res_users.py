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
import os
import threading
import numpy as np
import nomic
from nomic import embed

from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer

from odoo import models, fields, api, SUPERUSER_ID
from odoo.modules.registry import Registry

MINILM_MODEL = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

class ResUsers(models.Model):
    _inherit = "res.users"

    recommended_template_ids = fields.Many2many(
        "product.template",
        "user_recommendation_template_rel",
        "user_id",
        "template_id",
        string="Recommended Templates (legacy)"
    )
    recommended_products_data = fields.Json(string="Recommended Products Data (legacy)", default=list)

    def has_completed_order(self):
        """
        Checks if the current user has at least one confirmed sale order.
        Returns True if a 'sale' state order is found for the partner, otherwise False.
        """
        self.ensure_one()
        return bool(
            self.env['sale.order'].sudo().search_count([
                ('partner_id', '=', self.partner_id.id),
                ('state', '=', 'sale'),
            ])
        )

    def run_recommendation_async(self):
        """
        Initiates the product recommendation calculation in a daemonized background thread
        to ensure the website's frontend performance is not affected by the computation.
        """
        dbname = self._cr.dbname
        user_id = self.id
        t = threading.Thread(target=self._thread_job, args=(dbname, user_id), daemon=True)
        t.start()

    def _thread_job(self, dbname, user_id):
        """
        The worker function for the background thread. It establishes a new database
        cursor, synchronizes the environment, computes recommendations, and broadcasts
         the results to the web client via the Odoo Bus.
        """
        registry = Registry(dbname)
        with registry.cursor() as cr:
            try:
                env = api.Environment(cr, SUPERUSER_ID, {})
                user = env['res.users'].browse(user_id)
                user.compute_recommendation()

                channel = "reco_channel"
                env['bus.bus']._sendone(channel, "notifications", user.recommended_products_data)

                cr.commit()
            except Exception:
                pass

    def compute_recommendation(self):
        """
        Core recommendation engine. It fetches user purchase history, generates
        embeddings for purchased and available products using either Nomic (accurate)
        or MiniLM (fast), calculates cosine similarity, and saves the top results
        to the user's recommended_products_data field.
        """
        for user in self:
            conf = self.env['ir.config_parameter'].sudo()
            model_choice = conf.get_param('product_recommendation_ai.model_choice', 'fast')
            product_metadata = conf.get_param('product_recommendation_ai.product_metadata', 'description')
            recommendation_limit = int(conf.get_param('product_recommendation_ai.recommendation_limit', 4))

            last_order = self.env['sale.order'].sudo().search([
                ('partner_id', '=', user.partner_id.id),
                ('state', '=', 'sale'),
            ], order='date_order desc', limit=1)

            if not last_order:
                user.recommended_products_data = []
                return

            purchased_products = last_order.order_line.mapped('product_id.product_tmpl_id').filtered(
                lambda p: p.type in ['consu', 'combo', 'product']
            )

            all_products = self.env['product.template'].sudo().search([
                ('website_published', '=', True),
                ('id', 'not in', purchased_products.ids)
            ])

            if not purchased_products or not all_products:
                user.recommended_products_data = []
                return

            meta_map = {
                'name': self.meta_name,
                'name_categ': self.meta_name_categ,
                'name_description': self.meta_name_desc,
                'description': self.meta_desc,
            }
            meta_func = meta_map.get(product_metadata, self.meta_desc)
            purchased_meta = [meta_func(p) for p in purchased_products]
            all_meta = [meta_func(p) for p in all_products]

            try:
                if model_choice == "accurate":
                    nomic_token = conf.get_param('product_recommendation_ai.nomic_token')
                    if not nomic_token:
                        return

                    nomic.login(token=nomic_token)

                    purchased_embeddings = np.array(
                        embed.text(
                            texts=purchased_meta,
                            model="nomic-embed-text-v1.5",
                            task_type="search_query"
                        )["embeddings"]
                    )
                    all_embeddings = np.array(
                        embed.text(
                            texts=all_meta,
                            model="nomic-embed-text-v1.5",
                            task_type="search_document"
                        )["embeddings"]
                    )
                else:
                    purchased_embeddings = np.array(MINILM_MODEL.encode(purchased_meta))
                    all_embeddings = np.array(MINILM_MODEL.encode(all_meta))

                sim_matrix = cosine_similarity(purchased_embeddings, all_embeddings)
                product_scores = np.max(sim_matrix, axis=0)

                all_ids = all_products.ids
                scored_products = sorted(zip(all_ids, product_scores), key=lambda x: x[1], reverse=True)

                top_ids = [pid for pid, _ in scored_products[:recommendation_limit]]
                recommended_products = self.env['product.template'].browse(top_ids)

                data_list = []
                for prod in recommended_products:
                    data_list.append({
                        'product_id': prod.id,
                        'name': prod.name,
                        'display_text': meta_func(prod)[:150],
                        'list_price': prod.list_price,
                        'currency': prod.currency_id.symbol,
                        'image': f"/web/image/product.template/{prod.id}/image_1920",
                        'website_url': f"/shop/product/{prod.id}",
                    })
                user.recommended_products_data = data_list

            except Exception:
                pass

    def meta_name(self, prod):
        """Returns the name of the product template."""
        return prod.name

    def meta_name_categ(self, prod):
        """Returns the product name appended with its category name."""
        cat = prod.categ_id.name if prod.categ_id else ''
        return f"{prod.name}. Category: {cat}"

    def meta_name_desc(self, prod):
        """Returns the product name appended with either the eCommerce or sale description."""
        desc = prod.description_ecommerce or prod.description_sale or ''
        return f"{prod.name}. {desc}"

    def meta_desc(self, prod):
        """Returns the most detailed description available (eCommerce > Sale > Name)."""
        return prod.description_ecommerce or prod.description_sale or prod.name
