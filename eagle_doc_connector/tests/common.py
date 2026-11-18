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
from unittest.mock import patch

import requests
from odoo.addons.account.tests.common import AccountTestInvoicingCommon

API = 'odoo.addons.eagle_doc_connector.models.eagle_api.requests'


def set_param(env, key, value):
    """Set a system parameter independently of the ir.config_parameter API."""
    icp = env['ir.config_parameter'].sudo()
    record = icp.search([('key', '=', key)], limit=1)
    if record:
        record.value = value
    else:
        icp.create({'key': key, 'value': value})


def get_param(env, key):
    """Return a system parameter value, or False when unset."""
    record = env['ir.config_parameter'].sudo().search(
        [('key', '=', key)], limit=1)
    return record.value if record else False


class FakeResponse:
    """Minimal stand-in for ``requests.Response``."""

    def __init__(self, status_code=200, payload=None, text=''):
        """Store the status code, JSON payload and body text."""
        self.status_code = status_code
        self._payload = {} if payload is None else payload
        self.text = text

    def json(self):
        """Return the payload, or raise it when it is an exception."""
        if isinstance(self._payload, Exception):
            raise self._payload
        return self._payload

    def raise_for_status(self):
        """Raise ``HTTPError`` for 4xx and 5xx statuses."""
        if self.status_code >= 400:
            raise requests.exceptions.HTTPError(
                f"HTTP {self.status_code}", response=self)


def http_error(status_code, payload=None):
    """Return a fake error response with the given status code."""
    return FakeResponse(status_code, payload)


class EagleDocCommon(AccountTestInvoicingCommon):
    """Shared fixtures: API key configured and HTTP calls patchable."""

    @classmethod
    def setUpClass(cls):
        """Create the shared fixtures."""
        super().setUpClass()
        set_param(cls.env, 'eagle_doc.api_key', 'test-key')
        set_param(cls.env, 'eagle_doc.base_url', 'https://eagle.test')
        cls.company = cls.env.company

    def patch_http(self, verb, response=None, side_effect=None):
        """Patch ``requests.<verb>`` inside the Eagle Doc API module."""
        return patch.object(
            requests, verb,
            return_value=response, side_effect=side_effect)

    def make_move(self, move_type='in_invoice', **kwargs):
        """Create a draft invoice or bill with one line."""
        vals = {
            'move_type': move_type,
            'partner_id': self.partner_a.id,
            'invoice_date': '2026-01-15',
            'invoice_line_ids': [(0, 0, {
                'name': 'Line',
                'quantity': 1,
                'price_unit': 100.0,
                'tax_ids': [(6, 0, [])],
            })],
        }
        vals.update(kwargs)
        return self.env['account.move'].create(vals)
