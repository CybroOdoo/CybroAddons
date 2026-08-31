# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#
#    This program is under the terms of the Odoo Proprietary License v1.0(OPL-1)
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
import datetime
import requests
from odoo import fields, http
from odoo.http import request


class QuickBooksControllers(http.Controller):
    """ A controller to fetch the access token from the quickbook """
    @http.route(['/quickbook_access'], type="http", auth="public",
                csrf=False)
    def quickbook_access(self, **kw):
        """ Function to get the access token from quickbook """
        if kw.get('code'):
            quickbooks_id = request.env['quickbooks.connector'].search(
                [('quickbooks_realm', '=', kw.get('realmId'))], limit=1)
            quickbooks_id.write({
                'quickbooks_auth_code': kw.get('code'),
                'quickbooks_realm': kw.get('realmId')
            })
            b64 = str(
                quickbooks_id.quickbooks_client + ":" +
                quickbooks_id.quickbooks_client_secret).encode('utf-8')
            b64 = base64.b64encode(b64).decode('utf-8')
            headers = {
                'Authorization': 'Basic ' + b64,
                'Accept': 'application/json',
            }
            base_url = request.env['ir.config_parameter'].sudo().get_param(
                'web.base.url')
            payload = {
                'code': str(kw.get('code')),
                'redirect_uri': f'{base_url}/quickbook_access',
                'grant_type': 'authorization_code'
            }
            req = requests.post(quickbooks_id.quickbooks_access_token_url,
                                data=payload, headers=headers)
            if req.json() and req.json().get('access_token'):
                quickbooks_id.write({
                    'quickbooks_access_token': req.json().get('access_token'),
                    'quickbooks_refresh_token': req.json().get(
                        'refresh_token'),
                    'quickbooks_access_token_expiry': fields.Datetime.now()
                                                      + datetime.timedelta(
                        seconds=req.json().get('expires_in')),
                    'quickbooks_refresh_token_expiry': fields.Datetime.now()
                                                       + datetime.timedelta(
                        seconds=req.json().get('x_refresh_token_expires_in')),
                    'authorised': True
                })
                action = request.env.ref(
                    'odoo_quickbooks_online_connector'
                    '.action_quickbooks_connector')
                return request.redirect(
                    f'''/web#id={quickbooks_id.id}&view_type=form&model=cybrosys.quickbooks.data&action={action.id}''')
            else:
                return 'Something went wrong'
