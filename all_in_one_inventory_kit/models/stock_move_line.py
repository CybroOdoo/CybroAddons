# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Saneen K (odoo@cybrosys.com)
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
################################################################################
from odoo import api, fields, models


class StockMoveLine(models.Model):
    """Inherits Stock Move Line"""
    _inherit = "stock.move.line"

    cw_qty_done = fields.Float(string='CW-Qty Done',
                               compute='_compute_cw_qty_done', default=0,
                               digits=(16, 4),
                               help="Catch weight Quantity Done")
    category_id = fields.Many2one('uom.category',
                                  default=lambda self: self.env.ref(
                                      'uom.product_uom_categ_kgm'),
                                  help="Category")
    cw_uom_id = fields.Many2one('uom.uom', string='CW-Uom',
                                domain="[('category_id', '=', category_id)]",
                                compute='_compute_cw_uom_id',
                                help="Unit of measure")
    cw_hide = fields.Boolean(string='Is CW Product',
                             compute="_compute_cw_hide", default=False,
                             help="Catch weight hide")
    move_line_image = fields.Binary(string="Image",
                                    related="product_id.image_1920",
                                    help="Product image")
    scheduled_date = fields.Datetime(related="picking_id.scheduled_date",
                                     store=True, help="Scheduled date")
    date_done = fields.Datetime(related="picking_id.date_done",
                                help="Date of done")
    code = fields.Selection(related="picking_id.picking_type_id.code",
                            help="Code")
    picking_type_id = fields.Many2one(related="picking_id.picking_type_id",
                                      store=True, help="Picking type")
    origin = fields.Char(related="picking_id.origin", store=True,
                         help="Origin of the picking")
    reserved_available = fields.Float(
        related="picking_id.move_ids_without_package.forecast_availability",
        help="Reserved available")
    date_deadline = fields.Datetime(related="picking_id.date_deadline",
                                    string="Deadline", help="Date deadline")
    has_deadline_issue = fields.Boolean(string="Is late",
                                        related="picking_id.has_deadline_issue",
                                        help="is deadline has issue")

    # cw_stock functions
    @api.depends('product_id')
    def _compute_cw_uom_id(self):
        """Calculating cw uom"""
        for rec in self:
            if rec.product_id.catch_weight_ok:
                rec.cw_uom_id = rec.product_id.cw_uom_id
            else:
                rec.cw_uom_id = None

    @api.depends('product_id')
    def _compute_cw_hide(self):
        """ Computes the cw_hide feature"""
        for rec in self:
            rec.cw_hide = bool(rec.product_id.catch_weight_ok)

    @api.depends('product_id', 'qty_done')
    def _compute_cw_qty_done(self):
        """Calculating cw qty done"""
        for rec in self:
            if rec.product_id.catch_weight_ok:
                rec.cw_qty_done = rec.qty_done * rec.product_id.average_cw_qty
            else:
                rec.cw_qty_done = 0

    # cw_stock functions end
    @api.model
    def get_product_moves(self):
        """rpc method of product moves graph
            Returns product move product and quantity_done"""
        company_id = self.env.company.id
        query = ('''select product_template.name,sum(stock_move_line.qty_done)
         from stock_move_line
                inner join product_product on stock_move_line.product_id = 
                product_product.id
                inner join product_template on product_product.product_tmpl_id =
                 product_template.id
                where stock_move_line.company_id = %s group by
                 product_template.name''' % company_id)
        self._cr.execute(query)
        products_quantity = self._cr.dictfetchall()
        quantity_done = []
        name = []
        for record in products_quantity:
            quantity_done.append(record.get('sum'))
            name.append(record.get('name'))
        value = {'name': name, 'count': quantity_done}
        category_query = '''select product_category.id,product_category.name 
        from stock_move_line
                inner join product_product on stock_move_line.product_id = 
                product_product.id inner join product_template on 
                product_product.product_tmpl_id = product_template.id inner 
                join product_category on product_template.categ_id = 
                product_category.id where stock_move_line.company_id = %s and 
                stock_move_line.state = 'done' group by product_category.id''' \
                         % company_id
        self._cr.execute(category_query)
        category = self._cr.dictfetchall()
        category_id = []
        category_name = []
        for record in category:
            category_id.append(record.get('id'))
            category_name.append(record.get('name'))
        value1 = {'category_id': category_id, 'category_name': category_name}
        return value, value1

    @api.model
    def product_move_by_category(self, args):
        """rpc method of product moves by category
            Returns category name and quantity_done"""
        category_id = int(args)
        company_id = self.env.company.id
        self.env.cr.execute('''select product_template.name,sum(stock_move_line.qty_done) 
        from stock_move_line inner join product_product on stock_move_line.
        product_id = product_product.id inner join product_template on 
        product_product.product_tmpl_id = product_template.id inner join 
        product_category on product_template.categ_id = product_category.id
        where stock_move_line.company_id = %s and product_category.id = %s 
        group by product_template.name''' , (company_id,category_id))
        product_move = self._cr.dictfetchall()
        quantity_done = []
        name = []
        for record in product_move:
            quantity_done.append(record['sum'])
            name.append(record['name'])
        value = {
            'name': name,
            'count': quantity_done,
        }
        return value
