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
import base64
import json
import logging
import requests
import uuid
from odoo import _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class EagleDocAPI:
    """HTTP client for the Eagle Doc REST API."""

    def __init__(self, env):
        """Initialise the client by loading credentials from system parameters."""
        self.env = env
        self.api_key = self.env['ir.config_parameter'].sudo().get_param('eagle_doc.api_key')
        base_url_setting = self.env['ir.config_parameter'].sudo().get_param('eagle_doc.base_url')
        self.base_url = (base_url_setting or "https://bookkeeping-api-sandbox.eagle-doc.com").strip()

    def _get_headers(self, idempotency_key=None):
        """Get headers for Eagle Doc API requests."""
        if not self.api_key:
            raise UserError(_("Eagle Doc API Key is not configured."))
        headers = {
            "X-Partner-Api-Key": self.api_key,
            "Accept": "application/json",
        }
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key
        return headers

    def _extract_error_message(self, error):
        """Extract a human-readable message from HTTP error response."""
        try:
            body = error.response.json()
            code = body.get("code", "")
            message = body.get("message", "")
            return f"{code}: {message}".strip(": ")
        except Exception:
            return error.response.text if error.response is not None else str(error)

    def get_or_create_default_sub_business(self):
        """Get or create the default Eagle Doc sub-business ID for the company."""
        company = self.env.company

        if company.eagle_sub_business_id:
            _logger.debug(
                "Eagle Doc: reusing existing sub-business '%s' for company '%s' (id=%s).",
                company.eagle_sub_business_id, company.name, company.id,
            )
            return company.eagle_sub_business_id

        headers = self._get_headers()
        url = f"{self.base_url}/api/partner/v1/businesses"
        payload = {
            "externalRef": f"odoo-company-{company.id}",
            "businessName": company.name or "Default Company",
            "businessCurrency": company.currency_id.name or "EUR",
            "businessCountry": company.country_id.code or "DE",
            "businessDescription": (
                f"Odoo company: {company.name or ''} "
                f"(id={company.id}) — auto-created by Eagle Doc Connector"
            ),
            "businessIndustry": "IT",
            "bkAccountType": "SKR04",
        }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            response_json = response.json()
            sub_business_id = response_json.get("id")
            _logger.info(
                "Eagle Doc: created sub-business '%s' for company '%s' (id=%s). Response: %s",
                sub_business_id, company.name, company.id, response_json,
            )
        except requests.exceptions.HTTPError as error:
            status_code = error.response.status_code if error.response is not None else None
            if status_code == 403:
                raise UserError(_("Eagle Doc: API key lacks the 'manage:businesses' scope."))
            else:
                detail = self._extract_error_message(error)
                _logger.error(
                    "Eagle Doc: sub-business creation failed for company '%s' (id=%s): %s",
                    company.name, company.id, detail,
                )
                raise UserError(_("Eagle Doc API error: %s") % detail)
        except requests.exceptions.RequestException as error:
            _logger.error(
                "Eagle Doc: sub-business creation failed for company '%s' (id=%s): %s",
                company.name, company.id, str(error),
            )
            raise UserError(_("Eagle Doc API error: %s") % str(error))

        if not sub_business_id:
            raise UserError(_(
                "Eagle Doc did not return a sub-business ID for company '%s'. "
                "Please check your API key and try again."
            ) % company.name)

        company.sudo().eagle_sub_business_id = sub_business_id
        return sub_business_id

    def upload_invoice(self, sub_business_id, attachment, doc_type="INCOMING_INVOICE",
                       idempotency_key=None, timeout=30):
        """Upload an invoice document to Eagle Doc."""
        if not sub_business_id:
            raise UserError(_("A sub-business ID is required to upload to Eagle Doc."))

        if not idempotency_key:
            idempotency_key = str(uuid.uuid4())

        headers = self._get_headers(idempotency_key)
        url = f"{self.base_url}/api/partner/v1/businesses/{sub_business_id}/invoices"

        filename = attachment.name
        file_data = base64.b64decode(attachment.datas)

        files = {
            'file': (filename, file_data, attachment.mimetype),
        }
        data = {
            'docType': doc_type,
        }

        try:
            response = requests.post(url, headers=headers, files=files, data=data, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as error:
            status_code = error.response.status_code if error.response is not None else None
            if status_code == 404:
                raise UserError(_("Eagle Doc: sub-business not found or not owned by this partner."))
            elif status_code == 400:
                detail = self._extract_error_message(error)
                raise UserError(_("Eagle Doc: %s") % detail)
            elif status_code == 409:
                raise UserError(_("Eagle Doc: idempotency key conflict — retry was sent before the "
                                  "first request finished, or the key was reused for a different "
                                  "sub-business. Please retry."))
            else:
                _logger.error("Eagle Doc API upload error: %s", str(error))
                raise UserError(_("Eagle Doc API error: %s") % str(error))
        except requests.exceptions.RequestException as error:
            _logger.error("Eagle Doc API upload error: %s", str(error))
            raise UserError(_("Eagle Doc API error: %s") % str(error))

    def get_invoice_status(self, sub_business_id, task_id, timeout=30):
        """Get the status of an uploaded invoice task."""
        headers = self._get_headers()
        url = f"{self.base_url}/api/partner/v1/businesses/{sub_business_id}/invoices/{task_id}/status"

        try:
            response = requests.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as error:
            status_code = error.response.status_code if error.response is not None else None
            if status_code == 404:
                raise UserError(_("Eagle Doc: task or sub-business not found."))
            else:
                detail = self._extract_error_message(error)
                _logger.error("Eagle Doc status check error: %s", detail)
                raise UserError(_("Eagle Doc API error: %s") % detail)
        except requests.exceptions.RequestException as error:
            _logger.error("Eagle Doc status check error: %s", str(error))
            raise UserError(_("Eagle Doc API error: %s") % str(error))

    def get_invoice_statuses_batch(self, sub_business_id, task_ids, timeout=30):
        """Batch poll processing statuses for multiple invoice tasks."""
        if not task_ids:
            raise UserError(_("Eagle Doc: no task ids to poll."))
        if len(task_ids) > 200:
            raise UserError(_("Eagle Doc: cannot poll more than 200 tasks per batch request."))

        headers = self._get_headers()
        url = f"{self.base_url}/api/partner/v1/businesses/{sub_business_id}/invoices/status"
        params = {"taskIds": ",".join(task_ids)}

        try:
            response = requests.get(url, headers=headers, params=params, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as error:
            status_code = error.response.status_code if error.response is not None else None
            if status_code == 400:
                raise UserError(_("Eagle Doc: batch status request was invalid (empty or over 200 task ids)."))
            detail = self._extract_error_message(error)
            _logger.error("Eagle Doc batch status check error: %s", detail)
            raise UserError(_("Eagle Doc API error: %s") % detail)
        except requests.exceptions.RequestException as error:
            _logger.error("Eagle Doc batch status check error: %s", str(error))
            raise UserError(_("Eagle Doc API error: %s") % str(error))

    def get_processed_document(self, sub_business_id, document_id, timeout=30):
        """Fetch extracted data for a processed document."""
        headers = self._get_headers()
        url = f"{self.base_url}/api/partner/v1/businesses/{sub_business_id}/documents/{document_id}"

        try:
            response = requests.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()
            response_json = response.json()
            _logger.debug("Eagle Doc document response: %s", response_json)
            return response_json
        except requests.exceptions.HTTPError as error:
            status_code = error.response.status_code if error.response is not None else None
            if status_code == 404:
                raise UserError(_("Eagle Doc: document not found."))
            else:
                detail = self._extract_error_message(error)
                _logger.error("Eagle Doc document fetch error: %s", detail)
                raise UserError(_("Eagle Doc API error: %s") % detail)
        except requests.exceptions.RequestException as error:
            _logger.error("Eagle Doc document fetch error: %s", str(error))
            raise UserError(_("Eagle Doc API error: %s") % str(error))

    def list_sub_businesses(self, query=None, page=0, size=20, sort="businessName,asc", timeout=30):
        """List sub-businesses owned by this partner."""
        headers = self._get_headers()
        url = f"{self.base_url}/api/partner/v1/businesses"
        params = {"page": page, "size": size, "sort": sort}
        if query:
            params["q"] = query

        try:
            response = requests.get(url, headers=headers, params=params, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as error:
            detail = self._extract_error_message(error)
            _logger.error("Eagle Doc list sub-businesses error: %s", detail)
            raise UserError(_("Eagle Doc API error: %s") % detail)
        except requests.exceptions.RequestException as error:
            _logger.error("Eagle Doc list sub-businesses error: %s", str(error))
            raise UserError(_("Eagle Doc API error: %s") % str(error))

    def get_sub_business(self, sub_business_id, timeout=30):
        """Fetch one sub-business's full profile by its ID."""
        headers = self._get_headers()
        url = f"{self.base_url}/api/partner/v1/businesses/{sub_business_id}"

        try:
            response = requests.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as error:
            status_code = error.response.status_code if error.response is not None else None
            if status_code == 404:
                raise UserError(_("Eagle Doc: sub-business not found or not owned by this partner."))
            detail = self._extract_error_message(error)
            _logger.error("Eagle Doc get sub-business error: %s", detail)
            raise UserError(_("Eagle Doc API error: %s") % detail)
        except requests.exceptions.RequestException as error:
            _logger.error("Eagle Doc get sub-business error: %s", str(error))
            raise UserError(_("Eagle Doc API error: %s") % str(error))

    def create_sub_business(self, payload, timeout=30):
        """Create a new sub-business under this partner."""
        headers = self._get_headers()
        url = f"{self.base_url}/api/partner/v1/businesses"

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as error:
            status_code = error.response.status_code if error.response is not None else None
            if status_code == 403:
                raise UserError(_("Eagle Doc: API key lacks the 'manage:businesses' scope."))
            detail = self._extract_error_message(error)
            _logger.error("Eagle Doc create sub-business error: %s", detail)
            raise UserError(_("Eagle Doc API error: %s") % detail)
        except requests.exceptions.RequestException as error:
            _logger.error("Eagle Doc create sub-business error: %s", str(error))
            raise UserError(_("Eagle Doc API error: %s") % str(error))

    def batch_create_sub_businesses(self, businesses, timeout=60):
        """Batch create multiple sub-businesses."""
        if not businesses:
            raise UserError(_("Eagle Doc: no sub-businesses to create."))
        if len(businesses) > 200:
            raise UserError(_("Eagle Doc: cannot create more than 200 sub-businesses per request."))

        headers = self._get_headers()
        url = f"{self.base_url}/api/partner/v1/businesses/batch"

        try:
            response = requests.post(url, headers=headers, json={"businesses": businesses}, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as error:
            status_code = error.response.status_code if error.response is not None else None
            if status_code == 400:
                raise UserError(_("Eagle Doc: batch was empty or exceeded 200 items (PARTNER_BATCH_INVALID)."))
            detail = self._extract_error_message(error)
            _logger.error("Eagle Doc batch-create sub-businesses error: %s", detail)
            raise UserError(_("Eagle Doc API error: %s") % detail)
        except requests.exceptions.RequestException as error:
            _logger.error("Eagle Doc batch-create sub-businesses error: %s", str(error))
            raise UserError(_("Eagle Doc API error: %s") % str(error))

    def delete_sub_business(self, sub_business_id, timeout=30):
        """Soft-delete a sub-business. Returns ``True`` on success (HTTP 204)."""
        headers = self._get_headers()
        url = f"{self.base_url}/api/partner/v1/businesses/{sub_business_id}"

        try:
            response = requests.delete(url, headers=headers, timeout=timeout)
            response.raise_for_status()
            return True
        except requests.exceptions.HTTPError as error:
            status_code = error.response.status_code if error.response is not None else None
            if status_code == 404:
                raise UserError(_("Eagle Doc: sub-business not found or not owned by this partner."))
            detail = self._extract_error_message(error)
            _logger.error("Eagle Doc delete sub-business error: %s", detail)
            raise UserError(_("Eagle Doc API error: %s") % detail)
        except requests.exceptions.RequestException as error:
            _logger.error("Eagle Doc delete sub-business error: %s", str(error))
            raise UserError(_("Eagle Doc API error: %s") % str(error))

    def update_sub_business(self, sub_business_id, payload, timeout=30):
        """Partially update a sub-business profile."""
        headers = self._get_headers()
        url = f"{self.base_url}/api/partner/v1/businesses/{sub_business_id}"

        try:
            response = requests.patch(url, headers=headers, json=payload, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as error:
            status_code = error.response.status_code if error.response is not None else None
            if status_code == 404:
                raise UserError(_("Eagle Doc: sub-business not found or not owned by this partner."))
            detail = self._extract_error_message(error)
            _logger.error("Eagle Doc update sub-business error: %s", detail)
            raise UserError(_("Eagle Doc API error: %s") % detail)
        except requests.exceptions.RequestException as error:
            _logger.error("Eagle Doc update sub-business error: %s", str(error))
            raise UserError(_("Eagle Doc API error: %s") % str(error))

    def sync_vendor_customers_batch(self, sub_business_id, items, timeout=60):
        """Batch sync vendor/customer data to Eagle Doc."""
        if not sub_business_id:
            raise UserError(_("A sub-business ID is required to sync vendor/customer data."))
        if not items:
            raise UserError(_("Eagle Doc: no vendor/customer records to sync."))
        if len(items) > 500:
            raise UserError(_("Eagle Doc: cannot sync more than 500 vendor/customer records per request."))

        headers = self._get_headers()
        url = f"{self.base_url}/api/partner/v1/businesses/{sub_business_id}/vendor-customers/batch"

        try:
            response = requests.post(url, headers=headers, json={"vendorCustomers": items}, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as error:
            status_code = error.response.status_code if error.response is not None else None
            detail = self._extract_error_message(error)
            if status_code == 404:
                raise UserError(_("Eagle Doc: sub-business not found or not owned by this partner."))
            elif status_code == 400:
                raise UserError(_("Eagle Doc rejected the vendor/customer sync: %s") % detail)
            _logger.error("Eagle Doc vendor/customer sync error: %s", detail)
            raise UserError(_("Eagle Doc API error: %s") % detail)
        except requests.exceptions.RequestException as error:
            _logger.error("Eagle Doc vendor/customer sync error: %s", str(error))
            raise UserError(_("Eagle Doc API error: %s") % str(error))

    def submit_vendor_feedback(self, sub_business_id, payload, timeout=30):
        """Submit vendor feedback for matching correction."""
        if not sub_business_id:
            raise UserError(_("A sub-business ID is required to submit feedback."))

        headers = self._get_headers()
        url = f"{self.base_url}/api/partner/v1/businesses/{sub_business_id}/feedback/vendor-account-matching"

        _logger.info("Eagle Doc Vendor Feedback Request JSON:\n%s", json.dumps(payload, indent=4))

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=timeout)
            if response.status_code >= 400:
                _logger.error("Eagle Doc Vendor Feedback Error Response Content:\n%s", response.text)

            response.raise_for_status()
            response_json = response.json()
            _logger.info("Eagle Doc Vendor Feedback Response JSON:\n%s", json.dumps(response_json, indent=4))

            return response_json
        except requests.exceptions.HTTPError as error:
            status_code = error.response.status_code if error.response is not None else None
            if status_code == 404:
                raise UserError(_("Eagle Doc: sub-business not found or not owned by this partner."))
            elif status_code == 400:
                raise UserError(_("Eagle Doc: missing required fields for vendor feedback."))
            detail = self._extract_error_message(error)
            _logger.error("Eagle Doc vendor feedback error: %s", detail)
            raise UserError(_("Eagle Doc API error: %s") % detail)
        except requests.exceptions.RequestException as error:
            _logger.error("Eagle Doc vendor feedback error: %s", str(error))
            raise UserError(_("Eagle Doc API error: %s") % str(error))

    def submit_product_feedback(self, sub_business_id, payload, timeout=30):
        """Submit account/tax matching feedback for a vendor or product."""
        if not sub_business_id:
            raise UserError(_("A sub-business ID is required to submit feedback."))

        headers = self._get_headers()
        url = f"{self.base_url}/api/partner/v1/businesses/{sub_business_id}/feedback/product-account-matching"

        _logger.info("Eagle Doc Product Feedback Request JSON:\n%s", json.dumps(payload, indent=4))

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=timeout)
            if response.status_code >= 400:
                _logger.error("Eagle Doc Product Feedback Error Response Content:\n%s", response.text)

            response.raise_for_status()
            response_json = response.json()
            _logger.info("Eagle Doc Product Feedback Response JSON:\n%s", json.dumps(response_json, indent=4))

            return response_json
        except requests.exceptions.HTTPError as error:
            status_code = error.response.status_code if error.response is not None else None
            if status_code == 404:
                raise UserError(_("Eagle Doc: sub-business not found or not owned by this partner."))
            elif status_code == 400:
                raise UserError(_("Eagle Doc: missing required fields for product/account feedback."))
            detail = self._extract_error_message(error)
            _logger.error("Eagle Doc product feedback error: %s", detail)
            raise UserError(_("Eagle Doc API error: %s") % detail)
        except requests.exceptions.RequestException as error:
            _logger.error("Eagle Doc product feedback error: %s", str(error))
            raise UserError(_("Eagle Doc API error: %s") % str(error))

    def get_usage(self, period=None, timeout=30):
        """Fetch partner-wide usage statistics for a billing period."""
        headers = self._get_headers()
        url = f"{self.base_url}/api/partner/v1/usage"
        params = {"period": period} if period else {}

        try:
            response = requests.get(url, headers=headers, params=params, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as error:
            status_code = error.response.status_code if error.response is not None else None
            if status_code == 400:
                raise UserError(_("Eagle Doc: invalid period format. Use YYYY-MM."))
            detail = self._extract_error_message(error)
            _logger.error("Eagle Doc usage fetch error: %s", detail)
            raise UserError(_("Eagle Doc API error: %s") % detail)
        except requests.exceptions.RequestException as error:
            _logger.error("Eagle Doc usage fetch error: %s", str(error))
            raise UserError(_("Eagle Doc API error: %s") % str(error))