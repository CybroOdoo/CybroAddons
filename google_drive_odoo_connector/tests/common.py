# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Abhijith CK (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from datetime import timedelta
from unittest.mock import MagicMock
from odoo import fields

GOOGLE_FILE = {
    'id': 'gfile_123',
    'name': 'test.txt',
    'mimeType': 'text/plain',
    'webViewLink': 'https://drive.google.com/file/d/gfile_123/view',
    'size': '11',
    'thumbnailLink': 'https://lh3.googleusercontent.com/thumb=s220',
}


def mock_response(status_code=200, json_data=None, content=b'', text='',
                  headers=None):
    """Return a fake requests.Response with configurable values."""
    response = MagicMock()
    response.status_code = status_code
    response.json.return_value = json_data or {}
    response.content = content
    response.text = text
    response.headers = headers or {}
    if status_code >= 400:
        response.raise_for_status.side_effect = Exception(
            'HTTP %s' % status_code)
    return response


def create_account(env, **vals):
    """Create a google.drive.account with a valid, non-expired token."""
    values = {
        'name': 'Test Drive',
        'client_id': 'client-id',
        'client_secret': 'client-secret',
        'refresh_token': 'refresh-token',
        'access_token': 'access-token',
        'token_expiry': fields.Datetime.now() + timedelta(hours=1),
        'state': 'connected',
    }
    values.update(vals)
    return env['google.drive.account'].create(values)
