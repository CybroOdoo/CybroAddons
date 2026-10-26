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
#############################################################################
from odoo import fields, models


class AccountMove(models.Model):
    """Extension to account.move to track origin picking and return picking."""
    _inherit = 'account.move'

    origin_picking_id = fields.Many2one(
        'stock.picking',
        copy=False,
        help='Original delivery or receipt picking related to this Credit/Debit note.',
    )
    return_picking_id = fields.Many2one(
        'stock.picking',
        copy=False,
        help='Return picking that generated this Credit/Debit note.',
    )
