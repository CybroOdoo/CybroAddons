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
from odoo.exceptions import UserError
from odoo.addons.eagle_doc_connector.models.eagle_api import EagleDocAPI

_logger = logging.getLogger(__name__)


class ResCompany(models.Model):
    """Adds Eagle Doc sub-business linkage and profile-sync tracking to companies."""

    _inherit = 'res.company'

    eagle_sub_business_id = fields.Char(
        string="Eagle Doc Sub-Business ID",
        copy=False,
        help=(
            "The Eagle Doc sub-business ID linked to this company. "
            "Created automatically on first document upload. "
            "Each company in a multi-company setup has its own sub-business "
            "so documents are always uploaded to the correct Eagle Doc workspace."
        ),
    )
    eagle_sub_business_industry = fields.Selection([
        ('IT', 'IT'),
        ('RETAIL', 'Retail'),
        ('MANUFACTURING', 'Manufacturing'),
        ('CONSTRUCTION', 'Construction'),
        ('HEALTHCARE', 'Healthcare'),
        ('FINANCE', 'Finance'),
        ('EDUCATION', 'Education'),
        ('TRANSPORTATION', 'Transportation'),
        ('REAL_ESTATE', 'Real Estate'),
        ('RESTAURANT', 'Restaurant'),
        ('HOSPITALITY', 'Hospitality'),
        ('CONSULTING', 'Consulting'),
        ('SOFTWARE', 'Software'),
        ('LEGAL', 'Legal'),
        ('MARKETING', 'Marketing'),
        ('NON_PROFIT', 'Non-Profit'),
        ('OTHER', 'Other'),
    ], string="Eagle Doc Industry", default='IT',
        help="Used by Eagle Doc's AI classification when creating the sub-business.")
    eagle_sub_business_account_type = fields.Selection([
        ('SKR03', 'SKR03'),
        ('SKR04', 'SKR04'),
        ('SELF_DEFINED', 'Self-Defined'),
    ], string="Eagle Doc Account Standard", default='SKR04',
        help="DATEV chart-of-accounts standard used for this sub-business.")
    is_eagle_doc_profile_synced = fields.Boolean(
        string="Eagle Doc Profile Synced",
        default=True,
        copy=False,
        help=(
            "Whether the profile fields sent to Eagle Doc (name, address, "
            "industry, account standard, contact info) match what was last "
            "pushed. Automatically cleared when a relevant field is edited; "
            "set again after a successful Create or Update push."
        ),
    )

    is_eagle_doc_auto_create_partner = fields.Boolean(
        string="Auto-create Customer/Vendor",
        default=True,
        help="If enabled (default), a customer/vendor extracted by Eagle "
             "Doc that doesn't exist in Odoo is created automatically. "
             "If disabled, the document is left without a partner and "
             "flagged for manual review.",
    )
    is_eagle_doc_auto_create_product = fields.Boolean(
        string="Auto-create Product",
        default=False,
        help="If enabled, a product extracted by Eagle Doc that doesn't "
             "match any existing product.product is created automatically. "
             "If disabled (default), the line is kept as free text with no "
             "product_id set.",
    )
    is_eagle_doc_auto_create_tax = fields.Boolean(
        string="Auto-create Tax",
        default=False,
        help="If enabled, a tax rate extracted by Eagle Doc that doesn't "
             "match any existing account.tax is created automatically, "
             "using the placeholder tax accounts configured below. If "
             "disabled (default), tax is left blank on the line and the "
             "document is flagged for manual review — this is the safer "
             "option since an incorrect tax misstates a legal liability.",
    )
    eagle_doc_auto_tax_account_sale_id = fields.Many2one(
        'account.account',
        string="Placeholder Tax Account (Sales)",
        help="Used as the tax account when Eagle Doc auto-creates a Sales "
             "tax with no existing match. Required for auto-creating sale "
             "taxes; if left empty, auto-creation is skipped and the "
             "document is flagged for manual review instead.",
    )
    eagle_doc_auto_tax_account_purchase_id = fields.Many2one(
        'account.account',
        string="Placeholder Tax Account (Purchases)",
        help="Used as the tax account when Eagle Doc auto-creates a "
             "Purchase tax with no existing match. Required for "
             "auto-creating purchase taxes; if left empty, auto-creation "
             "is skipped and the document is flagged for manual review "
             "instead.",
    )

    def write(self, vals):
        """Flag the profile as out of sync when a field sent to Eagle Doc changes."""
        res = super().write(vals)
        relevant_fields = {
            'name', 'street', 'city', 'zip', 'country_id', 'currency_id',
            'vat', 'email', 'phone',
            'eagle_sub_business_industry', 'eagle_sub_business_account_type',
        }
        if relevant_fields.intersection(vals.keys()) and 'is_eagle_doc_profile_synced' not in vals:
            companies_with_link = self.filtered('eagle_sub_business_id')
            if companies_with_link:
                companies_with_link.is_eagle_doc_profile_synced = False
        return res

    def action_eagle_create_sub_business(self):
        """Create or fetch the Eagle Doc sub-business for this company."""
        self.ensure_one()
        if self.eagle_sub_business_id:
            raise UserError(_(
                "This company is already linked to Eagle Doc sub-business '%s'. "
                "Delete the link first if you want to re-create it."
            ) % self.eagle_sub_business_id)

        api_client = EagleDocAPI(self.env)
        payload = {
            "externalRef": f"odoo-company-{self.id}",
            "businessName": self.name or "Unnamed Company",
            "businessCurrency": self.currency_id.name or "EUR",
            "businessCountry": self.country_id.code or "DE",
            "businessDescription": f"Odoo company: {self.name or ''} (id={self.id})",
            "businessIndustry": self.eagle_sub_business_industry or 'IT',
            "bkAccountType": self.eagle_sub_business_account_type or 'SKR04',
            "email": self.email or '',
            "phone": self.phone or '',
            "street": self.street or '',
            "city": self.city or '',
            "zipCode": self.zip or '',
            "vatId": self.vat or '',
        }
        result = api_client.create_sub_business(payload)
        sub_business_id = result.get('id')
        if not sub_business_id:
            raise UserError(_("Eagle Doc did not return a sub-business ID."))

        self.eagle_sub_business_id = sub_business_id
        self.is_eagle_doc_profile_synced = True
        self.message_post(body=_(
            "Eagle Doc: sub-business created/linked (id: %s)."
        ) % sub_business_id)

    def action_eagle_refresh_sub_business(self):
        """Refresh and log the company's sub-business profile from Eagle Doc."""
        self.ensure_one()
        if not self.eagle_sub_business_id:
            raise UserError(_("This company has no linked Eagle Doc sub-business yet."))

        api_client = EagleDocAPI(self.env)
        result = api_client.get_sub_business(self.eagle_sub_business_id)
        self.message_post(body=_(
            "Eagle Doc sub-business profile: %s"
        ) % result)

    def action_eagle_update_sub_business(self):
        """Update the linked sub-business profile with current company data."""
        self.ensure_one()
        if not self.eagle_sub_business_id:
            raise UserError(_(
                "This company has no linked Eagle Doc sub-business yet. "
                "Create one first."
            ))

        api_client = EagleDocAPI(self.env)
        payload = {
            "businessName": self.name or "Unnamed Company",
            "businessCurrency": self.currency_id.name or "EUR",
            "businessCountry": self.country_id.code or "DE",
            "businessDescription": f"Odoo company: {self.name or ''} (id={self.id})",
            "businessIndustry": self.eagle_sub_business_industry or 'IT',
            "bkAccountType": self.eagle_sub_business_account_type or 'SKR04',
            "email": self.email or '',
            "phone": self.phone or '',
            "street": self.street or '',
            "city": self.city or '',
            "zipCode": self.zip or '',
            "vatId": self.vat or '',
        }
        api_client.update_sub_business(self.eagle_sub_business_id, payload)
        self.is_eagle_doc_profile_synced = True
        self.message_post(body=_(
            "Eagle Doc: sub-business '%s' profile updated from Odoo company data."
        ) % self.eagle_sub_business_id)
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _("Eagle Doc"),
                'message': _("Sub-business profile updated on Eagle Doc."),
                'type': 'success',
                'sticky': False,
            },
        }

    def action_eagle_delete_sub_business(self):
        """Delete the linked sub-business and clear the local reference."""
        self.ensure_one()
        if not self.eagle_sub_business_id:
            raise UserError(_("This company has no linked Eagle Doc sub-business to delete."))

        api_client = EagleDocAPI(self.env)
        api_client.delete_sub_business(self.eagle_sub_business_id)
        old_id = self.eagle_sub_business_id
        self.eagle_sub_business_id = False
        self.message_post(body=_(
            "Eagle Doc: sub-business '%s' deleted and unlinked from this company."
        ) % old_id)

    def action_eagle_batch_create_sub_businesses(self):
        """Batch create Eagle Doc sub-businesses for selected companies."""
        companies_to_create = self.filtered(lambda company: not company.eagle_sub_business_id)
        already_linked = self - companies_to_create
        if not companies_to_create:
            raise UserError(_(
                "All selected companies already have an Eagle Doc sub-business linked. "
                "Nothing to do."
            ))
        external_ref_to_company = {
            f"odoo-company-{company.id}": company for company in companies_to_create
        }
        payload = [
            {
                "externalRef": f"odoo-company-{company.id}",
                "businessName": company.name or "Unnamed Company",
                "businessCurrency": company.currency_id.name or "EUR",
                "businessCountry": company.country_id.code or "DE",
                "businessDescription": f"Odoo company: {company.name or ''} (id={company.id})",
                "businessIndustry": company.eagle_sub_business_industry or "IT",
                "bkAccountType": company.eagle_sub_business_account_type or "SKR04",
                "email": company.email or "",
                "phone": company.phone or "",
                "street": company.street or "",
                "city": company.city or "",
                "zipCode": company.zip or "",
                "vatId": company.vat or "",
            }
            for company in companies_to_create
        ]
        api_client = EagleDocAPI(self.env)
        result = api_client.batch_create_sub_businesses(payload)
        created = existed = failed = 0
        failed_names = []
        for result_item in result.get('results', []):
            external_ref = result_item.get('externalRef')
            company = external_ref_to_company.get(external_ref)
            if not company:
                continue
            outcome = (result_item.get('outcome') or '').upper()
            sub_business_id = result_item.get('subBusinessId')
            if outcome == 'FAILED' or not sub_business_id:
                failed += 1
                failed_names.append(company.name)
                _logger.error(
                    "Eagle Doc batch-create: failed for company '%s' (id=%s): %s",
                    company.name, company.id, result_item.get('error') or result_item,
                )
                continue
            company.eagle_sub_business_id = sub_business_id
            company.is_eagle_doc_profile_synced = True
            if outcome == 'EXISTS':
                existed += 1
            else:
                created += 1
            company.message_post(body=_(
                "Eagle Doc: sub-business created via batch (id: %s)."
            ) % sub_business_id)

        summary_parts = [_("%d created") % created, _("%d already existed") % existed]
        if failed:
            summary_parts.append(_("%d failed") % failed)
        if already_linked:
            summary_parts.append(_("%d skipped (already linked)") % len(already_linked))

        message = _("Eagle Doc batch sub-business creation: %s.") % ", ".join(summary_parts)
        if failed_names:
            message += _(" Failed: %s.") % ", ".join(failed_names)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _("Eagle Doc Batch Create"),
                'message': message,
                'type': 'warning' if failed else 'success',
                'sticky': bool(failed),
                'next': {
                    'type': 'ir.actions.client',
                    'tag': 'soft_reload',
                },
            },
        }

