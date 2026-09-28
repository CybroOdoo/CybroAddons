# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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

import logging
from odoo import models, fields, _
from odoo.exceptions import UserError

try:
    from odoo.addons.queue_job.job import job
except ImportError:
    def job(func):
        """Fallback decorator when queue_job is not installed."""
        return func

_logger = logging.getLogger(__name__)


class CsCartCategory(models.Model):
    """
    CS-Cart Category Model.

    Handles two-stage import and mapping of CS-Cart categories to Odoo's product.category model:
    - Stage 1: Fetch raw categories from CS-Cart REST API and save to cs.cart.category.
    - Stage 2: Map and build parent-child hierarchy in Odoo's native product.category model.
    """
    _name = "cs.cart.category"
    _description = "CS-Cart Category"

    name = fields.Char(string="Name")
    categ_id = fields.Integer(string="Category ID", index=True, copy=False)
    parent_id = fields.Integer(string="Parent ID", index=True, copy=False)
    status = fields.Boolean(string="Status", index=True, copy=False)

    def _convert_status(self, status):
        """
        Convert CS-Cart status code ('A' for Active) into boolean True/False.

        :param status: CS-Cart status string ('A', 'D', etc.)
        :type status: str
        :return: True if active ('A'), else False
        :rtype: bool
        """
        return status == "A"

    def _sync_cs_cart_categories(self, batch=None):
        """
        Stage-1 Category Import:
        Synchronize categories from CS-Cart API into cs.cart.category records,
        then invoke Stage-2 hierarchy sync to Odoo product.category.

        :param batch: Optional cs.cart.import.batch record set
        :type batch: cs.cart.import.batch, optional
        :raises UserError: If CS-Cart API request or sync fails.
        """
        api = self.env["cs.cart.api"]

        page = 1
        items_per_page = 10
        total_created = 0
        total_updated = 0

        try:
            existing_categories = self.search([])
            existing_map = {
                rec.categ_id: rec
                for rec in existing_categories
            }


            while True:
                if batch and batch.state == 'cancelled':
                    break

                res = api.request(
                    "GET",
                    "categories",
                    params={
                        "page": page,
                        "items_per_page": items_per_page,
                    }
                )

                categories = res.get("categories") or []
                params = res.get("params") or {}
                total_items = int(params.get("total_items") or 0)

                if not categories:
                    break

                for cat in categories:
                    cs_id = int(cat.get("category_id"))

                    vals = {
                        "name": cat.get("category"),
                        "parent_id": int(cat.get("parent_id") or 0),
                        "status": self._convert_status(cat.get("status")),
                        "categ_id": cs_id,
                    }

                    existing = existing_map.get(cs_id)

                    if not existing:
                        new_rec = self.create(vals)
                        existing_map[cs_id] = new_rec
                        _logger.debug("Created category %s", cs_id)
                        total_created += 1
                        continue

                    updates = {}
                    if existing.name != vals["name"]:
                        updates["name"] = vals["name"]

                    if existing.parent_id != vals["parent_id"]:
                        updates["parent_id"] = vals["parent_id"]

                    if existing.status != vals["status"]:
                        updates["status"] = vals["status"]

                    if updates:
                        existing.write(updates)
                        _logger.debug("Updated category %s", cs_id)
                        total_updated += 1

                if page * items_per_page >= total_items:
                    break

                page += 1

            self._sync_to_product_category()

        except Exception as e:
            raise UserError(f"Category sync failed: {str(e)}")

    @job
    def import_categories_queue(self, batch_id):
        """
        Queue Job worker method to execute category synchronization asynchronously.

        :param batch_id: Database ID of the related cs.cart.import.batch record
        :type batch_id: int
        """
        batch = self.env['cs.cart.import.batch'].browse(batch_id)
        if batch.state == 'cancelled':
            return
        batch.write({'state': 'in_progress', 'log_notes': '<p class="text-info">Category sync started...</p>'})
        try:
            self._sync_cs_cart_categories(batch)
            if batch.state == 'cancelled':
                return
            batch.write({
                'state': 'done',
                'log_notes': (batch.log_notes or '') + '<p class="text-success">🎉 Categories imported and synchronized successfully.</p>'
            })
        except Exception as e:
            if batch.state == 'cancelled':
                return
            batch.write({'state': 'failed', 'log_notes': (batch.log_notes or '') + f'<p class="text-danger">❌ Error: {str(e)}</p>'})

    def _sync_to_product_category(self):
        """
        Stage-2 Category Sync:
        Map cs.cart.category records to Odoo native product.category models
        and resolve parent-child hierarchy relationships without circular dependencies.
        """
        ProductCategory = self.env["product.category"]

        cs_categories = self.search([])
        cs_map = {c.categ_id: c for c in cs_categories}

        existing_product_map = {
            c.cs_cart_category_id: c
            for c in ProductCategory.search(
                [("cs_cart_category_id", "!=", False)]
            )
        }

        for cs_cat in cs_categories:
            vals = {
                "name": cs_cat.name,
                "cs_cart_category_id": cs_cat.categ_id,
            }

            existing = existing_product_map.get(cs_cat.categ_id)

            if not existing:
                new_cat = ProductCategory.create(vals)
                existing_product_map[cs_cat.categ_id] = new_cat
                _logger.debug("Created product.category for CS %s", cs_cat.categ_id)
                continue

            updates = {}
            if existing.name != vals["name"]:
                updates["name"] = vals["name"]

            if updates:
                existing.write(updates)
                _logger.debug("Updated basic info of product.category %s", cs_cat.categ_id)

        for cs_cat in cs_categories:
            existing = existing_product_map.get(cs_cat.categ_id)
            if not existing:
                continue

            parent_id_val = False
            if cs_cat.parent_id:
                parent_cs = cs_map.get(cs_cat.parent_id)
                if parent_cs:
                    parent_odoo = existing_product_map.get(parent_cs.categ_id)
                    if parent_odoo:
                        parent_id_val = parent_odoo.id

            current_parent_id = existing.parent_id.id or False
            target_parent_id = parent_id_val or False

            if current_parent_id != target_parent_id:
                existing.write({"parent_id": target_parent_id})
                _logger.debug("Updated parent of product.category %s", cs_cat.categ_id)