# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Akhil @ cybrosys,(odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###############################################################################
import base64
import os
import requests
from docusign_esign import ApiClient, ApiException, EnvelopeDefinition, \
    Document, Recipients
from docusign_esign import EnvelopesApi
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError

root_path = '.'


def action_login_docusign(user_id, account_id, integratorKey, privatekey):
    """
    Logs in to DocuSign using JWT authentication with the provided credentials
    and retrieves the status code of a GET request to fetch brands under the
    specified account.
    """
    api_client = ApiClient()
    api_client.host = 'https://demo.docusign.net/restapi'

    SCOPES = ["signature"]
    private_key = base64.b64decode(privatekey.datas)
    try:
        access_token = api_client.request_jwt_user_token(
            client_id=integratorKey,
            user_id=user_id,
            oauth_host_name="account-d.docusign.com",
            private_key_bytes=private_key,
            expires_in=3600,
            scopes=SCOPES
        )
        api_client.set_default_header(header_name="Authorization",
                                      header_value=f"Bearer {access_token.access_token}")
        envelope_api = EnvelopesApi(api_client)

        from_date = (datetime.utcnow() - timedelta(days=30)).isoformat()
        envelope_api.list_status_changes(
            account_id=account_id,
            from_date=from_date)
        headers = {'Authorization': f"Bearer {access_token.access_token}",
                   'Accept': 'application/json'}
        url = 'https://account-d.docusign.com/restapi/v2.1/accounts/' + account_id + '/brands'
        response = requests.get(url=url, headers=headers)
        status = response.status_code
        return status
    except ApiException as err:
        raise UserError(err)


def action_send_docusign_file(user_id, account_id, integratorKey, privatekey,
                              filename,
                              fileContents, receiver_name, receiver_email,
                              tabs1):
    """
      Sends a document for signature via DocuSign.
    """
    signers_list = []
    for i in range(0, len(receiver_email)):
        a = tabs1[i]['signHereTabs']
        for d in a:
            d['yPosition'] -= 30
        signer = {'email': receiver_email[i], 'name': receiver_name[i],
                  'recipientId': i + 1, 'tabs': tabs1[i]}
        signers_list.append(signer)
    api_client = ApiClient()
    envelope_api = EnvelopesApi(api_client)

    base64_file_content = fileContents.decode('ascii')

    # Create the document model
    document = Document(  # create the DocuSign document object
        document_base64=base64_file_content,
        name=filename,  # can be different from actual file name
        file_extension='pdf',  # many different document types are accepted
        document_id=1  # a label used to reference the doc
    )

    envelope_definition = EnvelopeDefinition(
        email_subject="Please sign this document",
        documents=[document],
        # The Recipients object wants arrays for each recipient type
        recipients=Recipients(signers=signers_list),
        status="sent")
    api_client.host = 'https://demo.docusign.net/restapi'
    SCOPES = ["signature"]

    private_key = base64.b64decode(privatekey.datas)
    try:
        access_token = api_client.request_jwt_user_token(
            client_id=integratorKey,
            user_id=user_id,
            oauth_host_name="account-d.docusign.com",
            private_key_bytes=private_key,
            expires_in=3600,
            scopes=SCOPES
        )
        api_client.set_default_header(header_name="Authorization",
                                      header_value=f"Bearer {access_token.access_token}")
        response = envelope_api.create_envelope(
            account_id=account_id,
            envelope_definition=envelope_definition)
        return response
    # append "/envelopes" to the baseUrl and use in the request
    except ApiException as err:
        raise UserError(err)


def download_documents(integratorKey, envelopeId, privatekey, user_id, account_id):
    """
    Downloads the completed document from DocuSign.
    """
    doc_status = get_status(integratorKey, envelopeId, privatekey, user_id, account_id)
    complete_path = ''

    if doc_status != 'completed':
        return doc_status, complete_path

    api_client = ApiClient()
    envelope_api = EnvelopesApi(api_client)
    api_client.host = 'https://demo.docusign.net/restapi'
    SCOPES = ["signature"]

    private_key = base64.b64decode(privatekey.datas)

    try:
        access_token = api_client.request_jwt_user_token(
            client_id=integratorKey,
            user_id=user_id,
            oauth_host_name="account-d.docusign.com",
            private_key_bytes=private_key,
            expires_in=3600,
            scopes=SCOPES
        )
        api_client.set_default_header(header_name="Authorization",
                                      header_value=f"Bearer {access_token.access_token}")

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

        # Prepare save path
        directory_path = os.path.join(root_path, "files")
        if not os.path.isdir(directory_path):
            try:
                os.mkdir(directory_path)
            except Exception:
                raise ValidationError("Please provide access rights to create files in this module.")

        attach_file_name = documents.envelope_documents[0].name or 'signed_document.pdf'
        file_path = os.path.join("files", attach_file_name)
        complete_path = os.path.join(root_path, file_path)

        # Save the binary content to disk
        with open(complete_path, "wb") as f:
            f.write(document_binary)

        return doc_status, complete_path

    except ApiException as err:
        raise UserError(f"DocuSign API Error: {err}")
    except Exception as ex:
        raise UserError(f"Unexpected Error: {ex}")


def get_status(integratorKey, envelopeId, privatekey, user_id, account_id):
    """
    Retrieve the status of a DocuSign envelope recipient.
    """
    # Get Envelope Recipient Status
    # append "/envelopes/" + envelopeId + "/recipients" to baseUrl and use in the request
    api_client = ApiClient()
    envelope_api = EnvelopesApi(api_client)
    api_client.host = 'https://demo.docusign.net/restapi'
    SCOPES = ["signature"]

    private_key = base64.b64decode(privatekey.datas)
    try:
        access_token = api_client.request_jwt_user_token(
            client_id=integratorKey,
            user_id=user_id,
            oauth_host_name="account-d.docusign.com",
            private_key_bytes=private_key,
            expires_in=3600,
            scopes=SCOPES
        )
        api_client.set_default_header(header_name="Authorization",
                                      header_value=f"Bearer {access_token.access_token}")

        results = envelope_api.get_envelope(
            account_id, envelopeId)
        return results.status
    except ApiException as err:
        raise UserError(err)
