# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Mohammed Dilshad Tk (odoo@cybrosys.com)
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
################################################################
from odoo import api, fields, models, _
from datetime import datetime, timedelta


class StockMove(models.Model):
    """Inherits stock.move"""
    _inherit = 'stock.move'

    barcode = fields.Char(string='Barcode', help="Barcode")
    category_id = fields.Many2one('uom.category',
                                  default=lambda self: self.env.ref(
                                      'uom.product_uom_categ_kgm'),
                                  help="category")
    cw_uom_id = fields.Many2one('uom.uom', string='CW-Uom',
                                help="Catch weight unit of measure",
                                domain="[('category_id', '=', category_id)]")
    cw_demand = fields.Float(string='CW-Demand', default=1.0, required=True,
                             digits=(16, 4),
                             compute='_cal_cw_demand',
                             help="Catch weight demand")
    cw_reserved = fields.Float(string='CW-Reserved', compute='_cal_cw_demand',
                               digits=(16, 4), help="Catch weight reserved")
    cw_done = fields.Float(string='CW-Done', digits=(16, 4),
                           help="Catch weight done")
    cw_hide = fields.Boolean(string='Is CW Product',
                             compute="_compute_cw_hide", default=False,
                             help="Catch weight hide")
    move_line_image = fields.Binary(string="Image",
                                    related="product_id.image_1920",
                                    help="Product image")

    # cw_stock functions
    @api.depends('product_id')
    def _compute_cw_hide(self):
        """ Computes the cw_hide feature"""
        for rec in self:
            rec.cw_hide = bool(rec.product_id.catch_weight_ok)

    @api.onchange('product_id', 'product_uom_qty')
    def _onchange_product_id(self):
        """Calculating cw demand and cw uom"""
        for rec in self:
            rec.cw_demand = rec.product_uom_qty * rec.product_id.average_cw_qty
            if rec.product_id.catch_weight_ok:
                rec.cw_uom_id = rec.product_id.cw_uom_id
            else:
                rec.cw_uom_id = None

    @api.onchange('cw_done')
    def _onchange_cw_done(self):
        """Calculating done qty"""
        for rec in self:
            if rec.product_id.catch_weight_ok and rec.product_id.average_cw_qty\
                    != 0:
                rec.quantity_done = rec.cw_done / rec.product_id.average_cw_qty

    @api.onchange('quantity_done')
    def _onchange_quantity_done(self):
        """Calculating cw done"""
        for rec in self:
            if rec.product_id.catch_weight_ok:
                rec.cw_done = rec.quantity_done * rec.product_id.average_cw_qty

    @api.onchange('cw_demand')
    def onchange_cw_demand(self):
        """Calculating cw qty"""
        for rec in self:
            if rec.product_id.catch_weight_ok and rec.product_id.average_cw_qty\
                    != 0:
                if rec.cw_uom_id == rec.product_uom:
                    rec.product_uom_qty = rec.cw_demand
                else:
                    rec.product_uom_qty = rec.cw_demand / rec.product_id.\
                        average_cw_qty

    @api.onchange('product_uom_qty')
    def _onchange_product_uom_qty(self):
        """Calculating cw demand"""
        for rec in self:
            if rec.product_id.catch_weight_ok and rec.product_id.average_cw_qty\
                    != 0:
                if rec.cw_uom_id == rec.product_uom:
                    rec.cw_demand = rec.product_uom_qty
                else:
                    rec.product_uom_qty = rec.cw_demand / rec.product_id.\
                        average_cw_qty

    def _cal_cw_demand(self):
        """Calculating cw demand,cw uom, cw reserved and cw done"""
        for rec in self:
            rec.update(
                {
                    'cw_demand': rec.product_uom_qty * rec.product_id.
                    average_cw_qty,
                    'cw_uom_id': rec.product_id.cw_uom_id,
                    'cw_done': rec.quantity_done * rec.product_id.
                    average_cw_qty,
                    'cw_reserved': rec.product_uom_qty * rec.product_id.
                    average_cw_qty,
                })

    # product barcode functions
    @api.onchange('barcode')
    def _onchange_barcode(self):
        """ gets product with given barcode """
        product_rec = self.env['product.product']
        if self.barcode:
            product = product_rec.search([('barcode', '=', self.barcode)])
            self.product_id = product.id

    @api.model
    def get_the_top_products(self):
        """Rpc method of top products graph
        Returns top ten products and done quantity"""
        company_id = self.env.company.id
        query = '''select product_template.name,sum(product_uom_qty)  from
         stock_move
            inner join stock_picking on stock_move.picking_id = stock_picking.id
            inner join stock_picking_type on stock_picking.picking_type_id = 
            stock_picking_type.id
            inner join product_product on stock_move.product_id = 
            product_product.id
            inner join product_template on product_template.id = 
            product_product.product_tmpl_id 
            where stock_move.state = 'done' and stock_move.company_id=%s and 
            stock_picking_type.code = 'outgoing' and 
            stock_move.create_date between (now() - interval '10 day') and now()
            group by product_template.name ORDER BY sum DESC''' % company_id
        self._cr.execute(query)
        top_product = self._cr.dictfetchall()
        total_quantity = []
        product_name = []
        for record in top_product[:10]:
            total_quantity.append(record.get('sum'))
            product_name.append(record.get('name')['en_US'])
        value = {'products': product_name, 'count': total_quantity}
        return value

    @api.model
    def top_products_last_ten(self):
        """rpc method of top products graph for last 10 days
        Returns top ten products and done quantity"""
        company_id = self.env.company.id
        query = '''select product_template.name,sum(product_uom_qty)  from 
            stock_move inner join stock_picking on stock_move.picking_id = 
            stock_picking.id inner join stock_picking_type on stock_picking.
            picking_type_id =  stock_picking_type.id
            inner join product_product on stock_move.product_id = 
            product_product.id inner join product_template on product_template.
            id = product_product.product_tmpl_id 
            where stock_move.state = 'done' and stock_move.company_id=%s 
            and stock_picking_type.code = 'outgoing' and 
            stock_move.create_date between (now() - interval '10 day') and now()
            group by product_template.name ORDER BY sum DESC''' % company_id
        self._cr.execute(query)
        top_product = self._cr.dictfetchall()
        total_quantity = []
        product_name = []
        for record in top_product[:10]:
            total_quantity.append(record.get('sum'))
            product_name.append(record.get('name')['en_US'])
        value = {'products': product_name, 'count': total_quantity}
        return value

    @api.model
    def top_products_last_thirty(self):
        """rpc method of top products graph for last 30 days
        Returns top ten products and done quantity"""
        company_id = self.env.company.id
        query = '''select product_template.name,sum(product_uom_qty)  from 
                stock_move inner join stock_picking on stock_move.picking_id = 
                stock_picking.id inner join stock_picking_type on stock_picking.
                picking_type_id = stock_picking_type.id
                inner join product_product on stock_move.product_id = 
                product_product.id inner join product_template on 
                product_template.id = product_product.product_tmpl_id 
                where stock_move.state = 'done' and stock_move.company_id=%s 
                and stock_picking_type.code = 'outgoing' 
                and stock_move.create_date between (now() - interval '30 day') 
                and now() group by product_template.name ORDER BY sum DESC''' \
                % company_id
        self._cr.execute(query)
        top_product = self._cr.dictfetchall()
        total_quantity = []
        product_name = []
        for record in top_product[:10]:
            total_quantity.append(record.get('sum'))
            product_name.append(record.get('name')['en_US'])
        value = {'products': product_name, 'count': total_quantity}
        return value

    @api.model
    def top_products_last_three_months(self):
        """RPC method of top products graph select last 3 months
        Returns top ten products and done quantity"""
        company_id = self.env.company.id
        now = datetime.now()
        start_three_months_ago = now - timedelta(days=90)
        query = '''
        SELECT product_template.name, SUM(stock_move.product_uom_qty)
        FROM stock_move
        INNER JOIN stock_picking ON stock_move.picking_id = stock_picking.id
        INNER JOIN stock_picking_type ON stock_picking.picking_type_id = stock_picking_type.id
        INNER JOIN product_product ON stock_move.product_id = product_product.id
        INNER JOIN product_template ON product_template.id = product_product.product_tmpl_id
        WHERE stock_move.state = 'done'
          AND stock_move.company_id = %s
          AND stock_picking_type.code = 'outgoing'
          AND stock_move.create_date BETWEEN %s AND %s
        GROUP BY product_template.name
        ORDER BY SUM(stock_move.product_uom_qty) DESC
        '''
        self._cr.execute(query, (company_id, start_three_months_ago, now))
        top_product = self._cr.dictfetchall()
        total_quantity = []
        product_name = []
        for record in top_product[:10]:
            total_quantity.append(record.get('sum'))
            product_name.append(record.get('name')['en_US'])
        value = {'products': product_name, 'count': total_quantity}
        return value

    @api.model
    def top_products_last_year(self):
        """RPC method of top products graph select last year
        Returns top ten products and done quantity"""
        company_id = self.env.company.id
        now = datetime.now()
        start_last_year = datetime(now.year - 1, 1, 1)
        end_last_year = datetime(now.year - 1, 12, 31, 23, 59, 59)
        query = '''
        SELECT product_template.name, SUM(stock_move.product_uom_qty)
        FROM stock_move
        INNER JOIN stock_picking ON stock_move.picking_id = stock_picking.id
        INNER JOIN stock_picking_type ON stock_picking.picking_type_id = stock_picking_type.id
        INNER JOIN product_product ON stock_move.product_id = product_product.id
        INNER JOIN product_template ON product_template.id = product_product.product_tmpl_id
        WHERE stock_move.state = 'done'
          AND stock_move.company_id = %s
          AND stock_picking_type.code = 'outgoing'
          AND stock_move.create_date BETWEEN %s AND %s
        GROUP BY product_template.name
        ORDER BY SUM(stock_move.product_uom_qty) DESC
        '''
        self._cr.execute(query, (company_id, start_last_year, end_last_year))
        top_product = self._cr.dictfetchall()
        total_quantity = []
        product_name = []
        for record in top_product[:10]:
            total_quantity.append(record.get('sum'))
            product_name.append(record.get('name')['en_US'])
        value = {'products': product_name, 'count': total_quantity}
        return value

    @api.model
    def get_stock_moves(self):
        """rpc method of stock moves graph
            Returns location name and quantity_done"""
        company_id = self.env.company.id
        query = ('''select stock_location.complete_name, count(stock_move.id) 
                from stock_move inner join stock_location on stock_move.
                location_id = stock_location.id where stock_move.state = 'done' 
            and stock_move.company_id = %s group by stock_location.complete_name
            ''' % company_id)
        self._cr.execute(query)
        stock_move = self._cr.dictfetchall()
        count = []
        complete_name = []
        for record in stock_move:
            count.append(record.get('count'))
            complete_name.append(record.get('complete_name'))
        value = {'name': complete_name, 'count': count}
        return value

    @api.model
    def stock_move_last_ten_days(self, post):
        """rpc method of stock moves graph select last ten days
            Returns location name and quantity_done"""
        company_id = self.env.company.id
        query = ('''select stock_location.name,sum(stock_move_line.qty_done) 
                from stock_move_line inner join stock_location on 
                stock_move_line.location_id = stock_location.id where 
                stock_move_line.state = 'done' and stock_move_line.company_id =
                 %s and stock_move_line.create_date between (now() - interval 
                 '10 day') and now() group by stock_location.name'''
                 % company_id)
        self._cr.execute(query)
        location_quantity = self._cr.dictfetchall()
        quantity_done = []
        name = []
        for record in location_quantity:
            quantity_done.append(record.get('sum'))
            name.append(record.get('name'))
        value = {'name': name, 'count': quantity_done}
        return value

    @api.model
    def this_month(self, post):
        """RPC method of stock moves graph select this month
        Returns location name and quantity_done"""
        company_id = self.env.company.id
        now = datetime.now()
        start_this_month = datetime(now.year, now.month, 1)
        end_this_month = now
        query = '''
        SELECT stock_location.name, SUM(stock_move_line.qty_done)
        FROM stock_move_line
        INNER JOIN stock_location ON stock_move_line.location_id = stock_location.id
        WHERE stock_move_line.state = 'done'
          AND stock_move_line.company_id = %s
          AND stock_move_line.create_date BETWEEN %s AND %s
        GROUP BY stock_location.name
        '''
        self._cr.execute(query, (company_id, start_this_month, end_this_month))
        location_quantity = self._cr.dictfetchall()
        quantity_done = []
        name = []
        for record in location_quantity:
            quantity_done.append(record.get('sum'))
            name.append(record.get('name'))
        value = {'name': name, 'count': quantity_done}
        return value

    @api.model
    def last_three_month(self, post):
        """rpc method of stock moves graph select 3 month
            Returns location name and quantity_done"""
        company_id = self.env.company.id
        query = ('''select stock_location.name,sum(stock_move_line.qty_done) 
        from stock_move_line inner join stock_location on stock_move_line.
        location_id = stock_location.id where stock_move_line.state = 
        'done' and stock_move_line.company_id = %s and stock_move_line.
        create_date between (now() - interval '3 months') and now() group by 
        stock_location.name''' % company_id)
        self._cr.execute(query)
        location_quantity = self._cr.dictfetchall()
        quantity_done = []
        name = []
        for record in location_quantity:
            quantity_done.append(record.get('sum'))
            name.append(record.get('name'))
        value = {'name': name, 'count': quantity_done}
        return value

    @api.model
    def last_year(self, post):
        """RPC method of stock moves graph select last year
        Returns location name and quantity_done"""
        company_id = self.env.company.id
        now = datetime.now()
        start_last_year = datetime(now.year - 1, 1, 1)
        end_last_year = datetime(now.year - 1, 12, 31, 23, 59, 59)
        query = '''
        SELECT stock_location.name, SUM(stock_move_line.qty_done) 
        FROM stock_move_line
        INNER JOIN stock_location ON stock_move_line.location_id = stock_location.id
        WHERE stock_move_line.state = 'done'
          AND stock_move_line.company_id = %s
          AND stock_move_line.create_date BETWEEN %s AND %s
        GROUP BY stock_location.name
        '''
        self._cr.execute(query, (company_id, start_last_year, end_last_year))
        location_quantity = self._cr.dictfetchall()
        quantity_done = []
        name = []
        for record in location_quantity:
            quantity_done.append(record.get('sum'))
            name.append(record.get('name'))
        value = {'name': name, 'count': quantity_done}
        return value

    @api.model
    def get_dead_of_stock(self):
        """rpc method of dead of stock graph
        Returns product name and dead quantity"""
        company_id = self.env.company.id
        sett_dead_stock_bool = self.env['ir.config_parameter'].sudo(). \
            get_param("inventory_stock_dashboard_odoo.dead_stock_bol",
                      default="")
        sett_dead_stock_quantity = self.env[
            'ir.config_parameter'].sudo().get_param(
            "inventory_stock_dashboard_odoo.dead_stock",
            default="")
        sett_dead_stock_type = self.env['ir.config_parameter'].sudo().get_param(
            "inventory_stock_dashboard_odoo.dead_stock_type",
            default="")
        if sett_dead_stock_bool == "True":
            if sett_dead_stock_quantity:
                out_stock_value = int(sett_dead_stock_quantity)
                query = '''select product_product.id,stock_quant.quantity from 
                product_product inner join stock_quant on product_product.id = 
                stock_quant.product_id where stock_quant.company_id = %s and 
                product_product.create_date not between (now() - interval '%s 
                %s') and now() and product_product.id NOT IN (select product_id
                from stock_move inner join stock_picking on stock_move.
                picking_id = stock_picking.id inner join stock_picking_type on 
                stock_picking.picking_type_id = stock_picking_type.id
                where stock_move.company_id = %s and stock_picking_type.code = 
                'outgoing' and stock_move.state = 'done'   and stock_move.
                create_date between (now() - interval '%s %s') and now()
                group by product_id)''' % \
                (company_id, out_stock_value, sett_dead_stock_type,
                 company_id, out_stock_value,
                 sett_dead_stock_type)
                self._cr.execute(query)
                result = self._cr.fetchall()
                total_quantity = []
                product_name = []
                for record in result:
                    if record[1] > 0:
                        complete_name = self.env['product.product'].browse(
                            record[0]).display_name
                        product_name.append(complete_name)
                        total_quantity.append(record[1])
                value = {
                    'product_name': product_name,
                    'total_quantity': total_quantity
                }
                return value
