# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Roopchand P M(<https://www.cybrosys.com>)
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
from odoo import api, fields, models, _


class OrderMrpMerge(models.TransientModel):
    """
    Wizard that allow us to merge mrp orders.
    """
    _name = 'order.mrp.merge'
    _description = 'Merge mrp orders'
    _check_company_auto = True

    def _default_merge_line_ids(self):
        """
        Default record in merge line based on selected mrp orders that help
        us to manage merge quantity.
        """
        order_id = self.env['mrp.production'].browse(
            self.env.context.get('records'))
        order = order_id.mapped('id')
        quantity = sum(order_id.mapped('product_qty'))
        return [(0, 0,
                 {'mrp_merge_order_ids': order,
                  'mrp_product_id': order_id[0].product_id.id,
                  'quantity': quantity
                  })]

    def _get_default_merge_type(self):
        """Default merge type in the wizard that selected in settings"""
        merge_type = self.env['ir.config_parameter'].sudo().get_param(
            'odoo_merge_mrp_orders.merge_mrp_type')
        return merge_type

    def _default_manage_qty(self):
        """Function to get default value of merge quantity from settings."""
        merge_qty = self.env['ir.config_parameter'].sudo().get_param(
            'odoo_merge_mrp_orders.merge_qty')
        return merge_qty

    product_id = fields.Many2one(
        string="Product",
        comodel_name='product.product',
        help='Merge order product'
    )
    bom_id = fields.Many2one(
        string="Bill of material",
        comodel_name='mrp.bom',
        help='Information of merge order bill of material'
    )
    production_ids = fields.Many2many(
        string="Production Orders",
        comodel_name='mrp.production',
        relation='mrp_productions_rel',
        compute='_compute_production_ids',
        help='Field used to return domain for mrp_order_id'
    )
    company_id = fields.Many2one(
        string='Company',
        comodel_name='res.company',
        index=True,
        default=lambda self: self.env.company,
        help='Company associated with the order.'
    )
    merge_mrp_type = fields.Selection(
        string="Merge Type",
        selection=[
            ('order_none', "New order and Do nothing with selected mrp orders"),
            ('order_cancel', "New order and Cancel selected mrp orders"),
            ('order_remove', "New order and Remove selected mrp orders"),
            ('merge_none',
             "Existing order and Do nothing with selected mrp orders"),
            ('merge_cancel', "Existing order and Cancel selected mrp orders"),
            ('merge_remove', "Existing order and Remove selected mrp orders")
        ],
        default=_get_default_merge_type,
        required=True,
        help='Type of merge operation to be performed.'
    )
    component_location_id = fields.Many2one(
        comodel_name='stock.location',
        string="Component Location",
        required=True,
        check_company=True,
        help='Component location for the merge operation'
    )
    component_destination_location_id = fields.Many2one(
        comodel_name='stock.location',
        string="Finished Product Location",
        required=True,
        check_company=True,
        help='Location for the finished product resulting from the merge '
             'operation.'
    )
    mrp_order_id = fields.Many2one(
        comodel_name='mrp.production',
        check_company=True,
        help='Manufacturing order to which the merge operation will be applied.'
    )
    merge_line_ids = fields.One2many(
        string='Merge lines',
        comodel_name='mrp.merge.line',
        inverse_name='merge_order_id',
        default=_default_merge_line_ids,
        help='Merge lines representing merge quantities for specific products.'
    )
    manage_qty = fields.Boolean(
        string='Manage Quantity',
        default=_default_manage_qty,
        help='Determines if merge quantity should be managed.'
    )

    @api.depends('merge_mrp_type')
    def _compute_production_ids(self):
        """
            Compute method for the 'production_ids' field.

            This method is called when the 'merge_mrp_type' field is changed.
            It computes the 'production_ids' based on the selected merge
            type."""
        if self.merge_mrp_type in ['merge_none', 'merge_cancel',
                                   'merge_remove']:
            production_ids = self.env['mrp.production'].search(
                [('product_id', '=', self.product_id.id),
                 ('bom_id', '=', self.bom_id.id),
                 ('state', 'in', ['draft', 'confirmed']),
                 ('id', 'not in', self.env.context.get('records'))
                 ])
            self.production_ids = production_ids
        else:
            self.production_ids = False

    def action_merge(self):
        """Button to merge selected mrp orders."""
        order_ids = self.env['mrp.production'].browse(
            self.env.context.get('records'))
        if self.manage_qty:
            total_quantity = sum(self.merge_line_ids.mapped('quantity'))
            if total_quantity > sum(order_ids.mapped('product_qty')):
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _("User Error"),
                        'type': 'warning',
                        'message': "Merge quantity should be less than equal to"
                                   "order's total quantity",
                        'next': {'type': 'ir.actions.act_window_close'},
                    }
                }
        else:
            total_quantity = sum(order_ids.mapped('product_qty'))
        merge_type = self.merge_mrp_type
        if merge_type in ['order_none', 'order_cancel', 'order_remove']:
            total_quantity = sum(order_ids.mapped('product_qty'))
            location_src_id = self.component_location_id.id
            location_dest_id = self.component_destination_location_id.id
            self.merge_manufacturing_order(order_ids, total_quantity,
                                           location_src_id, location_dest_id)
            if merge_type == 'order_cancel':
                order_ids.action_cancel()
            elif merge_type == 'order_remove':
                order_ids.unlink()
        elif merge_type in ['merge_none', 'merge_cancel', 'merge_remove']:
            total_qty = total_quantity
            self.merge_to_manufacturing_order(total_qty)
            if merge_type == 'merge_cancel':
                order_ids.action_cancel()
            elif merge_type == 'merge_remove':
                order_ids.unlink()

    def merge_manufacturing_order(self, order_ids, total_quantity,
                                  location_src_id, location_dest_id):
        """Creating a new manufacturing order based on selected mrp orders."""
        if self.manage_qty:
            total_quantity = self.merge_line_ids.quantity
        mrp_order = self.env['mrp.production'].create([{
            'product_id': order_ids[0].product_id.id,
            'product_qty': total_quantity,
            'product_uom_qty': total_quantity,
            'qty_produced': total_quantity,
            'product_uom_id': order_ids[0].product_uom_id.id,
            'bom_id': order_ids[0].bom_id.id,
            'origin': order_ids[0].origin,
            'location_src_id': location_src_id,
            'location_dest_id': location_dest_id,
        }])
        mrp_order._compute_product_uom_qty()
        mrp_order._compute_state()
        mrp_order._onchange_product_qty()
        mrp_order._onchange_move_raw()
        mrp_order._onchange_move_finished()
        name = ''
        for value in range(len(order_ids)):
            if value == 0:
                name += order_ids[value].name
            else:
                name += ',' + order_ids[value].name
        if self.notification_in_chatter_check():
            message = _(
                "This mrp order is created from %s") % name
            mrp_order.message_post(body=message)

    def merge_to_manufacturing_order(self, total_qty):
        """Merge the mrp orders to a selected order."""
        self.mrp_order_id.write({
            'product_qty': total_qty + int(self.mrp_order_id.product_qty)
        })
        self.mrp_order_id._compute_product_uom_qty()
        self.mrp_order_id._compute_state()
        self.mrp_order_id._onchange_product_qty()
        self.mrp_order_id._onchange_move_raw()
        self.mrp_order_id._onchange_move_finished()
        order_ids = self.env['mrp.production'].browse(
            self.env.context.get('records'))
        name = ''
        for value in range(len(order_ids)):
            if value == 0:
                name += order_ids[value].name
            else:
                name += ',' + order_ids[value].name
        if self.notification_in_chatter_check():
            message = _(
                "This mrp order is created from %s") % name
            self.mrp_order_id.message_post(body=message)

    def notification_in_chatter_check(self):
        """Check notify in the chatter options is enabled in settings."""
        result = self.env['ir.config_parameter'].sudo().get_param(
            'odoo_merge_mrp_orders.merge_order_notify')
        return result

    @api.onchange('mrp_order_id')
    def _onchange_mrp_order_id(self):
        """
        Update the quantity in merge_line_ids based on the selected
        mrp_order_id.
        """
        order_ids = self.env['mrp.production'].browse(
            self.env.context.get('records'))
        total = sum(order_ids.mapped('product_qty'))
        order = order_ids.mapped('id')

        if self.mrp_order_id and self.merge_mrp_type in ['merge_none',
                                                         'merge_cancel',
                                                         'merge_remove']:
            order += [self.mrp_order_id.id]
            total += self.mrp_order_id.product_qty

        self.merge_line_ids.write({
            'mrp_merge_order_ids': [(6, 0, order)],
            'quantity': total
        })


class MrpMergeLine(models.TransientModel):
    """
    Merge line to manage merge quantity
    """
    _name = 'mrp.merge.line'
    _description = 'MRP merge line'

    merge_order_id = fields.Many2one(
        string='Merge order',
        comodel_name='order.mrp.merge',
        help='Inverse field linking back to the order.mrp.merge model, '
             'representing the merge order.'
    )
    mrp_merge_order_ids = fields.Many2many(
        string='Orders',
        comodel_name='mrp.production',
        help='This field represents the list of MRP orders that are being'
             ' merged together.')
    mrp_product_id = fields.Many2one(
        string='Product',
        comodel_name='product.product',
        help='Product associated with the mrp order.')
    quantity = fields.Integer(string='Quantity', help='Quantity of the merge '
                                                      'order')
