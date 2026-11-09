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
    """Inheriting the model account.move"""
    _inherit = 'account.move'

    picking_id = fields.Many2one('stock.picking', string='Picking',
                                 help='Related picking for this accounting '
                                      'entry')
    transfer_ids = fields.Many2many('stock.picking', string='Transfers',
                                    help='Related transfers for this accounting'
                                         ' entry')
