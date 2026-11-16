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
import copy
import io
import logging
import os
import re
import requests
import tempfile
from docusign_esign import ApiClient, ApiException, EnvelopeDefinition, \
    Document, Recipients
from docusign_esign import EnvelopesApi
try:
    from docusign_esign import EventNotification, EnvelopeEvent, RecipientEvent
except ImportError:
    EventNotification, EnvelopeEvent, RecipientEvent = None, None, None
import time
from datetime import datetime, timedelta, timezone
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

_TOKEN_CACHE = {}  # (client_id, user_id, environment) -> (access_token, expire_timestamp)


def _get_docusign_endpoints(environment='demo'):
    """
    Returns (host, oauth_host_name) based on the environment ('demo' or 'production').
    """
    if environment == 'production':
        return 'https://www.docusign.net/restapi', 'account.docusign.com'
    return 'https://demo.docusign.net/restapi', 'account-d.docusign.com'


def get_docusign_access_token(integratorKey, user_id, privatekey, environment='demo'):
    """
    Retrieves a cached DocuSign access token or requests a new one if expired.
    DocuSign JWT tokens are valid for 3600 seconds (1 hour). Cached for 3300s (55 min).
    """
    cache_key = (integratorKey, user_id, environment)
    cached = _TOKEN_CACHE.get(cache_key)
    now = time.time()
    if cached and cached[1] > now:
        return cached[0]

    host, oauth_host_name = _get_docusign_endpoints(environment)
    api_client = ApiClient()
    api_client.host = host
    private_key = _get_private_key_bytes(privatekey)
    access_token_obj = api_client.request_jwt_user_token(
        client_id=integratorKey,
        user_id=user_id,
        oauth_host_name=oauth_host_name,
        private_key_bytes=private_key,
        expires_in=3600,
        scopes=["signature"]
    )
    token = access_token_obj.access_token
    _TOKEN_CACHE[cache_key] = (token, now + 3300)
    return token


def get_authenticated_api_client(integratorKey, user_id, privatekey, environment='demo'):
    """
    Returns an ApiClient authenticated with a valid cached Bearer access token.
    """
    host, _ = _get_docusign_endpoints(environment)
    api_client = ApiClient()
    api_client.host = host
    token = get_docusign_access_token(integratorKey, user_id, privatekey, environment=environment)
    api_client.set_default_header(header_name="Authorization",
                                  header_value=f"Bearer {token}")
    return api_client


def _get_private_key_bytes(privatekey):
    """
    Extracts the RSA private key bytes from the given privatekey object
    (ir.attachment record/recordset, bytes, or string).
    """
    if not privatekey:
        return b''
    # If it's an ir.attachment recordset
    if hasattr(privatekey, 'raw'):
        data = privatekey[:1].raw
    elif hasattr(privatekey, 'datas'):
        data = base64.b64decode(privatekey[:1].datas or b'')
    elif isinstance(privatekey, (bytes, memoryview)):
        data = bytes(privatekey)
    elif isinstance(privatekey, str):
        data = privatekey.encode('utf-8')
    else:
        data = b''

    if hasattr(data, 'content'):
        data = data.content
    elif isinstance(data, (bytes, bytearray, memoryview)):
        data = bytes(data)
    elif isinstance(data, str):
        data = data.encode('utf-8')

    # If the content was base64 encoded and not already in PEM format, decode it
    if data and not data.strip().startswith(b'-----BEGIN'):
        try:
            decoded = base64.b64decode(data, validate=True)
            if decoded.strip().startswith(b'-----BEGIN'):
                data = decoded
        except Exception as e:
            _logger.debug("Failed to decode base64 key: %s", e)

    return data


def action_login_docusign(user_id, account_id, integratorKey, privatekey, environment='demo'):
    """
    Logs in to DocuSign using JWT authentication with the provided credentials
    and retrieves the status code of a GET request to fetch brands under the
    specified account.
    """
    try:
        api_client = get_authenticated_api_client(integratorKey, user_id, privatekey, environment=environment)
        envelope_api = EnvelopesApi(api_client)

        from_date = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
        envelope_api.list_status_changes(
            account_id=account_id,
            from_date=from_date)
        token = get_docusign_access_token(integratorKey, user_id, privatekey, environment=environment)
        headers = {'Authorization': f"Bearer {token}",
                   'Accept': 'application/json'}
        _host, oauth_host_name = _get_docusign_endpoints(environment)
        url = f"https://{oauth_host_name}/restapi/v2.1/accounts/{account_id}/brands"
        response = requests.get(url=url, headers=headers, timeout=10)
        status = response.status_code
        return status
    except ApiException as err:
        raise UserError(err)

