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
import time

from odoo import fields, models, _
from odoo.exceptions import UserError
from odoo.tools import config

try:
    from odoo.addons.queue_job.job import job
except ImportError:
    def job(func):
        """Fallback decorator when queue_job is not installed."""
        return func

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    """
    Extends res.partner model to support exporting customers and vendors to CS-Cart.
    """
    _inherit = "res.partner"

    cs_cart_user_id = fields.Integer(string="CS-Cart User ID", index=True)
    cs_cart_company_id = fields.Integer(string="CS-Cart Company ID", index=True)

    def _queue_job_available(self):
        """
        Check if queue_job is configured server-wide.

        :return: True if queue_job is active server-wide, else False
        :rtype: bool
        """
        server_wide = config.get('server_wide_modules') or ''
        modules = {m.strip() for m in server_wide.split(',')} if isinstance(server_wide, str) else set(server_wide)
        return 'queue_job' in modules

    def action_export_to_cs_cart(self):
        """
        Export selected partners to CS-Cart as customers or vendors.

        :return: Web client action dictionary
        :rtype: dict
        """
        if self._queue_job_available():
            self.with_delay(description="Exporting partners to CS-Cart")._export_to_cs_cart_job(self.ids)
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("CS-Cart"),
                    "message": _("Partner export job queued in the background."),
                    "type": "info",
                    "sticky": False,
                },
            }
        return self._export_to_cs_cart_sync()

    @job
    def _export_to_cs_cart_job(self, partner_ids):
        """
        Queue Job worker method for background export of partners.

        :param partner_ids: List of res.partner record IDs
        :type partner_ids: list[int]
        """
        partners = self.browse(partner_ids)
        partners._export_to_cs_cart_sync()
    
    def _export_to_cs_cart_sync(self):
        """ Synchronous export of partners to CS-Cart. """
        api = self.env["cs.cart.api"]
        exported = 0
        failed = []

        store_id = 1
        try:
            stores_res = api.request("GET", "stores")
            stores = stores_res.get("stores") or []
            if stores:
                store_id = int(stores[0].get("company_id") or 1)
        except Exception as e:
            _logger.error("Failed to fetch stores: %s", str(e))

        for partner in self:
            try:
                # 1. Validate email
                email = (partner.email or "").strip().lower()
                if not email:
                    raise UserError(_("Email is required."))

                # 2. Determine payload
                is_vendor = partner.supplier_rank > 0
                _logger.info("cscart partner %s:supplier_rank=%s, customer_rank=%s,is_vedor=%s",partner.name,partner.supplier_rank,partner.customer_rank,is_vendor)
                if is_vendor:
                    if not partner.cs_cart_company_id:
                        try:
                            partner.cs_cart_company_id = api.get_or_create_company(partner)
                        except Exception:
                            partner.cs_cart_company_id = store_id
                    payload = self._prepare_vendor_payload(partner, partner.cs_cart_company_id)
                else:
                    payload = self._prepare_cs_cart_customer_payload(partner, store_id)

                payload["email"] = email

                # 3. Check existing user if user_id is not set
                # if not partner.cs_cart_user_id:
                partner.cs_cart_user_id = False
                for utype in ['C', 'A', 'V']:
                     try:
                            search_res = api.request("GET", "users", params={"email": email, "user_type": utype})
                            users_list = search_res.get("users") or []
                            _logger.info("cscartuser search for %s:%s",email,users_list)
                            _logger.info("cscartuser search count %s",len(users_list))
                            user_type = "V" if is_vendor else "C"
                            for user in users_list:
                                if(user.get("user_id") and user.get("user_type") == user_type and (user.get("email") or "").strip().lower() == email):
                                    partner.cs_cart_user_id = int(user["user_id"])
                                    break
                            _logger.info("cscart-mapped partner %s (%s) to user id %s",partner.name,email,partner.cs_cart_user_id,)
                                # if users_list and users_list[0].get("user_id"):
                                #     partner.cs_cart_user_id = int(users_list[0]["user_id"])
                                #     break
                            if partner.cs_cart_user_id:
                                break
                     except Exception as e:
                            _logger.warning("User search error (%s): %s", utype, e)
                # else:
                #     partner.cs_cart_user_id=False


                # 4. Create or Update
                if partner.cs_cart_user_id:
                    update_payload = payload.copy()
                    update_payload.pop("user_type", None)
                    api.request("PUT", f"users/{partner.cs_cart_user_id}", data=update_payload)
                else:
                    res = api.request("POST", "users", data=payload)
                    cs_id = res.get("user_id") if isinstance(res, dict) else None
                    if not cs_id:
                        raise UserError(_("CS-Cart did not return a valid user_id."))
                    partner.cs_cart_user_id = int(cs_id)

                exported += 1

            except Exception as e:
                _logger.error("Failed to export partner ID %s (%s): %s", partner.id, partner.name, str(e))
                failed.append(f"{partner.name}: {str(e)}")

        message = _("%s partner(s) exported successfully.") % exported
        if failed:
            message += _("\nFailed (%s):\n") % len(failed) + "\n".join(failed[:5])

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("CS-Cart Export"),
                "message": message,
                "type": "warning" if failed else "success",
                "sticky": bool(failed),
            },
        }


    def _prepare_vendor_payload(self, partner, company_id=1):
        """
        Prepare CS-Cart payload dictionary for exporting a vendor.

        :param partner: res.partner record set
        :type partner: res.partner
        :param company_id: Target company ID in CS-Cart
        :type company_id: int
        :return: Payload dictionary for CS-Cart API
        :rtype: dict
        """
        return {
            "user_type": "V",
            "company_id": partner.company_id or "",
            "email": partner.email,
            "firstname": partner.name,
            "status": "A",
        }

    def _prepare_cs_cart_customer_payload(self, partner, storefront_id=1):
        """
        Prepare CS-Cart payload dictionary for exporting a customer.

        :param partner: res.partner record set
        :type partner: res.partner
        :param storefront_id: Target storefront company ID in CS-Cart
        :type storefront_id: int
        :return: Payload dictionary for CS-Cart API
        :rtype: dict
        """
        names = (partner.name or "").split(" ", 1)
        firstname = names[0]
        lastname = names[1] if len(names) > 1 else ""

        return {
            "user_type": "C",
            "email": partner.email,
            "company_id": storefront_id or "",
            "firstname": firstname,
            "lastname": lastname,
            "phone": partner.phone or "",
            "address": partner.street or "",
            "address_2": partner.street2 or "",
            "city": partner.city or "",
            "zipcode": partner.zip or "",
            "country": partner.country_id.code if partner.country_id else "",
            "state": partner.state_id.code if partner.state_id else "",
            "status": "A",
        }
