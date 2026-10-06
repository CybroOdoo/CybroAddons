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
import re
from odoo import models, fields, api
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class JtlFfnProductSync(models.Model):
    """
    Handles:
      1. Exporting Odoo products to JTL-FFN (product catalogue push).
      2. Pulling real-time stock levels from FFN warehouses back into Odoo.
    """
    _name        = 'jtl.ffn.product.sync'
    _description = 'JTL FFN Product & Stock Synchronisation'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name    = 'sku'

    config_id   = fields.Many2one(
        'jtl.ffn.config', string="FFN Profile", required=True, tracking=True,
        help="JTL FFN configuration profile for this product sync."
    )
    product_id  = fields.Many2one(
        'product.product', string="Product", required=True, tracking=True,
        help="Odoo product registered for FFN synchronization."
    )

    ffn_product_id = fields.Char(
        string="FFN Product ID", copy=False, tracking=True,
        help="Unique identifier (JFSKU) assigned to the product in JTL FFN."
    )
    sku            = fields.Char(
        string="SKU / EAN", copy=False, tracking=True,
        help="Merchant SKU or barcode of the product."
    )

    last_pushed   = fields.Datetime(
        string="Last Pushed to FFN", readonly=True, tracking=True,
        help="Timestamp when product data was last pushed to JTL FFN."
    )
    last_pulled   = fields.Datetime(
        string="Last Stock Pull", readonly=True, tracking=True,
        help="Timestamp when stock level was last pulled from JTL FFN."
    )
    sync_state    = fields.Selection([
        ('pending', 'Pending'),
        ('synced',  'Synced'),
        ('error',   'Error'),
    ], default='pending', string="Sync State", tracking=True,
        help="Current synchronization state of the product (Pending, Synced, Error).")
    sync_error    = fields.Char(
        string="Last Sync Error", copy=False, tracking=True,
        help="Error message if the last product sync failed."
    )

    _sql_constraints = [
        ('unique_product_config',
         'unique(config_id, product_id)',
         'This product is already registered under this FFN profile.'),
    ]

    def sync_products_to_ffn(self, config):
        """Export all storable products that have a default_code (SKU) set."""
        products = self.env['product.product'].search([
            ('type',         'in', ['product', 'consu']),
            ('default_code', '!=', False),
            ('active',       '=',  True),
        ])
        pushed = 0
        for product in products:
            with self.env.cr.savepoint():
                try:
                    if product.weight <= 0:
                        raise UserError("Product weight must be greater than 0 to sync with JTL FFN.")
                    self._push_single_product(config, product)
                    pushed += 1
                except Exception as exc:
                    _logger.warning("FFN product push failed for %s: %s", product.default_code, exc)
                    sync_rec = self.search([
                        ('config_id',  '=', config.id),
                        ('product_id', '=', product.id),
                    ], limit=1)
                    vals = {
                        'config_id':       config.id,
                        'product_id':      product.id,
                        'sku':             product.default_code,
                        'sync_state':      'error',
                        'sync_error': str(exc)[:500],
                    }
                    if sync_rec:
                        sync_rec.write(vals)
                    else:
                        self.create(vals)
        _logger.info("JTL-FFN: pushed %d products to %s", pushed, config.name)
        return pushed

    def _find_ffn_product_by_sku(self, config, sku):
        """Search JTL FFN for a product by its merchantSku and return its jfsku."""
        try:
            result = config._api_request('GET', '/v1/products', params={'merchantSku': sku})
            items = result.get('items') or (result if isinstance(result, list) else [])
            for item in items:
                if item.get('merchantSku') == sku:
                    return item.get('jfsku') or item.get('id')
        except Exception as exc:
            _logger.warning("FFN: could not look up product by SKU %s: %s", sku, exc)
        return None

    def _push_single_product(self, config, product):
        """Build FFN product payload and POST/PUT to the API."""
        identifier = {}
        if product.barcode:
            identifier['ean'] = product.barcode

        payload = {
            'merchantSku': product.default_code,
            'name':        product.name,
            'weight':      product.weight,
            'identifier':  identifier,
        }
        if product.description_sale:
            payload['note'] = product.description_sale[:4096]
        sync_rec = self.search([
            ('config_id',  '=', config.id),
            ('product_id', '=', product.id),
        ], limit=1)

        if sync_rec and sync_rec.ffn_product_id:
            try:
                config._api_request(
                    'PATCH',
                    '/v1/products/%s' % sync_rec.ffn_product_id,
                    json=payload,
                )
                sync_rec.write({'last_pushed': fields.Datetime.now(), 'sync_state': 'synced', 'sync_error': False})
                return
            except UserError as exc:
                if 'Products_ProductNotFound' in str(exc) or '404' in str(exc):
                    # Stored JFSKU is stale — look up the real one from JTL by merchantSku
                    _logger.warning(
                        "FFN: stored JFSKU %s not found for SKU %s, looking up real JFSKU...",
                        sync_rec.ffn_product_id, product.default_code,
                    )
                    real_jfsku = self._find_ffn_product_by_sku(config, product.default_code)
                    if real_jfsku:
                        sync_rec.write({'ffn_product_id': real_jfsku})
                        config._api_request(
                            'PATCH',
                            '/v1/products/%s' % real_jfsku,
                            json=payload,
                        )
                        sync_rec.write({'last_pushed': fields.Datetime.now(), 'sync_state': 'synced', 'sync_error': False})
                        _logger.info("FFN: corrected JFSKU to %s for SKU %s", real_jfsku, product.default_code)
                        return
                raise
        else:

            try:
                result = config._api_request('POST', '/v1/products', json=payload)
                ffn_id = result.get('jfsku') or result.get('id') or result.get('productId') or product.default_code
                vals = {
                    'config_id':      config.id,
                    'product_id':     product.id,
                    'sku':            product.default_code,
                    'ffn_product_id': ffn_id,
                    'last_pushed':    fields.Datetime.now(),
                    'sync_state':     'synced',
                    'sync_error':     False,
                }
                if sync_rec:
                    sync_rec.write(vals)
                else:
                    self.create(vals)
            except UserError as exc:
                err_str = str(exc)
                if "Products_DuplicateProduct" in err_str:
                    match = re.search(r'"Jfsku"\s*:\s*"([^"]+)"', err_str)
                    if match:
                        ffn_id = match.group(1)
                        vals = {
                            'config_id':      config.id,
                            'product_id':     product.id,
                            'sku':            product.default_code,
                            'ffn_product_id': ffn_id,
                        }
                        if sync_rec:
                            sync_rec.write(vals)
                        else:
                            sync_rec = self.create(vals)
                        # Retry as PATCH now that we have the ffn_product_id
                        config._api_request(
                            'PATCH',
                            '/v1/products/%s' % ffn_id,
                            json=payload,
                        )
                        sync_rec.write({'last_pushed': fields.Datetime.now(), 'sync_state': 'synced', 'sync_error': False})
                        return
                raise

    def pull_stock_from_ffn(self, config):
        """Fetch stock levels from every mapped FFN warehouse and update Odoo inventory."""
        updated = 0
        for warehouse in config.warehouse_ids.filtered('active'):
            try:
                updated += self._pull_warehouse_stock(config, warehouse)
            except Exception as exc:
                _logger.error(
                    "FFN stock pull failed for warehouse %s: %s",
                    warehouse.ffn_warehouse_id, exc,
                )
        return updated

    def _pull_warehouse_stock(self, config, ffn_warehouse):
        """Pull stock for one FFN warehouse and reconcile with Odoo quants."""
        data = config._api_request(
            'GET',
            '/v1/stocks/warehouse/%s' % ffn_warehouse.ffn_warehouse_id,
        )
        items = data.get('items') or data.get('inventory') or []
        updated = 0

        odoo_location = ffn_warehouse.odoo_warehouse_id.lot_stock_id

        for item in items:
            sku      = item.get('merchantSku') or item.get('sku') or item.get('articleNumber')
            qty      = float(item.get('stockLevel') or item.get('quantity') or item.get('stock') or 0)
            product  = self.env['product.product'].search(
                [('default_code', '=', sku)], limit=1
            )
            if not product:
                _logger.debug("FFN stock: no Odoo product for SKU %s", sku)
                continue

            snap = self.env['jtl.ffn.stock.line'].search([
                ('warehouse_id', '=', ffn_warehouse.id),
                ('product_id',   '=', product.id),
            ], limit=1)
            snap_vals = {
                'warehouse_id': ffn_warehouse.id,
                'product_id':   product.id,
                'sku':          sku,
                'ffn_quantity': qty,
                'last_updated': fields.Datetime.now(),
            }
            if snap:
                snap.write(snap_vals)
            else:
                self.env['jtl.ffn.stock.line'].create(snap_vals)

            quant = self.env['stock.quant'].search([
                ('product_id',  '=', product.id),
                ('location_id', '=', odoo_location.id),
            ], limit=1)
            current_qty = quant.inventory_quantity if quant else 0.0
            if abs(current_qty - qty) > 0.001:
                self.env['stock.quant']._update_available_quantity(
                    product, odoo_location, qty - current_qty
                )
                updated += 1
            
            sync_rec = self.env['jtl.ffn.product.sync'].search([
                ('config_id', '=', config.id),
                ('product_id', '=', product.id)
            ], limit=1)
            if sync_rec:
                sync_rec.write({'last_pulled': fields.Datetime.now()})

        ffn_warehouse.write({'last_sync': fields.Datetime.now()})
        return updated

    @api.model
    def cron_sync_all(self):
        """Called by the scheduled action — loops all active profiles."""
        for config in self.env['jtl.ffn.config'].search([('active', '=', True)]):
            if config.sync_products:
                self.sync_products_to_ffn(config)
            if config.sync_stock:
                self.pull_stock_from_ffn(config)

    def action_sync_all(self):
        self.cron_sync_all()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Product Sync Register',
            'res_model': 'jtl.ffn.product.sync',
            'view_mode': 'list,form',
            'target': 'current',
        }

