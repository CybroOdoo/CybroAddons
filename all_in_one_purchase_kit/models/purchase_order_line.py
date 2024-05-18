# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Afra MP (odoo@cybrosys.com)
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
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class PurchaseOrderLine(models.Model):
    """Inherit purchase.order.line to add fields and methods"""
    _inherit = 'purchase.order.line'

    product_image = fields.Binary(
        related="product_id.image_1920",
        string="Product Image",
        help='For getting product image to purchase order line')
    purchase_date = fields.Datetime(
        comodel_name='purchase.order', related='order_id.date_order', store=True,
        string='Purchase Date', help="Purchase Date"
    )
    barcode_scan = fields.Char(
        string='Product Barcode',
        help="Here you can provide the barcode for the product")
    discount = fields.Float(
        string="Discount (%)", editable=True, help="Total Discount"
    )
    _sql_constraints = [
        (
            "maximum_discount",
            "CHECK (discount <= 100.0)",
            "Discount must be lower than 100%.",
        )
    ]

    @api.onchange('order_id')
    def _onchange_order_id(self):
        """ Restrict creating purchase order line for purchase order
                in locked, cancel and purchase order states"""
        if self.order_id.state in ['cancel', 'done', 'purchase']:
            raise UserError(_("You cannot select purchase order in "
                              "cancel or locked or purchase order state"))

    def get_product_form(self):
        """Get the product form"""
        self.product_id.order_partner_id = self.order_id.partner_id.id
        return {
            'name': self.product_id.name,
            'view_mode': 'form',
            'res_model': 'product.product',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'res_id': self.product_id.id
        }

    @api.onchange('barcode_scan')
    def _onchange_barcode_scan(self):
        """Search the product with the barcode entered"""
        if self.barcode_scan:
            product = self.env['product.product'].search([
                ('barcode', '=', self.barcode_scan)])
            self.product_id = product.id

    @api.depends("discount")
    def _compute_amount(self):
        """Add discount"""
        return super()._compute_amount()

    def _convert_to_tax_base_line_dict(self):
        """Update price unit"""
        vals = super()._convert_to_tax_base_line_dict()
        vals.update({"price_unit": self._get_discounted_price()})
        return vals

    @api.onchange('product_id')
    def calculate_discount_percentage(self):
        """Calculate the discount percentage"""
        vendor = self.order_id.partner_id
        sellers = self.product_id.product_tmpl_id.seller_ids
        for rec in sellers:
            if rec.partner_id.id == vendor.id:
                if rec.discount:
                    self.write({'discount': rec.discount})
                    self.update({'price_unit': rec.price})
                    break
            elif rec.partner_id.id != vendor.id:
                self.update({'discount': vendor.default_discount})
                break
            else:
                self.write({'discount': None})

    @api.depends('discount')
    def _get_discounted_price(self):
        """Returns discounted price"""
        self.ensure_one()
        if self.discount:
            return self.price_unit * (1 - self.discount / 100)
        return self.price_unit

    def _prepare_account_move_line(self, move=False):
        """Discount in account.move.line"""
        sup = super(PurchaseOrderLine, self)._prepare_account_move_line(move)
        sup.update({'discount': self.discount})
        return sup

    def add_catalog_control(self):
        """Method to call product.product model when click on catalog
        button in purchase order line"""
        return {
            'type': 'ir.actions.act_window',
            'name': _('Products'),
            'context': {'order_id': self.env.context.get('id')},
            'res_model': 'product.product',
            'view_mode': 'kanban,tree,form',
            'target': 'current',
        }

    def action_purchase_order(self):
        """Method action_purchase_order to return the form view of the
        model purchase.order"""
        return {
            'type': 'ir.actions.act_window',
            'name': _('Purchase Order'),
            'res_id': self.order_id.id,
            'res_model': 'purchase.order',
            'view_mode': 'form',
            'target': 'current',
        }

    @api.model
    def product_categ_analysis(self):
        """Get product category analysis data.
         :return: Product category analysis data
         :rtype: dict"""
        company_id = self.env.user.company_id.id
        quantity_query = """
                SELECT product_template.name, SUM(pl.product_qty) as total_quantity
                FROM purchase_order_line pl
                JOIN product_product ON pl.product_id = product_product.id
                JOIN product_template ON product_product.product_tmpl_id = 
                product_template.id
                WHERE pl.company_id = %s
                GROUP BY product_template.name
            """
        self._cr.execute(quantity_query, (company_id,))
        products_quantity = self._cr.fetchall()
        if not products_quantity:  # Check if products_quantity is empty
            return {'values': {'name': [], 'count': []}, 'category_id': []}
        name, quantity_done = zip(*products_quantity)
        categories = self.get_categories()
        value = {'name': name, 'count': quantity_done}
        return {'values': value, 'category_id': categories}

    def get_categories(self):
        """Get product categories.
        :return: Product categories
        :rtype: list"""
        category_query = """
                        SELECT pc.id, pc.name
                        FROM product_category pc
                        JOIN product_template pt ON pt.categ_id = pc.id
                        JOIN product_product pp ON pp.product_tmpl_id = pt.id
                        JOIN purchase_order_line pl ON pl.product_id = pp.id
                        WHERE pl.company_id = %s
                        GROUP BY pc.id, pc.name
                    """
        self._cr.execute(category_query, (self.env.user.company_id.id,))
        return self._cr.fetchall()

    @api.model
    def product_categ_data(self, args):
        """Get product category data.
        :param args: Category ID
        :type args: int
        :return: Product category data
        :rtype: dict"""
        category_id = int(args or 1)
        company_id = self.env.company.id
        query = """
                SELECT product_template.name, SUM(pl.product_qty)
                FROM purchase_order_line pl
                INNER JOIN product_product ON pl.product_id = product_product.id
                INNER JOIN product_template ON product_product.product_tmpl_id = 
                product_template.id
                WHERE pl.company_id = %s AND product_template.categ_id = %s
                GROUP BY product_template.name
            """
        self._cr.execute(query, (company_id, category_id))
        product_move = self._cr.dictfetchall()
        value = {
            'name': [record.get('name') for record in product_move],
            'count': [record.get('sum') for record in product_move],
        }
        return value
