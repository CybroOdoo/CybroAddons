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
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class JtlFfnTracking(models.Model):
    """
    Pulls shipment tracking numbers from FFN and writes them onto the
    corresponding Odoo stock.picking (delivery order).
    Also triggers the customer notification email when available.
    """
    _name        = 'jtl.ffn.tracking'
    _description = 'JTL FFN Shipment Tracking'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name           = fields.Char(
        string='Reference', required=True, copy=False, readonly=True, default=lambda self: 'New', tracking=True,
        help="Reference code for this tracking entry."
    )
    config_id      = fields.Many2one(
        'jtl.ffn.config', string="FFN Profile", tracking=True,
        help="JTL FFN configuration profile associated with this shipment."
    )
    order_sync_id  = fields.Many2one(
        'jtl.ffn.order.sync', string="FFN Order Sync", tracking=True,
        help="FFN order sync log record associated with this tracking entry."
    )
    sale_order_id  = fields.Many2one(
        'sale.order', string="Sale Order", tracking=True,
        help="Originating sale order for this tracking record."
    )
    picking_id     = fields.Many2one(
        'stock.picking', string="Delivery Order", tracking=True,
        help="Associated Odoo delivery picking."
    )

    ffn_shipment_id  = fields.Char(
        string="FFN Shipment ID", tracking=True,
        help="Shipment notification ID provided by JTL FFN."
    )
    carrier_name     = fields.Char(
        string="Carrier", tracking=True,
        help="Name of the shipping carrier."
    )
    tracking_number  = fields.Char(
        string="Tracking Number", tracking=True,
        help="Shipment tracking number."
    )
    tracking_url     = fields.Char(
        string="Tracking URL", tracking=True,
        help="URL to track the parcel package online."
    )
    shipped_at       = fields.Datetime(
        string="Shipped At", tracking=True,
        help="Timestamp when the parcel was shipped."
    )
    imported_at      = fields.Datetime(
        string="Imported At", default=fields.Datetime.now, tracking=True,
        help="Timestamp when tracking info was imported into Odoo."
    )

    state = fields.Selection([
        ('new',      'New'),
        ('applied',  'Applied to Delivery'),
        ('notified', 'Customer Notified'),
    ], default='new', string="State", tracking=True,
        help="State of the tracking record (New, Applied to Delivery, Customer Notified).")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('jtl.ffn.tracking') or 'New'
        return super().create(vals_list)

    def pull_tracking_numbers(self, config):
        """Query FFN for all shipped orders and write tracking info back to Odoo."""
        pending_syncs = self.env['jtl.ffn.order.sync'].search([
            ('config_id',  '=', config.id),
            ('push_state', 'in', ['sent', 'confirmed']),
            ('ffn_order_id', '!=', False),
        ])
        imported = 0
        for sync in pending_syncs:
            with self.env.cr.savepoint():
                try:
                    imported += self._fetch_and_apply_tracking(config, sync)
                except Exception as exc:
                    _logger.warning(
                        "FFN tracking fetch failed for FFN order %s: %s",
                        sync.ffn_order_id, exc,
                    )
        return imported

    def _fetch_and_apply_tracking(self, config, order_sync):
        """Fetch tracking for one FFN order and write it to Odoo."""
        data = config._api_request(
            'GET',
            '/v1/outbounds/%s/shipping-notifications' % order_sync.ffn_order_id,
        )
        # JTL returns a bare list [] OR a dict with a key — handle both
        if isinstance(data, list):
            shipments = data
        else:
            shipments = data.get('shippingNotifications') or data.get('shipments') or []

        applied = 0
        for shipment in shipments:
            tracking_no  = shipment.get('trackingNumber') or shipment.get('tracking_number')
            carrier      = shipment.get('carrierName')    or shipment.get('carrier')
            tracking_url = shipment.get('trackingUrl')    or ''
            shipped_at   = shipment.get('shippedAt')      or shipment.get('shipped_at')
            # Use outboundShippingNotificationId as primary key (tracking may be absent in sandbox)
            ffn_ship_id  = (
                shipment.get('outboundShippingNotificationId')
                or shipment.get('shipmentId')
                or shipment.get('id')
            )

            # Skip if we have neither a tracking number nor a notification ID to identify this shipment
            if not tracking_no and not ffn_ship_id:
                _logger.info(
                    "FFN: shipment for order %s has no tracking number or notification ID — skipped",
                    order_sync.ffn_order_id,
                )
                continue

            # De-duplicate using the notification ID (works even without tracking number)
            existing = self.search([
                ('order_sync_id',  '=', order_sync.id),
                ('ffn_shipment_id', '=', ffn_ship_id),
            ], limit=1)
            if existing:
                continue

            picking = self.env['stock.picking'].search([
                ('sale_id', '=', order_sync.sale_order_id.id),
                ('picking_type_code', '=', 'outgoing'),
                ('state', 'not in', ['done', 'cancel']),
            ], limit=1)

            rec = self.create({
                'config_id':       config.id,
                'order_sync_id':   order_sync.id,
                'sale_order_id':   order_sync.sale_order_id.id,
                'picking_id':      picking.id if picking else False,
                'ffn_shipment_id': ffn_ship_id,
                'carrier_name':    carrier or '',
                'tracking_number': tracking_no or '',
                'tracking_url':    tracking_url,
                'shipped_at':      shipped_at,
                'state':           'new',
            })

            if picking:
                write_vals = {}
                if tracking_no:
                    write_vals['carrier_tracking_ref'] = tracking_no
                if carrier:
                    write_vals['carrier_id'] = self._find_or_create_carrier(carrier)
                if write_vals:
                    picking.write(write_vals)
                if picking.state in ['confirmed', 'assigned']:
                    picking.with_context(skip_backorder=True).button_validate()
                rec.write({'state': 'applied'})

            order_sync.write({'push_state': 'shipped'})
            applied += 1
            _logger.info(
                "FFN: shipment %s (tracking: %s) applied to picking %s",
                ffn_ship_id, tracking_no or 'N/A', picking.name if picking else 'N/A',
            )
        return applied

    def _find_or_create_carrier(self, carrier_name):
        """Look up a delivery carrier by name, creating a stub if not found."""
        if not carrier_name:
            return False
        carrier = self.env['delivery.carrier'].search(
            [('name', 'ilike', carrier_name)], limit=1
        )
        if carrier:
            return carrier.id
        new_carrier = self.env['delivery.carrier'].create({
            'name':            carrier_name,
            'delivery_type':   'fixed',
            'product_id':      self.env.ref('delivery.product_product_delivery').id,
        })
        return new_carrier.id

    @api.model
    def cron_pull_tracking(self):
        """Scheduled action entry point - pull tracking numbers for all active FFN profiles."""
        for config in self.env['jtl.ffn.config'].search([
            ('active',        '=', True),
            ('sync_tracking', '=', True),
        ]):
            self.pull_tracking_numbers(config)

    def action_sync_all(self):
        self.cron_pull_tracking()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Shipment Tracking',
            'res_model': 'jtl.ffn.tracking',
            'view_mode': 'list,form',
            'target': 'current',
        }

