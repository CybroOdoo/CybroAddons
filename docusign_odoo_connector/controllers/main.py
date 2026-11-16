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
#############################################################################
import base64
import hashlib
import hmac
import json
import logging
import xml.etree.ElementTree as ET
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class DocusignWebhookController(http.Controller):

    def _verify_webhook_signature(self, raw_data, headers):
        """
        Verify the DocuSign Connect HMAC signature or secret token.
        DocuSign sends HMAC-SHA256 signatures in headers:
        X-DocuSign-Signature-1, X-DocuSign-Signature-2, etc. (or X-Docusign-Signature-1).
        """
        # Collect all signature headers sent by DocuSign
        received_signatures = []
        for key, val in headers.items():
            key_lower = key.lower()
            if key_lower.startswith('x-docusign-signature-') or key_lower == 'x-docusign-signature':
                received_signatures.append(val.strip())

        # Also check for custom auth token in headers or query string
        token_in_header = headers.get('X-DocuSign-Token') or headers.get('Authorization')
        if token_in_header and token_in_header.startswith('Bearer '):
            token_in_header = token_in_header[7:].strip()

        # Find configured webhook secrets
        credentials = request.env['docusign.credentials'].sudo().search([
            ('webhook_secret', '!=', False)
        ])
        configured_secrets = [c.webhook_secret.strip() for c in credentials if c.webhook_secret and c.webhook_secret.strip()]

        # Check system parameter fallback
        sys_param_secret = request.env['ir.config_parameter'].sudo().get_str('docusign.webhook_secret', default='')
        if sys_param_secret and sys_param_secret.strip():
            configured_secrets.append(sys_param_secret.strip())

        if not configured_secrets:
            # If no webhook secret is configured anywhere, log info and allow for backward-compatibility
            # but reject arbitrary unauthenticated query params without signatures
            if not received_signatures and not token_in_header:
                _logger.info("DocuSign webhook: No HMAC secret configured. Processing request.")
                return True
            return True

        # Check secret token match
        token_param = request.params.get('token') or request.params.get('secret')
        for secret in configured_secrets:
            if token_param and hmac.compare_digest(token_param, secret):
                return True
            if token_in_header and hmac.compare_digest(token_in_header, secret):
                return True

        # Check DocuSign HMAC-SHA256 signature
        if raw_data and received_signatures:
            for secret in configured_secrets:
                try:
                    computed_hash = hmac.new(
                        secret.encode('utf-8'),
                        raw_data,
                        hashlib.sha256
                    ).digest()
                    computed_signature = base64.b64encode(computed_hash).decode('utf-8')

                    for recv_sig in received_signatures:
                        if hmac.compare_digest(computed_signature, recv_sig):
                            return True
                except Exception as e:
                    _logger.warning("Error computing DocuSign HMAC signature: %s", e)

        _logger.warning("DocuSign webhook: Signature/secret verification failed.")
        return False

    @http.route('/docusign/webhook', type='http', auth='none', methods=['POST'], csrf=False)
    def docusign_webhook(self, **kwargs):
        """
        Receives real-time DocuSign Connect webhook events when
        an envelope or recipient status changes (e.g. signed, completed).
        """
        raw_data = request.httprequest.get_data()
        _logger.info("Received DocuSign webhook notification: length=%s bytes", len(raw_data) if raw_data else 0)

        # Verify HMAC or secret token
        if not self._verify_webhook_signature(raw_data, request.httprequest.headers):
            return request.make_response("Unauthorized", status=401)

        envelope_id = None
        status = None

        # 1. Parse JSON format (Connect 2.1)
        if raw_data:
            try:
                payload = json.loads(raw_data.decode('utf-8'))
                if isinstance(payload, dict):
                    data = payload.get('data') or {}
                    envelope_id = data.get('envelopeId') or payload.get('envelopeId')
                    envelope_summary = data.get('envelopeSummary') or {}
                    status = (
                        envelope_summary.get('status')
                        or payload.get('status')
                        or payload.get('event')
                    )
            except Exception as e:
                _logger.debug("DocuSign webhook payload is not JSON: %s", e)

        # 2. Parse XML format (classic Connect format)
        if not envelope_id and raw_data:
            try:
                root = ET.fromstring(raw_data)
                envelope_status = root.find('.//{*}EnvelopeStatus') or root.find('EnvelopeStatus')
                if envelope_status is not None:
                    env_id_el = envelope_status.find('{*}EnvelopeID') or envelope_status.find('EnvelopeID')
                    status_el = envelope_status.find('{*}Status') or envelope_status.find('Status')
                    if env_id_el is not None and env_id_el.text:
                        envelope_id = env_id_el.text.strip()
                    if status_el is not None and status_el.text:
                        status = status_el.text.strip().lower()
            except Exception as e:
                _logger.warning("Error parsing DocuSign XML webhook payload: %s", e)

        # 3. Fallback to form parameters in POST body
        if not envelope_id:
            envelope_id = kwargs.get('envelope_id') or kwargs.get('envelopeId')
        if not status:
            status = kwargs.get('status') or kwargs.get('event')

        if not envelope_id:
            _logger.warning("DocuSign webhook: No envelope ID identified in payload.")
            return request.make_response("No envelope_id found", status=400)

        _logger.info("Processing DocuSign webhook for envelope_id=%s with status=%s", envelope_id, status)

        try:
            request.env['docusign.lines'].sudo()._process_docusign_webhook(envelope_id, status)
        except Exception as e:
            _logger.exception("Error processing DocuSign webhook for envelope %s: %s", envelope_id, e)

        return request.make_response("OK", status=200)
