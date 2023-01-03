# -*- coding: utf-8 -*-
#############################################################################
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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

from odoo import models, fields, api


class StockPicking(models.Model):
    _inherit = 'stock.move'

    move_line_image = fields.Binary(string="Image",
                                    related="product_id.image_1920")


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    move_line_image = fields.Binary(string="Image",
                                    related="product_id.image_1920")
    scheduled_date = fields.Datetime(related="picking_id.scheduled_date", store=True)
    date_done = fields.Datetime(related="picking_id.date_done")
    code = fields.Selection(related="picking_id.picking_type_id.code")
    picking_type_id = fields.Many2one(related="picking_id.picking_type_id", store=True)
    origin = fields.Char(related="picking_id.origin", store=True)
    reserved_available = fields.Float(
        related="picking_id.move_ids.forecast_availability")
    date_deadline = fields.Datetime(related="picking_id.date_deadline",
                                    string="Deadline")
    has_deadline_issue = fields.Boolean(string="Is late",
                                        related="picking_id.has_deadline_issue")
