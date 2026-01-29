# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Ayana KP(odoo@cybrosys.com)
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
from odoo import models, fields


class StockPicking(models.Model):
    """ Inherits the stock.move model to add an image field related to
    the product. """
    _inherit = 'stock.move'

    move_line_image = fields.Binary(
        string="Image", related="product_id.image_1920",
        help="Displays the image of the related product.")


class StockMoveLine(models.Model):
    """ Inherits the stock.move.line model to add several related fields
    for better data representation and usability.  """
    _inherit = 'stock.move.line'

    move_line_image = fields.Binary(
        string="Image", related="product_id.image_1920",
        help="Displays the image of the related product.")
    scheduled_date = fields.Datetime(
        related="picking_id.scheduled_date", store=True,
        help="Scheduled date of the picking.")
    date_done = fields.Datetime(
        related="picking_id.date_done", help="Date when the picking was done.")
    code = fields.Selection(related="picking_id.picking_type_id.code",
        help="Code of the picking type.")
    picking_type_id = fields.Many2one(related="picking_id.picking_type_id",
        store=True, help="Type of the picking.")
    origin = fields.Char( related="picking_id.origin",
        store=True, help="Origin of the picking.")
    reserved_available = fields.Float(
        related="picking_id.move_lines.forecast_availability",
        help="Forecasted availability of the reserved items in the picking.")
    date_deadline = fields.Datetime(related="picking_id.date_deadline",
        string="Deadline", help="Deadline for the picking.")
    product_category_name = fields.Char(
        related="product_id.categ_id.complete_name", store=True,
        string="Product Category",help="Category of the product.")
    has_deadline_issue = fields.Boolean(
        string="Is late", related="picking_id.has_deadline_issue",
        help="Indicates if there is a deadline issue with the picking.")
