# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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

from odoo import fields, models


class MrpProduction(models.Model):
    """
    Inherited model for Manufacturing Orders.
    Adds reference fields linking back to the originating POS Order and Line.
    """
    _inherit = 'mrp.production'

    pos_order_id = fields.Many2one(
        'pos.order',
        string="POS Order",
        readonly=True,
        copy=False,
        help="POS Order that triggered the automated creation of this MO.",
    )
    pos_order_line_id = fields.Many2one(
        'pos.order.line',
        string="POS Order Line",
        readonly=True,
        copy=False,
        help="POS Order line that triggered this MO.",
    )
