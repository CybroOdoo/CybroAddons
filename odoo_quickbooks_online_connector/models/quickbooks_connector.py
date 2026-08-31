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
import json
import logging
import requests
from datetime import timedelta, datetime
from odoo.exceptions import UserError, ValidationError
from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)


class QuickbooksConnector(models.Model):
    """A class that represents a new model quickbooks connector"""
    _name = 'quickbooks.connector'
    _description = 'Quickbooks Connector Configuration'

    name = fields.Char(string='Name', required=True, copy=False,
                       help='The name of the store or record')
    quickbooks_auth_base_url = fields.Char(
        'Authorization URL',
        default="https://appcenter.intuit.com/connect/oauth2",
        help='Quickbooks Authorization URL')
    quickbooks_access_token_url = fields.Char(
        'Authorization Token URL',
        default="https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer",
        help='Quickbooks Authorization Token URL')
    quickbooks_api_url = fields.Char(
        'API URL',
        help='Quickbooks API URL')
    quickbooks_realm = fields.Char('Realm ID', required=True, copy=False,
                                   help='Quickbooks Realm ID')
    quickbooks_auth_code = fields.Char('Auth code',
                                       help='Quickbooks Authentication code')
    quickbooks_access_token = fields.Char(string='QuickBooks Token',
                                          help='Token provided by Quickbook')
    quickbooks_client_secret = fields.Char(string='QuickBooks Client Secret',
                                           required=True, copy=False,
                                           help='Client Secret given by'
                                                'Quickbook')
    quickbooks_client = fields.Char(string='QuickBooks Client ID',
                                    required=True, copy=False,
                                    help='Client ID given by Quickbook')
    quickbooks_refresh_token = fields.Char(string='QuickBooks Refresh Token',
                                           copy=False,
                                           help='Refresh token given by '
                                                'Quickbook')
    quickbooks_access_token_expiry = fields.Datetime(
        string='QuickBooks Access Token Expiry', copy=False,
        help='Expiry date of the access token')
    quickbooks_refresh_token_expiry = fields.Datetime(
        string='QuickBooks Refresh Token Expiry', copy=False,
        help='Expiry date of the refresh token')
    quickbooks_mode = fields.Selection(
        [('sandbox', 'Sandbox'), ('production', 'Production')],
        string='Mode', default='sandbox', help='The quickbook mode')
    minor_version = fields.Integer(string='Minor Version', default=3,
                                   help='Minor Version of quickbook')
    authorised = fields.Boolean(string='Authorised', default=False,
                                readonly=True, copy=False,
                                help='Is it authorised')

    @api.onchange('quickbooks_mode')
    def _onchange_quickbooks_mode(self):
        """Change the api url according to the mode"""
        self.quickbooks_api_url = 'https://sandbox-quickbooks.api.intuit.com/v3/company/' \
            if self.quickbooks_mode == 'sandbox' \
            else 'https://quickbooks.api.intuit.com/v3/company/'

    def action_quickbook_auth(self):
        """Returns QuickBooks authentication"""
        if not self.quickbooks_auth_base_url or not self.quickbooks_client:
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": "Error",
                    "message": "QuickBooks authentication parameters are "
                               "not set. Please configure the required "
                               "parameters.",
                    "sticky": True,
                }
            }
        try:
            base_url = self.env['ir.config_parameter'].sudo().get_param(
                'web.base.url')
            rtn_url = f'{base_url}/quickbook_access'
            url = f"""{self.quickbooks_auth_base_url}?client_id={self.quickbooks_client}&scope=com.intuit.quickbooks.accounting openid profile email phone address&redirect_uri={rtn_url}&response_type=code&state=state"""
            return {
                "type": "ir.actions.act_url",
                "url": url,
                "target": "self"
            }
        except Exception as e:
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": "Error",
                    "message": f"An error occurred while constructing the"
                               f" QuickBooks authentication URL: {str(e)}",
                    "sticky": True,
                }
            }

    def action_refresh_token(self):
        """Fetch the new token from QuickBooks"""
        try:
            if not all([self.quickbooks_client, self.quickbooks_client_secret,
                        self.quickbooks_refresh_token,
                        self.quickbooks_access_token_url]):
                return {
                    "type": "ir.actions.client",
                    "tag": "display_notification",
                    "params": {
                        "title": "Error",
                        "message": "QuickBooks token refresh parameters are"
                                   " not set. Please configure the required "
                                   "parameters.",
                        "sticky": True,
                    }
                }
            client_secret = f"{self.quickbooks_client}:{self.quickbooks_client_secret}"
            b64 = client_secret.encode('utf-8')
            b64 = base64.b64encode(b64).decode('utf-8')
            headers = {
                'Authorization': 'Basic ' + b64,
                'Accept': 'application/json'
            }
            data = {
                'grant_type': 'refresh_token',
                'refresh_token': self.quickbooks_refresh_token
            }
            req = requests.post(self.quickbooks_access_token_url,
                                headers=headers, data=data)
            if req.status_code == 200 and req.json() and req.json().get(
                    'access_token'):
                self.write({
                    'quickbooks_access_token': req.json().get('access_token'),
                    'quickbooks_refresh_token': req.json().get(
                        'refresh_token'),
                    'quickbooks_access_token_expiry':
                        fields.Datetime.now() + timedelta(
                            seconds=req.json().get('expires_in')),
                    'quickbooks_refresh_token_expiry':
                        fields.Datetime.now() + timedelta(
                            seconds=req.json().get(
                                'x_refresh_token_expires_in')),
                })
                return {
                    "type": "ir.actions.client",
                    "tag": "display_notification",
                    "params": {
                        "title": "Success",
                        "message": "Token refresh successful.",
                        "sticky": False,
                    }
                }
            else:
                error_message = req.json().get(
                    'error_description') if req.json() and req.json().get(
                    'error_description') else 'Unknown error'
                return {
                    "type": "ir.actions.client",
                    "tag": "display_notification",
                    "params": {
                        "title": "Error",
                        "message": f"Token refresh failed: {error_message}",
                        "sticky": True,
                    }
                }
        except Exception as e:
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": "Error",
                    "message": f"An error occurred during token refresh: {str(e)}",
                    "sticky": True,
                }
            }

    def get_import_query(self):
        """Gets the import query"""
        if self.quickbooks_access_token:
            headers = {
                'Authorization': 'Bearer ' + self.quickbooks_access_token,
                'Accept': 'application/json',
                'Content-Type': 'text/plain'
            }
            request_url = self.quickbooks_api_url + self.quickbooks_realm
            return {
                'url': request_url,
                'headers': headers
            }
        else:
            return False

    def _is_customer_tax_exempt(self, customer_id):
        """Check if partner or customer is tax exempt"""
        partner = self.env['res.partner'].browse(customer_id)
        return partner.qbooks_tax_exempt if partner else False

    def _apply_line_tax_exemption(self, line_vals, customer_id):
        """Apply tax exemption to a line if customer is tax exempt."""
        if self._is_customer_tax_exempt(customer_id):
            # Customer is tax exempt - remove all taxes from line
            if 'tax_id' in line_vals:
                line_vals['tax_id'] = [(6, 0, [])]  # For sale order lines
            if 'tax_ids' in line_vals:
                line_vals['tax_ids'] = [(6, 0, [])]  # For invoice lines
            if 'taxes_id' in line_vals:
                line_vals['taxes_id'] = [(6, 0, [])]  # For purchase order lines
        return line_vals

    def action_setup_tax_exempt_mappings(self):
        """Setup tax exempt fiscal position mappings after taxes are imported"""
        fiscal_position = self.env['account.fiscal.position'].search([
            ('name', '=', 'Quickbooks Tax Exempt')
        ], limit=1)

        if not fiscal_position:
            _logger.warning("Tax Exempt fiscal position not found")
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': 'Tax Exempt fiscal position not found. Please check your installation.',
                    'type': 'warning',
                    'sticky': False,
                }
            }

        self._tax_exempt_mappings(fiscal_position)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': 'Tax exempt mappings created successfully',
                'type': 'success',
                'sticky': False,
            }
        }

    def _tax_exempt_mappings(self, fiscal_position):
        """Ensure all active taxes have mappings to remove them"""
        tax_obj = self.env['account.tax']
        mapping_obj = self.env['account.fiscal.position.tax']

        active_taxes = tax_obj.search([
            ('active', '=', True),
            '|', ('type_tax_use', '=', 'sale'), ('type_tax_use', '=', 'purchase')
        ])

        existing_mappings = mapping_obj.search([
            ('position_id', '=', fiscal_position.id)
        ])
        mapped_tax_ids = existing_mappings.mapped('tax_src_id.id')

        for tax in active_taxes:
            if tax.id not in mapped_tax_ids:
                mapping_obj.create([{
                    'position_id': fiscal_position.id,
                    'tax_src_id': tax.id,
                    'tax_dest_id': False,  # False means remove the tax
                }])

    def _apply_tax_exemption_to_partner(self, partner, is_tax_exempt):
        """Apply or remove tax exemption fiscal position of a partner"""
        fiscal_position = self.env['account.fiscal.position'].search([
            ('name', '=', 'Quickbooks Tax Exempt')
        ], limit=1)

        if not fiscal_position:
            _logger.warning("Tax Exempt fiscal position not found")
            return

        if is_tax_exempt:
            if partner.property_account_position_id != fiscal_position:
                partner.write({
                    'property_account_position_id': fiscal_position.id,
                    'qbooks_tax_exempt': True
                })
                _logger.info(f"Applied tax exemption to partner {partner.name}")
        else:
            partner.write({
                'property_account_position_id': False,
                'qbooks_tax_exempt': False
            })

    def _get_or_create_quickbooks_tax_group(self):
        """Get or create QuickBooks tax group with default tax accounts"""
        tax_group = self.env['account.tax.group'].search([
            ('name', '=', 'QuickBooks Tax')
        ], limit=1)

        if not tax_group:
            tax_payable_account = self.env['account.account'].search([
                ('code', '=', '252000'),
            ], limit=1)

            tax_receivable_account = self.env['account.account'].search([
                ('code', '=', '132000'),
            ], limit=1)

            # Create tax group with accounts
            tax_group = self.env['account.tax.group'].create([{
                'name': 'QuickBooks Tax',
                'country_id': self.env.company.country_id.id,
                'tax_payable_account_id': tax_payable_account.id,
                'tax_receivable_account_id': tax_receivable_account.id,
            }])
            _logger.info("Created QuickBooks tax group with Tax Payable (252000) and Tax Receivable (132000) accounts")

            return {
                'tax_group': tax_group,
                'newly_created': True,
                'payable_account': tax_payable_account.code,
                'receivable_account': tax_receivable_account.code,
            }

        return {
            'tax_group': tax_group,
            'newly_created': False,
        }

    # Helper functions for importing exchnage rates from quickbook
    def _get_or_create_qbooks_rate(self, currency_id, rate, date):
        """Get or create a currency rate for QuickBooks transaction"""

        odoo_rate = 1.0 / rate if rate != 0 else 1.0

        existing_rate = self.env['res.currency.rate'].search([
            ('currency_id', '=', currency_id.id),
            ('name', '=', date),
            ('is_qbooks_rate', '=', True),
            ('company_id', '=', self.env.company.id),
        ], limit=1)

        if existing_rate:
            if abs(existing_rate.rate - odoo_rate) > 0.000001:
                existing_rate.write({
                    'rate': odoo_rate,
                    'qbooks_exchange_rate': rate,
                })
                _logger.info(f"Updated QuickBooks rate for {currency_id.name} on {date}: {rate}")
            return existing_rate
        else:
            rate_vals = {
                'currency_id': currency_id.id,
                'name': date,
                'rate': odoo_rate,
                'qbooks_exchange_rate': rate,
                'is_qbooks_rate': True,
                'company_id': self.env.company.id
            }
            return self.env['res.currency.rate'].create([rate_vals])

    def _apply_qbooks_exchange_rate(self, record_data, currency_code=None):
        """ Extract and apply QuickBooks exchange rate from transaction data"""

        result = {'currency_id': False, 'rate_applied': False}

        if not currency_code:
            currency_ref = record_data.get('CurrencyRef', {})
            currency_code = currency_ref.get('value')

        if not currency_code:
            return result

            # Find currency in Odoo
        currency = self.env['res.currency'].search([
            ('name', '=', currency_code)
        ], limit=1)

        if not currency:
            _logger.warning(f"Currency {currency_code} not found in Odoo")
            return result

        result['currency_id'] = currency.id

        # Skip if it's the company currency
        if currency == self.env.company.currency_id:
            return result

        # Get exchange rate from QuickBooks
        exchange_rate = record_data.get('ExchangeRate')
        if not exchange_rate:
            # Try to get from HomeBalance vs TotalAmt
            total_amt = record_data.get('TotalAmt')
            home_balance = record_data.get('HomeBalance')
            if total_amt and home_balance and total_amt != 0:
                exchange_rate = home_balance / total_amt

        # Get transaction date
        txn_date = record_data.get('TxnDate')
        if txn_date:
            date = datetime.strptime(txn_date, '%Y-%m-%d').date()
        else:
            date = fields.Date.today()

        if exchange_rate and exchange_rate != 0:
            self._get_or_create_qbooks_rate(currency, exchange_rate, date)
            result['rate_applied'] = True
            result['qbooks_rate'] = exchange_rate

        return result

    def _get_qbooks_currency_context(self, record_data, date=None):
        """Get context with QuickBooks currency rate for record creation/update"""
        context = {}

        currency_ref = record_data.get('CurrencyRef', {})
        currency_code = currency_ref.get('value')

        if not currency_code:
            return context

        currency = self.env['res.currency'].search([
            ('name', '=', currency_code)
        ], limit=1)

        if not currency or currency == self.env.company.currency_id:
            return context

        # Get or determine date
        if not date:
            txn_date = record_data.get('TxnDate')
            if txn_date:
                date = datetime.strptime(txn_date, '%Y-%m-%d').date()
            else:
                date = fields.Date.today()

        # Apply rate
        rate_info = self._apply_qbooks_exchange_rate(record_data, currency_code)

        if rate_info.get('rate_applied'):
            context['date'] = date

        return context

    def _get_or_create_pricelist_for_currency(self, currency_id):
        """Get or create a pricelist for a specific currency"""
        if not currency_id:
            return False

        pricelist = self.env['product.pricelist'].search([
            ('currency_id', '=', currency_id.id),
            ('name', '=', f'QuickBooks - {currency_id.name}')
        ], limit=1)

        if not pricelist:
            pricelist = self.env['product.pricelist'].create([{
                'name': f'QuickBooks - {currency_id.name}',
                'currency_id': currency_id.id,
                'company_id': self.env.company.id,
            }])
            _logger.info(f"Created pricelist for currency {currency_id.name}")

        return pricelist

    def action_import_product_category(self):
        """Function to import the product categories from QuickBooks"""
        url = self.get_import_query()
        run = True
        start_position = 1
        max_results = 100
        total = 0
        if url:
            while run:
                query = f'SELECT * FROM Item STARTPOSITION {start_position} MAXRESULTS {max_results}'
                get_url = url[
                              'url'] + f'/query?minorversion={self.minor_version}&query={query}'

                try:
                    response = requests.request('GET', get_url,
                                                headers=url['headers'])
                    data = response.json()
                    # Handle Authentication Refresh
                    if data.get('fault') and data.get('fault').get(
                        'type') == 'AUTHENTICATION':
                        self.action_refresh_token()
                        response = requests.request('GET', get_url,
                                                headers=url['headers'])
                        data = response.json()
                    if data.get('QueryResponse'):
                        items = data.get('QueryResponse').get('Item', [])
                        if not items:
                            run = False
                            break
                        for item in items:
                            if item.get('UnitPrice') or item.get('UnitPrice') == 0:
                                continue

                            exist = self.env['product.category'].search(
                                [('qbooks_product_category', '=', item.get('Id'))], limit=1)
                            if not exist:
                                category_vals = {
                                    'name': item.get('Name'),
                                    'qbooks_product_category': item.get('Id'),
                                    'qbooks_sync_token': item.get('SyncToken')
                                }
                                category = self.env['product.category'].create([category_vals])
                                total += 1

                                self._log_qbooks_operation(
                                    'Category Import', 'import', 'success',
                                    f"Imported category: {item.get('Name')}",
                                    record=category, response=item
                                )

                        start_position += max_results  # Move to next batch

                    else:
                        run = False
                except Exception as e:
                    self._log_qbooks_operation(
                        'Category Import', 'import', 'failed',
                        str(e), response=locals().get('data')
                    )
                    run = False

            message = f'{total} categories imported' if total > 0 else 'No new categories found'
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'QuickBooks Import',
                    'message': message,
                    'type': 'success' if total > 0 else 'warning',
                    'sticky': False
                }
            }

    def action_import_products(self):
        """Queue the job to import products with priority."""
        self.with_delay(priority=1)._run_import_product_job()

    def _run_import_product_job(self):
        """Fetching the products from QuickBooks(Queue Job)"""

        url = self.get_import_query()
        if not url:
            _logger.warning("No URL returned from import query.")
            return

        start_position = 1
        max_results = 100

        while True:
            query = f"SELECT * FROM Item STARTPOSITION {start_position} MAXRESULTS {max_results}"
            get_url = f"{url['url']}/query?query={query}&minorversion={self.minor_version}"

            try:
                response = requests.get(get_url, headers=url['headers'])
                data = response.json()

                if data.get('fault', {}).get('type') == 'AUTHENTICATION':
                    self.action_refresh_token()
                    response = requests.get(get_url, headers=url['headers'])
                    data = response.json()

            except Exception as e:
                _logger.error(
                    f"Error while fetching items from QuickBooks: {e}")
                break

            items = data.get('QueryResponse', {}).get('Item', [])
            if not items:
                break

            self.with_delay(priority=1)._batch_schedule_product_import(
                items, max_results=max_results, start_position=start_position)
            start_position += max_results

    def _batch_schedule_product_import(self, items, max_results, start_position):
        """Batching the fetched products"""
        size = 10
        item_list = [items[i:i + size] for i in range(0, len(items), size)]
        for index, item_chunk in enumerate(item_list):
            delay_time = fields.Datetime.now() + timedelta(seconds=index * 10)
            self.with_delay(priority=1, eta=delay_time)._product_import(
                item_chunk, max_results, start_position)

    def _product_import(self, items, max_results, start_position):
        """Creating the products from quickbook"""
        created_count = 0
        failed_count = 0
        for item in items:
            if item.get('Type') == 'Category':
                continue

            item_id = item.get('Id')
            item_name = item.get('Name', 'Unknown')

            exist = self.env['product.product'].search(
                [('qbooks_product', '=', item_id)], limit=1)
            if exist:
                continue

            try:
                if item.get('ParentRef'):
                    category = self.env['product.category'].search(
                        [('qbooks_product_category', '=',
                          item.get('ParentRef').get('value'))])
                    if not category:
                        raise ValidationError(
                            f"Category '{item['ParentRef'].get('name')}' not found. Please import it first."
                        )
                else:
                    category = self.env['product.category'].search(
                        [('name', '=', 'All'),
                         ('qbooks_product_category', '=', False)],
                        limit=1)
                if not category:
                    category = self.env['product.category'].create([{
                        'name': 'All',
                    }])
                    _logger.info(f"Created product category {category.name}")

                product_vals = {
                    'name': item.get('Name'),
                    'qbooks_product': item.get('Id'),
                    'qbooks_sync_token': item.get('SyncToken'),
                    'list_price': item.get('UnitPrice'),
                    'standard_price': item.get('PurchaseCost'),
                    'description_sale': item.get('Description') or '',
                    'description_purchase': item.get('PurchaseDesc') or '',
                    'active': item.get('Active', True),
                    'categ_id': category.id,
                }
                # Determine product type
                qbo_type = item.get('Type')
                if qbo_type == 'Service':
                    product_vals['type'] = 'service'
                elif qbo_type == 'NonInventory':
                    product_vals['type'] = 'consu'
                else:
                    product_vals['type'] = 'consu'
                    product_vals['is_storable'] = True

                if item.get('IncomeAccountRef'):
                    account = self.env['account.account'].search([
                        ('qbooks_account', '=', item['IncomeAccountRef']['value'])
                    ])
                    if account:
                        product_vals['property_account_income_id'] = account.id

                if item.get('AssetAccountRef'):
                    account = self.env['account.account'].search([
                        ('qbooks_account', '=', item['AssetAccountRef']['value'])
                    ])
                    if account:
                        product_vals['property_account_expense_id'] = account.id

                product = self.env['product.product'].create([product_vals])
                if item.get('QtyOnHand'):
                    self.env['stock.quant'].create([{
                        'product_id': product.id,
                        'location_id': self.env.ref(
                            'stock.stock_location_stock').id,
                        'inventory_quantity': item['QtyOnHand'],
                        'quantity': item['QtyOnHand'],
                    }])
                self._log_qbooks_operation(
                    operation_name=f"Product Import: {item_name}",
                    op_type='import',
                    status='success',
                    message=f"Product '{item_name}' (QBO ID: {item_id}) imported successfully.",
                    record=product,
                    payload=item,
                )
                created_count += 1
            except Exception as e:
                failed_count += 1
                _logger.error(
                    f"Failed to import product '{item_name}' (QBO ID: {item_id}): {e}")
                self._log_qbooks_operation(
                    operation_name=f"Product Import: {item_name}",
                    op_type='import',
                    status='failed',
                    message=str(e),
                    payload=item,
                )
                if isinstance(e, ValidationError):
                    raise

        self._log_qbooks_operation(
            operation_name="Product Import Batch",
            op_type='import',
            status='success' if not failed_count else 'failed',
            message=(
                f"Batch complete: {created_count} products imported successfully, "
                f"{failed_count} failed. "
                f"(start_position={start_position}, max_results={max_results})"
            ),
            payload={
                'start_position': start_position,
                'max_results': max_results,
                'created': created_count,
                'failed': failed_count,
            },
        )

        _logger.info(
            f"{created_count} products imported in batch from QuickBooks.")

    def action_import_customers(self):
        """Queue the job to import customers with priority."""
        self.with_delay(priority=1)._run_import_customer_job()

    def _run_import_customer_job(self):
        """Fetching the customers from QuickBooks"""

        url = self.get_import_query()
        if not url:
            _logger.warning("No URL returned from import query.")
            return

        start_position = 1
        max_results = 100

        while True:
            query = f"SELECT * FROM Customer STARTPOSITION {start_position} MAXRESULTS {max_results}"
            get_url = f"{url['url']}/query?query={query}&minorversion={self.minor_version}"

            try:
                response = requests.get(get_url, headers=url['headers'])
                data = response.json()

                if data.get('fault', {}).get('type') == 'AUTHENTICATION':
                    self.action_refresh_token()
                    response = requests.get(get_url, headers=url['headers'])
                    data = response.json()

                customers = data.get('QueryResponse', {}).get('Customer', [])

            except Exception as e:
                _logger.error(f"Error while fetching customers: {e}")
                break

            if not customers:
                break

            self.with_delay(priority=1)._batch_schedule_customer_import(
                customers, max_results=max_results, start_position=start_position
            )
            start_position += max_results

    def _batch_schedule_customer_import(self, customers, max_results, start_position):
        """Batching the customers"""
        size = 10
        customer_list = [customers[i:i + size] for i in range(0, len(customers), size)]
        for index, customer_chunk in enumerate(customer_list):
            delay_time = fields.Datetime.now() + timedelta(seconds=index * 10)
            self.with_delay(priority=1, eta=delay_time).create_partner(
                customer_chunk, max_results=max_results, start_position=start_position)

    def action_import_vendor(self):
        """Queue the job to import vendors with priority."""
        self.with_delay(priority=1)._run_import_vendor_job()

    def _run_import_vendor_job(self):
        """Fetching the vendors from quickbook"""
        url = self.get_import_query()
        if not url:
            _logger.warning("No URL returned from import query.")
            return

        start_position = 1
        max_results = 100

        while True:
            query = f"SELECT * FROM Vendor STARTPOSITION {start_position} MAXRESULTS {max_results}"
            get_url = f"{url['url']}/query?query={query}&minorversion={self.minor_version}"

            try:
                response = requests.get(get_url, headers=url['headers'])
                if response.json().get('fault', {}).get(
                        'type') == 'AUTHENTICATION':
                    self.action_refresh_token()
                    response = requests.get(get_url, headers=url['headers'])

                vendors = response.json().get('QueryResponse', {}).get('Vendor',
                                                                       [])

            except Exception as e:
                _logger.error(f"Error while fetching vendors: {e}")
                break

            if not vendors:
                break

            self.with_delay(priority=1)._batch_schedule_vendor_import(
                vendors, max_results=max_results, start_position=start_position
            )

            start_position += max_results

    def _batch_schedule_vendor_import(self, vendors, max_results, start_position):
        """Batching the vendors"""
        size = 10
        vendor_list = [vendors[i:i + size] for i in range(0, len(vendors), size)]
        for index, vendor_chunk in enumerate(vendor_list):
            delay_time = fields.Datetime.now() + timedelta(seconds=index * 10)
            self.with_delay(priority=1, eta=delay_time).create_partner(
                vendor_chunk, vendor=True, max_results=max_results,
                start_position=start_position
            )

    def create_partner(self, partners, vendor=False, max_results=0, start_position=0):
        """Function to create child partner and addresses"""
        partner_obj = self.env['res.partner']
        total = 0
        failed_count = 0
        partner_type = "vendor" if vendor else "customer"

        for partner in partners:
            qbooks_id = partner.get('Id')
            partner_name = partner.get('DisplayName') or partner.get(
                'CompanyName', 'Unknown')

            try:
                is_child = bool(partner.get('ParentRef'))
                domain = [('qbooks_vendor' if vendor else 'qbooks_customer', '=', qbooks_id)]
                existing = partner_obj.search(domain, limit=1)

                is_tax_exempt = partner.get('Taxable') == False

                currency_code = partner.get('CurrencyRef', {}).get('value')
                currency_id = False
                pricelist_id = False

                if currency_code:
                    currency_id = self.env['res.currency'].search([
                        ('name', '=', currency_code)
                    ], limit=1)

                    if currency_id and not vendor:  # Only set pricelist for customers
                        pricelist_id = self._get_or_create_pricelist_for_currency(currency_id)

                if existing:
                    # Update existing partner if currency/pricelist changed
                    update_vals = {}
                    if existing.qbooks_tax_exempt != is_tax_exempt:
                        self._apply_tax_exemption_to_partner(existing, is_tax_exempt)

                    if pricelist_id and existing.property_product_pricelist != pricelist_id:
                        update_vals['property_product_pricelist'] = pricelist_id.id

                    if update_vals:
                        existing.write(update_vals)
                    continue

                vals = {
                    'name': partner_name,
                    'qbooks_sync_token': partner.get('SyncToken'),
                    'company_type': 'person' if is_child else 'company',
                    'phone': partner.get('PrimaryPhone', {}).get('FreeFormNumber',
                                                                 ''),
                    'email': partner.get('PrimaryEmailAddr', {}).get('Address', ''),
                    'website': partner.get('WebAddr', {}).get('URI', ''),
                    'comment': partner.get('Notes', ''),
                    'qbooks_tax_exempt': is_tax_exempt,
                }

                if pricelist_id and not vendor:
                    vals['property_product_pricelist'] = pricelist_id.id

                if vendor:
                    vals['qbooks_vendor'] = qbooks_id
                else:
                    vals['qbooks_customer'] = qbooks_id

                addr = partner.get('BillAddr') or partner.get('ShipAddr')
                if addr:
                    lat = 0.0 if addr.get('Lat') == 'INVALID' else addr.get('Lat')
                    long = 0.0 if addr.get('Long') == 'INVALID' else addr.get('Long')
                    state = addr.get('CountrySubDivisionCode')
                    country = addr.get('Country')
                    country_id = self.env['res.country'].sudo().search([('name', '=', country)], limit=1) if country else False
                    state_id = self.env['res.country.state'].sudo().search([('name', '=', state)], limit=1) if state else False
                    vals.update({
                        'street': addr.get('Line1', ''),
                        'street2': addr.get('Line2', ''),
                        'city': addr.get('City', ''),
                        'zip': addr.get('PostalCode', ''),
                        'state_id': state_id.id if state_id else False,
                        'country_id': country_id.id if country_id else False,
                        'partner_latitude': lat,
                        'partner_longitude': long,
                        'type': 'delivery' if partner.get('BillAddr') and addr == partner.get('ShipAddr') else 'invoice',
                    })

                # If it's a child contact, find and link parent
                if is_child:
                    parent = partner_obj.search([
                        ('qbooks_customer', '=', partner['ParentRef']['value'])
                    ], limit=1)
                    if parent:
                        vals.update({
                            'company_type': 'person',
                            'parent_id': parent.id,
                        })
                        created = partner_obj.create([vals])
                        if is_tax_exempt:
                            self._apply_tax_exemption_to_partner(created, True)

                        # ✅ Log child contact success
                        self._log_qbooks_operation(
                            operation_name=f"{partner_type.title()} Import (Child): {partner_name}",
                            op_type='import',
                            status='success',
                            message=f"Child contact '{partner_name}' (QBO ID: {qbooks_id}) linked to parent '{parent.name}'.",
                            record=created,
                            payload=partner,
                        )
                        total += 1
                else:
                    created = partner_obj.create([vals])
                    if is_tax_exempt:
                        self._apply_tax_exemption_to_partner(created, True)

                    # ✅ Log main partner success
                    self._log_qbooks_operation(
                        operation_name=f"{partner_type.title()} Import: {partner_name}",
                        op_type='import',
                        status='success',
                        message=f"{partner_type.title()} '{partner_name}' (QBO ID: {qbooks_id}) imported successfully.",
                        record=created,
                        payload=partner,
                    )
                    total += 1

                    # Create ship address as child only if both addresses differ
                    if partner.get('BillAddr') and partner.get('ShipAddr') and \
                            partner['BillAddr'].get('Id') != partner['ShipAddr'].get('Id'):
                        ship = partner['ShipAddr']
                        ship_state = ship.get('CountrySubDivisionCode')
                        ship_country = ship.get('Country')
                        ship_country_id = self.env['res.country'].sudo().search([('name', '=', ship_country)], limit=1) if ship_country else False
                        ship_state_id = self.env['res.country.state'].sudo().search([('name', '=', ship_state)],limit=1) if ship_state else False

                        ship_partner = partner_obj.create([{
                            'name': partner_name,
                            'qbooks_customer': qbooks_id if not vendor else False,
                            'qbooks_vendor': qbooks_id if vendor else False,
                            'qbooks_sync_token': partner.get('SyncToken'),
                            'company_type': 'person',
                            'parent_id': created.id,
                            'street': ship.get('Line1', ''),
                            'street2': ship.get('Line2', ''),
                            'city': ship.get('City', ''),
                            'zip': ship.get('PostalCode', ''),
                            'state_id': ship_state_id.id if ship_state_id else False,
                            'country_id': ship_country_id.id if ship_country_id else False,
                            'phone': partner.get('PrimaryPhone', {}).get('FreeFormNumber', ''),
                            'website': partner.get('WebAddr', {}).get('URI', ''),
                            'comment': partner.get('Notes', ''),
                            'type': 'delivery',
                            'qbooks_tax_exempt': is_tax_exempt,
                        }])

                        # ✅ Log shipping address success
                        self._log_qbooks_operation(
                            operation_name=f"{partner_type.title()} Import (Ship Address): {partner_name}",
                            op_type='import',
                            status='success',
                            message=f"Delivery address created for '{partner_name}' (QBO ID: {qbooks_id}).",
                            record=ship_partner,
                            payload=ship,
                        )
                        total += 1
            except Exception as e:
                failed_count += 1
                _logger.error(
                    f"Failed to import {partner_type} '{partner_name}' (QBO ID: {qbooks_id}): {e}")

                # ❌ Log failure per partner
                self._log_qbooks_operation(
                    operation_name=f"{partner_type.title()} Import: {partner_name}",
                    op_type='import',
                    status='failed',
                    message=str(e),
                    payload=partner,
                )

        # 📊 Log batch summary
        self._log_qbooks_operation(
            operation_name=f"{partner_type.title()} Import Batch",
            op_type='import',
            status='success' if not failed_count else 'failed',
            message=(
                f"Batch complete: {total} {partner_type}(s) imported successfully, "
                f"{failed_count} failed. "
                f"(start_position={start_position}, max_results={max_results})"
            ),
            payload={
                'start_position': start_position,
                'max_results': max_results,
                'partner_type': partner_type,
                'created': total,
                'failed': failed_count,
            },
        )
        _logger.info("QuickBooks Import: %s %s record(s) imported.", total,
                     partner_type)

    def action_import_account(self):
        """Queue the job to import accounts with priority."""
        self.with_delay(priority=1)._run_import_account_job()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Import Started',
                'message': 'Accounts import has been queued in the background.',
                'type': 'info',
                'sticky': False,
            }
        }

    def _run_import_account_job(self):
        """Fetching the accounts from QuickBooks"""

        url = self.get_import_query()
        if not url:
            _logger.warning("No URL returned from import query.")
            return

        start_position = 1
        max_results = 100

        while True:
            query = f"SELECT * FROM Account STARTPOSITION {start_position} MAXRESULTS {max_results}"
            get_url = f"{url['url']}/query?query={query}&minorversion={self.minor_version}"

            try:
                response = requests.get(get_url, headers=url['headers'])
                data = response.json()

                if data.get('fault', {}).get('type') == 'AUTHENTICATION':
                    self.action_refresh_token()
                    response = requests.get(get_url, headers=url['headers'])
                    data = response.json()

            except Exception as e:
                _logger.error(f"Error while fetching accounts: {e}")
                break

            accounts = data.get('QueryResponse', {}).get('Account', [])
            if not accounts:
                break

            # self._batch_schedule_accounts_import(accounts, max_results=max_results, start_position=start_position)
            self.with_delay(priority=1)._batch_schedule_accounts_import(
                accounts, max_results=max_results, start_position=start_position
            )

            start_position += max_results

    def _batch_schedule_accounts_import(self, accounts, max_results, start_position):
        """Batching the accounts"""
        size = 10
        account_list = [accounts[i:i + size] for i in
                        range(0, len(accounts), size)]
        for index, account_chunk in enumerate(account_list):
            delay_time = fields.Datetime.now() + timedelta(seconds=index * 10)
            # self._accounts_import(account_chunk, max_results, start_position)

            self.with_delay(priority=1, eta=delay_time)._accounts_import(
                account_chunk, max_results, start_position
            )

    def _accounts_import(self, accounts, max_results, start_position):
        """Function to create chart of accounts"""
        total = 0
        type_map = {
            'Accounts Receivable': 'asset_receivable',
            'Accounts Payable': 'liability_payable',
            'Bank': 'asset_cash',
            'Credit Card': 'liability_credit_card',
            'Other Current Asset': 'asset_current',
            'Fixed Asset': 'asset_fixed',
            'Other Asset': 'asset_non_current',
            'Long Term Liability': 'liability_non_current',
            'Other Current Liability': 'liability_current',
            'Equity': 'equity',
            'Expense': 'expense',
            'Other Expense': 'expense',
            'Income': 'income',
            'Other Income': 'income_other',
            'Cost of Goods Sold': 'expense_direct_cost',
        }
        for account in accounts:
            try:
                exist = self.env['account.account'].search(
                    [('qbooks_account', '=', account.get('Id'))], limit=1)
                if exist:
                    continue

                account_type = type_map.get(account.get('AccountType'), False)
                account_vals = {
                    'qbooks_account': int(account.get('Id')),
                    'name': account.get('Name'),
                    'code': 'Q00' + account.get('Id'),
                    'account_type': account_type,
                    'qbooks_sync_token': account.get('SyncToken', ''),
                    'reconcile': account_type in ['asset_receivable',
                                                  'liability_payable'],
                }
                new_account = self.env['account.account'].create([account_vals])
                self._log_qbooks_operation('Account Import',
                                           'import', 'success',
                                           f"Created {account.get('Name')}",
                                           record=new_account)
                total += 1
            except Exception as e:
                # Log the specific failure for this account without stopping the whole loop
                self._log_qbooks_operation(
                    'Account Import Error',
                    'import',
                    'failed',
                    f"Error creating account {account.get('Name')}: {str(e)}",
                    payload=account
                )
                continue

        _logger.info(f"{total} accounts imported (start_position: {start_position})")
        self._log_qbooks_operation(
            'Account Batch Import',
            'import',
            'success',
            f"Batch starting at {start_position}: {total} accounts created."
        )

    def action_import_employees(self):
        """Entry point to trigger the queued employee import."""
        # We trigger the fetcher as a background job immediately
        self.with_delay(priority=1)._run_import_employees_job()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Import Started',
                'message': 'Employee import has been queued in the background.',
                'type': 'info',
                'sticky': False,
            }
        }

    def _run_import_employees_job(self):
        """Fetching the employees from QuickBooks with pagination logic."""
        url = self.get_import_query()
        if not url:
            _logger.warning("No URL returned from import query for employees.")
            return

        start_position = 1
        max_results = 100  # Smaller chunks for better job management

        while True:
            query = f"SELECT * FROM Employee STARTPOSITION {start_position} MAXRESULTS {max_results}"
            get_url = f"{url['url']}/query?query={query}&minorversion={self.minor_version}"

            try:
                response = requests.get(get_url, headers=url['headers'])
                data = response.json()

                # Handle Token Refresh
                if data.get('fault', {}).get('type') == 'AUTHENTICATION':
                    self.action_refresh_token()
                    # Re-fetch headers after refresh
                    new_url = self.get_import_query()
                    response = requests.get(get_url, headers=new_url['headers'])
                    data = response.json()

            except Exception as e:
                _logger.error(f"Error while fetching employees: {e}")
                break

            employees = data.get('QueryResponse', {}).get('Employee', [])
            if not employees:
                break

            # Queue the batcher to process these 100 records
            self.with_delay(priority=1)._batch_schedule_employees_import(
                employees, max_results=max_results,
                start_position=start_position
            )

            start_position += max_results

    def _batch_schedule_employees_import(self, employees, max_results,
                                         start_position):
        """Splits the 100 records into smaller chunks (e.g., 10) to avoid long-running jobs."""
        size = 10
        employee_chunks = [employees[i:i + size] for i in
                           range(0, len(employees), size)]

        for index, chunk in enumerate(employee_chunks):
            # Stagger the execution by 10 seconds per chunk to prevent DB locks
            delay_time = fields.Datetime.now() + timedelta(seconds=index * 10)

            self.with_delay(priority=1, eta=delay_time)._employees_import(
                chunk, max_results, start_position
            )

    def _employees_import(self, employees, max_results, start_position):
        """Final worker function to create hr.employee records."""
        total = 0
        failed_count = 0
        gender_map = {
            'Female': 'female',
            'Male': 'male'
        }

        for emp in employees:
            emp_id = emp.get('Id')
            emp_name = emp.get('DisplayName', 'Unknown')

            try:
                exist = self.env['hr.employee'].search(
                    [('qbooks_employee', '=', emp_id)], limit=1)
                if exist:
                    continue

                vals = {
                    'qbooks_employee': int(emp.get('Id')),
                    'name': emp.get('DisplayName'),
                    'qbooks_sync_token': emp.get('SyncToken', ''),
                    'active': emp.get('Active', True),
                    'sex': gender_map.get(emp.get('Gender'), False),
                    'birthday': fields.Date.from_string(
                        emp.get('BirthDate')) if emp.get('BirthDate') else False,
                }

                # Handle Nested Dictionary mappings
                if emp.get('PrimaryPhone'):
                    vals['work_phone'] = emp.get('PrimaryPhone').get(
                        'FreeFormNumber')
                if emp.get('Mobile'):
                    vals['mobile_phone'] = emp.get('Mobile').get('FreeFormNumber')
                if emp.get('PrimaryEmailAddr'):
                    vals['work_email'] = emp.get('PrimaryEmailAddr').get('Address')

                employee = self.env['hr.employee'].create([vals])
                # ✅ Log success per employee
                self._log_qbooks_operation(
                    operation_name=f"Employee Import: {emp_name}",
                    op_type='import',
                    status='success',
                    message=f"Employee '{emp_name}' (QBO ID: {emp_id}) imported successfully.",
                    record=employee,
                    payload=emp,
                )
                total += 1
            except Exception as e:
                failed_count += 1
                _logger.error(
                    f"Failed to import employee '{emp_name}' (QBO ID: {emp_id}): {e}")

                # ❌ Log failure per employee
                self._log_qbooks_operation(
                    operation_name=f"Employee Import: {emp_name}",
                    op_type='import',
                    status='failed',
                    message=str(e),
                    payload=emp,
                )

        self._log_qbooks_operation(
            operation_name="Employee Import Batch",
            op_type='import',
            status='success' if not failed_count else 'failed',
            message=(
                f"Batch complete: {total} employees imported successfully, "
                f"{failed_count} failed. "
                f"(start_position={start_position}, max_results={max_results})"
            ),
            payload={
                'start_position': start_position,
                'max_results': max_results,
                'created': total,
                'failed': failed_count,
            },
        )
        _logger.info(
            f"Imported {total} employees from batch starting at {start_position}")

    def action_import_tax_agency(self):
        """Function to import tax agencies from QuickBooks with pagination"""
        url = self.get_import_query()
        if url:
            start_position = 1
            max_results = 1000
            total = 0
            run = True

            while run:
                query = f"SELECT * FROM TaxAgency STARTPOSITION {start_position} MAXRESULTS {max_results}"
                get_url = f"{url['url']}/query?query={query}&minorversion={self.minor_version}"

                try:
                    response = requests.request('GET', get_url, headers=url['headers'])
                    data = response.json()

                    # Handle token expiration
                    if data.get('fault') and data.get('fault').get(
                            'type') == 'AUTHENTICATION':
                        self.action_refresh_token()
                        response = requests.request('GET', get_url,
                                                    headers=url['headers'])
                        data = response.json()
                    if data.get('QueryResponse'):
                        agencies = data.get('QueryResponse').get('TaxAgency',
                                                                    [])
                        if not agencies:
                            run = False
                            break

                        for agency in agencies:
                            exist = self.env['tax.agency'].search(
                                [('qbooks_agency', '=', agency.get('Id'))], limit=1)

                            if not exist:
                                tax_agency_vals = {
                                    'qbooks_agency': int(agency.get('Id')),
                                    'tax_agency': agency.get('DisplayName'),
                                    'qbooks_sync_token': agency.get('SyncToken',
                                                                    ''),
                                }
                                tax_agency = self.env['tax.agency'].create([tax_agency_vals])
                                total += 1
                                self._log_qbooks_operation(
                                    'Tax Agency Import', 'import', 'success',
                                    f"Imported tax agency: {agency.get('DisplayName')}",
                                    record=tax_agency, response=agency
                                )
                        start_position += max_results
                    else:
                        run = False
                except Exception as e:
                    self._log_qbooks_operation(
                        'Tax Agency Import', 'import', 'failed',
                        str(e), response=locals().get('data')
                    )
                    run = False

            message = f'{total} Tax agency imported' if total > 0 else 'No new tax agencies found'
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': message,
                    'type': 'success' if total > 0 else 'warning',
                    'sticky': False,
                }
            }

    def action_import_tax(self):
        """Function to import tax codes from QuickBooks with pagination"""
        url = self.get_import_query()
        if url:
            start_position = 1
            max_results = 1000
            total = 0
            run = True

            # Get or create QuickBooks tax group
            tax_group_info = self._get_or_create_quickbooks_tax_group()
            qbooks_tax_group = tax_group_info['tax_group']
            group_created = tax_group_info['newly_created']

            while run:
                query = f"SELECT * FROM TaxCode STARTPOSITION {start_position} MAXRESULTS {max_results}"
                get_url = f"{url['url']}/query?query={query}&minorversion={self.minor_version}"
                try:
                    response = requests.request('GET', get_url, headers=url['headers'])
                    data = response.json()

                    # Handle token expiration
                    if data.get('fault') and data.get('fault').get('type') == 'AUTHENTICATION':
                        self.action_refresh_token()
                        response = requests.request('GET', get_url,
                                                    headers=url['headers'])
                        data = response.json()

                    tax_codes = data.get('QueryResponse').get('TaxCode', [])
                    if not tax_codes:
                        run = False
                        break

                    for tax in tax_codes:
                        exist = self.env['account.tax'].search(
                            [('qbooks_tax', '=', tax.get('Id'))],
                            limit=1)
                        if exist:
                            continue

                                # Handle purchase tax rate
                        p_list = tax.get('PurchaseTaxRateList',
                                                {}).get('TaxRateDetail', [])
                        s_list = tax.get('SalesTaxRateList', {}).get(
                            'TaxRateDetail', [])

                        if p_list:
                            p_rate_ids = [self.import_tax_rate(r, 'purchase',
                                                               qbooks_tax_group.id)
                                          for r in p_list]
                            p_rate_ids = [i for i in p_rate_ids if i]  # Filter Nones

                            if p_rate_ids:
                                p_vals = {
                                    'name': f"{tax.get('Name')} (Purchase)",
                                    'qbooks_tax': tax.get('Id'),
                                    'amount_type': 'group',
                                    'type_tax_use': 'purchase',
                                    'children_tax_ids': [(6, 0, p_rate_ids)],
                                    'tax_group_id': qbooks_tax_group.id,
                                }
                                self.env['account.tax'].create([p_vals])
                                total += 1

                        # Handle sales tax rate
                        if s_list:
                            s_rate_ids = [self.import_tax_rate(r, 'sale',
                                                               qbooks_tax_group.id)
                                          for r in s_list]
                            s_rate_ids = [i for i in s_rate_ids if i]
                            if s_rate_ids:
                                s_vals = {
                                    'name': f"{tax.get('Name')} (Sale)",
                                    'qbooks_tax': f"{tax.get('Id')}_sale",
                                    'amount_type': 'group',
                                    'type_tax_use': 'sale',
                                    'children_tax_ids': [(6, 0, s_rate_ids)],
                                    'tax_group_id': qbooks_tax_group.id,
                                }
                                self.env['account.tax'].create([s_vals])
                                total += 1

                    start_position += max_results
                except Exception as e:
                    self._log_qbooks_operation('Tax Import', 'import', 'failed', str(e),
                               response=data)
                    break

        self._log_qbooks_operation('Tax Import Summary', 'import', 'success', f"Imported {total} tax records.")

    def import_tax_rate(self, purchase_tax_rate, tax_type, tax_group_id=False):
        """Function to import tax rate from quickbook"""
        url = self.get_import_query()
        if url:
            try:
                query = f"{url.get('url')}/taxrate/{purchase_tax_rate.get('TaxRateRef').get('value')}?minorversion={self.minor_version}"
                data = requests.get(query, headers=url.get('headers'))
                if data.json() and data.json().get('TaxRate'):
                    tax_rate = data.json().get('TaxRate')
                    account_tax_obj = self.env['account.tax']
                    exist = account_tax_obj.search(
                        [('qbooks_tax_rate', '=', tax_rate.get('Id'))])
                    if exist:
                        return exist.id

                    tax_name = f"{tax_rate.get('Name')} ({tax_type.capitalize()})"
                    vals = {
                        'name': tax_name,
                        'description': tax_rate.get('Description'),
                        'qbooks_tax_rate': tax_rate.get('Id'),
                        'amount_type': 'percent',
                        'amount': float(tax_rate.get('RateValue', 0.0)),
                        'type_tax_use': tax_type,
                    }
                    if tax_group_id:
                        vals['tax_group_id'] = tax_group_id

                    if tax_rate.get('AgencyRef'):
                        agency = self.env['tax.agency'].search([
                            ('qbooks_agency', '=', tax_rate.get('AgencyRef').get('value'))
                        ], limit=1)
                        if agency:
                            vals['tax_agency_id'] = agency.id
                        else:
                            _logger.warning(
                                f"Tax agency {tax_rate.get('AgencyRef').get('value')} not found for tax rate {tax_rate.get('Name')}")
                    return account_tax_obj.create([vals]).id
            except Exception as e:
                _logger.error(f"Error importing tax rate: {str(e)}")
                return False
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': 'No Tax to import',
                    'type': 'danger',
                    'sticky': False,
                }
            }

    def action_import_so(self):
        """Queue the job to import sale order with priority."""
        self.with_delay(priority=1)._run_import_so_job()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Import Started',
                'message': 'Sale Orders import has been queued in the background.',
                'type': 'info',
                'sticky': False,
            }
        }

    def _run_import_so_job(self):
        """Fetching sale orders from QuickBooks"""

        url = self.get_import_query()
        if not url:
            _logger.warning("No URL returned from import query.")
            return

        start_position = 1
        max_results = 100

        while True:
            query = f"SELECT * FROM Estimate STARTPOSITION {start_position} MAXRESULTS {max_results}"
            get_url = f"{url['url']}/query?minorversion={self.minor_version}&query={query}"

            try:
                response = requests.get(get_url, headers=url['headers'])
                data = response.json()

                if data.get('fault', {}).get('type') == 'AUTHENTICATION':
                    self.action_refresh_token()
                    response = requests.get(get_url, headers=url['headers'])
                    data = response.json()

            except Exception as e:
                _logger.error(f"Error while fetching sale orders: {e}")
                break

            sale_orders = data.get('QueryResponse', {}).get('Estimate', [])
            if not sale_orders:
                break

            self.with_delay(priority=1)._batch_schedule_so_import(
                sale_orders, max_results=max_results, start_position=start_position
            )

            start_position += max_results

    def _batch_schedule_so_import(self, sale_orders, max_results, start_position):
        """Batching sale orders"""
        size = 10
        sale_list = [sale_orders[i:i + size] for i in range(0, len(sale_orders), size)]
        for index, chunk in enumerate(sale_list):
            delay_time = fields.Datetime.now() + timedelta(seconds=index * 10)
            self.with_delay(priority=1, eta=delay_time)._sale_import(
                chunk, max_results, start_position)

    def _sale_import(self, sale_orders, max_results, start_position):
        """Creating sale orders with lines"""
        total = 0
        failed_count = 0

        for so in sale_orders:
            so_id = so.get('Id')
            so_number = so.get('DocNumber', 'Unknown')

            try:
                if self.env['sale.order'].search([('qbooks_sale', '=', so_id)]):
                    continue

                rate_info = self._apply_qbooks_exchange_rate(so)

                currency_id = self.env['res.currency'].browse(
                    rate_info.get('currency_id')
                ) if rate_info.get('currency_id') else self.env[
                    'res.currency'].search(
                    [('name', '=', so.get('CurrencyRef', {}).get('value'))],
                    limit=1
                )

                so_date = datetime.strptime(so.get('TxnDate'), '%Y-%m-%d')

                sale_orders_vals = {
                    'qbooks_sale': so_id,
                    'name': so_number,
                    'qbooks_sync_token': so.get('SyncToken', ''),
                    'date_order': so_date,
                    'order_line': [],
                    'invoice_ids': []
                }

                state_map = {
                    'Pending': 'draft',
                    'Accepted': 'sent',
                    'Closed': 'sale',
                    'Rejected': 'cancel'
                }
                sale_orders_vals['state'] = state_map.get(so.get('TxnStatus'),
                                                          'draft')

                customer_ref = so.get('CustomerRef', {}).get('value')
                customer_id = self.env['res.partner'].search(
                    [('qbooks_customer', '=', customer_ref)], limit=1)
                if not customer_id:
                    raise ValidationError(
                        'Customer not found. Please import customer first.')
                sale_orders_vals['partner_id'] = customer_id.id

                if currency_id:
                    pricelist = None
                    if customer_id.property_product_pricelist and \
                            customer_id.property_product_pricelist.currency_id == currency_id:
                        pricelist = customer_id.property_product_pricelist
                    else:
                        pricelist = self._get_or_create_pricelist_for_currency(
                            currency_id)
                        if pricelist:
                            if not customer_id.property_product_pricelist or \
                                    customer_id.property_product_pricelist.currency_id != currency_id:
                                customer_id.write({
                                                      'property_product_pricelist': pricelist.id})

                    if pricelist:
                        sale_orders_vals['pricelist_id'] = pricelist.id

                if so.get('CustomerMemo'):
                    sale_orders_vals['note'] = so['CustomerMemo'].get('value')

                if so.get('DiscountLineDetail'):
                    sale_orders_vals['discount'] = so['DiscountLineDetail'].get(
                        'DiscountPercent')

                bill_id = so.get('BillAddr', {}).get('Id')
                ship_id = so.get('ShipAddr', {}).get('Id')
                sale_orders_vals['partner_invoice_id'] = self.env[
                                                             'res.partner'].search(
                    [('qbooks_customer', '=', bill_id)],
                    limit=1).id or customer_id.id

                if ship_id:
                    sale_orders_vals['partner_shipping_id'] = self.env[
                                                                  'res.partner'].search(
                        [('qbooks_customer', '=', ship_id)],
                        limit=1).id or customer_id.id
                elif bill_id:
                    sale_orders_vals['partner_shipping_id'] = self.env[
                                                                  'res.partner'].search(
                        [('qbooks_customer', '=', bill_id)],
                        limit=1).id or customer_id.id

                # Linked invoices
                invoice_ids = []
                for txn in so.get('LinkedTxn', []):
                    if txn.get('TxnId'):
                        invoice_ids.append(self.import_invoice(txn['TxnId']))

                # Sale order lines
                for line in so.get('Line', []):
                    detail = line.get('SalesItemLineDetail')
                    if not detail:
                        continue
                    product_ref = detail.get('ItemRef', {}).get('value')
                    product_id = self.env['product.product'].search(
                        [('qbooks_product', '=', product_ref)], limit=1)
                    if not product_id:
                        raise ValidationError(
                            'Product not found. Please import product first.')

                    line_vals = {
                        'product_id': product_id.id,
                        'name': line.get('Description'),
                        'product_uom_qty': detail.get('Qty'),
                        'price_unit': detail.get('UnitPrice'),
                        'qbooks_sale_line': line.get('Id'),
                        'qbooks_sale': so_id,
                    }

                    tax_code_ref = detail.get('TaxCodeRef', {}).get('value')
                    if tax_code_ref == 'TAX':
                        tax_ref = so.get('TxnTaxDetail', {}).get(
                            'TxnTaxCodeRef', {}).get('value')
                        if tax_ref:
                            tax_id = self.env['account.tax'].search(
                                [('qbooks_tax', '=', tax_ref),
                                 ('type_tax_use', '=', 'sale')],
                                limit=1)
                            if tax_id:
                                line_vals['tax_ids'] = [(6, 0, [tax_id.id])]
                            else:
                                line_vals['tax_ids'] = [(6, 0, [])]
                        else:
                            line_vals['tax_ids'] = [(6, 0, [])]
                    else:
                        line_vals['tax_ids'] = [(6, 0, [])]

                    line_vals = self._apply_line_tax_exemption(line_vals,
                                                               customer_id.id)

                    if invoice_ids:
                        invoices = self.env['account.move'].browse(invoice_ids)
                        invoice_lines = invoices.mapped('invoice_line_ids')
                        related_invoice_lines = invoice_lines.filtered(
                            lambda inv: inv.qbooks_sale == so_id and
                                        inv.qbooks_invoice_line == line.get(
                                'Id'))
                        if related_invoice_lines:
                            line_vals['invoice_lines'] = [
                                (6, 0, related_invoice_lines.ids)]

                    sale_orders_vals['order_line'].append((0, 0, line_vals))

                ctx = self._get_qbooks_currency_context(so, so_date.date())
                created = self.env['sale.order'].with_context(**ctx).create(
                    [sale_orders_vals])

                # ✅ Log success per sale order
                self._log_qbooks_operation(
                    operation_name=f"Sale Order Import: {so_number}",
                    op_type='import',
                    status='success',
                    message=(
                        f"Sale order '{so_number}' (QBO ID: {so_id}) imported successfully "
                        f"for customer '{customer_id.name}' with {len(sale_orders_vals['order_line'])} line(s)"
                        f"{f' and {len(invoice_ids)} linked invoice(s)' if invoice_ids else ''}."
                    ),
                    record=created,
                    payload=so,
                )
                total += 1

            except Exception as e:
                failed_count += 1
                _logger.error(
                    f"Failed to import sale order '{so_number}' (QBO ID: {so_id}): {e}")

                # ❌ Log failure per sale order
                self._log_qbooks_operation(
                    operation_name=f"Sale Order Import: {so_number}",
                    op_type='import',
                    status='failed',
                    message=str(e),
                    payload=so,
                )
                # Re-raise ValidationErrors — missing customer/product must halt the batch
                if isinstance(e, ValidationError):
                    raise

        # 📊 Log batch summary
        self._log_qbooks_operation(
            operation_name="Sale Order Import Batch",
            op_type='import',
            status='success' if not failed_count else 'failed',
            message=(
                f"Batch complete: {total} sale order(s) imported successfully, "
                f"{failed_count} failed. "
                f"(start_position={start_position}, max_results={max_results})"
            ),
            payload={
                'start_position': start_position,
                'max_results': max_results,
                'created': total,
                'failed': failed_count,
            },
        )

        _logger.info(
            f"{total} sale orders imported (start_position: {start_position})")

    def import_invoice(self, txn_id, inv_type='out_invoice'):
        """Function to import invoice from sale order to quickbook"""
        url = self.get_import_query()
        if url:
            get_url = (f'{url["url"]}/invoice/{txn_id}?minorversion='
                       f'{self.minor_version}')
            data = requests.get(get_url, headers=url['headers'])
            if data.json() and data.json().get('Invoice'):
                invoice = data.json().get('Invoice')
                exist = self.env['account.move'].search(
                    [('qbooks_invoice', '=', invoice.get('Id'))])
                if exist:
                    return exist.id
                if invoice.get('CustomerRef'):
                    customer_id = self.env['res.partner'].search([(
                        'qbooks_customer',
                        '=',
                        invoice.get(
                            'CustomerRef').get(
                            'value'))],
                        limit=1).id
                else:
                    customer_id = False

                rate_info = self._apply_qbooks_exchange_rate(invoice)

                currency_id = self.env['res.currency'].browse(
                    rate_info.get('currency_id')
                ) if rate_info.get('currency_id') else self.env['res.currency'].search(
                    [('name', '=', invoice.get('CurrencyRef', {}).get('value'))], limit=1
                )

                invoice_date = datetime.strptime(invoice.get('TxnDate'), '%Y-%m-%d')

                invoice_vals = {
                    'qbooks_invoice': invoice.get('Id'),
                    'partner_id': customer_id,
                    'invoice_date': invoice_date,
                    'invoice_line_ids': [],
                    'move_type': inv_type,
                }
                if invoice.get('BillAddr'):
                    invoice_vals['partner_id'] = self.env[
                        'res.partner'].search([('qbooks_customer', '=',
                                                invoice.get('BillAddr').get(
                                                    'Id'))]).id
                if invoice.get('ShipAddr'):
                    invoice_vals['partner_shipping_id'] = self.env[
                        'res.partner'].search([('qbooks_customer', '=',
                                                invoice.get('ShipAddr').get(
                                                    'Id'))]).id
                for line in invoice.get('Line'):
                    if line.get('SalesItemLineDetail'):
                        product_id = self.env['product.product'].search([(
                            'qbooks_product',
                            '=',
                            line.get(
                                'SalesItemLineDetail').get(
                                'ItemRef').get(
                                'value'))])
                        if product_id:
                            line_vals = [(0, 0, {
                                'product_id': product_id.id,
                                'name': product_id.name,
                                'quantity': line.get(
                                    'SalesItemLineDetail').get('Qty'),
                                'price_unit': line.get(
                                    'SalesItemLineDetail').get('UnitPrice'),
                                'qbooks_invoice_line': line.get('Id'),
                                'qbooks_invoice': invoice.get('Id')
                            })]
                            tax_code_ref = line.get('SalesItemLineDetail').get('TaxCodeRef') and line.get(
                                'SalesItemLineDetail').get('TaxCodeRef').get('value')
                            if tax_code_ref == 'Tax':
                                if invoice.get('TxnTaxDetail') and invoice.get('TxnTaxDetail').get('TxnTaxCodeRef'):
                                    tax_id = self.env['account.tax'].search([
                                        ('qbooks_tax', '=',
                                         invoice.get('TxnTaxDetail').get('TxnTaxCodeRef').get('value')),
                                        ('type_tax_use', '=', 'sale')
                                    ], limit=1)
                                    if tax_id:
                                        line_vals[0][2]['tax_ids'] = [(6, 0, [tax_id.id])]
                                    else:
                                        line_vals[0][2]['tax_ids'] = [(6, 0, [])]
                                else:
                                    line_vals[0][2]['tax_ids'] = [(6, 0, [])]
                            else:
                                line_vals[0][2]['tax_ids'] = [(6, 0, [])]

                            if (line.get('LinkedTxn') and
                                    line.get('LinkedTxn')[0].get('TxnType')
                                    == 'Estimate'):
                                line_vals[0][2]['qbooks_sale'] = \
                                    line.get('LinkedTxn')[0].get('TxnId')
                            invoice_vals['invoice_line_ids'] += line_vals
                ctx = self._get_qbooks_currency_context(invoice, invoice_date.date())
                invoice_id = self.env['account.move'].with_context(**ctx).create([invoice_vals])
                return invoice_id.id
        return False

    def action_import_po(self):
        """Queue the job to import purchase order with priority."""
        self.with_delay(priority=1)._run_import_po_job()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Import Started',
                'message': 'Purchase orders import has been queued in the background.',
                'type': 'info',
                'sticky': False,
            }
        }

    def _run_import_po_job(self):
        """Fetching the purchase orders from QuickBooks"""
        url = self.get_import_query()
        if not url:
            _logger.warning("No URL returned from import query.")
            return

        start_position = 1
        max_results = 100

        while True:
            query = f"SELECT * FROM PurchaseOrder STARTPOSITION {start_position} MAXRESULTS {max_results}"
            get_url = f"{url['url']}/query?minorversion={self.minor_version}&query={query}"

            try:
                response = requests.get(get_url, headers=url['headers'])
                if response.json().get('fault', {}).get(
                        'type') == 'AUTHENTICATION':
                    self.action_refresh_token()
                    response = requests.get(get_url, headers=url['headers'])
            except Exception as e:
                _logger.error(f"Error while fetching purchase orders: {e}")
                break

            purchase_orders = response.json().get('QueryResponse', {}).get(
                'PurchaseOrder', [])
            if not purchase_orders:
                break

            self.with_delay(priority=1)._batch_schedule_po_import(
                purchase_orders, max_results=max_results,
                start_position=start_position
            )

            start_position += max_results

    def _batch_schedule_po_import(self, purchase_orders, max_results,
                                  start_position):
        """Batching the purchase orders"""
        size = 10
        purchase_list = [purchase_orders[i:i + size] for i in
                         range(0, len(purchase_orders), size)]

        for index, chunk in enumerate(purchase_list):
            delay_time = fields.Datetime.now() + timedelta(seconds=index * 10)
            self.with_delay(priority=1, eta=delay_time)._purchase_import(
                chunk, max_results, start_position
            )

    def _purchase_import(self, purchase_orders, max_results, start_position):
        """Creating the purchase orders"""
        total = 0
        failed_count = 0

        for po in purchase_orders:
            po_id = po.get('Id')
            po_number = po.get('DocNumber', 'Unknown')

            try:
                if self.env['purchase.order'].search(
                        [('qbooks_purchase', '=', po_id)], limit=1):
                    continue

                rate_info = self._apply_qbooks_exchange_rate(po)
                currency_id = self.env['res.currency'].browse(
                    rate_info.get('currency_id')
                ) if rate_info.get('currency_id') else self.env[
                    'res.currency'].search(
                    [('name', '=', po.get('CurrencyRef', {}).get('value'))],
                    limit=1
                )

                vendor_ref = po.get('VendorRef', {}).get('value')
                vendor_id = self.env['res.partner'].search(
                    [('qbooks_vendor', '=', vendor_ref)], limit=1)
                po_date = datetime.strptime(po.get('TxnDate'),
                                            '%Y-%m-%d') if po.get(
                    'TxnDate') else fields.Datetime.now()

                if not vendor_id:
                    raise ValidationError(
                        "Vendor not found. Please import vendor first.")

                purchase_order_vals = {
                    'qbooks_purchase': po_id,
                    'name': po_number,
                    'currency_id': currency_id.id if currency_id else False,
                    'partner_id': vendor_id.id,
                    'order_line': [],
                    'date_order': po_date,
                }

                state_map = {
                    'Open': 'draft',
                    'Closed': 'purchase'
                }
                purchase_order_vals['state'] = state_map.get(po.get('POStatus'),
                                                             'draft')

                invoice_ids = []
                for txn in po.get('LinkedTxn', []):
                    if txn.get('TxnId'):
                        invoice_ids.append(
                            self.import_vendor_bill(txn['TxnId']))

                for line in po.get('Line', []):
                    detail = line.get('ItemBasedExpenseLineDetail')
                    if not detail or not detail.get('ItemRef'):
                        continue

                    product_id = self.env['product.product'].search(
                        [('qbooks_product', '=', detail['ItemRef']['value'])],
                        limit=1)
                    if not product_id:
                        raise ValidationError(
                            'Product not found. Please import product first.')

                    line_vals = {
                        'product_id': product_id.id,
                        'name': line.get('Description'),
                        'product_qty': detail.get('Qty'),
                        'price_unit': detail.get('UnitPrice'),
                        'qbooks_purchase_line': line.get('Id'),
                        'qbooks_purchase': po_id,
                        'date_planned': fields.Datetime.now(),
                        'invoice_lines': [],
                    }

                    tax_code_ref = detail.get('TaxCodeRef', {}).get('value')
                    if tax_code_ref == "TAX":
                        tax_ref = po.get('TxnTaxDetail', {}).get(
                            'TxnTaxCodeRef', {}).get('value')
                        if tax_ref:
                            tax_id = self.env['account.tax'].search(
                                [('qbooks_tax', '=', tax_ref),
                                 ('type_tax_use', '=', 'purchase')], limit=1)
                            line_vals['tax_ids'] = [
                                (6, 0, [tax_id.id])] if tax_id else [(6, 0, [])]
                        else:
                            line_vals['tax_ids'] = [(6, 0, [])]
                    else:
                        line_vals['tax_ids'] = [(6, 0, [])]

                    if invoice_ids:
                        invoices = self.env['account.move'].browse(invoice_ids)
                        invoice_lines = invoices.mapped('invoice_line_ids')
                        matched_invoice_lines = [
                            inv_line.id for inv_line in invoice_lines
                            if inv_line.qbooks_invoice_line == line.get('Id')
                        ]
                        if matched_invoice_lines:
                            line_vals['invoice_lines'] = [
                                (6, 0, matched_invoice_lines)]

                    purchase_order_vals['order_line'].append((0, 0, line_vals))

                ctx = self._get_qbooks_currency_context(po, po_date.date())
                created = self.env['purchase.order'].with_context(**ctx).create(
                    [purchase_order_vals])

                # ✅ Log success per purchase order
                self._log_qbooks_operation(
                    operation_name=f"Purchase Order Import: {po_number}",
                    op_type='import',
                    status='success',
                    message=(
                        f"Purchase order '{po_number}' (QBO ID: {po_id}) imported successfully "
                        f"for vendor '{vendor_id.name}' with {len(purchase_order_vals['order_line'])} line(s)"
                        f"{f' and {len(invoice_ids)} linked vendor bill(s)' if invoice_ids else ''}."
                    ),
                    record=created,
                    payload=po,
                )
                total += 1

            except Exception as e:
                failed_count += 1
                _logger.error(
                    f"Failed to import purchase order '{po_number}' (QBO ID: {po_id}): {e}")

                # ❌ Log failure per purchase order
                self._log_qbooks_operation(
                    operation_name=f"Purchase Order Import: {po_number}",
                    op_type='import',
                    status='failed',
                    message=str(e),
                    payload=po,
                )
                # Re-raise ValidationErrors — missing vendor/product must halt the batch
                if isinstance(e, ValidationError):
                    raise

        # 📊 Log batch summary
        self._log_qbooks_operation(
            operation_name="Purchase Order Import Batch",
            op_type='import',
            status='success' if not failed_count else 'failed',
            message=(
                f"Batch complete: {total} purchase order(s) imported successfully, "
                f"{failed_count} failed. "
                f"(start_position={start_position}, max_results={max_results})"
            ),
            payload={
                'start_position': start_position,
                'max_results': max_results,
                'created': total,
                'failed': failed_count,
            },
        )

        _logger.info(
            f"{total} purchase orders imported (start_position: {start_position})")

    def import_vendor_bill(self, txn_id, inv_type='in_invoice'):
        """Function to import vendor bills from quickbook"""
        url = self.get_import_query()
        if url:
            get_url = (f'{url["url"]}/bill/{txn_id}?minorversion='
                       f'{self.minor_version}')
            data = requests.get(get_url, headers=url['headers'])
            if data.json() and data.json().get('Bill'):
                bill = data.json().get('Bill')
                bill_obj = self.env['account.move']
                exist = bill_obj.search(
                    [('qbooks_bill', '=', bill.get('Id'))])
                if exist:
                    return exist.id

                rate_info = self._apply_qbooks_exchange_rate(bill)
                currency_id = self.env['res.currency'].browse(
                    rate_info.get('currency_id')
                ) if rate_info.get('currency_id') else self.env['res.currency'].search(
                    [('name', '=', bill.get('CurrencyRef', {}).get('value'))], limit=1
                )

                bill_date = datetime.strptime(bill.get('TxnDate'), '%Y-%m-%d')

                if bill.get('VendorRef'):
                    vendor_id = self.env['res.partner'].search([(
                        'qbooks_vendor',
                        '=', bill.get(
                            'VendorRef').get(
                            'value'))],
                        limit=1).id
                else:
                    vendor_id = False
                invoice_vals = {
                    'qbooks_bill': bill.get('Id'),
                    'partner_id': vendor_id,
                    'invoice_date': bill_date,
                    'invoice_line_ids': [],
                    'move_type': inv_type,
                }
                if bill.get('BillAddr'):
                    invoice_vals['partner_id'] = self.env[
                        'res.partner'].search([('qbooks_vendor', '=',
                                                bill.get('BillAddr').get(
                                                    'Id'))]).id
                if bill.get('ShipAddr'):
                    invoice_vals['partner_shipping_id'] = self.env[
                        'res.partner'].search([('qbooks_vendor', '=',
                                                bill.get('ShipAddr').get(
                                                    'Id'))]).id
                for line in bill.get('Line'):
                    if line.get('ItemBasedExpenseLineDetail') and line.get(
                            'ItemBasedExpenseLineDetail').get('ItemRef'):
                        product_id = self.env['product.product'].search([(
                            'qbooks_product',
                            '=',
                            line.get(
                                'ItemBasedExpenseLineDetail').get(
                                'ItemRef').get(
                                'value'))])
                        if product_id:
                            line_vals = [(0, 0, {
                                'product_id': product_id.id,
                                'name': product_id.name,
                                'quantity': line.get(
                                    'ItemBasedExpenseLineDetail').get('Qty'),
                                'price_unit': line.get(
                                    'ItemBasedExpenseLineDetail').get(
                                    'UnitPrice'),
                                'qbooks_invoice_line': line.get('Id'),
                                'qbooks_bill': bill.get('Id')
                            })]
                            # Tax handling
                            tax_code_ref = line.get('ItemBasedExpenseLineDetail').get(
                                'TaxCodeRef') and line.get('ItemBasedExpenseLineDetail').get('TaxCodeRef').get('value')
                            if tax_code_ref == "TAX":
                                if bill.get('TxnTaxDetail') and bill.get('TxnTaxDetail').get('TxnTaxCodeRef'):
                                    tax_id = self.env['account.tax'].search([
                                        ('qbooks_tax', '=', bill.get('TxnTaxDetail').get('TxnTaxCodeRef').get('value')),
                                        ('type_tax_use', '=', 'purchase')], limit=1)
                                    if tax_id:
                                        line_vals[0][2]['tax_ids'] = [(6, 0, [tax_id.id])]
                                    else:
                                        line_vals[0][2]['tax_ids'] = [(6, 0, [])]
                                else:
                                    line_vals[0][2]['tax_ids'] = [(6, 0, [])]
                            else:
                                # Tax exempted
                                line_vals[0][2]['tax_ids'] = [(6, 0, [])]

                            if (bill.get('LinkedTxn') and
                                    bill.get('LinkedTxn')[0].get('TxnType')
                                    == 'BillPaymentCheck'):
                                line_vals[0][2]['qbooks_payment'] = \
                                    bill.get('LinkedTxn')[0].get('TxnId')
                            invoice_vals['invoice_line_ids'] += line_vals
                ctx = self._get_qbooks_currency_context(bill, bill_date.date())
                bill_id = bill_obj.with_context(**ctx).create([invoice_vals])
                return bill_id.id
        return False

    def action_import_bill(self):
        """Queue job function to import vendor bills"""
        self.with_delay(priority=1)._run_import_bill_job()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Import Started',
                'message': 'Bills import has been queued in the background.',
                'type': 'info',
                'sticky': False,
            }
        }

    def _run_import_bill_job(self):
        """Function to batch and import bill"""
        url = self.get_import_query()
        if not url:
            _logger.warning("No URL returned from import query.")
            return

        start_position = 1
        max_results = 100

        while True:
            query = f'SELECT * FROM Bill STARTPOSITION {start_position} MAXRESULTS {max_results}'
            get_url = f"{url['url']}/query?minorversion={self.minor_version}&query={query}"

            try:
                response = requests.get(get_url, headers=url['headers'])
                if response.json().get('fault', {}).get(
                        'type') == 'AUTHENTICATION':
                    self.action_refresh_token()
                    response = requests.get(get_url, headers=url['headers'])
            except Exception as e:
                _logger.error(f"Error while fetching invoices: {e}")
                break

            query_resp = response.json().get('QueryResponse') or {}
            bills = query_resp.get('Bill', [])

            if not bills:
                break

            self.with_delay(priority=1)._batch_schedule_bill_import(
                bills, total=0, max_results=max_results,
                start_position=start_position
            )
            start_position += max_results

    def _batch_schedule_bill_import(self, bills, total, max_results,
                                    start_position):
        """Function to patch and import bills"""
        size = 10
        bills_list = [bills[i:i + size] for i in range(0, len(bills), size)]

        for index, bill_chunk in enumerate(bills_list):
            delay_time = fields.Datetime.now() + timedelta(seconds=index * 10)
            self.with_delay(priority=1, eta=delay_time)._bill_import(
                bill_chunk, total, max_results, start_position)

    def _bill_import(self, bills, total, max_results, start_position):
        """Importing bills"""
        failed_count = 0

        for bill in bills:
            bill_id = bill.get('Id')
            bill_vendor = bill.get('VendorRef', {}).get('name', 'Unknown')

            try:
                exist = self.env['account.move'].search(
                    [('qbooks_bill', '=', bill_id)])
                if exist:
                    if len(exist) > 1:
                        exist[1:].unlink()
                    continue

                rate_info = self._apply_qbooks_exchange_rate(bill)
                currency = bill.get('CurrencyRef')
                currency_id = self.env['res.currency'].browse(
                    rate_info.get('currency_id')
                ) if rate_info.get('currency_id') else self.env[
                    'res.currency'].search(
                    [('name', '=', currency['value'])]
                )
                bill_date = datetime.strptime(bill.get('TxnDate'), '%Y-%m-%d')

                invoice_vals = {
                    'qbooks_bill': bill_id,
                    'invoice_date': bill_date,
                    'invoice_line_ids': [],
                    'move_type': 'in_invoice',
                    'currency_id': currency_id.id,
                }

                # Vendor handling
                if bill.get('VendorRef'):
                    vendor = self.env['res.partner'].search(
                        [('qbooks_vendor', '=',
                          bill.get('VendorRef').get('value'))], limit=1)
                    if vendor:
                        invoice_vals['partner_id'] = vendor.id
                        bill_vendor = vendor.name  # use resolved name for log messages
                    else:
                        raise ValidationError(
                            f"Vendor with QuickBooks ID {bill.get('VendorRef').get('value')} not found. Please import vendors first."
                        )
                else:
                    continue

                # Handle linked vendor payment
                if bill.get('LinkedTxn') and bill.get('LinkedTxn')[0].get(
                        'TxnType') == 'BillPaymentCheck':
                    self.import_ven_pay(bill.get('LinkedTxn')[0].get('TxnId'),
                                        currency_id)

                for line in bill.get('Line', []):
                    # Item-based line
                    if line.get('DetailType') == 'ItemBasedExpenseLineDetail':
                        item_detail = line.get('ItemBasedExpenseLineDetail')
                        if item_detail and item_detail.get('ItemRef'):
                            product = self.env['product.product'].search(
                                [('qbooks_product', '=',
                                  item_detail.get('ItemRef').get('value'))],
                                limit=1)

                            if product:
                                line_vals = [(0, 0, {
                                    'product_id': product.id,
                                    'name': product.name,
                                    'quantity': item_detail.get('Qty'),
                                    'price_unit': item_detail.get('UnitPrice'),
                                    'qbooks_invoice_line': line.get('Id'),
                                    'qbooks_bill': bill_id,
                                })]

                                if item_detail.get('AccountRef'):
                                    account = self.env[
                                        'account.account'].search(
                                        [('qbooks_account', '=',
                                          item_detail.get('AccountRef').get(
                                              'value'))],
                                        limit=1)
                                    if account:
                                        line_vals[0][2][
                                            'account_id'] = account.id

                                    tax_code_ref = item_detail.get(
                                        'TextCodeRef', {}).get('value')
                                    if tax_code_ref == "TAX":
                                        if bill.get(
                                                'TxnTaxDetail') and bill.get(
                                                'TxnTaxDetail').get(
                                            'TxnTaxCodeRef'):
                                            tax = self.env[
                                                'account.tax'].search(
                                                [('qbooks_tax', '=',
                                                  bill.get('TxnTaxDetail')
                                                  .get('TxnTaxCodeRef').get(
                                                      'value')),
                                                 ('type_tax_use', '=',
                                                  'purchase')], limit=1)
                                            line_vals[0][2]['tax_ids'] = [
                                                (6, 0, [tax.id])] if tax else [
                                                (6, 0, [])]
                                        else:
                                            line_vals[0][2]['tax_ids'] = [
                                                (6, 0, [])]
                                    else:
                                        line_vals[0][2]['tax_ids'] = [
                                            (6, 0, [])]

                                    if bill.get('LinkedTxn') and \
                                            bill.get('LinkedTxn')[0].get(
                                                'TxnType') == 'BillPaymentCheck':
                                        line_vals[0][2]['qbooks_payment'] = \
                                            bill.get('LinkedTxn')[0].get(
                                                'TxnId')

                                    invoice_vals[
                                        'invoice_line_ids'] += line_vals

                    # Account-based line
                    elif line.get(
                            'DetailType') == 'AccountBasedExpenseLineDetail':
                        item_detail = line.get('AccountBasedExpenseLineDetail')
                        if item_detail and item_detail.get('AccountRef'):
                            name = line.get('Description') or item_detail.get(
                                'AccountRef', {}).get('name') or 'Expense'

                            line_vals = [(0, 0, {
                                'name': name,
                                'quantity': 1,
                                'price_unit': line.get('Amount') or bill.get(
                                    'TotalAmt'),
                                'qbooks_invoice_line': line.get('Id'),
                                'qbooks_bill': bill_id,
                            })]

                            account = self.env['account.account'].search(
                                [('qbooks_account', '=',
                                  item_detail.get('AccountRef').get('value'))],
                                limit=1)
                            if account:
                                line_vals[0][2]['account_id'] = account.id

                            if (item_detail.get('TaxCodeRef') and
                                    item_detail.get('TaxCodeRef').get(
                                        'value') == "TAX" and
                                    bill.get('TxnTaxDetail') and
                                    bill.get('TxnTaxDetail').get(
                                        'TxnTaxCodeRef')):
                                tax = self.env['account.tax'].search(
                                    [('qbooks_tax', '=',
                                      bill.get('TxnTaxDetail')
                                      .get('TxnTaxCodeRef').get('value'))],
                                    limit=1)
                                line_vals[0][2]['tax_ids'] = [
                                    (6, 0, [tax.id])] if tax else [(6, 0, [])]
                            else:
                                line_vals[0][2]['tax_ids'] = [(6, 0, [])]

                            if bill.get('LinkedTxn') and \
                                    bill.get('LinkedTxn')[0].get(
                                        'TxnType') == 'BillPaymentCheck':
                                line_vals[0][2]['qbooks_payment'] = \
                                    bill.get('LinkedTxn')[0].get('TxnId')

                            invoice_vals['invoice_line_ids'] += line_vals

                ctx = self._get_qbooks_currency_context(bill, bill_date.date())
                created = self.env['account.move'].with_context(**ctx).create(
                    [invoice_vals])

                # ✅ Log success per bill
                self._log_qbooks_operation(
                    operation_name=f"Vendor Bill Import: {bill_vendor}",
                    op_type='import',
                    status='success',
                    message=(
                        f"Vendor bill (QBO ID: {bill_id}) imported successfully "
                        f"for vendor '{bill_vendor}' with {len(invoice_vals['invoice_line_ids'])} line(s)"
                        f"{', linked to BillPaymentCheck: ' + bill['LinkedTxn'][0]['TxnId'] if bill.get('LinkedTxn') and bill['LinkedTxn'][0].get('TxnType') == 'BillPaymentCheck' else ''}."
                    ),
                    record=created,
                    payload=bill,
                )
                total += 1

            except Exception as e:
                failed_count += 1
                _logger.error(
                    f"Failed to import vendor bill (QBO ID: {bill_id}) for '{bill_vendor}': {e}")

                # ❌ Log failure per bill
                self._log_qbooks_operation(
                    operation_name=f"Vendor Bill Import: {bill_vendor}",
                    op_type='import',
                    status='failed',
                    message=str(e),
                    payload=bill,
                )
                # Re-raise ValidationErrors — missing vendor must halt the batch
                if isinstance(e, ValidationError):
                    raise

        # 📊 Log batch summary
        self._log_qbooks_operation(
            operation_name="Vendor Bill Import Batch",
            op_type='import',
            status='success' if not failed_count else 'failed',
            message=(
                f"Batch complete: {total} vendor bill(s) imported successfully, "
                f"{failed_count} failed. "
                f"(start_position={start_position}, max_results={max_results})"
            ),
            payload={
                'start_position': start_position,
                'max_results': max_results,
                'created': total,
                'failed': failed_count,
            },
        )

        # Pagination logic (pre-existing bug: run/start_position not returned)
        if len(bills) < max_results:
            run = False
        else:
            start_position += max_results

        if total != 0:
            _logger.info(f"{total} vendor bills imported from QuickBooks.")
        else:
            _logger.info("No vendor bills to import.")

    def import_ven_pay(self, txn_id, currency_id):
        """Function to import vendor payments from quickbook"""
        url = self.get_import_query()
        if url:
            get_url = (f'{url["url"]}/billpayment/{txn_id}?minorversion='
                       f'{self.minor_version}')
            data = requests.get(get_url, headers=url['headers'])
            if data.json() and data.json().get('BillPayment'):
                payment = data.json().get('BillPayment')
                payment_obj = self.env['account.payment']
                exist = payment_obj.search(
                    [('qbooks_payment', '=', payment.get('Id'))])
                if exist:
                    if len(exist) > 1:
                        exist[1:].unlink()
                    return True
                if payment.get('VendorRef'):
                    vendor_id = self.env['res.partner'].search([(
                        'qbooks_vendor',
                        '=',
                        payment.get(
                            'VendorRef').get(
                            'value'))],
                        limit=1).id
                else:
                    vendor_id = False
                payment_vals = {
                    'qbooks_payment': payment.get('Id'),
                    'partner_id': vendor_id,
                    'date': datetime.strptime(payment.get('TxnDate'),
                                                       '%Y-%m-%d'),
                    'amount': payment.get('TotalAmt'),
                    'payment_type': 'outbound',
                    'partner_type': 'supplier',
                    'currency_id': currency_id.id,
                }
                payment_id = payment_obj.create([payment_vals])
                return payment_id.id
        return False

    def action_import_vendor_payment(self):
        """Queue the job to import vendor payments with priority."""
        self.with_delay(priority=1)._run_import_ven_payment_job()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Import Started',
                'message': 'Vendor payments import has been queued in the background.',
                'type': 'info',
                'sticky': False,
            }
        }

    def _run_import_ven_payment_job(self):
        """Fetching vendor payments from QuickBooks"""
        url = self.get_import_query()
        if not url:
            _logger.warning("No URL returned from import query.")
            return

        start_position = 1
        max_results = 100

        while True:
            query = f"SELECT * FROM BillPayment STARTPOSITION {start_position} MAXRESULTS {max_results}"
            get_url = f"{url['url']}/query?minorversion={self.minor_version}&query={query}"

            try:
                response = requests.get(get_url, headers=url['headers'])
                if response.json().get('fault', {}).get(
                        'type') == 'AUTHENTICATION':
                    self.action_refresh_token()
                    response = requests.get(get_url, headers=url['headers'])
            except Exception as e:
                _logger.error(f"Error while fetching vendor payments: {e}")
                break

            payments = response.json().get('QueryResponse', {}).get(
                'BillPayment', [])
            if not payments:
                break

            self.with_delay(priority=1)._batch_schedule_ven_payment_import(
                payments, max_results=max_results, start_position=start_position
            )
            start_position += max_results

    def _batch_schedule_ven_payment_import(self, payments, max_results, start_position):
        """Batching the vendor payments"""
        size = 10
        payment_list = [payments[i:i + size] for i in range(0, len(payments), size)]
        for index, payment_chunk in enumerate(payment_list):
            delay_time = fields.Datetime.now() + timedelta(seconds=index * 10)
            self.with_delay(priority=1, eta=delay_time)._ven_payment_import(
                payment_chunk, max_results, start_position
            )

    def _ven_payment_import(self, payments, max_results, start_position):
        """Creating vendor payments"""
        payment_obj = self.env['account.payment']
        total = 0
        failed_count = 0

        for payment in payments:
            pay_id = payment.get('Id')
            pay_number = payment.get('DocNumber', 'Unknown')
            vendor_name = payment.get('VendorRef', {}).get('name', 'Unknown')

            try:
                exist = payment_obj.search([('qbooks_payment', '=', pay_id)])
                if exist:
                    if len(exist) > 1:
                        exist[1:].unlink()
                    continue

                rate_info = self._apply_qbooks_exchange_rate(payment)
                currency_id = self.env['res.currency'].browse(
                    rate_info.get('currency_id')
                ) if rate_info.get('currency_id') else self.env[
                    'res.currency'].search(
                    [('name', '=',
                      payment.get('CurrencyRef', {}).get('value'))], limit=1
                )

                payment_date = datetime.strptime(payment.get('TxnDate'),
                                                 '%Y-%m-%d')

                payment_vals = {
                    'qbooks_payment': pay_id,
                    'name': pay_number,
                    'amount': payment.get('TotalAmt'),
                    'date': payment_date,
                    'partner_type': 'supplier',
                    'payment_type': 'outbound',
                    'currency_id': currency_id.id if currency_id else False,
                }

                vendor_ref = payment.get('VendorRef', {}).get('value')
                vendor = self.env['res.partner'].search(
                    [('qbooks_vendor', '=', vendor_ref)], limit=1)
                if not vendor:
                    raise ValidationError(
                        "Vendor not found. Please import vendor first.")

                vendor_name = vendor.name  # resolve to Odoo name for log messages
                payment_vals['partner_id'] = vendor.id

                # Ensure all linked vendor bills exist before creating payment
                linked_bill_ids = []
                for line in payment.get('Line', []):
                    for txn in line.get('LinkedTxn', []):
                        if txn.get('TxnId'):
                            self.import_vendor_bill(txn['TxnId'])
                            linked_bill_ids.append(txn['TxnId'])

                ctx = self._get_qbooks_currency_context(payment,
                                                        payment_date.date())
                created = payment_obj.with_context(**ctx).create([payment_vals])

                # ✅ Log success per vendor payment
                self._log_qbooks_operation(
                    operation_name=f"Vendor Payment Import: {pay_number}",
                    op_type='import',
                    status='success',
                    message=(
                        f"Vendor payment '{pay_number}' (QBO ID: {pay_id}) of {payment.get('TotalAmt')} "
                        f"imported for vendor '{vendor_name}'"
                        f"{f', ensured {len(linked_bill_ids)} linked bill(s): {linked_bill_ids}' if linked_bill_ids else ', no linked bills'}."
                    ),
                    record=created,
                    payload=payment,
                )
                total += 1

            except Exception as e:
                failed_count += 1
                _logger.error(
                    f"Failed to import vendor payment '{pay_number}' (QBO ID: {pay_id}): {e}")

                # ❌ Log failure per vendor payment
                self._log_qbooks_operation(
                    operation_name=f"Vendor Payment Import: {pay_number}",
                    op_type='import',
                    status='failed',
                    message=str(e),
                    payload=payment,
                )
                # Re-raise ValidationErrors — missing vendor must halt the batch
                if isinstance(e, ValidationError):
                    raise

        # 📊 Log batch summary
        self._log_qbooks_operation(
            operation_name="Vendor Payment Import Batch",
            op_type='import',
            status='success' if not failed_count else 'failed',
            message=(
                f"Batch complete: {total} vendor payment(s) imported successfully, "
                f"{failed_count} failed. "
                f"(start_position={start_position}, max_results={max_results})"
            ),
            payload={
                'start_position': start_position,
                'max_results': max_results,
                'created': total,
                'failed': failed_count,
            },
        )

        _logger.info(
            f"{total} vendor payments imported (start_position: {start_position})")

    def action_import_customer_payment(self):
        """Queue the job to import customer payments with priority."""
        self.with_delay(priority=1)._run_import_cust_payment_job()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Import Started',
                'message': 'Customer payment import has been queued in the background.',
                'type': 'info',
                'sticky': False,
            }
        }

    def _run_import_cust_payment_job(self):
        """Fetching the customer payments"""
        url = self.get_import_query()
        if not url:
            _logger.warning("No URL returned from import query.")
            return

        start_position = 1
        max_results = 100

        while True:
            query = f'SELECT * FROM Payment STARTPOSITION {start_position} MAXRESULTS {max_results}'
            get_url = f"{url['url']}/query?minorversion={self.minor_version}&query={query}"

            try:
                response = requests.get(get_url, headers=url['headers'])
                if response.json().get('fault', {}).get(
                        'type') == 'AUTHENTICATION':
                    self.action_refresh_token()
                    response = requests.get(get_url, headers=url['headers'])
            except Exception as e:
                _logger.error(f"Error while fetching customer payments: {e}")
                break

            payments = response.json().get('QueryResponse', {}).get('Payment',
                                                                    [])
            if not payments:
                break

            self.with_delay(priority=1)._batch_schedule_cust_payment_import(
                payments, max_results=max_results, start_position=start_position
            )

            start_position += max_results

    def _batch_schedule_cust_payment_import(self, payments, max_results, start_position):
        """Batching the customer payments"""
        size = 10
        payment_list = [payments[i:i + size] for i in range(0, len(payments), size)]
        for index, payment_chunk in enumerate(payment_list):
            delay_time = fields.Datetime.now() + timedelta(seconds=index * 10)
            self.with_delay(priority=1, eta=delay_time)._cust_payment_import(
                payment_chunk, max_results, start_position
            )

    def _cust_payment_import(self, payments, max_results, start_position):
        """Creating customer payments"""
        payment_obj = self.env['account.payment']
        total = 0
        failed_count = 0

        for payment in payments:
            pay_id = payment.get('Id')
            pay_number = payment.get('DocNumber', 'Unknown')

            try:
                exist = payment_obj.search([('qbooks_payment', '=', pay_id)])
                if exist:
                    if len(exist) > 1:
                        exist[1:].unlink()
                    continue

                rate_info = self._apply_qbooks_exchange_rate(payment)
                currency_id = self.env['res.currency'].browse(
                    rate_info.get('currency_id')
                ) if rate_info.get('currency_id') else self.env[
                    'res.currency'].search(
                    [('name', '=',
                      payment.get('CurrencyRef', {}).get('value'))], limit=1
                )

                payment_date = datetime.strptime(payment.get('TxnDate'),
                                                 '%Y-%m-%d')
                payment_vals = {
                    'qbooks_payment': pay_id,
                    'name': pay_number,
                    'amount': payment.get('TotalAmt'),
                    'date': payment_date,
                    'partner_type': 'customer',
                    'payment_type': 'inbound',
                    'currency_id': currency_id.id if currency_id else False,
                }

                customer_ref = payment.get('CustomerRef', {}).get('value')
                customer = self.env['res.partner'].search(
                    [('qbooks_customer', '=', customer_ref)], limit=1
                )

                # ⚠️ Safe skip — log the warning and move on
                if not customer:
                    _logger.warning(
                        "Skipping payment %s — Customer not found in Odoo.",
                        pay_number)
                    self._log_qbooks_operation(
                        operation_name=f"Customer Payment Import: {pay_number}",
                        op_type='import',
                        status='failed',
                        message=f"Skipped — customer (QBO ref: {customer_ref}) not found in Odoo. Please import customers first.",
                        payload=payment,
                    )
                    failed_count += 1
                    continue

                payment_vals['partner_id'] = customer.id

                ctx = self._get_qbooks_currency_context(payment,
                                                        payment_date.date())
                odoo_payment = payment_obj.with_context(**ctx).create(
                    [payment_vals])
                odoo_payment.action_post()

                # Reconcile linked invoices
                reconciled_invoices = []
                for line in payment.get('Line', []):
                    for linked in line.get('LinkedTxn', []):
                        if linked.get('TxnType') == 'Invoice':
                            qbo_inv_id = linked.get('TxnId')
                            invoice = self.env['account.move'].search([
                                ('qbooks_invoice', '=', qbo_inv_id),
                                ('move_type', '=', 'out_invoice')
                            ], limit=1)

                            if invoice:
                                if invoice.state == 'draft':
                                    if invoice.line_ids:
                                        invoice.action_post()

                                outstanding_line = odoo_payment.move_id.line_ids.filtered(
                                    lambda
                                        l: l.account_id.account_type == 'asset_receivable'
                                           and not l.reconciled
                                )
                                if outstanding_line:
                                    invoice.js_assign_outstanding_line(
                                        outstanding_line.id)
                                    reconciled_invoices.append(qbo_inv_id)

                # ✅ Log success per payment
                self._log_qbooks_operation(
                    operation_name=f"Customer Payment Import: {pay_number}",
                    op_type='import',
                    status='success',
                    message=(
                        f"Payment '{pay_number}' (QBO ID: {pay_id}) of {payment.get('TotalAmt')} "
                        f"imported and posted for customer '{customer.name}'"
                        f"{f', reconciled against invoice(s): {reconciled_invoices}' if reconciled_invoices else ', no invoices reconciled'}."
                    ),
                    record=odoo_payment,
                    payload=payment,
                )
                total += 1

            except Exception as e:
                failed_count += 1
                _logger.error(
                    f"Failed to import customer payment '{pay_number}' (QBO ID: {pay_id}): {e}")

                # ❌ Log failure per payment
                self._log_qbooks_operation(
                    operation_name=f"Customer Payment Import: {pay_number}",
                    op_type='import',
                    status='failed',
                    message=str(e),
                    payload=payment,
                )

        # 📊 Log batch summary
        self._log_qbooks_operation(
            operation_name="Customer Payment Import Batch",
            op_type='import',
            status='success' if not failed_count else 'failed',
            message=(
                f"Batch complete: {total} payment(s) imported successfully, "
                f"{failed_count} failed or skipped. "
                f"(start_position={start_position}, max_results={max_results})"
            ),
            payload={
                'start_position': start_position,
                'max_results': max_results,
                'created': total,
                'failed': failed_count,
            },
        )

        _logger.info(
            f"{total} customer payments imported (start_position: {start_position})")

    def action_import_credit_note(self):
        self.with_delay(priority=1)._run_import_credit_note_job()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Import Started',
                'message': 'Credit note import has been queued in the background.',
                'type': 'info',
                'sticky': False,
            }
        }

    def _run_import_credit_note_job(self):
        url = self.get_import_query()
        if not url:
            _logger.warning("No URL returned from import query.")
            return

        start_position = 1
        max_results = 100

        while True:
            query = f"SELECT * FROM CreditMemo STARTPOSITION {start_position} MAXRESULTS {max_results}"
            get_url = f"{url['url']}/query?minorversion={self.minor_version}&query={query}"

            try:
                response = requests.get(get_url, headers=url['headers'])
                if response.json().get('fault', {}).get('type') == 'AUTHENTICATION':
                    self.action_refresh_token()
                    response = requests.get(get_url, headers=url['headers'])
            except Exception as e:
                _logger.error(f"Error while fetching credit notes: {e}")
                break

            credit_notes = response.json().get('QueryResponse', {}).get('CreditMemo', [])
            if not credit_notes:
                break

            self.with_delay(priority=1)._batch_schedule_credit_note_import(
                credit_notes, total=0, max_results=max_results,
                start_position=start_position
            )
            start_position += max_results

    def _batch_schedule_credit_note_import(self, credit_notes, total, max_results, start_position):
        """ Batch credit note import"""
        size = 10
        credit_note_list = [credit_notes[i:i + size] for i in range(0, len(credit_notes), size)]

        for index, credit_note_chunk in enumerate(credit_note_list):
            delay_time = fields.Datetime.now() + timedelta(seconds=index * 10)
            self.with_delay(priority=1, eta=delay_time)._credit_note_import(
                credit_note_chunk, total, max_results, start_position
            )

    def _credit_note_import(self, credit_notes, total, max_results,
                            start_position):
        failed_count = 0

        for credit in credit_notes:
            credit_id = credit.get('Id')
            customer_ref = credit.get('CustomerRef', {}).get('value', 'Unknown')
            customer_name = credit.get('CustomerRef', {}).get('name', 'Unknown')

            try:
                exist = self.env['account.move'].search(
                    [('qbooks_credit', '=', credit_id)])
                if exist:
                    if len(exist) > 1:
                        exist[1:].unlink()
                    continue

                rate_info = self._apply_qbooks_exchange_rate(credit)
                currency_id = self.env['res.currency'].browse(
                    rate_info.get('currency_id')
                ) if rate_info.get('currency_id') else self.env[
                    'res.currency'].search(
                    [('name', '=', credit.get('CurrencyRef', {}).get('value'))],
                    limit=1
                )

                credit_date = datetime.strptime(credit.get('TxnDate'),
                                                '%Y-%m-%d')

                credit_vals = {
                    'qbooks_credit': credit_id,
                    'invoice_date': credit_date,
                    'currency_id': currency_id.id,
                    'invoice_line_ids': [],
                    'move_type': 'out_refund',
                }

                if credit.get('CustomerRef'):
                    customer_id = self.env['res.partner'].search([
                        ('qbooks_customer', '=', customer_ref)
                    ], limit=1).id
                    if customer_id:
                        credit_vals['partner_id'] = customer_id
                        # Resolve display name from Odoo record for log messages
                        customer_name = self.env['res.partner'].browse(
                            customer_id).name
                    else:
                        raise ValidationError(
                            f"Customer with QuickBooks ID {customer_ref} not found. Please import customers first."
                        )
                else:
                    continue  # skip if no customer

                for line in credit.get('Line'):
                    if line.get('SalesItemLineDetail'):
                        product_id = self.env['product.product'].search([
                            ('qbooks_product', '=',
                             line.get('SalesItemLineDetail').get('ItemRef').get(
                                 'value'))
                        ], limit=1)

                        if product_id:
                            line_dict = {
                                'product_id': product_id.id,
                                'name': product_id.name,
                                'quantity': line.get('SalesItemLineDetail').get(
                                    'Qty'),
                                'price_unit': line.get(
                                    'SalesItemLineDetail').get('UnitPrice'),
                                'qbooks_invoice_line': line.get('Id'),
                                'qbooks_invoice': credit_id,
                            }

                            tax_code_ref = line.get('SalesItemLineDetail').get(
                                'TaxCodeRef', {}).get('value')
                            if tax_code_ref == "TAX":
                                if credit.get('TxnTaxDetail') and \
                                        credit.get('TxnTaxDetail').get(
                                            'TxnTaxCodeRef'):
                                    tax_id = self.env['account.tax'].search([
                                        ('qbooks_tax', '=',
                                         credit.get('TxnTaxDetail')
                                         .get('TxnTaxCodeRef').get('value')),
                                        ('type_tax_use', '=', 'sale')
                                    ], limit=1)
                                    line_dict['tax_ids'] = [
                                        (6, 0, [tax_id.id])] if tax_id else [
                                        (6, 0, [])]
                                else:
                                    line_dict['tax_ids'] = [(6, 0, [])]
                            else:
                                line_dict['tax_ids'] = [(6, 0, [])]

                            line_dict = self._apply_line_tax_exemption(
                                line_dict, customer_id)
                            credit_vals['invoice_line_ids'].append(
                                (0, 0, line_dict))
                        else:
                            raise ValidationError(
                                'Product Not Found, Please import products first.')

                ctx = self._get_qbooks_currency_context(credit,
                                                        credit_date.date())
                created = self.env['account.move'].with_context(**ctx).create(
                    [credit_vals])

                # ✅ Log success per credit note
                self._log_qbooks_operation(
                    operation_name=f"Credit Note Import: {customer_name}",
                    op_type='import',
                    status='success',
                    message=(
                        f"Credit note (QBO ID: {credit_id}) imported successfully "
                        f"for customer '{customer_name}' with "
                        f"{len(credit_vals['invoice_line_ids'])} line(s)."
                    ),
                    record=created,
                    payload=credit,
                )
                total += 1

            except Exception as e:
                failed_count += 1
                _logger.error(
                    f"Failed to import credit note (QBO ID: {credit_id}) "
                    f"for customer '{customer_name}': {e}")

                # ❌ Log failure per credit note
                self._log_qbooks_operation(
                    operation_name=f"Credit Note Import: {customer_name}",
                    op_type='import',
                    status='failed',
                    message=str(e),
                    payload=credit,
                )
                # Re-raise ValidationErrors — missing customer/product must halt the batch
                if isinstance(e, ValidationError):
                    raise

        # 📊 Log batch summary
        self._log_qbooks_operation(
            operation_name="Credit Note Import Batch",
            op_type='import',
            status='success' if not failed_count else 'failed',
            message=(
                f"Batch complete: {total} credit note(s) imported successfully, "
                f"{failed_count} failed. "
                f"(start_position={start_position}, max_results={max_results})"
            ),
            payload={
                'start_position': start_position,
                'max_results': max_results,
                'created': total,
                'failed': failed_count,
            },
        )

        # Pagination logic (pre-existing bug: run/start_position not returned)
        if len(credit_notes) < max_results:
            run = False
        else:
            start_position += max_results

        if total != 0:
            _logger.info(f"{total} Credit Notes imported from QuickBooks.")
        else:
            _logger.info("No credit notes to import.")

    def action_import_refunds(self):
        self.with_delay(priority=1)._run_import_refunds_job()

    def _run_import_refunds_job(self):
        url = self.get_import_query()
        if not url:
            _logger.warning("No URL returned from import query.")
            return

        start_position = 1
        max_results = 100

        while True:
            query = f"SELECT * FROM RefundReceipt STARTPOSITION {start_position} MAXRESULTS {max_results}"
            get_url = f"{url['url']}/query?minorversion={self.minor_version}&query={query}"

            try:
                response = requests.get(get_url, headers=url['headers'])
                if response.json().get('fault', {}).get('type') == 'AUTHENTICATION':
                    self.action_refresh_token()
                    response = requests.get(get_url, headers=url['headers'])
            except Exception as e:
                _logger.error(f"Error while fetching credit notes: {e}")
                break

            refunds = response.json().get('QueryResponse', {}).get('RefundReceipt', [])
            if not refunds:
                break

            self.with_delay(priority=1)._batch_schedule_refunds_import(
                refunds, total=0, max_results=max_results,
                start_position=start_position
            )
            start_position += max_results

    def _batch_schedule_refunds_import(self, refunds, total, max_results, start_position):
        size = 10
        refunds_list = [refunds[i:i + size] for i in range(0, len(refunds), size)]

        for index, refunds_chunk in enumerate(refunds_list):
            delay_time = fields.Datetime.now() + timedelta(seconds=index * 10)
            self.with_delay(priority=1, eta=delay_time)._refunds_import(
                refunds_chunk, total, max_results, start_position
            )

    def _refunds_import(self, refunds, total, max_results, start_position):
        for refund in refunds:
            exist = self.env['account.move'].search([('qbooks_refund', '=', refund.get('Id'))])
            if exist:
                if len(exist) > 1:
                    exist[1:].unlink()
                continue

            rate_info = self._apply_qbooks_exchange_rate(refund)
            currency_id = self.env['res.currency'].browse(
                rate_info.get('currency_id')
            ) if rate_info.get('currency_id') else self.env['res.currency'].search(
                [('name', '=', refund.get('CurrencyRef', {}).get('value'))], limit=1
            )

            refund_date = datetime.strptime(refund.get('TxnDate'), '%Y-%m-%d')

            refund_vals = {
                'qbooks_refund': refund.get('Id'),
                'invoice_date': refund_date,
                'currency_id': currency_id.id,
                'invoice_line_ids': [],
                'move_type': 'out_refund',
            }

            if refund.get('CustomerRef'):
                customer_id = self.env['res.partner'].search([
                    ('qbooks_customer', '=', refund.get('CustomerRef').get('value'))
                ], limit=1).id
                if customer_id:
                    refund_vals['partner_id'] = customer_id
                else:
                    raise ValidationError(
                        f"Customer with QuickBooks ID {refund.get('CustomerRef').get('value')} not found. Please import customers first."
                    )
            else:
                continue  # skip if no customer

            for line in refund.get('Line'):
                if line.get('SalesItemLineDetail'):
                    product_id = self.env['product.product'].search([
                        ('qbooks_product', '=', line.get('SalesItemLineDetail').get('ItemRef').get('value'))
                    ], limit=1)

                    if product_id:
                        line_dict = {
                            'product_id': product_id.id,
                            'name': product_id.name,
                            'quantity': line.get('SalesItemLineDetail').get('Qty'),
                            'price_unit': line.get('SalesItemLineDetail').get('UnitPrice'),
                            'qbooks_invoice_line': line.get('Id'),
                            'qbooks_invoice': refund.get('Id')
                        }
                        tax_code_ref = line.get('SalesItemLineDetail').get('TaxCodeRef', {}).get('value')
                        if tax_code_ref == "TAX":
                            if refund.get('TxnTaxDetail') and refund.get('TxnTaxDetail').get('TxnTaxCodeRef'):
                                tax_id = self.env['account.tax'].search([
                                    ('qbooks_tax', '=', refund.get('TxnTaxDetail').get('TxnTaxCodeRef').get('value')),
                                    ('type_tax_use', '=', 'sale')], limit=1)
                                if tax_id:
                                    line_dict['tax_ids'] = [(6, 0, [tax_id.id])]
                                else:
                                    line_dict['tax_ids'] = [(6, 0, [])]
                            else:
                                line_dict['tax_ids'] = [(6, 0, [])]
                        else:
                            line_dict['tax_ids'] = [(6, 0, [])]

                        line_dict = self._apply_line_tax_exemption(line_dict, customer_id)

                        refund_vals['invoice_line_ids'].append((0, 0, line_dict))
                    else:
                        raise ValidationError(
                            'Product Not Found, Please import products first.')

            ctx = self._get_qbooks_currency_context(refund, refund_date.date())
            self.env['account.move'].with_context(**ctx).create([refund_vals])
            total += 1

        if len(refund) < max_results:
            run = False
        else:
            start_position += max_results

        if total != 0:
            _logger.info(f"{total} refund Notes imported from QuickBooks.")
        else:
            _logger.info("No refund notes to import.")

    def action_export_product_category(self):
        """Function to export product category"""
        url = self.get_import_query()
        total = 0
        failed_count = 0
        if url:
            req_url = f'{url["url"]}/item?minorversion={4}'
            headers = url.get('headers')
            headers['Content-Type'] = 'application/json'
            product_category_ids = self.env['product.category'].search([
                ('qbooks_product_category', '=', False)
            ])
            for product_category in product_category_ids:
                try:
                    self.create_product_category_data(product_category, req_url,
                                                      headers)
                    total += 1
                except Exception as e:
                    failed_count += 1
                    _logger.error(
                        f"Failed to export category {product_category.name}: {str(e)}"
                    )
                    self._log_qbooks_operation(
                        'Product Category Export', 'export', 'failed',
                        f"Error exporting category '{product_category.name}': {str(e)}",
                        record=product_category
                    )

            # Log Batch Summary
            if total > 0 or failed_count > 0:
                self._log_qbooks_operation(
                    'Product Category Export Summary', 'export',
                    'success' if failed_count == 0 else 'failed',
                    f"Export process finished. Success: {total}, Failed: {failed_count}."
                )
        if total != 0:
            message = f'{total} product categories exported'
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Export Success',
                    'message': message,
                    'type': 'success',
                    'sticky': False,
                }
            }
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Export Notice',
                    'message': 'No new product categories were exported.',
                    'type': 'warning',
                    'sticky': False,
                }
            }

    def create_product_category_data(self, product_category, url, headers):
        """Function to create product category data"""
        req_body = {
            "Type": "Category",
            "Name": product_category.name,
        }
        if product_category.parent_id:
            req_body['SubItem'] = True
            if product_category.parent_id.qbooks_product_category:
                req_body['ParentRef'] = {
                    "value": product_category.parent_id.qbooks_product_category
                }
            else:
                self.create_product_category_data(product_category.parent_id,
                                                  url, headers)
                req_body['ParentRef'] = {
                    "value": product_category.parent_id.qbooks_product_category
                }
        else:
            req_body['SubItem'] = False
        response = requests.post(url, data=json.dumps(req_body),
                                 headers=headers)
        res_data = response.json()

        if response.status_code == 200 and res_data.get('Item'):
            res = res_data.get('Item')
            product_category.write({
                'qbooks_product_category': res.get('Id'),
                'qbooks_sync_token': res.get('SyncToken')
            })
            # ✅ LOG SUCCESS PER CATEGORY
            self._log_qbooks_operation(
                'Product Category Export', 'export', 'success',
                f"Successfully exported category: {product_category.name}",
                record=product_category, payload=req_body, response=res_data
            )
            # Commit to ensure parent ID is available for children in the same loop
            self.env.cr.commit()
        elif res_data.get('fault') or res_data.get('Fault'):
            fault = res_data.get('fault') or res_data.get('Fault')
            error = fault.get('error') or fault.get('Error')
            error_msg = error[0].get('Message') if error else "Unknown Error"

            # ✅ LOG FAILURE PER CATEGORY
            self._log_qbooks_operation(
                'Product Category Export', 'export', 'failed',
                f"QuickBooks rejected category '{product_category.name}': {error_msg}",
                record=product_category, payload=req_body, response=res_data
            )

            if error[0].get('code') == '3200':
                raise UserError(_("Token expired. Kindly refresh token"))
            raise UserError(_("QuickBooks Error: %s") % error_msg)

    def action_export_account(self):
        """Chunks accounts and schedules batch export jobs"""
        url_data = self.get_import_query()
        if not url_data:
            raise UserError(_("QuickBooks configuration not found."))

        # 1. Search for accounts not yet in QBO
        account_ids = self.env['account.account'].search([
            ('qbooks_account', '=', False)
        ]).ids  # Get IDs to keep the queue job payload light
        if not account_ids:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': 'No accounts to export',
                    'type': 'warning'
                }
            }

        # 2. Split into batches of 10
        batch_size = 10
        batches = [account_ids[i:i + batch_size] for i in
                   range(0, len(account_ids), batch_size)]

        for index, batch_ids in enumerate(batches):
            # 3. Add a staggered delay (10 seconds apart) to prevent API rate limiting
            delay_time = fields.Datetime.now() + timedelta(seconds=index * 10)

            self.with_delay(priority=2, eta=delay_time)._run_batch_export_job(
                batch_ids, url_data)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Batch Export Started',
                'message': f'Scheduled {len(batches)} batch jobs for {len(account_ids)} accounts.',
                'type': 'success',
            }
        }

    def _run_batch_export_job(self, account_ids, url_data):
        """Processes a small batch of accounts inside a single queue job"""
        accounts = self.env['account.account'].browse(account_ids)

        # Mapping table (Internal to job to ensure it's always available)
        type_mapping = {
            'asset_receivable': ('Accounts Receivable', 'AccountsReceivable'),
            'liability_payable': ('Accounts Payable', 'AccountsPayable'),
            'asset_cash': ('Bank', 'CashOnHand'),
            'liability_credit_card': ('Credit Card', 'CreditCard'),
            'asset_current': ('Other Current Asset', 'Inventory'),
            'asset_fixed': ('Fixed Asset', 'FurnitureAndFixtures'),
            'asset_non_current': ('Other Asset', 'Licenses'),
            'liability_non_current': ('Long Term Liability', 'NotesPayable'),
            'liability_current': ('Other Current Liability',
                                  'OtherCurrentLiabilities'),
            'equity': ('Equity', 'PartnersEquity'),
            'expense_direct_cost': ('Cost of Goods Sold',
                                    'SuppliesMaterialsCogs'),
            'expense': ('Other Expense', 'Depreciation'),
            'income': ('Income', 'SalesOfProductIncome'),
            'income_other': ('Other Income', 'OtherInvestmentIncome'),
            'equity_unaffected': ('Equity', 'PaidInCapitalOrSurplus'),
            'asset_prepayments': ('Other Current Asset', 'PrepaidExpenses'),
        }

        success_count = 0
        failed_count = 0
        for account in accounts:
            if account.qbooks_account:
                continue

            types = type_mapping.get(account.account_type)
            if not types:
                msg = f"Skipping Account {account.name}: Type {account.account_type} not mapped."
                _logger.warning(msg)
                self._log_qbooks_operation('Account Export', 'export', 'failed',
                                           msg, record=account)
                failed_count += 1
                continue

            try:
                # Use a savepoint for each account in the batch
                with self.env.cr.savepoint():
                    self._export_single_account_logic(account, types[0],
                                                      types[1], url_data)
                    success_count += 1
            except Exception as e:
                failed_count += 1
                # Log the error but allow the loop to continue to the next account in the batch
                _logger.error("Batch Export Error for %s: %s", account.name,
                              str(e))
                continue
        # Batch Summary Log
        self._log_qbooks_operation(
            'Account Batch Export Summary', 'export',
            'success' if failed_count == 0 else 'failed',
            f"Batch completed. Success: {success_count}, Failed: {failed_count}. IDs: {account_ids}"
        )

    def _export_single_account_logic(self, account, account_type,
                                     account_sub_type, url_data):
        req_url = f'{url_data["url"]}/account'
        headers = url_data.get('headers')
        headers['Content-Type'] = 'application/json'

        req_body = {
            "Name": account.name,
            "AccountType": account_type,
            "AccountSubType": account_sub_type
        }

        try:
            response = requests.post(req_url, data=json.dumps(req_body),
                                     headers=headers)

            # Handle Refresh Token
            if response.status_code == 401:
                self.action_refresh_token()
                url_data = self.get_import_query()  # Get fresh headers
                response = requests.post(req_url, data=json.dumps(req_body),
                                         headers=url_data.get('headers'))

            res_data = response.json()
        except Exception as e:
            self._log_qbooks_operation(
                'Account Export', 'export', 'failed',
                f"Request failed: {str(e)}", record=account, payload=req_body
            )
        account_data = res_data.get('Account')
        fault = res_data.get('Fault') or res_data.get('fault')

        if account_data:
            account.write({
                'qbooks_account': account_data.get('Id'),
                'qbooks_sync_token': account_data.get('SyncToken')
            })
            # ✅ LOG SUCCESS
            self._log_qbooks_operation(
                'Account Export', 'export', 'success',
                f"Account '{account.name}' exported successfully.",
                record=account, payload=req_body, response=res_data
            )
        elif fault:
            err = (fault.get('Error') or fault.get('error') or [{}])[0]
            msg = err.get('Message', 'Unknown QBO Error')

            # ✅ LOG FAILURE
            self._log_qbooks_operation(
                'Account Export', 'export', 'failed',
                f"QuickBooks rejected account '{account.name}': {msg}",
                record=account, payload=req_body, response=res_data
            )

    def action_export_products(self):
        """Chunks products and schedules batch export jobs"""
        url_data = self.get_import_query()
        if not url_data:
            raise UserError(_("QuickBooks configuration not found."))

        # Find products needing export (Real Time valuation and no QBO ID)
        product_ids = self.env['product.product'].search([
            ('qbooks_product', '=', False)
        ]).ids

        if not product_ids:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': 'No products to export or products already exported.',
                    'type': 'warning'
                }
            }

        # Split into batches of 10
        batch_size = 10
        batches = [product_ids[i:i + batch_size] for i in
                   range(0, len(product_ids), batch_size)]

        for index, batch_ids in enumerate(batches):
            # Staggered ETA to prevent QBO rate limiting (every 15 seconds)
            delay_time = fields.Datetime.now() + timedelta(seconds=index * 15)

            self.with_delay(priority=5, eta=delay_time)._run_batch_export_product_job(
                batch_ids, url_data)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Product Export Started',
                'message': f'Scheduled {len(batches)} batch jobs for {len(product_ids)} products.',
                'type': 'success',
            }
        }

    def _run_batch_export_product_job(self, product_ids, url_data):
        """Processes product batches in the background"""
        products = self.env['product.product'].browse(product_ids)
        success_count = 0
        failed_count = 0

        for product in products:
            if product.qbooks_product:
                continue

            try:
                with self.env.cr.savepoint():
                    self._export_single_product_logic(product, url_data)
                    success_count += 1
            except Exception as e:
                failed_count += 1
                _logger.error("Product Export: Error for %s: %s", product.name,
                              str(e))
                continue
        # Batch Summary Log
        self._log_qbooks_operation(
            'Product Batch Export Summary', 'export',
            'success' if failed_count == 0 else 'failed',
            f"Batch completed. Success: {success_count}, Failed: {failed_count}. Batch IDs: {product_ids}"
        )

    def _export_single_product_logic(self, product, url_data):
        """ Export product to quick book."""
        req_url = f'{url_data["url"]}/item?minorversion=4'
        headers = url_data.get('headers')
        headers['Content-Type'] = 'application/json'

        product_type_map = {
            'service': 'Service',
            'consu': 'NonInventory',
            'product': 'Inventory',
        }

        # Prepare body
        req_body = {
            "Name": f"{product.name} [CODE-{product.id}]",
            "Description": product.description_sale or product.name,
            "Active": True,
            "UnitPrice": product.list_price,
            "PurchaseCost": product.standard_price,
            "Type": product_type_map.get(product.type, 'NonInventory'),
            "PurchaseDesc": product.description_sale or product.name,
            "IncomeAccountRef": {
                "value": product.categ_id.property_account_income_categ_id.qbooks_account or '',
                "name": "Product Sales"
            },
            "AssetAccountRef": {
                "value": product.categ_id.property_stock_valuation_account_id.qbooks_account or '',
                "name": product.categ_id.property_stock_valuation_account_id.name or ''
            },
            "ExpenseAccountRef": {
                "value": product.categ_id.property_account_expense_categ_id.qbooks_account or '',
                "name": "Expenses"
            },
            "InvStartDate": "2022-01-01"
        }

        # Quantity handling for Inventory types
        if product_type_map.get(product.type) == 'Inventory':
            # Sum quantity from all quants for this product
            quants = self.env['stock.quant'].search(
                [('product_id', '=', product.id)])
            total_qty = sum(quants.mapped('quantity'))
            req_body.update({"TrackQtyOnHand": True, "QtyOnHand": total_qty})
        else:
            req_body.update({"TrackQtyOnHand": False})

        try:
            response = requests.post(req_url, data=json.dumps(req_body),
                                     headers=headers)
            # Token Refresh Logic
            if response.status_code == 401:
                self.action_refresh_token()
                url_data = self.get_import_query()
                response = requests.post(req_url, data=json.dumps(req_body),
                                         headers=url_data.get('headers'),
                                         timeout=30)

            res_json = response.json()
        except Exception as e:
            self._log_qbooks_operation('Product Export', 'export', 'failed',
                                       f"Request Error: {str(e)}",
                                       record=product, payload=req_body)
            raise e

        item_data = res_json.get('Item')
        fault = res_json.get('Fault') or res_json.get('fault')

        if item_data:
            product.write({
                'qbooks_product': item_data.get('Id'),
                'qbooks_sync_token': item_data.get('SyncToken')
            })
            self._log_qbooks_operation(
                'Product Export', 'export', 'success',
                f"Product '{product.name}' synced successfully.",
                record=product, payload=req_body, response=res_json
            )
        elif fault:
            error = (fault.get('Error') or fault.get('error') or [{}])[0]
            err_msg = error.get('Message', 'Unknown QBO Error')
            self._log_qbooks_operation(
                'Product Export', 'export', 'failed',
                f"QBO Rejected Product: {err_msg}",
                record=product, payload=req_body, response=res_json
            )
            raise Exception(f"QBO Error: {err_msg}")

    def action_export_employees(self):
        """Entry point to trigger the queued employee export."""
        self.with_delay(priority=1)._run_export_employees_job()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Export Started',
                'message': 'Employee export has been queued in the background.',
                'type': 'info',
                'sticky': False,
            }
        }

    def _run_export_employees_job(self):
        """Fetches all employees to export and schedules batched jobs."""
        url_data = self.get_import_query()
        if not url_data:
            _logger.warning("No URL returned from export query for employees.")
            return

        employees = self.env['hr.employee'].search(
            [('qbooks_employee', '=', False)])

        if not employees:
            _logger.info("No employees to export to QuickBooks.")
            return

        # Split into chunks of 10 and schedule each as a separate job
        batch_size = 10
        employee_chunks = [
            employees[i:i + batch_size].ids
            for i in range(0, len(employees), batch_size)
        ]

        for index, chunk_ids in enumerate(employee_chunks):
            # Stagger execution by 10 seconds per chunk to prevent DB locks
            delay_time = fields.Datetime.now() + timedelta(seconds=index * 10)
            self.with_delay(priority=1, eta=delay_time)._export_employee_batch(
                chunk_ids, url_data
            )

        _logger.info(
            "Scheduled export of %d employees across %d batches.",
            len(employees), len(employee_chunks)
        )

    def _export_employee_batch(self, employee_ids, url_data):
        """Worker job: exports a single batch of employees to QuickBooks."""
        req_url = f'{url_data["url"]}/employee?minorversion=40'
        headers = {**url_data.get('headers', {}),
                   'Content-Type': 'application/json'}

        employees = self.env['hr.employee'].browse(employee_ids)
        total = 0
        failed_count = 0

        for employee in employees:
            # Safety check in case another job already processed this record
            if employee.qbooks_employee:
                continue

            try:
                self.create_employee_data(employee, req_url, headers)
                total += 1
            except Exception as e:
                failed_count += 1
                _logger.error("Employee Export Error for %s: %s", employee.name,
                              str(e))
                continue
        # Log Batch Summary
        self._log_qbooks_operation(
            'Employee Batch Export Summary', 'export',
            'success' if failed_count == 0 else 'failed',
            f"Batch completed. Success: {total}, Failed: {failed_count}."
        )

    def create_employee_data(self, employee, url, headers):
        """Function to create employee data"""
        req_body = {
            "DisplayName": employee.name,
            "GivenName": employee.name,
            "FamilyName": employee.family_name,
            "Active": True,
        }
        if employee.work_phone:
            req_body.update({"PrimaryPhone": {
                "FreeFormNumber": employee.work_phone
            }})
        if employee.mobile_phone:
            req_body.update({"Mobile": {
                "FreeFormNumber": employee.mobile_phone
            }})
        if employee.work_email:
            req_body.update({"PrimaryEmailAddr": {
                "Address": employee.work_email
            }})

        if employee.sex:
            selection = employee._fields['sex'].selection
            if callable(selection):
                selection = selection(employee)
            gender_value = dict(selection).get(employee.sex)
            if gender_value:
                req_body.update({"Gender": gender_value})

        if employee.birthday:
            req_body.update(
                {"BirthDate": employee.birthday.strftime("%m/%d/%Y")})
        if employee.private_street:
            req_body.update({"PrimaryAddr": {
                "CountrySubDivisionCode": employee.private_state_id.name if employee.private_state_id
                else '',
                "City": employee.private_city if employee.private_city else '',
                "PostalCode": employee.private_zip if employee.private_zip else '',
                "Line1": employee.private_street if employee.private_street else '',
                "Line2": employee.private_street2 if employee.private_street2 else '',
                "Country": employee.private_country_id.name if employee.private_country_id else '',
            }})
        try:
            response = requests.post(url, data=json.dumps(req_body),
                                     headers=headers)
            res_data = response.json()
        except Exception as e:
            self._log_qbooks_operation('Employee Export', 'export', 'failed',
                                       f"Request Failed: {str(e)}",
                                       record=employee, payload=req_body)
            raise e

        if res_data.get('Employee'):
            res = res_data.get('Employee')
            employee.write({
                'qbooks_employee': res.get('Id'),
                'qbooks_sync_token': res.get('SyncToken')
            })
            self._log_qbooks_operation(
                'Employee Export', 'export', 'success',
                f"Successfully exported employee: {employee.name}",
                record=employee, payload=req_body, response=res_data
            )
        else:
            # Handle Faults
            fault = res_data.get('Fault') or res_data.get('fault')
            errors = fault.get('Error') or fault.get('error') or [{}]
            error_msg = errors[0].get('Message', 'Unknown Error')
            error_code = str(errors[0].get('code', ''))

            self._log_qbooks_operation(
                'Employee Export', 'export', 'failed',
                f"QuickBooks Error [{error_code}]: {error_msg}",
                record=employee, payload=req_body, response=res_data
            )

            if error_code == '6240':
                raise UserError(
                    _("Duplicate name for employee %s in QBO.") % employee.name)
            elif error_code == '3200':
                raise UserError(_("Token expired. Please refresh."))
            raise UserError(_("QBO Error: %s") % error_msg)

    def action_export_customer(self):
        """Entry point to trigger the queued customer export."""
        self.with_delay(priority=1)._run_export_customers_job()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Export Started',
                'message': 'Customer export has been queued in the background.',
                'type': 'info',
                'sticky': False,
            }
        }

    def _run_export_customers_job(self):
        """Collects all exportable customers and schedules batched jobs."""
        url_data = self.get_import_query()
        if not url_data:
            _logger.warning("No URL returned from export query for customers.")
            return

        # Collect partner IDs from sale orders
        sale_partner_ids = self.env['sale.order'].search([]).mapped(
            'partner_id.id')

        # Collect partner IDs from customer invoices
        invoice_partner_ids = self.env['account.move'].search(
            [('move_type', '=', 'out_invoice')]
        ).mapped('partner_id.id')

        # Merge, deduplicate, and filter only those not yet in QuickBooks
        all_partner_ids = list(set(sale_partner_ids + invoice_partner_ids))
        customers = self.env['res.partner'].search([
            ('id', 'in', all_partner_ids),
            ('qbooks_customer', '=', False),
        ])

        if not customers:
            _logger.info("No customers to export to QuickBooks.")
            return

        # Split into chunks of 10 and schedule each as a separate job
        batch_size = 10
        customer_chunks = [
            customers[i:i + batch_size].ids
            for i in range(0, len(customers), batch_size)
        ]

        for index, chunk_ids in enumerate(customer_chunks):
            delay_time = fields.Datetime.now() + timedelta(seconds=index * 10)
            self.with_delay(priority=1, eta=delay_time)._export_customer_batch(
                chunk_ids, url_data
            )

        _logger.info(
            "Scheduled export of %d customers across %d batches.",
            len(customers), len(customer_chunks)
        )

    def _export_customer_batch(self, customer_ids, url_data):
        """Worker job: exports a single batch of customers to QuickBooks."""
        req_url = f'{url_data["url"]}/customer?minorversion=40'
        headers = {**url_data.get('headers', {}),
                   'Content-Type': 'application/json'}

        customers = self.env['res.partner'].browse(customer_ids)
        total = 0
        failed_count = 0

        for customer in customers:
            if customer.qbooks_customer:
                continue
            try:
                self.create_customer_data(customer, req_url, headers)
                total += 1
            except Exception as e:
                failed_count += 1
                _logger.error("Customer Export Error for %s: %s", customer.name,
                              str(e))
                continue
        # Log Batch Summary
        self._log_qbooks_operation(
            'Customer Batch Export Summary', 'export',
            'success' if failed_count == 0 else 'failed',
            f"Batch completed. Success: {total}, Failed: {failed_count}."
        )

    def create_customer_data(self, customer, url, headers):
        """Builds payload and POSTs a single customer to QuickBooks."""
        req_body = {
            "DisplayName": customer.name,
            "Notes": customer.comment or "",
            "BillAddr": {
                "CountrySubDivisionCode": customer.state_id.name or "",
                "City": customer.city or "",
                "PostalCode": customer.zip or "",
                "Line1": customer.street or "",
                "Line2": customer.street2 or "",
                "Country": customer.country_id.name or "",
            },
        }

        # Only include phone fields if they have values
        if customer.phone:
            req_body["PrimaryPhone"] = {"FreeFormNumber": customer.phone}
        if customer.phone_mobile_search:
            req_body["Mobile"] = {"FreeFormNumber": customer.phone_mobile_search}
        if customer.email:
            req_body["PrimaryEmailAddr"] = {"Address": customer.email}
        if customer.parent_id:
            req_body["CompanyName"] = customer.parent_id.name

        if customer.website and isinstance(customer.website, str):
            clean_url = customer.website.strip().lower()
            if clean_url not in ("false", "none", "null", ""):
                if not clean_url.startswith(("http://", "https://")):
                    clean_url = "https://" + clean_url
                req_body["WebAddr"] = {"URI": clean_url}

        try:
            response = requests.post(url, json=req_body, headers=headers,
                                     timeout=30)
            data = response.json()
        except Exception as e:
            self._log_qbooks_operation('Customer Export', 'export', 'failed',
                                       f"Connection Error: {str(e)}",
                                       record=customer, payload=req_body)
            raise e

        if response.status_code == 401:
            self._log_qbooks_operation('Customer Export', 'export', 'failed',
                                       "401: Token Expired", record=customer)
            raise UserError(_("Token expired. Kindly refresh token."))

        customer_data = data.get("Customer")
        if customer_data:
            customer.write({
                "qbooks_customer": customer_data.get("Id"),
                "qbooks_sync_token": customer_data.get("SyncToken"),
            })
            self._log_qbooks_operation(
                'Customer Export', 'export', 'success',
                f"Successfully exported customer: {customer.name}",
                record=customer, payload=req_body, response=data
            )
            return

        fault = data.get("Fault") or data.get("fault")
        if fault:
            error_list = fault.get("Error") or fault.get("error") or []
            if error_list:
                error = error_list[0]
                code = str(error.get("code", ""))
                message = error.get("Detail") or error.get(
                    "Message") or error.get("detail")

                # Log the specific fault from QuickBooks
                self._log_qbooks_operation(
                    'Customer Export', 'export', 'failed',
                    f"QuickBooks Fault [{code}]: {message}",
                    record=customer, payload=req_body, response=data
                )

                # ✅ DUPLICATE NAME
                if code == "6240":
                    _logger.warning(
                        "Duplicate name for customer %s. Renaming and retrying.",
                        customer.name
                    )
                    customer.write({"name": f"{customer.name} - Odoo"})
                    # Retry once with the new name — no further recursion
                    return self.create_customer_data(customer, url, headers)

                # ✅ TOKEN EXPIRED
                if code == "3200":
                    raise UserError(_("Token expired. Kindly refresh token."))

                raise UserError(_("QuickBooks Error: %s") % message)

        # ✅ FALLBACK
        self._log_qbooks_operation('Customer Export', 'export',
                                   'failed',
                                   "Unexpected Response Format",
                                   record=customer, response=data)
        raise UserError(
            _("Unexpected QuickBooks response while exporting customer '%s'.") % customer.name)

    def action_export_vendor(self):
        """Entry point to trigger the queued vendor export."""
        self.with_delay(priority=1)._run_export_vendor_job()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Export Started',
                'message': 'Vendor export has been queued in the background.',
                'type': 'info',
                'sticky': False,
            }
        }

    def _run_export_vendor_job(self):
        """Collects all unsynced vendors from purchase orders and schedules batched jobs."""
        url_data = self.get_import_query()
        if not url_data:
            _logger.warning("No URL returned from export query for vendors.")
            return

        partner_ids = self.env['purchase.order'].search([]).mapped(
            'partner_id.id')

        vendors = self.env['res.partner'].search([
            ('id', 'in', partner_ids),
            ('qbooks_vendor', '=', False),
        ])

        if not vendors:
            _logger.info("No vendors to export to QuickBooks.")
            return

        batch_size = 10
        chunks = [
            vendors[i:i + batch_size].ids
            for i in range(0, len(vendors), batch_size)
        ]

        for index, chunk_ids in enumerate(chunks):
            delay_time = fields.Datetime.now() + timedelta(seconds=index * 10)
            self.with_delay(priority=1, eta=delay_time)._export_vendor_batch(
                chunk_ids, url_data
            )

        _logger.info(
            "Scheduled export of %d vendors across %d batches.",
            len(vendors), len(chunks)
        )

    def _export_vendor_batch(self, vendor_ids, url_data):
        """Worker job: exports a single batch of vendors to QuickBooks."""
        req_url = f'{url_data["url"]}/vendor?minorversion=63'
        headers = {
            **url_data.get('headers', {}),
            'Content-Type': 'application/json',
        }

        vendors = self.env['res.partner'].browse(vendor_ids)
        total = 0
        failed_count = 0

        for vendor in vendors:
            if vendor.qbooks_vendor:
                continue
            try:
                self.create_vendor_data(vendor, req_url, headers)
                total += 1
            except Exception as e:
                failed_count += 1
                _logger.error("Vendor Export Error for %s: %s", vendor.name,
                              str(e))
                # Individual error log is handled inside create_vendor_data
                continue
        # Log Batch Summary
        self._log_qbooks_operation(
            'Vendor Batch Export Summary', 'export',
            'success' if failed_count == 0 else 'failed',
            f"Batch completed. Success: {total}, Failed: {failed_count}."
        )

    def create_vendor_data(self, vendor, url, headers):
        """Builds payload and POSTs a single vendor to QuickBooks."""

        req_body = {
            "DisplayName": vendor.name,
            "Notes": vendor.comment or "",
            "TaxIdentifier": vendor.vat or "",
            "BillAddr": {
                "Line1": vendor.street or "",
                "City": vendor.city or "",
                "PostalCode": vendor.zip or "",
                "CountrySubDivisionCode": vendor.state_id.name or "",
                "Country": vendor.country_id.name or "",
            },
        }

        if vendor.phone:
            req_body["PrimaryPhone"] = {"FreeFormNumber": vendor.phone}
        if vendor.phone_mobile_search:
            req_body["Mobile"] = {"FreeFormNumber": vendor.phone_mobile_search}
        if vendor.email:
            req_body["PrimaryEmailAddr"] = {"Address": vendor.email}
        if vendor.parent_id:
            req_body["CompanyName"] = vendor.parent_id.name

        if vendor.website and isinstance(vendor.website, str):
            clean_url = vendor.website.strip().lower()
            if clean_url not in ("false", "none", "null", ""):
                if not clean_url.startswith(("http://", "https://")):
                    clean_url = "https://" + clean_url
                req_body["WebAddr"] = {"URI": clean_url}

        try:
            response = requests.post(url, json=req_body, headers=headers,
                                     timeout=30)
            data = response.json()
        except Exception as e:
            self._log_qbooks_operation(
                'Vendor Export', 'export', 'failed',
                f"Connection Error: {str(e)}", record=vendor, payload=req_body
            )
            raise e
        if response.status_code == 401:
            self._log_qbooks_operation('Vendor Export', 'export', 'failed',
                                       "401: Token Expired", record=vendor)
            raise UserError(_("Token expired. Kindly refresh token."))

        vendor_data = data.get("Vendor")
        if vendor_data:
            vendor.write({
                "qbooks_vendor": vendor_data.get("Id"),
                "qbooks_sync_token": vendor_data.get("SyncToken"),
            })
            self._log_qbooks_operation(
                'Vendor Export', 'export', 'success',
                f"Successfully exported vendor: {vendor.name}",
                record=vendor, payload=req_body, response=data
            )
            return

        fault = data.get("Fault") or data.get("fault")
        if fault:
            error_list = fault.get("Error") or fault.get("error") or []
            if error_list:
                error = error_list[0]
                code = str(error.get("code", ""))
                message = (
                        error.get("Detail")
                        or error.get("detail")
                        or error.get("Message")
                )

                # Log the specific fault
                self._log_qbooks_operation(
                    'Vendor Export', 'export', 'failed',
                    f"QuickBooks Fault [{code}]: {message}",
                    record=vendor, payload=req_body, response=data
                )
                # DUPLICATE NAME HANDLING
                if code == "6240":
                    _logger.warning(
                        "Duplicate vendor name for %s. Renaming and retrying.",
                        vendor.name
                    )
                    vendor.write({"name": f"{vendor.name} - Odoo"})
                    # Single retry — if the renamed version also duplicates, raise
                    return self.create_vendor_data(vendor, url, headers)

                if code == "3200":
                    raise UserError(_("Token expired. Kindly refresh token."))

                raise UserError(_("QuickBooks Vendor Error: %s") % message)

        self._log_qbooks_operation('Vendor Export', 'export', 'failed',
                                   "Unexpected Response Format", record=vendor,
                                   response=data)
        raise UserError(
            _("Unexpected QuickBooks response while exporting vendor '%s'.")
            % vendor.name
        )

    def action_export_agency(self):
        """Function to export agency"""
        url = self.get_import_query()
        total = 0
        failed_count = 0
        if url:
            req_url = f'{url["url"]}/taxagency?minorversion=63'
            headers = url.get('headers')
            headers['Content-Type'] = 'application/json'
            agency_ids = self.env['tax.agency'].search([
                ('qbooks_agency', '=', False)
            ])
            for agency in agency_ids:
                try:
                    self.create_agency_data(agency, req_url, headers)
                    total += 1
                except Exception as e:
                    failed_count += 1
                    _logger.error(
                        f"Failed to export tax agency {agency.tax_agency}: {str(e)}"
                    )
                    continue
            # Log Batch Summary
            if total > 0 or failed_count > 0:
                self._log_qbooks_operation(
                    'Tax Agency Export Summary', 'export',
                    'success' if failed_count == 0 else 'failed',
                    f"Tax Agency export finished. Success: {total}, Failed: {failed_count}."
                )
        if total != 0:
            message = f'{total} tax agencies exported successfully'
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': message,
                    'type': 'success',
                    'sticky': False,
                }
            }
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': 'No new tax agencies to export.',
                    'type': 'danger',
                    'sticky': False,
                }
            }

    def create_agency_data(self, agency, url, headers):
        """Function to create tax agency data"""
        req_body = {
            "DisplayName": agency.tax_agency,
        }
        try:
            response = requests.post(url, data=json.dumps(req_body),
                                     headers=headers)
            res_data = response.json()
        except Exception as e:
            self._log_qbooks_operation(
                'Tax Agency Export', 'export', 'failed',
                f"Connection error: {str(e)}", record=agency, payload=req_body
            )
            raise e
        # Success Case
        if res_data.get('TaxAgency'):
            res = res_data.get('TaxAgency')
            if 'Id' in res:
                agency.write({
                    'qbooks_agency': res.get('Id'),
                    'qbooks_sync_token': res.get('SyncToken')
                })

                self._log_qbooks_operation(
                    'Tax Agency Export', 'export', 'success',
                    f"Successfully exported tax agency: {agency.tax_agency}",
                    record=agency, payload=req_body, response=res_data
                )
                self.env.cr.commit()
            elif res_data.get('Fault') or res_data.get('fault'):
                fault = res_data.get('Fault') or res_data.get('fault')
                errors = fault.get('Error') or fault.get('error') or [{}]
                error_msg = errors[0].get('Message', 'Unknown QuickBooks Error')
                error_code = str(errors[0].get('code', ''))

                self._log_qbooks_operation(
                    'Tax Agency Export', 'export', 'failed',
                    f"QuickBooks Error [{error_code}]: {error_msg}",
                    record=agency, payload=req_body, response=res_data
                )
                if error_code == '6240':
                    raise UserError(
                        _("Duplicate name error for tax agency '%s' in QuickBooks.") % agency.tax_agency)
                elif error_code == '3200':
                    raise UserError(_("Token expired. Kindly refresh token."))
                else:
                    raise UserError(_("QuickBooks Error: %s") % error_msg)

    def action_export_tax_service(self):
        """Function to export tax service"""
        url = self.get_import_query()
        total = 0
        failed_count = 0
        if url:
            req_url = f'{url["url"]}/taxservice/taxcode?minorversion=63'
            headers = url.get('headers')
            headers['Content-Type'] = 'application/json'

            tax_ids = self.env['account.tax'].search([
                ('qbooks_tax', '=', False),
                ('qbooks_tax_rate', '=', False)
            ])
            agency = self.env['tax.agency'].search([])
            for tax in tax_ids:
                try:
                    if tax.amount_type != 'group':
                        self.create_tax_service_data(tax, agency, req_url, headers)
                        total += 1
                    else:
                        self.create_tax_group_data(tax, agency, req_url, headers)
                        total += 1
                except Exception as e:
                    failed_count += 1
                    _logger.error(f"Tax Export Failed for {tax.name}: {str(e)}")
                    continue
            # Batch Summary Log
            if total > 0 or failed_count > 0:
                self._log_qbooks_operation(
                    'Tax Service Export Summary', 'export',
                    'success' if failed_count == 0 else 'failed',
                    f"Tax sync finished. Success: {total}, Failed: {failed_count}."
                )
        if total != 0:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': f'{total} Tax records exported',
                    'type': 'success',
                    'sticky': False,
                }
            }
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': 'No new Tax records to export',
                'type': 'danger',
                'sticky': False,
            }
        }

    def create_tax_group_data(self, tax, agency, url, headers):
        """Function to create tax group data"""
        req_body = {
            "TaxRateDetails": [],
            "TaxCode": tax.name
        }
        for rec in tax.children_tax_ids:
            if not rec.qbooks_tax_rate:
                self.create_tax_service_data(rec, agency, url, headers)
            req_body['TaxRateDetails'].append({
                "RateValue": rec.amount,
                "TaxRateId": rec.qbooks_tax_rate,
                "TaxRateName": rec.name
            })
        try:
            response = requests.post(url, data=json.dumps(req_body),
                                     headers=headers)
            res_data = response.json()

            if res_data.get('TaxCodeId'):
                tax.write({'qbooks_tax': res_data.get('TaxCodeId')})
                self._log_qbooks_operation(
                    'Tax Group Export', 'export', 'success',
                    f"Tax Group '{tax.name}' synced.",
                    record=tax, payload=req_body, response=res_data
                )
                self.env.cr.commit()
            else:
                self._handle_tax_error(tax, req_body, res_data, "Group")

        except Exception as e:
            self._log_qbooks_operation('Tax Group Export', 'export',
                                       'failed', str(e), record=tax,
                                       payload=req_body)
            raise e

    def create_tax_service_data(self, tax, agency, url, headers):
        """Function to create tax service data"""
        if not tax.tax_agency_id:
            msg = f"Tax '{tax.name}' has no Tax Agency assigned."
            self._log_qbooks_operation('Tax Rate Export', 'export', 'failed',
                                       msg, record=tax)
            raise UserError(msg)

        req_body = {
            "TaxRateDetails": [
                {
                    "RateValue": tax.amount,
                    "TaxAgencyId": tax.tax_agency_id.qbooks_agency,
                    "TaxRateName": tax.name,
                    "TaxApplicableOn": "Sales" if tax.type_tax_use == 'sale' else "Purchase" if tax.type_tax_use == 'purchase' else "Other"
                }
            ],
            "TaxCode": tax.name
        }

        try:
            response = requests.post(url, data=json.dumps(req_body),
                                     headers=headers)
            res_data = response.json()
            if res_data.get('TaxRateDetails'):
                rate_id = res_data.get('TaxRateDetails')[0].get('TaxRateId')
                tax.write({'qbooks_tax_rate': rate_id})
                self._log_qbooks_operation(
                    'Tax Rate Export', 'export', 'success',
                    f"Tax Rate '{tax.name}' synced.",
                    record=tax, payload=req_body, response=res_data
                )
                self.env.cr.commit()
            else:
                self._handle_tax_error(tax, req_body, res_data, "Rate")
        except Exception as e:
            self._log_qbooks_operation('Tax Rate Export', 'export',
                                       'failed', str(e), record=tax,
                                       payload=req_body)
            raise e

    def _handle_tax_error(self, tax, payload, response, tax_type):
        """Internal helper to process QBO tax faults"""
        fault = response.get('Fault') or response.get('fault')
        errors = fault.get('Error') or fault.get('error') or [{}]
        msg = errors[0].get('Message', 'Unknown Error')
        code = str(errors[0].get('code', ''))

        self._log_qbooks_operation(
            f'Tax {tax_type} Export', 'export', 'failed',
            f"QBO Error [{code}]: {msg}",
            record=tax, payload=payload, response=response
        )

        if code == '6240':
            raise UserError(
                _("Duplicate Name error in QuickBooks for Tax: %s") % tax.name)
        elif code == '3200':
            raise UserError(_("Token expired. Please refresh."))
        raise UserError(_("QuickBooks Error: %s") % msg)

    def action_export_so(self):
        """Entry point to trigger the queued sales order export."""
        self.with_delay(priority=1)._run_export_so_job()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Export Started',
                'message': 'Sales order export has been queued in the background.',
                'type': 'info',
                'sticky': False,
            }
        }

    def _run_export_so_job(self):
        """Collects all confirmed, unsynced SOs and schedules batched jobs."""
        url_data = self.get_import_query()
        if not url_data:
            _logger.warning("No URL returned from export query for sales orders.")
            return

        so_ids = self.env['sale.order'].search([
            ('state', '=', 'sale'),
            ('qbooks_sale', '=', False),
        ]).ids

        if not so_ids:
            _logger.info("No sales orders to export to QuickBooks.")
            return

        batch_size = 10
        chunks = [
            so_ids[i:i + batch_size]
            for i in range(0, len(so_ids), batch_size)
        ]

        for index, chunk_ids in enumerate(chunks):
            delay_time = fields.Datetime.now() + timedelta(seconds=index * 10)
            self.with_delay(priority=1, eta=delay_time)._export_so_batch(
                chunk_ids, url_data
            )

        _logger.info(
            "Scheduled export of %d sales orders across %d batches.",
            len(so_ids), len(chunks)
        )

    def _export_so_batch(self, so_ids, url_data):
        """Worker job: exports a single batch of sales orders to QuickBooks."""
        req_url = f'{url_data["url"]}/estimate?minorversion=40'
        headers = {
            **url_data.get('headers', {}),
            'Content-Type': 'application/json;charset=UTF-8'
        }

        orders = self.env['sale.order'].browse(so_ids)
        success_count = 0
        failed_count = 0

        for so in orders:
            if so.qbooks_sale:
                continue
            try:
                self.create_so_data(so, req_url, headers)
                success_count += 1
            except Exception as e:
                failed_count += 1
                _logger.error("SO Export Error for %s: %s", so.name, str(e))
                continue
        # Log Batch Summary
        self._log_qbooks_operation(
            'SO Batch Export Summary', 'export',
            'success' if failed_count == 0 else 'failed',
            f"Batch completed. Success: {success_count}, Failed: {failed_count}."
        )

    def create_so_data(self, so, url, headers):
        """Builds payload and POSTs a single sale order to QuickBooks as an Estimate."""
        unsynced_products = so.order_line.filtered(
            lambda l: not l.product_id.qbooks_product
        )
        if unsynced_products:
            names = ', '.join(unsynced_products.mapped('product_id.name'))
            raise UserError(
                _("The following products are not synced with QuickBooks: %s") % names
            )

        partner = so.partner_id
        lines = []
        for line in so.order_line:
            lines.append({
                "DetailType": "SalesItemLineDetail",
                "Amount": line.price_subtotal,
                "SalesItemLineDetail": {
                    "Qty": line.product_uom_qty,
                    "UnitPrice": line.price_unit,
                    "ItemRef": {
                        "name": line.product_id.name,
                        "value": line.product_id.qbooks_product,
                    },
                },
            })

        req_body = {
            "TotalAmt": so.amount_total,
            "CustomerMemo": {
                "value": "Thank you for your business and have a great day!"
            },
            "BillEmail": {
                "Address": partner.email or ""
            },
            "ShipAddr": {
                "Line1": partner.street or "",
                "City": partner.city or "",
                "PostalCode": partner.zip or "",
                "CountrySubDivisionCode": partner.state_id.name or "",
            },
            "BillAddr": {
                "Line1": partner.street or "",
                "City": partner.city or "",
                "PostalCode": partner.zip or "",
                "CountrySubDivisionCode": partner.state_id.name or "",
            },
            "PrintStatus": "NeedToPrint",
            "Line": lines,
        }
        if partner.qbooks_customer:
            req_body.update({"CustomerRef": {
                    "name": partner.name,
                    "value": partner.qbooks_customer
            }})
        else:
            self.action_export_customer()
            req_body.update({"CustomerRef": {
                "name": partner.name,
                "value": partner.qbooks_customer
            }})
        try:
            response = requests.post(url, json=req_body, headers=headers,
                                     timeout=30)
            if response.status_code == 401:
                self.action_refresh_token()
                # Re-fetch headers after refresh
                url_data = self.get_import_query()
                response = requests.post(url, json=req_body,
                                         headers=url_data.get('headers'),
                                         timeout=30)

            data = response.json()
        except Exception as e:
            self._log_qbooks_operation('SO Export', 'export', 'failed',
                                       f"Connection Error: {str(e)}", record=so,
                                       payload=req_body)
            raise e
        estimate = data.get('Estimate')
        fault = data.get('Fault')

        if estimate:
            so.write({
                'qbooks_sale': estimate.get('Id'),
                'qbooks_sync_token': estimate.get('SyncToken'),
            })
            self._log_qbooks_operation(
                'SO Export', 'export', 'success',
                f"Successfully exported Sale Order as Estimate: {so.name}",
                record=so, payload=req_body, response=data
            )
            return

        elif fault:
            error = (fault.get('Error') or fault.get('error') or [{}])[0]
            code = str(error.get('code', ''))
            msg = error.get('Detail') or error.get(
                'Message') or "Unknown QBO Error"

            self._log_qbooks_operation(
                'SO Export', 'export', 'failed',
                f"QuickBooks Error [{code}]: {msg}",
                record=so, payload=req_body, response=data
            )
            if code == '3200':
                raise UserError(_("Token expired. Please refresh."))
            raise UserError(_("QuickBooks Error: %s") % msg)

    def action_export_invoice(self):
        """Entry point to trigger the queued invoice export."""
        self.with_delay(priority=1)._run_export_invoice_job()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Export Started',
                'message': 'Invoice export has been queued in the background.',
                'type': 'info',
                'sticky': False,
            }
        }

    def _run_export_invoice_job(self):
        """Collects all unsynced customer invoices and schedules batched jobs."""
        url_data = self.get_import_query()
        if not url_data:
            _logger.warning("No URL returned from export query for invoices.")
            return

        invoice_ids = self.env['account.move'].search([
            ('move_type', '=', 'out_invoice'),
            ('qbooks_invoice', '=', False),
        ]).ids

        if not invoice_ids:
            _logger.info("No invoices to export to QuickBooks.")
            return

        batch_size = 10
        chunks = [
            invoice_ids[i:i + batch_size]
            for i in range(0, len(invoice_ids), batch_size)
        ]

        for index, chunk_ids in enumerate(chunks):
            delay_time = fields.Datetime.now() + timedelta(seconds=index * 10)
            self.with_delay(priority=1, eta=delay_time)._export_invoice_batch(
                chunk_ids, url_data
            )

        _logger.info(
            "Scheduled export of %d invoices across %d batches.",
            len(invoice_ids), len(chunks)
        )

    def _export_invoice_batch(self, invoice_ids, url_data):
        """Worker job: exports a single batch of invoices to QuickBooks."""
        req_url = f'{url_data["url"]}/invoice?minorversion=40'
        headers = {
            **url_data.get('headers', {}),
            'Content-Type': 'application/json',
        }

        invoices = self.env['account.move'].browse(invoice_ids)
        total_success = 0
        total_failed = 0

        for invoice in invoices:
            if invoice.qbooks_invoice:
                continue
            try:
                self.create_invoice_data(invoice, req_url, headers)
                total_success += 1
            except Exception as e:
                total_failed += 1
                _logger.error("Invoice Export Error for %s: %s", invoice.name,
                              str(e))
                # Individual log is already created inside create_invoice_data
                continue
        # Log Batch Summary
        self._log_qbooks_operation(
            'Invoice Batch Export Summary', 'export',
            'success' if total_failed == 0 else 'failed',
            f"Batch completed. Success: {total_success}, Failed: {total_failed}."
        )

    def create_invoice_data(self, invoice, url, headers):
        """Builds payload and POSTs a single invoice to QuickBooks."""

        # Pre-flight: all products on the invoice must be synced
        unsynced = invoice.invoice_line_ids.filtered(
            lambda l: l.product_id and not l.product_id.qbooks_product
        )
        if unsynced:
            names = ', '.join(unsynced.mapped('product_id.name'))
            msg = f"The following products are not synced with QuickBooks: {names}"
            self._log_qbooks_operation('Invoice Export', 'export', 'failed',
                                       msg, record=invoice)
            raise UserError(_(msg))

        lines = []
        for line in invoice.invoice_line_ids.filtered(
                lambda l: l.product_id):
            lines.append({
                "DetailType": "SalesItemLineDetail",
                "Amount": line.price_subtotal,
                "SalesItemLineDetail": {
                    "Qty": line.quantity,
                    "UnitPrice": line.price_unit,
                    "ItemRef": {
                        "name": line.product_id.name,
                        "value": line.product_id.qbooks_product,
                    },
                },
            })

        if not lines:
            msg = f"Invoice {invoice.name} - {invoice.id} has no exportable lines."
            self._log_qbooks_operation('Invoice Export', 'export', 'failed',
                                       msg, record=invoice)
            raise UserError(_(msg))

        req_body = {
            "TotalAmt": invoice.amount_total,
            "Line": lines,
        }
        if invoice.partner_id.qbooks_customer:
            req_body.update({"CustomerRef": {
                "value": invoice.partner_id.qbooks_customer
            }})
        else:
            g = self.action_export_customer()
            req_body.update({"CustomerRef": {
                "value": invoice.partner_id.qbooks_customer
            }})

        if invoice.invoice_date_due:
            req_body["DueDate"] = invoice.invoice_date_due.strftime("%Y-%m-%d")

        if invoice.partner_id.email:
            req_body["BillEmail"] = {"Address": invoice.partner_id.email}
        try:
            response = requests.post(url, json=req_body, headers=headers,
                                     timeout=30)
            if response.status_code == 401:
                self.action_refresh_token()
                url_data = self.get_import_query()
                response = requests.post(url, json=req_body,
                                         headers=url_data.get('headers'),
                                         timeout=30)

            data = response.json()
        except Exception as e:
            self._log_qbooks_operation('Invoice Export', 'export', 'failed',
                                       f"Request Error: {str(e)}",
                                       record=invoice, payload=req_body)
            raise e
        invoice_data = data.get('Invoice')
        fault = data.get('Fault') or data.get('fault')

        if invoice_data:
            invoice.write({
                'qbooks_invoice': invoice_data.get('Id'),
                'qbooks_sync_token': invoice_data.get('SyncToken'),
            })
            self._log_qbooks_operation(
                'Invoice Export', 'export', 'success',
                f"Successfully exported Invoice: {invoice.name}",
                record=invoice, payload=req_body, response=data
            )
        elif fault:
            error_list = fault.get('Error') or fault.get('error') or [{}]
            code = str(error_list[0].get('code', ''))
            msg = error_list[0].get('Detail') or error_list[0].get(
                'Message') or "Unknown QBO Error"

            self._log_qbooks_operation(
                'Invoice Export', 'export', 'failed',
                f"QuickBooks Error [{code}]: {msg}",
                record=invoice, payload=req_body, response=data
            )
            if code == '3200':
                raise UserError(_("Token expired. Please refresh."))
            raise UserError(_("QuickBooks Error: %s") % msg)

    def action_export_customer_payment(self):
        """Entry point to trigger the queued customer payment export."""
        self.with_delay(priority=1)._run_export_payment_job()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Export Started',
                'message': 'Customer payment export has been queued in the background.',
                'type': 'info',
                'sticky': False,
            }
        }

    def _run_export_payment_job(self):
        """Collects all unsynced payments and schedules batched jobs."""
        url_data = self.get_import_query()
        if not url_data:
            _logger.warning("No URL returned from export query for payments.")
            return

        payment_ids = self.env['account.payment'].search([
            ('qbooks_payment', '=', False),
            ('move_id', '!=', False),
        ]).ids

        if not payment_ids:
            _logger.info("No customer payments to export to QuickBooks.")
            return

        batch_size = 10
        chunks = [
            payment_ids[i:i + batch_size]
            for i in range(0, len(payment_ids), batch_size)
        ]

        for index, chunk_ids in enumerate(chunks):
            delay_time = fields.Datetime.now() + timedelta(seconds=index * 10)
            self.with_delay(priority=1, eta=delay_time)._export_payment_batch(
                chunk_ids, url_data
            )

        _logger.info(
            "Scheduled export of %d payments across %d batches.",
            len(payment_ids), len(chunks)
        )

    def _export_payment_batch(self, payment_ids, url_data):
        """Worker job: exports a single batch of payments to QuickBooks."""
        req_url = f'{url_data["url"]}/journalentry?minorversion=40'
        headers = {
            **url_data.get('headers', {}),
            'Content-Type': 'application/json;charset=UTF-8',
        }

        payments = self.env['account.payment'].browse(payment_ids)
        total_success = 0
        total_failed = 0

        for payment in payments:
            if payment.qbooks_payment or not payment.move_id:
                continue
            try:
                self.create_payment_data(payment, payment.move_id, req_url,
                                         headers)
                total_success += 1
            except Exception as e:
                total_failed += 1
                _logger.error("Payment Export Error for %s: %s", payment.name,
                              str(e))
                # Individual logging is handled inside create_payment_data
                continue

        # Log Batch Summary
        self._log_qbooks_operation(
            'Customer Payment Batch Export Summary', 'export',
            'success' if total_failed == 0 else 'failed',
            f"Batch completed. Success: {total_success}, Failed: {total_failed}."
        )

    def create_payment_data(self, payment, move, url, headers):
        """Builds a Journal Entry payload and POSTs it to QuickBooks."""

        if not move.line_ids:
            msg = _("Payment '%s' has no journal lines to export.") % move.name
            self._log_qbooks_operation('Payment Export', 'export', 'failed',
                                       msg, record=payment)
            raise UserError(_(msg))

        # Pre-flight: all accounts must be synced
        unsynced_accounts = move.line_ids.filtered(
            lambda l: not l.account_id.qbooks_account
        )
        if unsynced_accounts:
            names = ', '.join(unsynced_accounts.mapped('account_id.name'))
            msg = _(
                "The following accounts are not synced to QuickBooks: %s") % names
            # LOG THE ERROR BEFORE RAISING
            self._log_qbooks_operation(
                'Payment Export',
                'export',
                'failed',
                msg,
                record=payment
            )
            raise UserError(msg)

        lines = []
        for line in move.line_ids:
            if line.debit > 0:
                posting_type = "Debit"
                amount = line.debit
            elif line.credit > 0:
                posting_type = "Credit"
                amount = line.credit
            else:
                continue  # skip zero-amount lines

            line_data = {
                "DetailType": "JournalEntryLineDetail",
                "Amount": float(amount),
                "Description": move.name or "",
                "JournalEntryLineDetail": {
                    "PostingType": posting_type,
                    "AccountRef": {
                        "value": str(line.account_id.qbooks_account),
                        "name": line.account_id.name,
                    },
                },
            }

            # Attach customer entity to receivable credit lines
            if (
                    posting_type == "Credit"
                    and move.partner_id
                    and move.partner_id.qbooks_customer
                    and line.account_id.account_type == "asset_receivable"
            ):
                line_data["JournalEntryLineDetail"]["Entity"] = {
                    "Type": "Customer",
                    "EntityRef": {
                        "value": str(move.partner_id.qbooks_customer),
                        "name": move.partner_id.name,
                    },
                }

            lines.append(line_data)

        # A valid journal entry requires at least one debit and one credit
        has_debit = any(
            l["JournalEntryLineDetail"]["PostingType"] == "Debit" for l in
            lines
        )
        has_credit = any(
            l["JournalEntryLineDetail"]["PostingType"] == "Credit" for l in
            lines
        )
        if not has_debit or not has_credit:
            msg = _(
                "Payment '%s' does not produce a balanced journal entry.") % move.name
            self._log_qbooks_operation('Payment Export', 'export', 'failed',
                                       msg, record=payment)
            raise UserError(msg)

        req_body = {"Line": lines}

        if move.date:
            req_body["TxnDate"] = move.date.strftime("%Y-%m-%d")
        try:
            response = requests.post(url, json=req_body, headers=headers,
                                     timeout=30)
            # Handle Auth Refresh
            if response.status_code == 401:
                self.action_refresh_token()
                url_data = self.get_import_query()
                response = requests.post(url, json=req_body,
                                         headers=url_data.get('headers'),
                                         timeout=30)

            data = response.json()
        except Exception as e:
            self._log_qbooks_operation('Payment Export', 'export', 'failed',
                                       f"Request Error: {str(e)}",
                                       record=payment, payload=req_body)
            raise e

        journal_entry = data.get("JournalEntry")
        fault = data.get("Fault") or data.get("fault")

        if journal_entry:
            payment.write({'qbooks_payment': journal_entry.get('Id')})
            move.write({
                'qbooks_invoice': journal_entry.get('Id'),
                'qbooks_sync_token': journal_entry.get('SyncToken'),
            })
            self._log_qbooks_operation(
                'Payment Export', 'export', 'success',
                f"Successfully exported Payment as Journal Entry: {payment.name}",
                record=payment, payload=req_body, response=data
            )
        elif fault:
            error = (fault.get("Error") or fault.get("error") or [{}])[0]
            code = str(error.get("code", ""))
            msg = error.get("Detail") or error.get(
                "Message") or "Unknown QBO Error"

            self._log_qbooks_operation(
                'Payment Export', 'export', 'failed',
                f"QuickBooks Error [{code}]: {msg}",
                record=payment, payload=req_body, response=data
            )

            if code == "3200":
                raise UserError(_("Token expired. Kindly refresh token."))
            raise UserError(_("QuickBooks Error: %s") % msg)

    def action_export_po(self):
        """Entry point to trigger the queued purchase order export."""
        self.with_delay(priority=1)._run_export_po_job()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Export Started',
                'message': 'Purchase order export has been queued in the background.',
                'type': 'info',
                'sticky': False,
            }
        }

    def _run_export_po_job(self):
        """Collects all unsynced purchase orders and schedules batched jobs."""
        url_data = self.get_import_query()
        if not url_data:
            _logger.warning(
                "No URL returned from export query for purchase orders.")
            return

        po_ids = self.env['purchase.order'].search([
            ('qbooks_purchase', '=', False),
        ]).ids

        if not po_ids:
            _logger.info("No purchase orders to export to QuickBooks.")
            return

        batch_size = 10
        chunks = [
            po_ids[i:i + batch_size]
            for i in range(0, len(po_ids), batch_size)
        ]

        for index, chunk_ids in enumerate(chunks):
            delay_time = fields.Datetime.now() + timedelta(seconds=index * 10)
            self.with_delay(priority=1, eta=delay_time)._export_po_batch(
                chunk_ids, url_data
            )

        _logger.info(
            "Scheduled export of %d purchase orders across %d batches.",
            len(po_ids), len(chunks)
        )

    def _export_po_batch(self, po_ids, url_data):
        """Worker job: exports a single batch of purchase orders to QuickBooks."""
        req_url = f'{url_data["url"]}/purchaseorder?minorversion=63'
        headers = {
            **url_data.get('headers', {}),
            'Content-Type': 'application/json',
        }

        orders = self.env['purchase.order'].browse(po_ids)
        total_success = 0
        total_failed = 0

        for po in orders:
            if po.qbooks_purchase:
                continue
            try:
                self.create_po_data(po, req_url, headers)
                total_success += 1
            except Exception as e:
                total_failed += 1
                _logger.error("PO Export Error for %s: %s", po.name, str(e))
                # Individual error log is handled inside create_po_data
                continue
        # Log Batch Summary
        self._log_qbooks_operation(
            'PO Batch Export Summary', 'export',
            'success' if total_failed == 0 else 'failed',
            f"Batch completed. Success: {total_success}, Failed: {total_failed}."
        )

    def create_po_data(self, po, url, headers):
        """Builds payload and POSTs a single purchase order to QuickBooks."""

        # Pre-flight: all products must be synced
        unsynced_products = po.order_line.filtered(
            lambda l: not l.product_id.qbooks_product
        )
        if unsynced_products:
            names = ', '.join(unsynced_products.mapped('product_id.name'))
            msg = f"Products not synced with QuickBooks: {names}"
            self._log_qbooks_operation('PO Export', 'export', 'failed', msg,
                                       record=po)
            raise UserError(_(msg))

        # Pre-flight: AP account must be synced.
        # The AP account is taken from the vendor (po.partner_id), not order lines,
        # which is more reliable — order lines may belong to different partners.
        ap_account = po.partner_id.property_account_payable_id
        if not ap_account or not ap_account.qbooks_account:
            msg = f"Payable account '{ap_account.name if ap_account else 'None'}' is not synced to QBO."
            self._log_qbooks_operation('PO Export', 'export', 'failed', msg,
                                       record=po)
            raise UserError(_(msg))

        if not po.partner_id.qbooks_vendor:
            msg = f"Vendor '{po.partner_id.name}' not synced with QuickBooks."
            self._log_qbooks_operation('PO Export', 'export', 'failed', msg,
                                       record=po)
            raise UserError(_(msg))

        lines = []
        for line in po.order_line:
            lines.append({
                "DetailType": "ItemBasedExpenseLineDetail",
                "Amount": line.price_subtotal,
                "ItemBasedExpenseLineDetail": {
                    "ItemRef": {
                        "name": line.product_id.name,
                        "value": line.product_id.qbooks_product,
                    },
                    "Qty": line.product_qty,
                    "UnitPrice": line.price_unit,
                },
            })

        req_body = {
            "TotalAmt": po.amount_total,
            "VendorRef": {
                "name": po.partner_id.name,
                "value": po.partner_id.qbooks_vendor,
            },
            "APAccountRef": {
                "name": ap_account.name,
                "value": ap_account.qbooks_account,
            },
            "Line": lines,
        }

        if po.date_order:
            req_body["TxnDate"] = po.date_order.strftime("%Y-%m-%d")

        if po.partner_id.qbooks_vendor:
            req_body.update({"VendorRef": {
                "name": po.partner_id.name,
                "value": po.partner_id.qbooks_vendor
            }})
        else:
            self.action_export_vendor()
            req_body.update({"VendorRef": {
                "name": po.partner_id.name,
                "value": po.partner_id.qbooks_vendor
            }})
        try:
            response = requests.post(url, json=req_body, headers=headers,
                                     timeout=30)

            # Handle Auth Refresh
            if response.status_code == 401:
                self.action_refresh_token()
                url_data = self.get_import_query()
                response = requests.post(url, json=req_body,
                                         headers=url_data.get('headers'),
                                         timeout=30)

            data = response.json()
        except Exception as e:
            self._log_qbooks_operation('PO Export', 'export', 'failed',
                                       f"Request Error: {str(e)}", record=po,
                                       payload=req_body)
            raise e

        purchase_order = data.get("PurchaseOrder")
        fault = data.get("Fault") or data.get("fault")

        if purchase_order:
            po.write({
                "qbooks_purchase": purchase_order.get("Id"),
                "qbooks_sync_token": purchase_order.get("SyncToken"),
            })
            self._log_qbooks_operation(
                'PO Export', 'export', 'success',
                f"Successfully exported Purchase Order: {po.name}",
                record=po, payload=req_body, response=data
            )

        elif fault:
            error_list = fault.get('Error') or fault.get('error') or [{}]
            code = str(error_list[0].get('code', ''))
            msg = error_list[0].get('Detail') or error_list[0].get(
                'Message') or "Unknown QBO Error"

            self._log_qbooks_operation(
                'PO Export', 'export', 'failed',
                f"QuickBooks Error [{code}]: {msg}",
                record=po, payload=req_body, response=data
            )

            if code == "3200":
                raise UserError(_("Token expired. Kindly refresh token."))
            raise UserError(_("QuickBooks PO Error: %s") % msg)

    def action_export_bill(self):
        """Entry point to trigger the queued vendor bill export."""
        self.with_delay(priority=1)._run_export_bill_job()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Export Started',
                'message': 'Vendor bill export has been queued in the background.',
                'type': 'info',
                'sticky': False,
            }
        }

    def _run_export_bill_job(self):
        """Collects all unsynced vendor bills and schedules batched jobs."""
        url_data = self.get_import_query()
        if not url_data:
            _logger.warning(
                "No URL returned from export query for vendor bills.")
            return

        bill_ids = self.env['account.move'].search([
            ('move_type', '=', 'in_invoice'),
            ('qbooks_bill', '=', False),
        ]).ids

        if not bill_ids:
            _logger.info("No vendor bills to export to QuickBooks.")
            return

        batch_size = 10
        chunks = [
            bill_ids[i:i + batch_size]
            for i in range(0, len(bill_ids), batch_size)
        ]

        for index, chunk_ids in enumerate(chunks):
            delay_time = fields.Datetime.now() + timedelta(seconds=index * 10)
            self.with_delay(priority=1, eta=delay_time)._export_bill_batch(
                chunk_ids, url_data
            )

        _logger.info(
            "Scheduled export of %d vendor bills across %d batches.",
            len(bill_ids), len(chunks)
        )

    def _export_bill_batch(self, bill_ids, url_data):
        """Worker job: exports a single batch of vendor bills to QuickBooks."""
        req_url = f'{url_data["url"]}/bill?minorversion=63'
        headers = {
            **url_data.get('headers', {}),
            'Content-Type': 'application/json',
        }

        bills = self.env['account.move'].browse(bill_ids)
        total_success = 0
        total_failed = 0
        for bill in bills:
            if bill.qbooks_bill:
                continue
            try:
                self.create_bill_data(bill, req_url, headers)
                total_success += 1
            except Exception as e:
                total_failed += 1
                _logger.error("Vendor Bill Export Error for %s: %s", bill.name,
                              str(e))
                # Individual error log is already handled inside create_bill_data
                continue
        # Log Batch Summary
        self._log_qbooks_operation(
            'Bill Batch Export Summary', 'export',
            'success' if total_failed == 0 else 'failed',
            f"Batch completed. Success: {total_success}, Failed: {total_failed}."
        )

    def create_bill_data(self, bill, url, headers):
        """Builds payload and POSTs a single vendor bill to QuickBooks."""

        # Pre-flight: vendor must be synced
        if not bill.partner_id.qbooks_vendor:
            msg = f"Vendor '{bill.partner_id.name}' is not synced with QuickBooks."
            self._log_qbooks_operation('Bill Export', 'export', 'failed', msg,
                                       record=bill)
            raise UserError(_(msg))

        # Pre-flight: AP account must be synced
        ap_account = bill.partner_id.property_account_payable_id
        if not ap_account or not ap_account.qbooks_account:
            msg = f"Payable account '{ap_account.name if ap_account else 'None'}' is not synced to QBO."
            self._log_qbooks_operation('Bill Export', 'export', 'failed', msg,
                                       record=bill)
            raise UserError(_(msg))

        # Pre-flight: all products must be synced
        billable_lines = bill.invoice_line_ids.filtered(
            lambda l: l.product_id and l.display_type not in ('line_section',
                                                              'line_note')
        )
        unsynced_products = billable_lines.filtered(
            lambda l: not l.product_id.qbooks_product
        )
        if unsynced_products:
            names = ', '.join(unsynced_products.mapped('product_id.name'))
            msg = f"Products not synced with QuickBooks: {names}"
            self._log_qbooks_operation('Bill Export', 'export', 'failed', msg,
                                       record=bill)
            raise UserError(_(msg))

        if not billable_lines:
            msg = f"Bill '{bill.name}' has no exportable lines."
            self._log_qbooks_operation('Bill Export', 'export', 'failed', msg,
                                       record=bill)
            raise UserError(_(msg))

        lines = []
        for line in billable_lines:
            lines.append({
                "DetailType": "ItemBasedExpenseLineDetail",
                "Amount": line.price_subtotal,
                "ItemBasedExpenseLineDetail": {
                    "Qty": line.quantity,
                    "UnitPrice": line.price_unit,
                    "ItemRef": {
                        "name": line.product_id.name,
                        "value": line.product_id.qbooks_product,
                    },
                },
            })

        req_body = {
            "TotalAmt": bill.amount_total,
            "VendorRef": {
                "name": bill.partner_id.name,
                "value": bill.partner_id.qbooks_vendor,
            },
            "APAccountRef": {
                "name": ap_account.name,
                "value": ap_account.qbooks_account,
            },
            "Line": lines,
        }

        try:
            response = requests.post(url, json=req_body, headers=headers,
                                     timeout=30)
            if response.status_code == 401:
                self.action_refresh_token()
                url_data = self.get_import_query()
                response = requests.post(url, json=req_body,
                                         headers=url_data.get('headers'),
                                         timeout=30)
            res_data = response.json()
        except Exception as e:
            self._log_qbooks_operation('Bill Export', 'export',
                                       'failed',
                                       f"Connection Error: {str(e)}",
                                       record=bill, payload=req_body)
            raise e
        if response.status_code == 200 and 'Bill' in res_data:
            bill_res = res_data.get("Bill")
            bill.write({
                "qbooks_bill": bill_res.get("Id"),
                "qbooks_sync_token": bill_res.get("SyncToken"),
            })
            self._log_qbooks_operation(
                "Bill Export", "export", "success",
                f"Successfully exported Vendor Bill: {bill.name}",
                record=bill, payload=req_body, response=res_data
            )
        else:
            fault = res_data.get('Fault') or res_data.get('fault')
            errors = fault.get('Error') or fault.get('error') or [{}]
            msg = errors[0].get('Detail') or errors[0].get(
                'Message') or "API Rejected"

            self._log_qbooks_operation(
                "Bill Export", "export", "failed",
                f"QuickBooks Error: {msg}",
                record=bill, payload=req_body, response=res_data
            )
            raise UserError(_("QuickBooks Error: %s") % msg)

    def action_import_invoice(self):
        """ Import invoice. """
        self.with_delay(priority=1)._run_import_invoice_job()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Export Started',
                'message': 'Import invoice has been queued in the background.',
                'type': 'info',
                'sticky': False,
            }
        }

    def _run_import_invoice_job(self):
        """ Import invoice job"""
        url = self.get_import_query()
        if not url:
            _logger.warning("No URL returned from import query.")
            return

        start_position = 1
        max_results = 100

        while True:
            query = f"SELECT * FROM Invoice STARTPOSITION {start_position} MAXRESULTS {max_results}"
            get_url = f"{url['url']}/query?minorversion={self.minor_version}&query={query}"

            try:
                response = requests.get(get_url, headers=url['headers'])
                if response.json().get('fault', {}).get(
                        'type') == 'AUTHENTICATION':
                    self.action_refresh_token()
                    response = requests.get(get_url, headers=url['headers'])
            except Exception as e:
                _logger.error(f"Error while fetching invoices: {e}")
                break

            invoices = response.json().get('QueryResponse', {}).get('Invoice',
                                                                    [])
            if not invoices:
                break

            self.with_delay(priority=1)._batch_schedule_invoice_import(
                invoices, total=0, max_results=max_results,
                start_position=start_position
            )

            start_position += max_results

    def _batch_schedule_invoice_import(self, invoices, total, max_results,
                                       start_position):
        """ Batch invoice import. """
        size = 10
        invoice_list = [invoices[i:i + size] for i in range(0, len(invoices), size)]

        for index, invoice_chunk in enumerate(invoice_list):
            delay_time = fields.Datetime.now() + timedelta(seconds=index * 10)
            self.with_delay(priority=1, eta=delay_time)._invoice_import(
                invoice_chunk, total, max_results, start_position)

    def _invoice_import(self, invoices, total, max_results, start_position):
        """ Invoice import. """
        failed_count = 0

        for invoice in invoices:
            inv_id = invoice.get('Id')
            inv_number = invoice.get('DocNumber', 'Unknown')

            try:
                exist = self.env['account.move'].search(
                    [('qbooks_invoice', '=', inv_id)])
                if exist:
                    if len(exist) > 1:
                        exist[1:].unlink()
                    continue

                rate_info = self._apply_qbooks_exchange_rate(invoice)
                currency_id = self.env['res.currency'].browse(
                    rate_info.get('currency_id')
                ) if rate_info.get('currency_id') else self.env[
                    'res.currency'].search(
                    [('name', '=',
                      invoice.get('CurrencyRef', {}).get('value'))],
                    limit=1
                )
                invoice_date = datetime.strptime(invoice.get('TxnDate'),
                                                 '%Y-%m-%d')

                invoice_vals = {
                    'name': inv_number,
                    'qbooks_invoice': inv_id,
                    'invoice_date': invoice_date,
                    'currency_id': currency_id.id if currency_id else False,
                    'invoice_line_ids': [],
                    'move_type': 'out_invoice',
                }

                if invoice.get('CustomerRef'):
                    customer_id = self.env['res.partner'].search([
                        ('qbooks_customer', '=',
                         invoice.get('CustomerRef').get('value'))
                    ], limit=1).id
                    if customer_id:
                        invoice_vals['partner_id'] = customer_id
                    else:
                        raise ValidationError(
                            f"Customer with QuickBooks ID {invoice.get('CustomerRef').get('value')} not found. Please import customers first."
                        )
                else:
                    continue  # skip if no customer

                for line in invoice.get('Line'):
                    if line.get('SalesItemLineDetail'):
                        product_id = self.env['product.product'].search([
                            ('qbooks_product', '=',
                             line.get('SalesItemLineDetail').get('ItemRef').get(
                                 'value'))
                        ], limit=1)
                        if product_id:
                            line_dict = {
                                'product_id': product_id.id,
                                'name': product_id.name,
                                'quantity': line.get('SalesItemLineDetail').get(
                                    'Qty'),
                                'price_unit': line.get(
                                    'SalesItemLineDetail').get('UnitPrice'),
                                'qbooks_invoice_line': line.get('Id'),
                                'qbooks_invoice': inv_id,
                            }

                            tax_code_ref = line.get('SalesItemLineDetail',
                                                    {}).get(
                                'TaxCodeRef', {}).get('value')
                            if tax_code_ref == "TAX":
                                tax_ref_id = invoice.get('TxnTaxDetail',
                                                         {}).get(
                                    'TxnTaxCodeRef', {}).get('value')
                                if tax_ref_id:
                                    tax_id = self.env['account.tax'].search([
                                        ('qbooks_tax', '=',
                                         invoice.get('TxnTaxDetail').get(
                                             'TxnTaxCodeRef').get('value')),
                                        ('type_tax_use', '=', 'sale')
                                    ], limit=1)
                                    line_dict['tax_ids'] = [
                                        (6, 0, [tax_id.id])] if tax_id else [
                                        (6, 0, [])]
                                else:
                                    line_dict['tax_ids'] = [(6, 0, [])]
                            else:
                                line_dict['tax_ids'] = [(6, 0, [])]

                            if invoice.get('LinkedTxn') and \
                                    invoice.get('LinkedTxn')[0].get(
                                        'TxnType') == 'Estimate':
                                line_dict['qbooks_payment'] = \
                                invoice.get('LinkedTxn')[0].get('TxnId')

                            invoice_vals['invoice_line_ids'].append(
                                (0, 0, line_dict))
                        else:
                            raise ValidationError(
                                'Product Not Found, Please import products first.')

                ctx = self._get_qbooks_currency_context(invoice,
                                                        invoice_date.date())
                created = self.env['account.move'].with_context(**ctx).create(
                    [invoice_vals])

                # ✅ Log success per invoice
                self._log_qbooks_operation(
                    operation_name=f"Invoice Import: {inv_number}",
                    op_type='import',
                    status='success',
                    message=(
                        f"Invoice '{inv_number}' (QBO ID: {inv_id}) imported successfully "
                        f"with {len(invoice_vals['invoice_line_ids'])} line(s)."
                    ),
                    record=created,
                    payload=invoice,
                )
                total += 1

            except Exception as e:
                failed_count += 1
                _logger.error(
                    f"Failed to import invoice '{inv_number}' (QBO ID: {inv_id}): {e}")

                # ❌ Log failure per invoice
                self._log_qbooks_operation(
                    operation_name=f"Invoice Import: {inv_number}",
                    op_type='import',
                    status='failed',
                    message=str(e),
                    payload=invoice,
                )
                # Re-raise ValidationErrors — missing customer/product must halt the batch
                if isinstance(e, ValidationError):
                    raise

        # 📊 Log batch summary
        self._log_qbooks_operation(
            operation_name="Invoice Import Batch",
            op_type='import',
            status='success' if not failed_count else 'failed',
            message=(
                f"Batch complete: {total} invoice(s) imported successfully, "
                f"{failed_count} failed. "
                f"(start_position={start_position}, max_results={max_results})"
            ),
            payload={
                'start_position': start_position,
                'max_results': max_results,
                'created': total,
                'failed': failed_count,
            },
        )

        if total != 0:
            _logger.info(f"{total} Customer invoices imported from QuickBooks.")
        else:
            _logger.info("No customer invoices to import.")

        if len(invoices) < max_results:
            run = False
        else:
            start_position += max_results

    def _log_qbooks_operation(self, operation_name, op_type, status, message,
                              record=None, payload=None, response=None):
        """
        Universal Logger for QuickBooks
        :param operation_name: String (e.g., 'Vendor Bill Sync', 'Product Import')
        :param op_type: 'import' or 'export'
        :param status: 'success' or 'failed'
        :param record: The Odoo record object (optional)
        """
        log_vals = {
            'name': operation_name,
            'operation_type': op_type,
            'status': status,
            'message': message,
            'payload': json.dumps(payload, indent=2) if isinstance(payload,
                                                                   (dict,
                                                                    list)) else str(
                payload),
            'response': json.dumps(response, indent=2) if isinstance(response,
                                                                     (dict,
                                                                      list)) else str(
                response),
        }

        if record:
            log_vals.update({
                'res_model': record._name,
                'res_id': record.id,
            })

        return self.env['qbooks.logs'].create([log_vals])
