# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
from odoo import Command, fields, models
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    """Add the manufacturing orders created from the sale order, the smart
    button that lists them and the action that creates them."""
    _inherit = 'sale.order'

    mrp_count = fields.Integer(
        compute='_compute_mrp_count',
        string="MRP Count",
        groups='mrp.group_mrp_user',
        help="Number of manufacturing orders created from this sale order.",
    )
    mrp_order_ids = fields.Many2many(
        'mrp.production',
        string="MRP Orders",
        copy=False,
        groups='mrp.group_mrp_user',
        help="Manufacturing orders created from this sale order.",
    )

    def _compute_mrp_count(self):
        """Count the manufacturing orders of each sale order."""
        counts = dict(self.env['mrp.production']._read_group(
            [('sale_order_id', 'in', self.ids)],
            ['sale_order_id'],
            ['__count'],
        ))
        for record in self:
            record.mrp_count = counts.get(record, 0)

    def _get_manufacturable_lines(self):
        """Return the order lines whose product has a Bill of Materials.
        Sections, notes, services and kits are not manufactured."""
        self.ensure_one()
        lines = self.order_line.filtered(
            lambda line: not line.display_type and line.product_id)
        boms = self.env['mrp.bom']._bom_find(
            lines.product_id, company_id=self.company_id.id,
            bom_type='normal')
        return lines.filtered(lambda line: boms.get(line.product_id))

    def _check_mrp_order_creation(self):
        """Check all the selected orders before anything is created, and
        report every problem at once."""
        Production = self.env['mrp.production']
        already_has_mrp = {
            order for order, in Production._read_group(
                [('sale_order_id', 'in', self.ids)], ['sale_order_id'])
        }
        non_draft_orders = []
        no_bom_orders = []
        zero_qty_orders = {}
        for order in self:
            if order in already_has_mrp:
                continue
            if order.state != 'draft':
                non_draft_orders.append(order.name)
                continue
            lines = order._get_manufacturable_lines()
            if not lines:
                no_bom_orders.append(order.name)
            zero_qty_lines = lines.filtered(
                lambda line: line.product_uom_qty <= 0)
            if zero_qty_lines:
                zero_qty_orders[order.name] = zero_qty_lines.product_id.mapped(
                    'display_name')

        errors = []
        if already_has_mrp:
            errors.append(self.env._(
                "The following sale order(s) already have a manufacturing "
                "order: %(orders)s",
                orders=", ".join(order.name for order in already_has_mrp)))
        if non_draft_orders:
            errors.append(self.env._(
                "The following sale order(s) are not in draft state: "
                "%(orders)s", orders=", ".join(non_draft_orders)))
        if no_bom_orders:
            errors.append(self.env._(
                "The following sale order(s) have no product with a Bill of "
                "Materials: %(orders)s", orders=", ".join(no_bom_orders)))
        if zero_qty_orders:
            detail = "; ".join(
                f"{order} → {', '.join(products)}"
                for order, products in zero_qty_orders.items())
            errors.append(self.env._(
                "The following product(s) have zero quantity: %(details)s",
                details=detail))
        if errors:
            raise ValidationError("\n".join(errors))

    def action_mrp_order(self):
        """Create one manufacturing order for each manufacturable line of
        the selected sale orders."""
        self._check_mrp_order_creation()
        for order in self:
            productions = self.env['mrp.production'].with_company(
                order.company_id).create([{
                    'product_id': line.product_id.id,
                    'product_qty': line.product_uom_qty,
                    'product_uom_id': line.product_uom_id.id,
                    'sale_order_id': order.id,
                    'origin': order.name,
                } for line in order._get_manufacturable_lines()])
            order.mrp_order_ids = [Command.set(productions.ids)]

    def get_mrp(self):
        """Open the manufacturing orders of this sale order."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._('Manufacturing Orders'),
            'view_mode': 'list,form',
            'res_model': 'mrp.production',
            'domain': [('sale_order_id', '=', self.id)],
            'context': {'create': False},
        }