def _get_pdf_page_dimensions(raw_bytes):
    """Return a mapping of 1-based page numbers to (width, height) in PDF points."""
    default_dims = (595.0, 792.0)
    dims = {'default': default_dims}
    if not raw_bytes:
        return dims

    try:
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(raw_bytes))
        for idx, page in enumerate(reader.pages, start=1):
            box = page.cropbox or page.mediabox
            w = abs(float(box.width))
            h = abs(float(box.height))
            if int(page.get('/Rotate', 0) or 0) % 180 == 90:
                w, h = h, w
            if w > 0 and h > 0:
                dims[idx] = (w, h)
                if idx == 1:
                    dims['default'] = (w, h)
        if len(dims) > 1:
            return dims
    except Exception as e:
        _logger.debug("Could not read PDF dimensions via pypdf, falling back to regex: %s", e)

    boxes = re.findall(
        rb'/(?:CropBox|MediaBox)\s*\[\s*([0-9.\-]+)\s+([0-9.\-]+)\s+([0-9.\-]+)\s+([0-9.\-]+)\s*\]',
        raw_bytes,
    )
    for idx, (x0, y0, x1, y1) in enumerate(boxes, start=1):
        try:
            w = abs(float(x1) - float(x0))
            h = abs(float(y1) - float(y0))
            if w > 0 and h > 0:
                dims[idx] = (w, h)
                if idx == 1:
                    dims['default'] = (w, h)
        except ValueError:
            continue
    return dims


def _clamp_user_tabs(user_tabs, page_dims):
    """Adjust and clamp tab coordinates so DocuSign never rejects out-of-bounds tabs."""
    if user_tabs.get('signHereTabs'):
        for d in user_tabs['signHereTabs']:
            if isinstance(d, dict) and 'yPosition' in d and d['yPosition'] is not None:
                d['yPosition'] = max(0, d['yPosition'] - 30)

    for tab_key, tab_list in user_tabs.items():
        if not isinstance(tab_list, list):
            continue
        margin_x, margin_y = (100, 50) if tab_key == 'signHereTabs' else (180, 50)
        for d in tab_list:
            if not isinstance(d, dict):
                continue
            try:
                page_num = int(d.get('pageNumber') or 1)
            except (TypeError, ValueError):
                page_num = 1
            page_w, page_h = page_dims.get(page_num, page_dims.get('default', (595.0, 792.0)))
            if 'xPosition' in d and d['xPosition'] is not None:
                max_x = max(0, int(page_w) - margin_x)
                d['xPosition'] = max(0, min(int(round(float(d['xPosition']))), max_x))
            if 'yPosition' in d and d['yPosition'] is not None:
                max_y = max(0, int(page_h) - margin_y)
                d['yPosition'] = max(0, min(int(round(float(d['yPosition']))), max_y))


