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

from odoo import api, models, _

try:
    from odoo.addons.queue_job.job import job
except ImportError:
    def job(func):
        """Fallback decorator when queue_job is not installed."""
        return func

_logger = logging.getLogger(__name__)


class CsCartCustomerSync(models.Model):
    """
    CS-Cart Customer Synchronization Model.

    This model is responsible for synchronizing customer (user_type = 'C')
    records from CS-Cart into Odoo. It fetches customer data via the
    CS-Cart API, identifies existing partners using the CS-Cart user ID
    or email address, and creates or updates customer records accordingly.

    The synchronization ensures that customer contact and address details
    in Odoo remain consistent with CS-Cart.
    """
    _name = 'cs.cart.customer.sync'
    _description = 'CsCartCustomerSync'

    @api.model
    def sync_customers(self, batch=None):
        """
                Synchronize customers from CS-Cart into Odoo.

                This method:
                - Retrieves customer records from CS-Cart using paginated API calls
                - Filters users by customer type (user_type = 'C')
                - Matches existing Odoo partners using:
                    - CS-Cart user ID
                    - Email address
                - Updates existing customer records with latest CS-Cart data
                - Creates new customer records when no match is found
                - Logs all create and update operations
                - Displays a success notification upon completion

        """
        api = self.env['cs.cart.api']
        Partner = self.env['res.partner'].sudo()

        page = 1
        items_per_page = 50
        total_created = 0
        total_updated = 0


        while True:
            if batch and batch.state == 'cancelled':
                break
            res = api.request(
                "GET",
                "users",
                params={
                    "user_type": "C",
                    "page": page,
                    "items_per_page": items_per_page,
                }
            )

            users = res.get("users", [])
            params = res.get("params", {})

            if not users:
                break

            for user in users:
                user_id = user.get("user_id")
                email = user.get("email")

                if not user_id:
                    continue

                partner = Partner.search(
                    ['|',
                     ('cs_cart_user_id', '=', user_id),
                     ('email', '=', email)],
                    limit=1
                )

                name = f"{user.get('firstname', '')} {user.get('lastname', '')}".strip()
                if not name:
                    name = email or f"CS-Customer-{user_id}"

                vals = {
                    "name": name,
                    "email": email,
                    "phone": user.get("phone"),
                    "street": user.get("address"),
                    "city": user.get("city"),
                    "zip": user.get("zipcode"),
                    "cs_cart_user_id": user_id,
                    "customer_rank": 1,
                }

                if partner:
                    partner.write(vals)
                    total_updated += 1
                    _logger.debug("Updated CS-Cart customer %s", user_id)
                else:
                    Partner.create(vals)
                    total_created += 1
                    _logger.debug("Created CS-Cart customer %s", user_id)

            total_items = int(params.get("total_items", 0))
            if page * items_per_page >= total_items:
                break

            page += 1

        return {
            "success": True,
            "created": total_created,
            "updated": total_updated,
        }

    @job
    def import_customers_queue(self, batch_id):
        """Queue Job wrapper for customer sync"""
        batch = self.env['cs.cart.import.batch'].browse(batch_id)
        if batch.state == 'cancelled':
            return
        batch.write({'state': 'in_progress', 'log_notes': '<p class="text-info">Customer sync started...</p>'})
        try:
            res = self.sync_customers(batch)
            if batch.state == 'cancelled':
                return
            batch.write({
                'state': 'done',
                'log_notes': (batch.log_notes or '') + f'🎉 Customers imported successfully. Created: {res.get("created", 0)}, Updated: {res.get("updated", 0)}'
            })
        except Exception as e:
            if batch.state == 'cancelled':
                return
            batch.write({'state': 'failed', 'log_notes': (batch.log_notes or '') + f'<p class="text-danger">❌ Error: {str(e)}</p>'})
