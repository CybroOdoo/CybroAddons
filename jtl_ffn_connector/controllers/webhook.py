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
from odoo import http
from odoo.http import request

from odoo.addons.web.controllers.home import Home

_logger = logging.getLogger(__name__)


class JtlFfnHome(Home):
    @http.route('/', type='http', auth="none")
    def index(self, s_action=None, **kw):
        code = kw.get('code')
        if code and len(code) > 10 and 'debug' not in kw:
            html = f"""
            <html>
                <head>
                    <title>JTL Auth Code</title>
                    <style>
                        body {{ font-family: sans-serif; background: #f8f9fa; color: #333; text-align: center; padding: 50px; }}
                        .container {{ background: #fff; padding: 30px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); display: inline-block; max-width: 600px; }}
                        .code-box {{ background: #e9ecef; border: 1px solid #ced4da; padding: 15px 30px; font-size: 20px; font-weight: bold; margin: 20px 0; border-radius: 4px; word-break: break-all; }}
                        .help-text {{ color: #6c757d; margin-bottom: 20px; }}
                        a.btn {{ display: inline-block; margin-top: 20px; padding: 10px 20px; background: #714B67; color: #fff; text-decoration: none; border-radius: 4px; font-weight: bold; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h2 style="margin-top: 0; color: #714B67;">JTL FFN Authorization Successful</h2>
                        <p>Your authorization code has been successfully retrieved:</p>
                        <div class="code-box">{code}</div>
                        <p class="help-text">Please copy this code and paste it into the <b>OAuth Auth Code Helper</b> field in your JTL FFN configuration in Odoo.</p>
                        <a class="btn" href="/odoo">Continue to Odoo</a>
                    </div>
                </body>
            </html>
            """
            return request.make_response(html)
        return super().index(s_action, **kw)


class JtlFfnWebhookController(http.Controller):
    """
    Receives inbound webhook events from JTL-FFN.

    FFN posts JSON payloads to this endpoint whenever:
      - Stock levels change at a warehouse
      - An order status changes (confirmed / shipped)
      - A return is registered

    Endpoint: POST /jtl_ffn/webhook/<config_id>
    """

    @http.route(
        '/jtl_ffn/webhook/<int:config_id>',
        type='jsonrpc',
        auth='public',
        methods=['POST'],
        csrf=False,
    )
    def receive_webhook(self, config_id, **kwargs):
        """Entry point for inbound JTL-FFN webhook POST events."""
        config = request.env['jtl.ffn.config'].sudo().browse(config_id)
        if not config.exists() or not config.active:
            _logger.warning("FFN webhook: unknown or inactive config id %d", config_id)
            return {'status': 'ignored'}

        payload = request.get_json_data()
        event   = payload.get('event') or payload.get('eventType') or ''

        _logger.info("FFN webhook received: event=%s config=%s", event, config.name)

        if event in ('stock.updated', 'inventory.updated'):
            self._handle_stock_update(config, payload)

        elif event in ('order.shipped', 'fulfillment.shipped'):
            self._handle_order_shipped(config, payload)

        elif event in ('return.received', 'return.registered'):
            self._handle_return(config, payload)

        elif event in ('order.confirmed', 'fulfillment.confirmed'):
            self._handle_order_confirmed(config, payload)

        return {'status': 'ok'}

    def _handle_stock_update(self, config, payload):
        """Real-time stock push: update Odoo quant immediately."""
        items = payload.get('items') or []
        for item in items:
            sku = item.get('merchantSku') or item.get('sku') or item.get('articleNumber')
            qty = float(item.get('quantity') or 0)
            product = request.env['product.product'].sudo().search(
                [('default_code', '=', sku)], limit=1
            )
            if not product:
                continue
            ffn_wh_id = payload.get('warehouseId')
            ffn_wh    = request.env['jtl.ffn.warehouse'].sudo().search([
                ('config_id',       '=', config.id),
                ('ffn_warehouse_id','=', str(ffn_wh_id)),
            ], limit=1)
            if not ffn_wh:
                continue
            location = ffn_wh.odoo_warehouse_id.lot_stock_id
            quant    = request.env['stock.quant'].sudo().search([
                ('product_id',  '=', product.id),
                ('location_id', '=', location.id),
            ], limit=1)
            current = quant.inventory_quantity if quant else 0.0
            if abs(current - qty) > 0.001:
                request.env['stock.quant'].sudo()._update_available_quantity(
                    product, location, qty - current
                )
        _logger.info("FFN webhook: stock update processed")

    def _handle_order_shipped(self, config, payload):
        """Mark FFN order sync as shipped and store tracking number."""
        ffn_order_id  = str(payload.get('outboundId') or payload.get('fulfillmentOrderId') or payload.get('orderId') or '')
        tracking_no   = payload.get('trackingNumber') or ''
        carrier       = payload.get('carrierName') or ''
        tracking_url  = payload.get('trackingUrl') or ''

        order_sync = request.env['jtl.ffn.order.sync'].sudo().search([
            ('config_id',   '=', config.id),
            ('ffn_order_id','=', ffn_order_id),
        ], limit=1)
        if not order_sync:
            _logger.warning("FFN webhook shipped: no order sync for FFN order %s", ffn_order_id)
            return

        order_sync.write({'push_state': 'shipped'})

        if tracking_no:
            tracking_model = request.env['jtl.ffn.tracking'].sudo()
            existing = tracking_model.search([
                ('order_sync_id',   '=', order_sync.id),
                ('tracking_number', '=', tracking_no),
            ], limit=1)
            if not existing:
                tracking_model.create({
                    'config_id':       config.id,
                    'order_sync_id':   order_sync.id,
                    'sale_order_id':   order_sync.sale_order_id.id,
                    'carrier_name':    carrier,
                    'tracking_number': tracking_no,
                    'tracking_url':    tracking_url,
                })
        _logger.info("FFN webhook: order %s marked shipped, tracking=%s", ffn_order_id, tracking_no)

    def _handle_order_confirmed(self, config, payload):
        """Update order sync state to confirmed when FFN confirms the order."""
        ffn_order_id = str(payload.get('outboundId') or payload.get('fulfillmentOrderId') or payload.get('orderId') or '')
        order_sync   = request.env['jtl.ffn.order.sync'].sudo().search([
            ('config_id',   '=', config.id),
            ('ffn_order_id','=', ffn_order_id),
        ], limit=1)
        if order_sync:
            order_sync.write({'push_state': 'confirmed'})

    def _handle_return(self, config, payload):
        """Inbound return notification — trigger import."""
        request.env['jtl.ffn.return'].sudo()._import_return(config, payload)
        _logger.info("FFN webhook: return %s imported", payload.get('returnId'))
