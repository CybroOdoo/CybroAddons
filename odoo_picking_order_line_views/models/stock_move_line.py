# -*- coding: utf-8 -*-
#############################################################################
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
#############################################################################
from odoo import api, fields, models


class StockMoveLine(models.Model):
    """Inherited the class StockMoveLine to add custom fields"""
    _inherit = 'stock.move.line'

    move_line_image = fields.Binary(string="Product Image",
                                    related="product_id.image_1920",
                                    help="Move Line product image")
    scheduled_date = fields.Datetime(related="picking_id.scheduled_date",
                                     string='Scheduled Date', store=True,
                                     help="Scheduled Date for the picking")
    date_done = fields.Datetime(related="picking_id.date_done",
                                string='Effective Date',
                                help="Date for the completed picking")
    code = fields.Selection(related="picking_id.picking_type_id.code",
                            string="Operation",
                            help="Code for the operation")
    picking_type_id = fields.Many2one(related="picking_id.picking_type_id",
                                      compute=None, store=True,
                                      help="Type for the operation")
    origin = fields.Char(compute='_compute_origin', related=None,
                         store=True, help="Source for the operation")
    reserved_available = fields.Float(
        related="move_id.forecast_availability", string="Reserved",
        help="Forecasted availability of the stock move of this line")
    date_deadline = fields.Datetime(related="picking_id.date_deadline",
                                    string="Deadline",
                                    help="Deadline for the operation")
    has_deadline_issue = fields.Boolean(string="Is late",
                                        related="picking_id.has_deadline_issue",
                                        help="The operation deadline")

    @api.depends('picking_id.origin', 'move_id.origin')
    def _compute_origin(self):
        """Use the source document of the picking, or the one of the stock
        move for lines without picking (manufacturing, scrap, ...)."""
        for line in self:
            line.origin = line.picking_id.origin or line.move_id.origin
