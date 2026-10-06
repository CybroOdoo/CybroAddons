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
from odoo import models, fields

_logger = logging.getLogger(__name__)


class JtlFfnWarehouse(models.Model):
    """
    Maps an Odoo warehouse to a JTL-FFN fulfillment location / partner.

    One JtlFfnConfig can have many warehouses, allowing orders to be
    routed to different fulfillment centers based on configurable rules.
    """
    _name        = 'jtl.ffn.warehouse'
    _description = 'JTL FFN Fulfillment Warehouse Mapping'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order       = 'sequence, id'

    config_id = fields.Many2one(
        'jtl.ffn.config', string="FFN Profile",
        required=True, ondelete='cascade', index=True, tracking=True,
        help="JTL FFN configuration profile associated with this warehouse mapping."
    )
    name = fields.Char(
        string="Mapping Name", required=True, tracking=True,
        help="Descriptive name for this warehouse mapping."
    )

    odoo_warehouse_id = fields.Many2one(
        'stock.warehouse', string="Odoo Warehouse", required=True, tracking=True,
        help="Corresponding Odoo stock warehouse."
    )

    ffn_warehouse_id   = fields.Char(
        string="FFN Warehouse ID", required=True, tracking=True,
        help="Unique identifier of the warehouse in JTL FFN."
    )
    ffn_warehouse_name = fields.Char(
        string="FFN Warehouse Name", tracking=True,
        help="Name of the warehouse in JTL FFN."
    )

    is_default = fields.Boolean(
        string="Default Warehouse",
        help="Orders not matching any other rule are sent to this warehouse.", tracking=True
    )
    sequence = fields.Integer(
        string="Sequence", default=10, tracking=True,
        help="Priority sequence used for warehouse routing."
    )

    route_country_ids = fields.Many2many(
        'res.country', string="Route for Countries",
        help="If set, orders shipping to these countries go to this warehouse.", tracking=True
    )

    active = fields.Boolean(
        default=True, tracking=True,
        help="Set to false to deactivate this warehouse mapping."
    )
    last_sync = fields.Datetime(
        string="Last Stock Sync", readonly=True, tracking=True,
        help="Timestamp when stock was last synchronized for this warehouse."
    )
    stock_line_ids = fields.One2many(
        'jtl.ffn.stock.line', 'warehouse_id', string="Current Stock Snapshot",
        help="Snapshot lines of stock levels reported by JTL FFN."
    )

    _sql_constraints = [
        ('unique_ffn_warehouse_per_config',
         'unique(config_id, ffn_warehouse_id)',
         'This FFN Warehouse ID is already mapped under this profile.'),
    ]



class JtlFfnStockLine(models.Model):
    """
    Snapshot of stock levels per SKU as reported by FFN.
    Updated each time a stock pull runs.
    """
    _name        = 'jtl.ffn.stock.line'
    _description = 'JTL FFN Stock Snapshot Line'

    warehouse_id  = fields.Many2one(
        'jtl.ffn.warehouse', ondelete='cascade', index=True,
        help="Fulfillment warehouse associated with this stock snapshot line."
    )
    product_id    = fields.Many2one(
        'product.product', string="Product",
        help="Odoo product corresponding to this stock line."
    )
    sku           = fields.Char(
        string="SKU",
        help="Stock keeping unit (SKU) of the product."
    )
    ffn_quantity  = fields.Float(
        string="FFN Reported Qty", digits=(16, 2),
        help="Stock quantity reported by JTL FFN for this product."
    )
    last_updated  = fields.Datetime(
        string="Last Updated",
        help="Timestamp when this stock line was last updated."
    )
