# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0 (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NON INFRINGEMENT. IN NO EVENT SHALL
#    THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,DAMAGES OR OTHER
#    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,ARISING
#    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
###############################################################################
import logging
from odoo import models, fields, api, _
from odoo.exceptions import AccessError
from odoo.addons.eagle_doc_connector.models.eagle_api import EagleDocAPI

_logger = logging.getLogger(__name__)

EAGLE_DOC_VENDOR_CUSTOMER_BATCH_SIZE = 500

class ResPartner(models.Model):
    """Adds Eagle Doc vendor/customer sync tracking to partners."""

    _inherit = 'res.partner'

    is_eagle_doc_synced = fields.Boolean(
        string="Synced to Eagle Doc",
        copy=False,
        help="Whether this vendor/customer's master data has been pushed to "
             "Eagle Doc's vendor/customer matching database.",
    )
    eagle_doc_last_sync = fields.Datetime(
        string="Eagle Doc Last Sync",
        copy=False,
    )

    def write(self, vals):
        """Flag vendors/customers as needing re-sync when a matching-relevant field changes."""
        res = super().write(vals)
        relevant_fields = {'name', 'vat', 'street', 'city', 'zip', 'country_id',
                           'supplier_rank', 'customer_rank'}
        if relevant_fields.intersection(vals.keys()):
            partners_to_flag = self.filtered(lambda partner: partner.supplier_rank > 0 or partner.customer_rank > 0)
            if partners_to_flag:
                partners_to_flag.with_context(eagle_doc_skip_flag=True).write({'is_eagle_doc_synced': False})
        return res

    def action_eagle_doc_sync_now(self):
        """Manually sync selected partners to Eagle Doc in batches."""
        if not self.env.su and not self.env.user.has_group('account.group_account_user'):
            raise AccessError(_("Only accountants can sync vendors/customers to Eagle Doc."))

        partners = self.filtered(lambda p: p.supplier_rank > 0 or p.customer_rank > 0)
        if not partners:
            return
        api_client = EagleDocAPI(self.env)
        sub_business_id = api_client.get_or_create_default_sub_business()
        partner_list = list(partners)
        total_created = total_updated = total_failed = 0
        for i in range(0, len(partner_list), EAGLE_DOC_VENDOR_CUSTOMER_BATCH_SIZE):
            chunk = partner_list[i:i + EAGLE_DOC_VENDOR_CUSTOMER_BATCH_SIZE]
            items = [partner._eagle_doc_vendor_customer_payload() for partner in chunk]
            result = api_client.sync_vendor_customers_batch(sub_business_id, items)
            total_created += result.get('created', 0)
            total_updated += result.get('updated', 0)
            total_failed += result.get('failed', 0)
            row_results = result.get('results', [])
            synced_ids = []
            for partner, row in zip(chunk, row_results):
                if not row.get('error'):
                    synced_ids.append(partner.id)
            if synced_ids:
                self.env['res.partner'].browse(synced_ids).with_context(
                    eagle_doc_skip_flag=True
                ).write({
                    'is_eagle_doc_synced': True,
                    'eagle_doc_last_sync': fields.Datetime.now(),
                })

            for partner, row in zip(chunk, row_results):
                if row.get('error'):
                    partner.message_post(body=_(
                        "Eagle Doc: vendor/customer sync failed for this record: %s"
                    ) % row.get('error'))
        _logger.info(
            "Eagle Doc: vendor/customer sync finished — created=%s updated=%s failed=%s (of %s)",
            total_created, total_updated, total_failed, len(partner_list),
        )
        return {
            'created': total_created,
            'updated': total_updated,
            'failed': total_failed,
        }

    def _eagle_doc_account_number(self):
        """Get the unique account number key for Eagle Doc partner matching."""
        self.ensure_one()
        return (self.vat or '').strip() or f"odoo-partner-{self.id}"

    def _eagle_doc_vendor_customer_payload(self):
        """Build the vendor/customer payload for Eagle Doc batch upsert."""
        self.ensure_one()
        is_vendor = self.supplier_rank > 0
        is_customer = self.customer_rank > 0
        if is_vendor and is_customer:
            partner_type = "BOTH"
        elif is_customer:
            partner_type = "CUSTOMER"
        else:
            partner_type = "VENDOR"
        return {
            "externalRef": f"odoo-partner-{self.id}",
            "accountNumber": self._eagle_doc_account_number(),
            "companyName": self.name or '',
            "type": partner_type,
            "street": self.street or '',
            "city": self.city or '',
            "zip": self.zip or '',
            "country": self.country_id.code or '',
            "vatId": self.vat or '',
        }

    @api.model
    def _cron_sync_eagle_doc_vendor_customers(self):
        """Cron job to sync unsynced or modified partners to Eagle Doc."""
        partners = self.search([
            ('is_eagle_doc_synced', '=', False),
            '|', ('supplier_rank', '>', 0), ('customer_rank', '>', 0),
        ])
        if not partners:
            return
        partners.action_eagle_doc_sync_now()
