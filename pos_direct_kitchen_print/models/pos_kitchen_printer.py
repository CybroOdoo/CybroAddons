# -*- coding: utf-8 -*-
###############################################################################
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
###############################################################################
from odoo import api, fields, models


class PosKitchenPrinter(models.Model):
    """Model to define kitchen printers and their product categories."""
    _name = "pos.kitchen.printer"
    _description = "POS Kitchen Printer"

    name = fields.Char(string="Printer Name", required=True)
    printer_id = fields.Many2one('printer.details', string="PrintNode Printer", required=True)
    pos_config_ids = fields.Many2many('pos.config', string="Allowed POS",
                                      help="Select restaurant POS session to be chosen", required=True,
                                      domain=[('module_pos_restaurant', '=', True)])
    category_ids = fields.Many2many('pos.category', string="Product Categories", help='Choose categories',
                                    domain="[('id', 'in', allowed_pos_category_ids)]")
    allowed_pos_category_ids = fields.Many2many('pos.category', compute='_compute_allowed_pos_category_ids',
                                                help="Technical field to compute allowed categories based on POS")

    @api.depends('pos_config_ids')
    def _compute_allowed_pos_category_ids(self):
        """Restrict categories by selected POS"""
        for record in self:
            if not record.pos_config_ids:
                record.allowed_pos_category_ids = self.env['pos.category']
                continue

            if any(not config.limit_categories for config in record.pos_config_ids):
                record.allowed_pos_category_ids = self.env['pos.category'].search([])
            else:
                record.allowed_pos_category_ids = record.pos_config_ids.mapped('iface_available_categ_ids')
