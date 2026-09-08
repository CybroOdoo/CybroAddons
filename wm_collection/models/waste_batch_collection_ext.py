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
#    If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import fields, models


class WasteBatch(models.Model):
    """Extends Waste Batch with collection route linkage and batch intake tracking."""
    _inherit = 'waste.batch'

    collection_order_id = fields.Many2one(
        'wm.collection.order', string='Collection Order', tracking=True,
        help='The source Collection Order from which this waste batch was generated.')
    route_id = fields.Many2one(
        'wm.route', string='Collection Route', tracking=True,
        help='The source Collection Route from which this waste batch was consolidated.')
    collection_order_ids = fields.Many2many(
        'wm.collection.order', string='Collection Orders',
        help='Collection orders consolidated into this waste batch.')
