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
import dateutil.parser
import pytz
from odoo import models, fields, api
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


def _parse_iso_date(date_str):
    """Convert an ISO-8601 string (with optional timezone/milliseconds) to
    a naive UTC datetime string that Odoo's Datetime field accepts.
    Returns None if the value is falsy or unparseable."""
    if not date_str:
        return None
    try:
        dt = dateutil.parser.parse(str(date_str))
        # Normalise to UTC, then strip tzinfo so Odoo stores it as-is
        return dt.astimezone(pytz.utc).replace(tzinfo=None).strftime('%Y-%m-%d %H:%M:%S')
    except Exception:
        return None


class JtlFfnReturn(models.Model):
    """
    Pulls return / reverse-logistics data from JTL-FFN and:
      - Creates a stock return picking in Odoo.
      - Restocks inventory at the correct location.
      - Links the return back to the originating sale order.
    """
    _name        = 'jtl.ffn.return'
    _description = 'JTL FFN Returns Management'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name    = 'name'

    name = fields.Char(
        string="Return Reference", copy=False,
        readonly=True, default='New', tracking=True,
        help="Reference code of the return entry."
    )

    config_id     = fields.Many2one(
        'jtl.ffn.config', string="FFN Profile", tracking=True,
        help="JTL FFN configuration profile associated with this return."
    )
    order_sync_id = fields.Many2one(
        'jtl.ffn.order.sync', string="Original Order Sync", tracking=True,
        help="Original order sync record corresponding to this return."
    )
    sale_order_id = fields.Many2one(
        'sale.order', string="Sale Order", tracking=True,
        help="Original sale order linked to this return."
    )

    ffn_return_id  = fields.Char(
        string="FFN Return ID", tracking=True,
        help="Unique identifier of the return in JTL FFN."
    )
    ffn_order_id   = fields.Char(
        string="FFN Order ID (original)", tracking=True,
        help="Original FFN order ID for this return."
    )
    return_date    = fields.Datetime(
        string="Return Date", tracking=True,
        help="Date and time when the return was registered or created in FFN."
    )
    return_reason  = fields.Char(
        string="Return Reason", tracking=True,
        help="Reason given for the return."
    )

    line_ids       = fields.One2many(
        'jtl.ffn.return.line', 'return_id', string="Return Lines",
        help="Detailed product line items included in this return."
    )

    state = fields.Selection([
        ('new',      'Received from FFN'),
        ('pending',  'Pending Review'),
        ('restocked','Restocked in Odoo'),
        ('cancelled','Cancelled'),
    ], default='new', string="State", compute="_compute_state", store=True, readonly=False, tracking=True,
        help="Processing state of the return (Received from FFN, Pending Review, Restocked in Odoo, Cancelled).")

    odoo_return_picking_id = fields.Many2one(
        'stock.picking', string="Odoo Return Picking", readonly=True, tracking=True,
        help="Incoming stock picking created in Odoo to receive returned items."
    )

    @api.depends('odoo_return_picking_id', 'odoo_return_picking_id.state')
    def _compute_state(self):
        for record in self:
            if record.odoo_return_picking_id:
                if record.odoo_return_picking_id.state == 'done':
                    record.state = 'restocked'
                elif record.odoo_return_picking_id.state == 'cancel':
                    record.state = 'cancelled'
                else:
                    record.state = 'pending'
            else:
                if not record.state:
                    record.state = 'new'


    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') or vals['name'] == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('jtl.ffn.return') or 'New'
        return super().create(vals_list)

    def pull_returns(self, config):
        """Fetch all returns reported by FFN that haven't been imported yet."""
        data = config._api_request('GET', '/v1/returns')
        returns = data.get('items') or (data if isinstance(data, list) else [])
        imported = 0
        for ret in returns:
            ffn_return_id = ret.get('returnId') or ret.get('id')
            if not ffn_return_id:
                continue
            with self.env.cr.savepoint():
                existing = self.search([
                    ('config_id',    '=', config.id),
                    ('ffn_return_id','=', str(ffn_return_id)),
                ], limit=1)
                if existing:
                    try:
                        existing._update_from_ffn_data(ret)
                    except Exception as exc:
                        _logger.warning("FFN return update failed for %s: %s", ffn_return_id, exc)
                    continue
                try:
                    self._import_return(config, ret)
                    imported += 1
                except Exception as exc:
                    _logger.warning("FFN return import failed for %s: %s", ffn_return_id, exc)
        return imported

    def _import_return(self, config, ret_data):
        """Create an Odoo return record and corresponding stock picking."""
        ffn_return_id = str(ret_data.get('returnId') or ret_data.get('id'))
        lines_data    = ret_data.get('lines') or ret_data.get('items') or []
        first_item    = lines_data[0] if lines_data else {}
        reason        = first_item.get('reason') or ''

        ffn_order_id  = str(
            ret_data.get('outboundId') or
            ret_data.get('fulfillmentOrderId') or
            ret_data.get('orderId') or
            first_item.get('outboundId') or ''
        )

        mod_info        = ret_data.get('modificationInfo') or {}
        return_date_raw = mod_info.get('createdAt') or ret_data.get('returnedAt') or ret_data.get('returnDate')
        return_date     = _parse_iso_date(return_date_raw)

        order_sync = False
        ret_jfsku  = first_item.get('jfsku')
        if ret_jfsku:
            order_sync = self.env['jtl.ffn.order.sync'].search([
                ('config_id', '=', config.id),
                ('ffn_jfsku', 'like', ret_jfsku),
            ], limit=1)

        if not order_sync and ffn_order_id:
            order_sync = self.env['jtl.ffn.order.sync'].search([
                ('config_id',   '=', config.id),
                ('ffn_order_id','=', ffn_order_id),
            ], limit=1)

        if not order_sync and ffn_order_id:
            sale_order = self.env['sale.order'].search([
                ('name', '=', ffn_order_id),
            ], limit=1)
            if sale_order:
                order_sync = self.env['jtl.ffn.order.sync'].search([
                    ('config_id',     '=', config.id),
                    ('sale_order_id', '=', sale_order.id),
                ], limit=1)
            if not order_sync and sale_order:
                order_sync = self.env['jtl.ffn.order.sync'].new({
                    'config_id':     config.id,
                    'sale_order_id': sale_order.id,
                })
                order_sync.sale_order_id = sale_order

        order_sync_id   = order_sync.id if (order_sync and order_sync._origin) else False
        sale_order_obj  = order_sync.sale_order_id if order_sync else False
        sale_order_id   = sale_order_obj.id if sale_order_obj else False

        return_rec = self.create({
            'config_id':     config.id,
            'order_sync_id': order_sync_id,
            'sale_order_id': sale_order_id,
            'ffn_return_id': ffn_return_id,
            'ffn_order_id':  ffn_order_id,
            'return_date':   return_date,
            'return_reason': reason,
            'state':         'new',
        })

        for line in lines_data:
            sku = line.get('merchantSku') or line.get('sku') or line.get('articleNumber')
            qty = float(line.get('quantity') or 0)
            product = self.env['product.product'].search(
                [('default_code', '=', sku)], limit=1
            )
            self.env['jtl.ffn.return.line'].create({
                'return_id':  return_rec.id,
                'product_id': product.id if product else False,
                'sku':        sku,
                'quantity':   qty,
                'condition':  line.get('condition') or 'unknown',
            })

        if sale_order_id:
            return_rec._create_odoo_return_picking()

        return_rec._update_from_ffn_data(ret_data)
        return return_rec

    def _update_from_ffn_data(self, ret_data):
        """Update existing return state/picking if FFN reports it as Arrived/Completed."""
        self.ensure_one()
        ffn_state = ret_data.get('state')
        item_states = [item.get('state') for item in (ret_data.get('lines') or ret_data.get('items') or [])]
        
        arrived = ffn_state in ('Arrived', 'Completed') or any(s in ('Arrived', 'Completed') for s in item_states)
        
        if arrived and self.odoo_return_picking_id and self.odoo_return_picking_id.state not in ('done', 'cancel'):
            picking = self.odoo_return_picking_id
            picking.action_assign()
            for move in picking.move_ids:
                move.quantity = move.product_uom_qty
                if hasattr(move, 'picked'):
                    move.picked = True
            picking.with_context(skip_backorder=True).button_validate()
            _logger.info("FFN return %s marked as Arrived/Completed in FFN. Auto-validated Odoo picking %s.", self.name, picking.name)

    def _create_odoo_return_picking(self):
        """Create a return (incoming) picking to restock returned items."""
        self.ensure_one()
        sale_order = self.sale_order_id
        if not sale_order:
            return

        orig_picking = self.env['stock.picking'].search([
            ('sale_id',           '=', sale_order.id),
            ('picking_type_code', '=', 'outgoing'),
            ('state',             '=', 'done'),
        ], limit=1)
        if not orig_picking:
            _logger.warning("FFN return: no done outgoing picking for %s", sale_order.name)
            self.write({'state': 'pending'})
            return

        return_wiz = self.env['stock.return.picking'].with_context(
            active_id=orig_picking.id,
            active_model='stock.picking',
        ).create({'picking_id': orig_picking.id})

        for wiz_line in return_wiz.product_return_moves:
            for ret_line in self.line_ids:
                if wiz_line.product_id.default_code == ret_line.sku:
                    wiz_line.write({'quantity': ret_line.quantity})

        result       = return_wiz._create_returns()
        new_picking  = self.env['stock.picking'].browse(result[0])
        self.write({
            'odoo_return_picking_id': new_picking.id,
        })
        _logger.info(
            "FFN return %s → Odoo picking %s created",
            self.ffn_return_id, new_picking.name,
        )

    def action_view_picking(self):
        """Open the associated Odoo return stock picking in form view."""
        self.ensure_one()
        if not self.odoo_return_picking_id:
            raise UserError("No return picking has been created yet.")
        return {
            'type':      'ir.actions.act_window',
            'res_model': 'stock.picking',
            'res_id':    self.odoo_return_picking_id.id,
            'view_mode': 'form',
        }

    @api.model
    def cron_pull_returns(self):
        """Scheduled action entry point - pull returns for all active FFN profiles."""
        for config in self.env['jtl.ffn.config'].search([
            ('active',       '=', True),
            ('sync_returns', '=', True),
        ]):
            self.pull_returns(config)

    def action_sync_all(self):
        self.cron_pull_returns()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Returns',
            'res_model': 'jtl.ffn.return',
            'view_mode': 'list,form',
            'target': 'current',
        }



class JtlFfnReturnLine(models.Model):
    _name        = 'jtl.ffn.return.line'
    _description = 'JTL FFN Return Line'

    return_id  = fields.Many2one(
        'jtl.ffn.return', ondelete='cascade',
        help="Parent FFN return record."
    )
    product_id = fields.Many2one(
        'product.product', string="Product",
        help="Returned Odoo product."
    )
    sku        = fields.Char(
        string="SKU",
        help="Stock keeping unit (SKU) of returned item."
    )
    quantity   = fields.Float(
        string="Returned Qty",
        help="Quantity of items returned."
    )
    condition  = fields.Char(
        string="Condition",
        help="Condition of returned item (e.g. good, damaged)."
    )
