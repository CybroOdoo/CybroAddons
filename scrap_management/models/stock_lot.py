# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Shafna K(odoo@cybrosys.com)
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
import datetime
from odoo import api, fields, models


class StockLot(models.Model):
    """To add fields in stock lot and compute move date"""
    _inherit = "stock.lot"

    move_date = fields.Datetime(string="Move Date",
                                help="Date which product need to be moved to "
                                     "scrap", compute='_compute_move_date')
    move_scrap = fields.Boolean(string="Move To Scrap",
                                help="Enable to automatically move product to "
                                     "scrap based on expiry date",
                                compute='_compute_move_scrap')

    @api.depends('product_id', 'expiration_date', 'move_scrap')
    def _compute_move_date(self):
        """Compute function to calculate the date of moving to scrap based on
        expiration date and days given in configuration settings"""
        self.move_date = False
        for rec in self:
            if rec.product_id.use_expiration_date:
                move_days = self.env['ir.config_parameter'].sudo().get_param(
                    'scrap_management.move_to_scrap_days')
                if not rec.product_id.use_expiration_date and not \
                        rec.move_scrap and rec.product_qty <= 0:
                    rec.move_date = False
                elif rec.expiration_date and rec.move_scrap and \
                        rec.product_qty > 0:
                    rec.move_date = rec.expiration_date + datetime.timedelta(
                        days=int(move_days))

    def _compute_move_scrap(self):
        """Compute function to get the value of boolean field whether move to
        scrap based on expiration date or not"""
        for rec in self:
            rec.move_scrap = rec.env['ir.config_parameter'].sudo().get_param(
                'scrap_management.move_to_scrap')

    def action_scrap_order(self):
        """To create a scrap order automatically when product is expired"""
        today_start = fields.Date.start_of(fields.Datetime.today(), 'day')
        today_end = fields.Date.end_of(fields.Datetime.today(), 'day')
        for rec in self.env['stock.lot'].search([]):
            if rec.expiration_date and rec.move_date:
                expiry_date = rec.filtered(
                    lambda date: today_start <= date.move_date <= today_end)
                for recs in expiry_date:
                    self.env['stock.scrap'].create({
                        'product_id': recs.product_id.id,
                        'lot_id': recs.id,
                        'scrap_qty': recs.product_qty,
                    })