def action_send_docusign_file(user_id, account_id, integratorKey, privatekey,
                              filename,
                              fileContents, receiver_name, receiver_email,
                              tabs1, webhook_url=None, environment='demo'):
    """
      Sends a document for signature via DocuSign.
    """
    raw_pdf_bytes = b''
    if hasattr(fileContents, 'to_base64'):
        base64_file_content = fileContents.to_base64()
        try:
            raw_pdf_bytes = base64.b64decode(base64_file_content)
        except Exception:
            raw_pdf_bytes = b''
    elif isinstance(fileContents, (bytes, bytearray, memoryview)):
        raw_pdf_bytes = bytes(fileContents)
        base64_file_content = base64.b64encode(raw_pdf_bytes).decode('ascii')
    elif isinstance(fileContents, str):
        base64_file_content = fileContents
        try:
            raw_pdf_bytes = base64.b64decode(fileContents)
        except Exception:
            raw_pdf_bytes = b''
    else:
        base64_file_content = ''

    page_dims = _get_pdf_page_dimensions(raw_pdf_bytes)

    signers_list = []
    for i in range(0, len(receiver_email)):
        signer = {'email': receiver_email[i], 'name': receiver_name[i],
                  'recipientId': i + 1}
        if tabs1 and i < len(tabs1) and isinstance(tabs1[i], dict):
            user_tabs = copy.deepcopy(tabs1[i])
            _clamp_user_tabs(user_tabs, page_dims)
            user_tabs.pop('recipient', None)
            if any(isinstance(v, list) and len(v) > 0 for v in user_tabs.values()):
                signer['tabs'] = user_tabs
        signers_list.append(signer)

    file_ext = os.path.splitext(filename or '')[1].lstrip('.').lower() or 'pdf'

    # Create the document model
    document = Document(  # create the DocuSign document object
        document_base64=base64_file_content,
        name=filename,  # can be different from actual file name
        file_extension=file_ext,  # many different document types are accepted
        document_id=1  # a label used to reference the doc
    )

    envelope_kwargs = {
        'email_subject': "Please sign this document",
        'documents': [document],
        'recipients': Recipients(signers=signers_list),
        'status': "sent",
    }

    if webhook_url and webhook_url.startswith('https://') and EventNotification:
        try:
            envelope_kwargs['event_notification'] = EventNotification(
                url=webhook_url,
                logging_enabled="true",
                require_acknowledgment="true",
                use_soap_interface="false",
                include_certificate_with_soap="false",
                sign_hash_with_w_sec="false",
                include_documents="false",
                include_envelope_xml="true",
                envelope_events=[
                    EnvelopeEvent(envelope_event_status_code="completed"),
                    EnvelopeEvent(envelope_event_status_code="declined"),
                    EnvelopeEvent(envelope_event_status_code="voided"),
                    EnvelopeEvent(envelope_event_status_code="sent"),
                    EnvelopeEvent(envelope_event_status_code="delivered"),
                ],
                recipient_events=[
                    RecipientEvent(recipient_event_status_code="Completed"),
                    RecipientEvent(recipient_event_status_code="Declined"),
                    RecipientEvent(recipient_event_status_code="Delivered"),
                    RecipientEvent(recipient_event_status_code="Sent"),
                ]
            )
        except Exception as e:
            _logger.warning("Could not attach EventNotification to DocuSign envelope: %s", e)

    envelope_definition = EnvelopeDefinition(**envelope_kwargs)

    try:
        api_client = get_authenticated_api_client(integratorKey, user_id, privatekey, environment=environment)
        envelope_api = EnvelopesApi(api_client)
        response = envelope_api.create_envelope(
            account_id=account_id,
            envelope_definition=envelope_definition)
        return response
    # append "/envelopes" to the baseUrl and use in the request
    except ApiException as err:
        raise UserError(err)


def download_documents(integratorKey, envelopeId, privatekey, user_id, account_id, environment='demo'):
    """
    Downloads the completed document from DocuSign using a cached authenticated client.
    Single-pass check: queries status and downloads document in one session if completed.
    """
    try:
        api_client = get_authenticated_api_client(integratorKey, user_id, privatekey, environment=environment)
        envelope_api = EnvelopesApi(api_client)

        results = envelope_api.get_envelope(account_id, envelopeId)
        doc_status = results.status
        complete_path = ''

        if doc_status != 'completed':
            return doc_status, complete_path

        # Get the document list from the envelope
        documents = envelope_api.list_documents(
            account_id=account_id,
            envelope_id=envelopeId
        )

        # Get the actual document binary content
        document_binary = envelope_api.get_document(
            account_id=account_id,
            document_id='1',  # usually the document ID is '1' for the main signed doc
            envelope_id=envelopeId
        )

        attach_file_name = (
            documents.envelope_documents[0].name
            if (documents.envelope_documents and documents.envelope_documents[0].name)
            else f"{envelopeId}.pdf"
        )
        if not attach_file_name.lower().endswith('.pdf'):
            attach_file_name += '.pdf'

        # Use tempfile directory instead of server root_path
        temp_dir = tempfile.mkdtemp(prefix="docusign_")
        complete_path = os.path.join(temp_dir, attach_file_name)

        # Save the binary content to temporary file
        with open(complete_path, "wb") as f:
            f.write(document_binary)

        return doc_status, complete_path

    except ApiException as err:
        raise UserError(_("DocuSign API Error: %s", err))  # pylint: disable=prefer-env-translation
    except Exception as ex:
        raise UserError(_("Unexpected Error: %s", ex))  # pylint: disable=prefer-env-translation


def get_status(integratorKey, envelopeId, privatekey, user_id, account_id, environment='demo'):
    """
    Retrieve the status of a DocuSign envelope.
    """
    try:
        api_client = get_authenticated_api_client(integratorKey, user_id, privatekey, environment=environment)
        envelope_api = EnvelopesApi(api_client)
        results = envelope_api.get_envelope(account_id, envelopeId)
        return results.status
    except ApiException as err:
        raise UserError(err)

