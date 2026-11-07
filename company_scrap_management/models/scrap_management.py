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
from odoo import api, fields, models


class ScrapManagement(models.Model):
    """ This class define a new model for scrap management."""
    _name = "scrap.management"
    _description = "Scrap Management"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'scrap_management_number'

    scrap_management_number = fields.Char(
        string="Scrap Number", readonly=True, required=True, copy=False,
        default="New", help="Field to specify sequence number")
    scrap_order_id = fields.Many2one(
        'stock.move', string="Scrap Order", required=True,
        help="Field to choose scrap order",
        domain="[('is_scrap', '=', True),"
               "('state', '=', 'done'),"
               "('typ_of_reuse', '=', 'dismantle'),"
               "('state_management', '=', 'none')]")
    bill_of_material_id = fields.Many2one(
        'mrp.bom', related="scrap_order_id.bill_of_material_id",
        string="Bill of Material", help="Field to choose bill of material")
    product_id = fields.Many2one(
        'product.product',
        string="Product", related="scrap_order_id.product_id",
        help="Field to choose product")
    date = fields.Date(string="Date", help="Field to give the date")
    qty = fields.Float(string="Quantity", related="scrap_order_id.quantity",
                       help="Field to specify quantity")
    scrap_management_line_ids = fields.One2many(
        'scrap.management.line', 'scrap_management_id',
        string="Components", help="Field to specify components")
    location_id = fields.Many2one(
        'stock.location', string="Transfer location",
        domain="[('usage', '=', 'internal')]", required=True,
        help="Field to specify location")
    state = fields.Selection(
        [('draft', 'Draft'), ('confirm', 'Confirm'), ('done', 'Done')],
        string="State", default="draft",
        help="Field to specify state of Scrap Management")

    @api.model_create_multi
    def create(self, vals_list):
        """
           Summary:
               function return sequence number for record
           Args:
               vals_list: To store the sequence created
           return:
                result: return sequence created
         """
        for val in vals_list:
            if val.get('scrap_management_number', 'New') == 'New':
                val['scrap_management_number'] = (
                    self.env['ir.sequence'].next_by_code('scrap.management') or 'New'
                )
        return super().create(vals_list)

    def action_confirm(self):
        """Function to confirm the Scrap Management and add value to one2many"""
        for record in self:
            lines = []
            bom_qty = record.bill_of_material_id.product_qty or 1.0
            for line in record.bill_of_material_id.bom_line_ids:
                if line.product_id.type not in ['combo', 'service']:
                    lines.append((0, 0, {
                        'product_id': line.product_id.id,
                        'dismantle_qty': (record.qty * line.product_qty) / bom_qty
                    }))
            record.write({
                'scrap_management_line_ids': lines,
                'state': "confirm"
            })

    def action_done(self):
        """Function to complete the Scrap Management and
        process stock moves for recovered and scrapped components"""
        for record in self:
            scrap_loc = record.scrap_order_id.location_dest_id
            for line in record.scrap_management_line_ids:
                scrap_qty = line.dismantle_qty - line.useful_qty
                if line.useful_qty > 0:
                    move_vals = {
                        'origin': record.scrap_management_number,
                        'company_id': record.env.company.id,
                        'product_id': line.product_id.id,
                        'uom_id': line.product_id.uom_id.id,
                        'product_uom_qty': line.useful_qty,
                        'location_id': scrap_loc.id,
                        'location_dest_id': record.location_id.id,
                        'move_line_ids': [(0, 0, {
                            'product_id': line.product_id.id,
                            'uom_id': line.product_id.uom_id.id,
                            'quantity': line.useful_qty,
                            'location_id': scrap_loc.id,
                            'location_dest_id': record.location_id.id,
                        })],
                    }
                    move = record.env['stock.move'].create(move_vals)
                    move._action_done()
                if scrap_qty > 0:
                    move_vals = {
                        'origin': record.scrap_management_number,
                        'company_id': record.env.company.id,
                        'product_id': line.product_id.id,
                        'uom_id': line.product_id.uom_id.id,
                        'product_uom_qty': scrap_qty,
                        'location_id': scrap_loc.id,
                        'location_dest_id': scrap_loc.id,
                        'move_line_ids': [(0, 0, {
                            'product_id': line.product_id.id,
                            'uom_id': line.product_id.uom_id.id,
                            'quantity': scrap_qty,
                            'location_id': scrap_loc.id,
                            'location_dest_id': scrap_loc.id,
                        })],
                    }
                    move = record.env['stock.move'].create(move_vals)
                    move._action_done()

            record.write({
                'state': "done"
            })
            record.scrap_order_id.write({
                'state_management': "dismantled"
            })
            record.date = fields.Date.context_today(record)

    def action_product_moves(self):
        """Function to return the product moves"""
        self.ensure_one()
        return {
            'name': "Product Moves",
            'type': 'ir.actions.act_window',
            'view_mode': 'list,form',
            'res_model': 'stock.move.line',
            'domain': [('move_id.origin', '=', self.scrap_management_number)]
        }
