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
from odoo import models, api, _

try:
    from odoo.addons.queue_job.job import job
except ImportError:
    def job(func):
        """Fallback decorator when queue_job is not installed."""
        return func

_logger = logging.getLogger(__name__)


class CsCartAttributeSync(models.Model):
    """
    CS-Cart Attribute Sync Model.

    Responsible for synchronizing Product Attributes and Features from CS-Cart to Odoo.
    Maps CS-Cart features to Odoo's product.attribute and feature variants to product.attribute.value.
    """
    _name = "cs.cart.attribute.sync"
    _description = "CS-Cart Attribute Sync"

    @api.model
    def sync_attributes(self, batch=None):
        """
        Synchronize CS-Cart features and feature variants into Odoo product attributes.

        :param batch: Optional cs.cart.import.batch record set
        :type batch: cs.cart.import.batch, optional
        :return: Statistics dictionary containing created/updated counters
        :rtype: dict
        """
        api = self.env["cs.cart.api"]
        
        Attribute = self.env["product.attribute"].sudo()
        AttributeValue = self.env["product.attribute.value"].sudo()

        page = 1
        items_per_page = 50
        total_created_attrs = 0
        total_updated_attrs = 0
        total_created_vals = 0
        total_updated_vals = 0


        existing_attributes = Attribute.search([('cs_cart_feature_id', '!=', False)])
        attribute_by_cs_id = {attr.cs_cart_feature_id: attr for attr in existing_attributes}

        existing_values = AttributeValue.search([('cs_cart_variant_id', '!=', False)])
        value_by_cs_id = {val.cs_cart_variant_id: val for val in existing_values}

        while True:
            if batch and batch.state == 'cancelled':
                break
            res = api.request(
                "GET",
                "features",
                params={
                    "page": page,
                    "items_per_page": items_per_page,
                }
            )

            features = res.get("features") or []
            params = res.get("params") or {}

            if isinstance(features, dict):
                features = list(features.values())

            if not features:
                break

            for feat in features:
                feature_id = int(feat.get("feature_id") or 0)
                if not feature_id:
                    continue

                name = feat.get("description") or f"CS-Feature-{feature_id}"
                
                attr_vals = {
                    "name": name,
                    "cs_cart_feature_id": feature_id,
                }

                attribute = attribute_by_cs_id.get(feature_id)
                if attribute:
                    if attribute.name != name:
                        attribute.write({"name": name})
                        total_updated_attrs += 1
                else:
                    attribute = Attribute.create(attr_vals)
                    attribute_by_cs_id[feature_id] = attribute
                    total_created_attrs += 1

                variants_dict = feat.get("variants") or {}
                if isinstance(variants_dict, dict):
                    variants = list(variants_dict.values())
                elif isinstance(variants_dict, list):
                    variants = variants_dict
                else:
                    variants = []

                for var in variants:
                    variant_id = int(var.get("variant_id") or 0)
                    if not variant_id:
                        continue

                    var_name = var.get("variant") or f"CS-Val-{variant_id}"
                    
                    val_vals = {
                        "name": var_name,
                        "attribute_id": attribute.id,
                        "cs_cart_variant_id": variant_id,
                    }

                    value = value_by_cs_id.get(variant_id)
                    if value:
                        if value.name != var_name or value.attribute_id != attribute:
                            value.write({
                                "name": var_name,
                                "attribute_id": attribute.id,
                            })
                            total_updated_vals += 1
                    else:
                        value = AttributeValue.create(val_vals)
                        value_by_cs_id[variant_id] = value
                        total_created_vals += 1

            total_items = int(params.get("total_items") or 0)
            if page * items_per_page >= total_items:
                break

            page += 1

        return {
            "success": True,
            "created_attrs": total_created_attrs,
            "updated_attrs": total_updated_attrs,
            "created_vals": total_created_vals,
            "updated_vals": total_updated_vals,
        }

    @job
    def import_attributes_queue(self, batch_id):
        """
        Queue Job worker method to execute attribute synchronization asynchronously.

        :param batch_id: Database ID of the related cs.cart.import.batch record
        :type batch_id: int
        """
        batch = self.env['cs.cart.import.batch'].browse(batch_id)
        if batch.state == 'cancelled':
            return
        batch.write({'state': 'in_progress', 'log_notes': '<p class="text-info">Attribute sync started...</p>'})
        try:
            res = self.sync_attributes(batch)
            if batch.state == 'cancelled':
                return
            batch.write({
                'state': 'done',
                'log_notes': (batch.log_notes or '') + f'<p class="text-success">🎉 Attributes and values imported successfully. Attributes Created/Updated: {res.get("created_attrs", 0)}/{res.get("updated_attrs", 0)}, Values Created/Updated: {res.get("created_vals", 0)}/{res.get("updated_vals", 0)}</p>'
            })
        except Exception as e:
            if batch.state == 'cancelled':
                return
            batch.write({'state': 'failed', 'log_notes': (batch.log_notes or '') + f'<p class="text-danger">❌ Error: {str(e)}</p>'})
