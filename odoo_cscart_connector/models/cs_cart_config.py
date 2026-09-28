# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

import logging
import re
import requests
from requests.auth import HTTPBasicAuth

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools import config

_logger = logging.getLogger(__name__)


class CsCartConfig(models.Model):
    """
    CS-Cart Configuration Model.

    Manages connection credentials, synchronization settings, connection testing,
    and manual triggering of import/export batch jobs between Odoo and CS-Cart.
    """
    _name = "cs.cart.config"
    _description = "CS-Cart Configuration"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Store name", required=True)
    store_url = fields.Char(string="Store URL", required=True, help="Your CS Cart store URL")
    email = fields.Char(string="Email", required=True, help="CS Cart Email Address")
    api_key = fields.Char(string="Api Key", required=True, help="Cs Cart REST API For the Email Address", copy=False)

    sync_categories = fields.Boolean(string="Categories", default=False)
    sync_attributes = fields.Boolean(string="Attributes", default=False)
    sync_products = fields.Boolean(string="Products", default=False)
    sync_customers = fields.Boolean(string="Customers", default=False)
    sync_orders = fields.Boolean(string="Orders", default=False)

    realtime_stock_sync = fields.Boolean(
        string="Real-time Stock Sync",
        default=False,
        help="Automatically sync stock changes to CS-Cart in real-time."
    )
    stock_sync_type = fields.Selection([
        ('qty_available', 'Quantity on Hand'),
        ('virtual_available', 'Forecasted Quantity')
    ], string="Stock Sync Type", default='qty_available', help="Which Odoo stock quantity should sync to CS-Cart.")

    connected_status = fields.Selection([
        ('connected', 'Connected'),
        ('disconnected', 'Disconnected')
    ], string='Connection Status', default='disconnected', readonly=True)

    last_sync_status = fields.Selection([
        ('success', 'Success'),
        ('failed', 'Failed')
    ], string='Last Sync Status', readonly=True)
    last_sync_message = fields.Char(string='Last Sync Message', readonly=True)

    @api.onchange('sync_products')
    def _onchange_sync_products(self):
        """
        Onchange handler for sync_products field.
        Automatically enables categories and attributes sync when products sync is checked.
        """
        for rec in self:
            rec.sync_categories = rec.sync_products
            rec.sync_attributes = rec.sync_products

    def _reset_sync_flags(self):
        """
        Reset entity selection checkboxes after an import or export operation.
        """
        self.write({
            'sync_categories': False,
            'sync_attributes': False,
            'sync_products': False,
            'sync_customers': False,
            'sync_orders': False,
        })

    def _notify(self, title, message, type='success', reload=False):
        """
        Helper method to construct a client action web notification.

        :param title: Title of the notification banner
        :type title: str
        :param message: Content message of the notification banner
        :type message: str
        :param type: Type of notification ('success', 'warning', 'danger', 'info')
        :type type: str
        :param reload: Whether to trigger a client view reload after notification
        :type reload: bool
        :return: Client action dictionary for web notification
        :rtype: dict
        """
        action = {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": title,
                "message": message,
                "type": type,
                "sticky": reload,
            },
        }

        if reload:
            action["params"]["next"] = {
                "type": "ir.actions.client",
                "tag": "reload",
            }

        return action

    def _queue_job_runner_available(self):
        """
        Check whether queue_job module is configured server-wide.

        :return: True if queue_job is loaded server-wide, else False
        :rtype: bool
        """
        server_wide_modules = config.get('server_wide_modules') or ''
        if isinstance(server_wide_modules, str):
            modules = {
                module.strip()
                for module in server_wide_modules.split(',')
                if module.strip()
            }
        else:
            modules = set(server_wide_modules)
        return 'queue_job' in modules

    def _run_import_job(self, model_name, method_name, batch):
        """
        Execute an import job via queue_job if available, or fall back to synchronous request execution.

        :param model_name: Name of the target Odoo model
        :type model_name: str
        :param method_name: Name of the import queue method to invoke
        :type method_name: str
        :param batch: cs.cart.import.batch record set
        :type batch: cs.cart.import.batch
        :return: Execution mode ('queued' or 'direct')
        :rtype: str
        """
        model = self.env[model_name]

        if self._queue_job_runner_available():
            job = getattr(model.with_delay(), method_name)(batch.id)
            if job and hasattr(job, 'db_record'):
                batch.queue_job_id = job.db_record().id
            return 'queued'

        _logger.warning(
            "queue_job is not available as a server-wide module; running %s directly",
            method_name,
        )
        getattr(
            model.with_context(queue_job__no_delay=True),
            method_name,
        )(batch.id)
        return 'direct'

    # ===================== Connection Management =====================

    def action_test_connection(self):
        """
        Test API connection to the configured CS-Cart store instance.

        :return: Client action notification dictionary upon success
        :rtype: dict
        :raises UserError: If store credentials are bad or connection fails.
        """
        self.ensure_one()
        if not all([self.store_url, self.email, self.api_key]):
            raise UserError("Please provide valid credentials before testing the connection.")
        try:
            url = f"{self.store_url.rstrip('/')}/api/products"

            response = requests.get(
                url,
                auth=HTTPBasicAuth(self.email, self.api_key),
                params={'items_per_page': 1},
                timeout=10
            )

            if response.status_code == 200:
                self.connected_status = 'connected'
                return {
                    "type": "ir.actions.client",
                    "tag": "display_notification",
                    "params": {
                        "title": "Connection Successful",
                        "message": f"Successfully connected to CS-Cart: {self.name}",
                        "type": "success",
                        "sticky": False,
                        "next": {"type": "ir.actions.client", "tag": "reload"},
                    },
                }
            else:
                self.connected_status = 'disconnected'
                raise UserError(f"Connection failed. Status: {response.status_code}, Message: {response.text}")
        except Exception as e:
            self.connected_status = 'disconnected'
            raise UserError(f"Connection failed for {self.name}: {str(e)}")

    def action_disconnect(self):
        """
        Disconnect from CS-Cart store instance.

        :return: Client action notification dictionary
        :rtype: dict
        """
        self.ensure_one()
        self.connected_status = 'disconnected'
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "Disconnected",
                "message": f"Disconnected from CS-Cart: {self.name}",
                "type": "info",
                "sticky": False,
                "next": {"type": "ir.actions.client", "tag": "reload"},
            },
        }

    def action_import_selected(self):
        """
        Trigger manual import of all selected CS-Cart entities.

        :return: Web notification client action with execution results
        :rtype: dict
        """
        self.ensure_one()
        if not (self.sync_categories or self.sync_attributes or self.sync_products or
                self.sync_customers or self.sync_orders):
            return self._notify("Nothing Selected", "Select at least one item to import.", type="warning", reload=True)

        self.write({
            'last_sync_status': False,
            'last_sync_message': False
        })
        execution_modes = set()
        batches = []

        if self.sync_categories:
            batch = self.env['cs.cart.import.batch'].create({
                'name': f'Category Import - {fields.Datetime.now()}',
                'import_type': 'categories',
                'state': 'pending',
                'cs_cart_config_id': self.id
            })
            batches.append(batch)
            execution_modes.add(
                self._run_import_job('cs.cart.category', 'import_categories_queue', batch)
            )

        if self.sync_attributes:
            batch = self.env['cs.cart.import.batch'].create({
                'name': f'Attribute Import - {fields.Datetime.now()}',
                'import_type': 'attributes',
                'state': 'pending',
                'cs_cart_config_id': self.id
            })
            batches.append(batch)
            execution_modes.add(
                self._run_import_job('cs.cart.attribute.sync', 'import_attributes_queue', batch)
            )

        if self.sync_products:
            batch = self.env['cs.cart.import.batch'].create({
                'name': f'Product Import - {fields.Datetime.now()}',
                'import_type': 'products',
                'state': 'pending',
                'cs_cart_config_id': self.id
            })
            batches.append(batch)
            execution_modes.add(
                self._run_import_job('cs.cart.product.sync', 'import_products_queue', batch)
            )

        if self.sync_customers:
            batch = self.env['cs.cart.import.batch'].create({
                'name': f'Customer Import - {fields.Datetime.now()}',
                'import_type': 'customers',
                'state': 'pending',
                'cs_cart_config_id': self.id
            })
            batches.append(batch)
            execution_modes.add(
                self._run_import_job('cs.cart.customer.sync', 'import_customers_queue', batch)
            )

        if self.sync_orders:
            batch = self.env['cs.cart.import.batch'].create({
                'name': f'Order Import - {fields.Datetime.now()}',
                'import_type': 'orders',
                'state': 'pending',
                'cs_cart_config_id': self.id
            })
            batches.append(batch)
            execution_modes.add(
                self._run_import_job('cs.cart.order.sync', 'import_orders_queue', batch)
            )

        self._reset_sync_flags()

        if 'direct' in execution_modes:
            failed_batches = [b for b in batches if b.state == 'failed']
            if failed_batches:
                raw_notes = failed_batches[0].log_notes or "Unknown error"
                clean_error = re.sub('<[^<]+?>', '', raw_notes).replace('❌', '').replace('⚠️', '').replace('Error:', '').strip()
                return self._notify("Import Failed", f"Validation Error: {clean_error}", type="danger", reload=True)

            success_messages = []
            for b in batches:
                if b.state == 'done':
                    clean_notes = re.sub('<[^<]+?>', '', b.log_notes or '').replace('🎉', '').strip()
                    success_messages.append(clean_notes)
            if success_messages:
                return self._notify("Import Completed", " | ".join(success_messages), type="success", reload=True)

        if execution_modes == {'queued'}:
            return self._notify("Import Queued", f"Selected imports queued for {self.name}.", type="success", reload=True)
        return self._notify("Import Started", f"Selected imports started for {self.name}.", type="success", reload=True)

    def action_export_selected(self):
        """
        Trigger manual export of selected entities to CS-Cart.

        :return: Web notification client action with export summary
        :rtype: dict
        """
        self.ensure_one()
        if not (self.sync_categories or self.sync_attributes or self.sync_products or
                self.sync_customers or self.sync_orders):
            return self._notify("Nothing Selected", "Select at least one item to export.", type="warning", reload=True)

        log_messages = []
        try:
            if self.sync_categories:
                category_stats = self.env['product.category'].export_categories_to_cscart()
                log_messages.append(f"Categories: {category_stats.get('created', 0)} created, {category_stats.get('present', 0)} already present.")

            if self.sync_products:
                products = self.env['product.product'].search([])
                valid_products = self.env['product.product']
                for p in products:
                    categ = p.product_tmpl_id.categ_id
                    while categ and not categ.cs_cart_category_id:
                        categ = categ.parent_id
                    if categ and categ.cs_cart_category_id:
                        valid_products |= p
                
                if valid_products:
                    valid_products.action_export_to_cs_cart()
                    log_messages.append(f"Products: {len(valid_products)} exported.")
                else:
                    log_messages.append("Products: No products with mapped categories to export.")

            if self.sync_customers:
                partners = self.env['res.partner'].search([('email', '!=', False)])
                valid_partners = self.env['res.partner']
                for partner in partners:
                    if (partner.customer_rank > 0 and partner.supplier_rank == 0) or \
                       (partner.supplier_rank > 0 and partner.customer_rank == 0) or \
                       (partner.customer_rank > 0 and partner.supplier_rank > 0):
                        valid_partners |= partner
                if valid_partners:
                    valid_partners.action_export_to_cs_cart()
                    log_messages.append(f"Partners: {len(valid_partners)} exported.")
                else:
                    log_messages.append("Partners: No partners to export.")

            if self.sync_orders:
                orders = self.env['sale.order'].search([('cs_cart_order_id', '=', False)])
                if orders:
                    orders.action_export_to_cs_cart()
                    log_messages.append(f"Orders: {len(orders)} exported.")
                else:
                    log_messages.append("Orders: No new orders to export.")

            if self.sync_attributes:
                log_messages.append("Attributes export not supported by the connector.")

            self._reset_sync_flags()
            msg = " | ".join(log_messages)
            return self._notify("Export Completed", f"Successfully completed exports: {msg}", reload=True)

        except Exception as e:
            _logger.error("Exception during export: %s", str(e), exc_info=True)
            return self._notify("Export Failed", f"Error: {str(e)}", type="danger", reload=True)
