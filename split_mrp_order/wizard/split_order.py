# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Saneen K(<https://www.cybrosys.com>)
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
#############################################################################
import math
import re

from odoo import Command, fields, models
from odoo.exceptions import ValidationError


class SplitOrder(models.TransientModel):
    """New transient model for Split manufacture order by different methods"""
    _name = 'split.order'
    _description = "Split Orders"

    splitting_method = fields.Selection([
        ('by_no_of_quantity', 'By Number of Quantity'),
        ('by_no_of_split', 'By Number of Split'),
        ('split_manually', 'Split Manually')], string="Splitting Method",
        required=True, help="To select splitting method",
        default="by_no_of_quantity")
    no_of_quantity = fields.Integer(string="No of Quantity",
                                    help="Number of quantity splitting")
    no_of_split = fields.Integer(string="No of Split",
                                 help="Number of splits quantity")
    order_id = fields.Many2one('mrp.production', string="Order",
                               help="Manufacturing production order")
    split_manually = fields.Char(string="Splitting Quantities",
                                 help="Can split mrp manually")
    work_center_id = fields.Many2one('mrp.workcenter',
                                     string="Work Center",
                                     required=True, help="work center")
    works = fields.Boolean(string="Works", copy=False,
                           help="For visible work center on wizard")

    def action_split_done(self):
        """ Split by no of quantity,If no of quantity
         is greater than product quantity no action required."""
        vals = {
            'workcenter_id': self.work_center_id.id,
            'product_uom_id': self.order_id.product_uom_id.id,
            'name': self.work_center_id.name,
        }
        order = self.order_id
        qty = order.product_qty
        no_qty = self.no_of_quantity
        no_split = self.no_of_split
        manually = self.split_manually
        if qty > 1 and no_qty:
            if no_qty > qty:
                raise ValidationError("Choose Valid Quantity")
            elif no_qty == qty:
                return False
            else:
                if order.move_raw_ids and not order.bom_id:
                    move_raw_ids_list = []
                    for res in order.move_raw_ids:
                        uom = math.floor(
                            ((1 / qty) * (qty - no_qty)) * res.product_uom_qty)
                        by_product_uom = res.product_uom_qty - uom
                        components = {
                            'product_id': res.product_id.id,
                            'product_uom_qty': uom
                        }
                        res.update(components)
                        move_raw_ids_list.append({
                            'product_id': res.product_id.id,
                            'name': res.product_id.name,
                            'product_uom': res.product_id.uom_id.id,
                            'location_id': order.location_src_id.id,
                            'location_dest_id': order.location_dest_id.id,
                            'product_uom_qty': abs(by_product_uom)
                        })
                    self.env['mrp.production'].create({
                        'product_qty': no_qty,
                        'product_id': order.product_id.id,
                        'product_uom_id': order.product_uom_id.id,
                        'move_raw_ids': [Command.create(data) for data in
                                         move_raw_ids_list],
                    })
                    order.write(
                        {
                            'product_qty': qty - no_qty,
                            'workorder_ids': [Command.create(vals)]
                        })
                else:
                    order.write(
                        {
                            'product_qty': qty - no_qty,
                            'workorder_ids': [Command.create(vals)]
                        })
                    self.env['mrp.production'].sudo().create({
                        'product_qty': no_qty,
                        'product_id': order.product_id.id,
                        'product_uom_id': order.product_uom_id.id,
                    })
        """Split manufacture order by no of splits,If no of quantity
         is greater than product quantity no action required."""
        if qty > 1 and no_split:
            if no_split > qty:
                raise ValidationError("Choose Valid Quantity")
            elif no_split == qty:
                return False
            else:
                split = qty // no_split
                reminder = qty % no_split
                value = qty - reminder
                if order.move_raw_ids and not order.bom_id:
                    if value == 0:
                        return False
                    else:
                        for val in range(int(split)):
                            move_raw_ids_list = []
                            for rec in order.move_raw_ids:
                                if no_split != 0:
                                    by_product_split = rec.product_uom_qty // no_split
                                    by_product_reminder = rec.product_uom_qty % no_split
                                    by_product_value = rec.product_uom_qty - by_product_reminder
                                    if by_product_split != 0:
                                        by_product_split_qty = by_product_value // by_product_split
                                        move_raw_ids_list.append({
                                            'product_id': rec.product_id.id,
                                            'name': rec.product_id.name,
                                            'product_uom': rec.product_id.uom_id.id,
                                            'location_id': order.location_src_id.id,
                                            'location_dest_id': order.location_dest_id.id,
                                            'product_uom_qty': by_product_split_qty
                                        })
                                    else:
                                        raise ValidationError(
                                            "Please cross check the quantities"
                                            "of components")
                            self.env[
                                'mrp.production'].create(
                                {
                                    'product_qty': value // split,
                                    'product_id': order.product_id.id,
                                    'product_uom_id': order.product_id.uom_id.id,
                                    'workorder_ids': [Command.create(vals)],
                                    'move_raw_ids': [Command.create(data)
                                                     for data in
                                                     move_raw_ids_list],
                                })
                    if reminder > 0:
                        order.write(
                            {
                                'product_qty': reminder,
                                'workorder_ids': [Command.create(vals)]
                            })
                    else:
                        order.unlink()
                else:
                    split = qty // no_split
                    reminder = qty % no_split
                    value = qty - reminder
                    if value == 0:
                        return False
                    else:
                        for val in range(int(split)):
                            create_mo_split = self.env['mrp.production'].create(
                                {
                                    'product_qty': value // split,
                                    'product_id': order.product_id.id,
                                    'product_uom_id': order.product_uom_id.id
                                })
                            create_mo_split.write(
                                {'workorder_ids': [Command.create(vals)]})
                    if reminder > 0:
                        order.write(
                            {
                                'product_qty': reminder,
                                'workorder_ids': [Command.create(vals)]
                            })
                    else:
                        order.unlink()
        """ Split manufacture order by Manually"""
        if qty > 1 and manually:
            split_value = manually.split(",")
            split_sum = 0
            val = []
            split_manually = self.split_manually
            pattern = r'^[\d,]+$'
            validation = re.match(pattern, split_manually) is not None
            if validation:
                for rec in split_value:
                    if rec != '':
                        split_sum += int(rec)
                        val.append(int(rec))
                    for record in val:
                        if record == 0:
                            val.remove(0)
                if split_sum != qty or split_sum == 0:
                    raise ValidationError("Choose Valid Quantity. The "
                                          "split quantities are not "
                                          "matched with the required quantity"
                                          "for MO.")
                if order.move_raw_ids and not order.bom_id:
                    for rec in val:
                        move_raw_ids_list = []
                        for line in order.move_raw_ids:
                            move_raw_ids_list.append({
                                'product_id': line.product_id.id,
                                'name': line.product_id.name,
                                'product_uom': line.product_id.uom_id.id,
                                'location_id': order.location_src_id.id,
                                'location_dest_id': order.location_dest_id.id,
                                'product_uom_qty': round(
                                    (1 / split_sum) * line.product_uom_qty * rec)
                            })
                        self.env['mrp.production'].create({
                            'product_qty': int(rec),
                            'product_id': order.product_id.id,
                            'product_uom_id': order.product_id.uom_id.id,
                            'move_raw_ids': [Command.create(data) for data in
                                             move_raw_ids_list],
                        })
                    order.unlink()
                else:
                    order.write(
                        {
                            'product_qty': int(val[0]),
                            'workorder_ids': [Command.create(vals)],
                        })
                    val.pop(0)
                    for rec in val:
                        self.env['mrp.production'].create({
                            'product_qty': int(rec),
                            'product_id': order.product_id.id,
                            'product_uom_id': order.product_uom_id.id
                        })
            else:
                raise ValidationError("Enter the correct value")
