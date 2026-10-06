# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
import logging
import requests
from datetime import timedelta
from odoo import models, fields, api, tools
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

FFN_TOKEN_URL = 'https://oauth2.api.jtl-software.com/token'

FFN_API_URLS = {
    'sandbox':    'https://ffn-sbx.api.jtl-software.com',
    'production': 'https://ffn2.api.jtl-software.com',
}


class JtlFfnConfig(models.Model):
    """
    JTL FFN Configuration and Connection Manager.

    One record = one FFN tenant / credential set.
    Multiple records are supported for multi-warehouse/multi-tenant setups.
    """
    _name = 'jtl.ffn.config'
    _description = 'JTL FFN Configuration and Connection Manager'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string="Profile Name", required=True, default="JTL FFN Live", tracking=True,
        help="Name of this JTL FFN configuration profile."
    )
    environment = fields.Selection([
        ('sandbox',    'Sandbox / Testing'),
        ('production', 'Production / Live'),
    ], string="Environment", default='sandbox', required=True, tracking=True,
        help="Target environment for API requests (Sandbox or Production).")

    client_id     = fields.Char(
        string="Client ID", required=True, tracking=True,
        help="OAuth2 Client ID provided by JTL FFN."
    )
    client_secret = fields.Char(
        string="Client Secret", required=True,
        help="OAuth2 Client Secret provided by JTL FFN."
    )

    refresh_token = fields.Char(
        string="Refresh Token",
        copy=False,
        help="Paste the refresh_token obtained from a one-time manual OAuth login at "
             "https://oauth2.api.jtl-software.com/authorize. "
             "The connector uses this to obtain access tokens automatically."
    )

    access_token = fields.Char(
        string="Active Token", copy=False,
        help="Currently active OAuth2 access token for JTL FFN API."
    )

    token_expiry = fields.Datetime(
        string="Token Expires At", copy=False, tracking=True,
        help="Expiration timestamp of the current access token."
    )
    active = fields.Boolean(
        string="Active", default=True, tracking=True,
        help="Indicates whether this JTL FFN profile is active for synchronization. "
             "Inactive (archived) profiles are excluded from all scheduled sync jobs."
    )
    auth_code    = fields.Char(
        string="Authorization Code", copy=False,
        help="One-time authorization code retrieved during OAuth login."
    )

    sync_products = fields.Boolean(
        string="Sync Products", default=True, tracking=True,
        help="Enable synchronization of products to JTL FFN."
    )
    sync_stock    = fields.Boolean(
        string="Sync Stock", default=True, tracking=True,
        help="Enable pulling stock levels from JTL FFN into Odoo."
    )
    sync_orders   = fields.Boolean(
        string="Push Orders", default=True, tracking=True,
        help="Enable pushing sale orders to JTL FFN for fulfillment."
    )
    sync_tracking = fields.Boolean(
        string="Pull Tracking", default=True, tracking=True,
        help="Enable pulling tracking numbers for shipped orders from JTL FFN."
    )
    sync_returns  = fields.Boolean(
        string="Sync Returns", default=True, tracking=True,
        help="Enable pulling customer returns from JTL FFN."
    )

    fallback_shipping_method_id = fields.Char(
        string="Fallback Shipping Method ID", tracking=True,
        help="Fallback shipping method ID sent to JTL FFN when no specific mapping exists."
    )
    fallback_shipping_type = fields.Selection([
        ('Standard', 'Standard'),
        ('Express', 'Express'),
        ('Freight', 'Freight'),
        ('Postal', 'Postal')
    ], string="Fallback Shipping Type", default='Standard', tracking=True,
        help="Fallback shipping type (Standard, Express, Freight, Postal) used for FFN orders.")

    warehouse_ids = fields.One2many(
        'jtl.ffn.warehouse', 'config_id', string="Fulfillment Warehouses",
        help="List of fulfillment warehouses mapped under this profile."
    )

    connection_state = fields.Selection([
        ('not_tested', 'Not Tested'),
        ('ok',         'Connected'),
        ('error',      'Error'),
    ], string="Connection Status", default='not_tested', copy=False, tracking=True,
        help="Current API connection status for this configuration profile.")
    connection_error = fields.Char(
        string="Last Error", copy=False,
        help="Details of the last connection or authentication error."
    )

    def write(self, vals):
        """Override write to conditionally log connection errors to the chatter."""
        res = super().write(vals)
        if vals.get('connection_state') == 'error' and vals.get('connection_error'):
            for record in self:
                record.message_post(
                    body=f"<b>Connection Error:</b> {vals.get('connection_error')}",
                    subtype_xmlid="mail.mt_note"
                )
        return res

    def _get_base_url(self):
        """Return the canonical base URL of this Odoo instance (from system parameter)."""
        base = self.env['ir.config_parameter'].sudo().get_param('web.base.url', 'http://localhost:8069')
        return base.rstrip('/')

    def _get_access_token(self):
        """Fetch a fresh access token using the OAuth2 Refresh Token Grant."""
        self.ensure_one()
        if not self.refresh_token:
            raise UserError(
                "JTL FFN: No Refresh Token configured. "
                "Please perform a one-time manual login at:\n"
                "https://oauth2.api.jtl-software.com/authorize"
                "?response_type=code"
                "&redirect_uri=%s"
                "&client_id=%s"
                "&scope=ffn.merchant.read%%20ffn.merchant.write\n\n"
                "Then exchange the code for tokens and paste the "
                "refresh_token into the Refresh Token field." % (self._get_base_url(), self.client_id)
            )
        try:
            c_id = (self.client_id or '').strip()
            c_secret = (self.client_secret or '').strip()
            r_token = (self.refresh_token or '').strip()
            
            resp = requests.post(
                FFN_TOKEN_URL,
                auth=(c_id, c_secret),
                data={
                    'grant_type':    'refresh_token',
                    'refresh_token': r_token,
                    'client_id':     c_id,
                    'client_secret': c_secret,
                },
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                timeout=15,
            )
            
            if not resp.ok:
                try:
                    err_detail = resp.json()
                    err_msg = "%s - %s" % (err_detail.get('error'), err_detail.get('error_description'))
                except Exception:
                    err_msg = resp.text
                raise UserError("JTL OAuth Server rejected credentials: %s (HTTP %s)" % (err_msg, resp.status_code))
                
            data = resp.json()
            token         = data.get('access_token')
            new_refresh   = data.get('refresh_token')
            expires_in    = data.get('expires_in', 1800)
            expiry        = fields.Datetime.now() + timedelta(seconds=max(expires_in - 600, 60))
            write_vals = {
                'access_token':     token,
                'token_expiry':     expiry,
                'connection_state': 'ok',
                'connection_error': False,
            }
            if new_refresh:
                write_vals['refresh_token'] = new_refresh
            self.write(write_vals)
            return token
        except UserError as err:
            self.write({
                'connection_state': 'error',
                'connection_error': str(err.args[0] if err.args else err),
            })
            raise
        except Exception as exc:
            self.write({
                'connection_state': 'error',
                'connection_error': str(exc),
            })
            raise UserError("JTL FFN auth failed: %s" % exc)

    def _get_valid_token(self):
        """Return a cached token, refreshing it when expired."""
        self.ensure_one()
        self.invalidate_recordset()
        if (
            not self.access_token
            or not self.token_expiry
            or fields.Datetime.now() >= self.token_expiry
        ):
            return self._get_access_token()
        return self.access_token

    def _api_request(self, method, path, json=None, params=None):
        """Make an authenticated HTTP request to the JTL FFN REST API."""
        self.ensure_one()
        base   = FFN_API_URLS[self.environment]
        token  = self._get_valid_token()
        
        if path.startswith('/v1/'):
            path = '/api/v1/merchant/' + path[4:]
            
        url    = "%s%s" % (base, path)
        headers = {
            'Authorization': 'Bearer %s' % token,
            'Content-Type':  'application/json',
            'Accept':        'application/json',
        }
        resp = requests.request(
            method, url, json=json, params=params,
            headers=headers, timeout=30,
        )
        if resp.status_code == 401:
            _logger.warning("FFN: 401 on %s, forcing token refresh", path)
            self.write({'access_token': False, 'token_expiry': False})
            self.invalidate_recordset()
            token = self._get_access_token()
            headers['Authorization'] = 'Bearer %s' % token
            resp = requests.request(
                method, url, json=json, params=params,
                headers=headers, timeout=30,
            )
        if not resp.ok:
            raise UserError(
                "JTL FFN API error [%s %s]: %s" % (resp.status_code, path, resp.text[:400])
            )
        if resp.content:
            return resp.json()
        return {}

    def action_exchange_auth_code(self):
        """Exchange a one-time OAuth authorization code for access and refresh tokens."""
        self.ensure_one()
        if not self.auth_code:
            raise UserError("Please enter an Authorization Code first.")
        try:
            c_id = (self.client_id or '').strip()
            c_secret = (self.client_secret or '').strip()
            code = (self.auth_code or '').strip()
            resp = requests.post(
                FFN_TOKEN_URL,
                auth=(c_id, c_secret),
                data={
                    'grant_type':    'authorization_code',
                    'code':          code,
                    'redirect_uri':  self._get_base_url(),
                    'client_id':     c_id,
                    'client_secret': c_secret,
                },
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                timeout=15,
            )
            if not resp.ok:
                try:
                    err_detail = resp.json()
                    err_msg = "%s - %s" % (err_detail.get('error'), err_detail.get('error_description'))
                except Exception:
                    err_msg = resp.text
                raise UserError("JTL OAuth Server rejected auth code: %s (HTTP %s)" % (err_msg, resp.status_code))
            data = resp.json()
            token = data.get('access_token')
            new_refresh = data.get('refresh_token')
            expires_in = data.get('expires_in', 1800)
            expiry = fields.Datetime.now() + timedelta(seconds=max(expires_in - 600, 60))
            self.write({
                'refresh_token': new_refresh,
                'access_token': token,
                'token_expiry': expiry,
                'connection_state': 'ok',
                'connection_error': False,
                'auth_code': False,
            })
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Exchange Successful',
                    'message': 'Refresh token received and saved.',
                    'type': 'success',
                    'sticky': False,
                    'next': {
                        'type': 'ir.actions.client',
                        'tag': 'reload',
                    }
                }
            }
        except Exception as exc:
            self.write({
                'connection_state': 'error',
                'connection_error': str(exc.args[0] if hasattr(exc, 'args') and exc.args else exc),
            })
            if not tools.config['test_enable']:
                self.env.cr.commit()
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Exchange Failed',
                    'message': str(exc.args[0] if hasattr(exc, 'args') and exc.args else exc),
                    'type': 'danger',
                    'sticky': True,
                    'next': {
                        'type': 'ir.actions.client',
                        'tag': 'reload',
                    }
                }
            }

    def action_test_connection(self):
        """Test the connection by fetching a fresh access token."""
        self.ensure_one()
        try:
            self._get_access_token()
            return {
                'type':   'ir.actions.client',
                'tag':    'display_notification',
                'params': {
                    'title':   'Connection Successful',
                    'message': 'Token retrieved and cached. Profile "%s" is ready.' % self.name,
                    'type':    'success',
                    'sticky':  False,
                    'next': {
                        'type': 'ir.actions.client',
                        'tag': 'reload',
                    }
                }
            }
        except Exception as exc:
            return {
                'type':   'ir.actions.client',
                'tag':    'display_notification',
                'params': {
                    'title':   'Connection Failed',
                    'message': str(exc.args[0] if hasattr(exc, 'args') and exc.args else exc),
                    'type':    'danger',
                    'sticky':  True,
                    'next': {
                        'type': 'ir.actions.client',
                        'tag': 'reload',
                    }
                }
            }

    def action_run_full_sync(self):
        """Trigger all enabled sync operations manually."""
        self.ensure_one()
        results = []
        errors = []

        def _run(label, fn):
            """Execute a single sync function and track errors."""
            try:
                count = fn()
                results.append("%s: %d" % (label, count or 0))
            except Exception as exc:
                errors.append("%s failed: %s" % (label, str(exc)[:120]))
                _logger.error("FFN manual sync — %s failed: %s", label, exc)

        if self.sync_products:
            _run("Products pushed", lambda: self.env['jtl.ffn.product.sync'].sync_products_to_ffn(self))
        if self.sync_stock:
            _run("Stock lines updated", lambda: self.env['jtl.ffn.product.sync'].pull_stock_from_ffn(self))
        if self.sync_orders:
            _run("Orders sent", lambda: self.env['jtl.ffn.order.sync'].push_pending_orders(self))
        if self.sync_tracking:
            _run("Tracking numbers imported", lambda: self.env['jtl.ffn.tracking'].pull_tracking_numbers(self))
        if self.sync_returns:
            _run("Returns synced", lambda: self.env['jtl.ffn.return'].pull_returns(self))

        if not results and not errors:
            msg = "Nothing to sync — all sync options are disabled."
            notif_type = "warning"
        elif errors:
            msg = " | ".join(results + errors)
            notif_type = "warning"
        else:
            msg = " | ".join(results)
            notif_type = "success"

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Full Sync Complete',
                'message': msg,
                'type': notif_type,
                'sticky': bool(errors),
                'next': {
                    'type': 'ir.actions.client',
                    'tag': 'reload',
                },
            },
        }

    @api.model
    def cron_refresh_tokens(self):
        """Cron job: proactively refresh tokens that are close to expiring."""
        # Find active configs that have a refresh token
        configs = self.search([('active', '=', True), ('refresh_token', '!=', False)])
        now = fields.Datetime.now()
        refreshed = 0
        for config in configs:
            # Refresh if token expires in less than 5 minutes or already expired
            if not config.token_expiry or config.token_expiry < now or (config.token_expiry - now).total_seconds() < 300:
                try:
                    config._get_access_token()
                    refreshed += 1
                except Exception as e:
                    _logger.error("Failed to proactively refresh token for FFN config %s: %s", config.name, e)
        return refreshed
