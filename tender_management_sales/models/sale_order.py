# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Nikhil M (odoo@cybrosys.com)
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
from odoo import api, fields, models, _, Command
from collections import defaultdict


class SaleOrderGroup(models.Model):
    """Creating a model to group all the orders for tender management."""
    _name = 'sale.order.group'
    _description = "Technical model to group Orders for tender management."

    order_ids = fields.One2many('sale.order', 'sale_group_id',help='Sale orders')

    def write(self, vals):
        """Remove records where the length of the order_ids is less than
         or equal to 1"""
        res = super().write(vals)
        self.filtered(lambda g: len(g.order_ids) <= 1).unlink()
        return res


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    tender_id = fields.Many2one('sale.tender',
                                string='Sale Agreement',
                                copy=False, help='Tender being used in order')
    sale_group_id = fields.Many2one('sale.order.group',
                                    help='Sale Group')
    alternative_so_ids = fields.One2many(
        'sale.order', related='sale_group_id.order_ids', readonly=False,
        domain="[('id', '!=', id), ('state', 'in', ['draft', 'sent'])]",
        string="Alternative SOs", check_company=True,
        help="Other potential sale orders for selling products")

    @api.onchange('sale_order_template_id')
    def _onchange_sale_order_template_id(self):
        """
        This method is triggered when the 'sale_order_template_id' field is changed.
        It overrides the default behavior to check for the presence of a 'tender_id' field:
        """
        # Call the parent class method using super()
        if self.tender_id:
            if self.sale_order_template_id:
                super(SaleOrder, self)._onchange_sale_order_template_id()
        else:
            super(SaleOrder, self)._onchange_sale_order_template_id()

    def write(self, vals):
        """Overriding the write function to add the cases in case of tender
         is added."""
        if vals.get('sale_group_id', False):
            orig_sale_group = self.sale_group_id
        result = super(SaleOrder,self).write(vals)
        if vals.get('alternative_so_ids', False):
            if not self.sale_group_id and len(self.alternative_so_ids + self) > len(self):
                # create/merge a new group
                self.env['sale.order.group'].create({'order_ids': [Command.set(self.ids + self.alternative_so_ids.ids)]})
            elif self.sale_group_id and len(self.alternative_so_ids + self) <= 1:
                # write in purchase group isn't called so we have to manually
                # unlink obsolete groups here
                self.sale_group_id.unlink()
        if vals.get('sale_group_id', False):
            additional_groups = orig_sale_group - self.sale_group_id
            if additional_groups:
                additional_sos = (additional_groups.order_ids - self.saled_group_id.order_ids)
                additional_groups.unlink()
                if additional_sos:
                    self.sale_group_id.order_ids |= additional_sos

        return result

    @api.model_create_multi
    def create(self, vals_list):
        """Overriding the Create function to update vals in case of tender id."""
        orders = super().create(vals_list)
        if self.env.context.get('origin_so_id'):
            origin_so_id = self.env['sale.order'].browse(
                self.env.context.get('origin_so_id'))
            if origin_so_id.sale_group_id:
                origin_so_id.sale_group_id.order_ids |= orders
            else:
                self.env['sale.order.group'].create({'order_ids': [Command.set(origin_so_id.ids + orders.ids)]})
        return orders

    def action_confirm(self):
        """Updated the state of other related orders and the agreement state on confirming the order."""
        res = super(SaleOrder, self).action_confirm()
        for so in self:
            if not so.tender_id:
                continue
            if so.tender_id.type_id.exclusive == 'exclusive':
                others_so = so.tender_id.mapped('sale_order_ids').filtered(lambda r: r.id != so.id)
                others_so.action_cancel()
                if so.state not in ['draft', 'sent']:
                    so.tender_id.action_done()
        return res

    @api.onchange('tender_id')
    def _onchange_tender_id(self):
        """Function to update all the values from the tender from agreement to the sale order."""
        if not self.tender_id:
            return
        if self.sale_order_template_id:
            self.sale_order_template_id = False
            data = [fields.Command.clear()]
            self.sale_order_option_ids = data
            self.order_line = data

        self = self.with_company(self.company_id)
        tender = self.tender_id
        if self.partner_id:
            partner = self.partner_id
        else:
            partner = tender.customer_id

        FiscalPosition = self.env['account.fiscal.position']
        fpos = FiscalPosition.with_company(
            self.company_id)._get_fiscal_position(partner)
        self.partner_id = partner.id
        self.company_id = tender.company_id.id
        self.currency_id = tender.currency_id.id
        if not self.origin or tender.name not in self.origin.split(', '):
            if self.origin:
                if tender.name:
                    self.origin = self.origin + ', ' + tender.name
            else:
                self.origin = tender.name
        self.note = tender.description
        self.date_order = fields.Datetime.now()

        if tender.type_id.line_copy != 'copy':
            return

        # Create SO lines if necessary
        order_lines = []
        for line in tender.line_ids:
            # Compute name
            product_lang = line.product_id.with_context(
                lang=partner.lang or self.env.user.lang,
                partner_id=partner.id
            )
            name = product_lang.display_name
            if product_lang.description_purchase:
                name += '\n' + product_lang.description_purchase

            # Compute taxes
            taxes_ids = fpos.map_tax(line.product_id.supplier_taxes_id.filtered(lambda tax: tax.company_id == tender.company_id)).ids
            # Compute quantity and price_unit
            if line.product_uom_id != line.product_id.uom_id:
                product_qty = line.product_uom_id._compute_quantity(line.product_qty, line.product_id.uom_id)
                price_unit = line.product_uom_id._compute_price(line.price_unit, line.product_id.uom_id)
            else:
                product_qty = line.product_qty
                price_unit = line.price_unit

            if tender.type_id.quantity_copy != 'copy':
                product_qty = 0

            # Create SO line
            order_line_values = line._prepare_sale_order_line(
                name=name, product_qty=product_qty, price_unit=price_unit,
                taxes_ids=taxes_ids)
            order_lines.append((0, 0, order_line_values))
        self.order_line = order_lines

    def action_compare_alternative_lines(self):
        """" Function to return to the view of line compare tree."""
        ctx = dict(
            self.env.context,
            search_default_product=True,
            sale_order_id=self.id,
        )
        view_id = self.env.ref('tender_management_sales.sale_order_line_compare_tree').id
        return {
            'name': _('Compare Order Lines'),
            'type': 'ir.actions.act_window',
            'view_mode': 'list',
            'res_model': 'sale.order.line',
            'views': [(view_id, "list")],
            'domain': [('order_id', 'in', (self | self.alternative_so_ids).ids), ('display_type', '=', False)],
            'context': ctx,
        }

    def action_create_alternative(self):
        """Function to create alternative orders."""
        ctx = dict(**self.env.context, default_origin_so_id=self.id)
        return {
            'name': _('Create alternative'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'sale.tender.create.alternative',
            'view_id': self.env.ref('tender_management_sales.sale_tender_create_alternative_form').id,
            'target': 'new',
            'context': ctx,
        }

    def get_tender_best_lines(self):
        """" Function to get the best order lines from grouped orders."""
        product_to_best_price_line = defaultdict(lambda: self.env['sale.order.line'])
        product_to_best_price_unit = defaultdict(lambda: self.env['sale.order.line'])
        so_alternatives = self | self.alternative_so_ids

        multiple_currencies = False
        if len(so_alternatives.currency_id) > 1:
            multiple_currencies = True

        for line in so_alternatives.order_line:
            if not line.product_uom_qty or not line.price_subtotal or line.state in ['cancel', 'purchase', 'done']:
                continue

            if not product_to_best_price_line[line.product_id]:
                product_to_best_price_line[line.product_id] = line
                product_to_best_price_unit[line.product_id] = line
            else:
                price_subtotal = line.price_subtotal
                price_unit = line.price_unit
                current_price_subtotal = product_to_best_price_line[line.product_id][0].price_subtotal
                current_price_unit = product_to_best_price_unit[line.product_id][0].price_unit
                if multiple_currencies:
                    price_subtotal /= line.order_id.currency_rate
                    price_unit /= line.order_id.currency_rate
                    current_price_subtotal /= product_to_best_price_line[line.product_id][0].order_id.currency_rate
                    current_price_unit /= product_to_best_price_unit[line.product_id][0].order_id.currency_rate
                if current_price_subtotal < price_subtotal:
                    product_to_best_price_line[line.product_id] = line
                elif current_price_subtotal == price_subtotal:
                    product_to_best_price_line[line.product_id] |= line

                if current_price_unit < price_unit:
                    product_to_best_price_unit[line.product_id] = line
                elif current_price_unit == price_unit:
                    product_to_best_price_unit[line.product_id] |= line

        best_price_ids = set()
        best_price_unit_ids = set()
        for lines in product_to_best_price_line.values():
            best_price_ids.update(lines.ids)
        for lines in product_to_best_price_unit.values():
            best_price_unit_ids.update(lines.ids)
        return list(best_price_ids), list(best_price_unit_ids)


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def action_clear_quantities(self):
        """" Function to clear quantities from the current line."""
        zeroed_lines = self.filtered(lambda l: l.state not in ['cancel', 'sale', 'done'])
        zeroed_lines.write({'product_uom_qty': 0})
        if len(self) > len(zeroed_lines):
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _("Some not cleared"),
                    'message': _("Some quantities were not cleared because their status is not a Draft."),
                    'sticky': False,
                }
            }
        return False

    def action_choose(self):
        """" Function to choose a line among different order lines so that other lines quantities will update to null."""
        order_lines = (self.order_id | self.order_id.alternative_so_ids).mapped('order_line')
        order_lines = order_lines.filtered(lambda l: l.product_uom_qty and l.product_id.id in self.product_id.ids and l.id not in self.ids)
        if order_lines:
            return order_lines.action_clear_quantities()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _("Nothing to clear"),
                'message': _("There are no quantities to clear."),
                'sticky': False,
            }
        }
