# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Aysha Shalin (odoo@cybrosys.com)
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
from odoo import api, models


class StockMove(models.Model):
    """ Extends 'stock.move' and provides methods for retrieving data for
    dashboard."""
    _inherit = "stock.move"

    @api.model
    def get_the_top_products(self):
        """ Returns top ten products and done quantity."""
        company_id = self.env.company.id
        query = '''select product_template.name,sum(product_uom_qty)  from stock_move
            inner join stock_picking on stock_move.picking_id = stock_picking.id
            inner join stock_picking_type on stock_picking.picking_type_id = stock_picking_type.id
            inner join product_product on stock_move.product_id = product_product.id
            inner join product_template on product_template.id = product_product.product_tmpl_id 
            where stock_move.state = 'done' and stock_move.company_id=%s and stock_picking_type.code = 'outgoing' and 
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
        """ Returns top ten products and done quantity for last 10 days."""
        company_id = self.env.company.id
        query = '''select product_template.name,sum(product_uom_qty)  from stock_move
            inner join stock_picking on stock_move.picking_id = stock_picking.id
            inner join stock_picking_type on stock_picking.picking_type_id = stock_picking_type.id
            inner join product_product on stock_move.product_id = product_product.id
            inner join product_template on product_template.id = product_product.product_tmpl_id 
            where stock_move.state = 'done' and stock_move.company_id=%s and stock_picking_type.code = 'outgoing' and 
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
        """ Returns top ten products and done quantity for last 30 days."""
        company_id = self.env.company.id
        query = '''select product_template.name,sum(product_uom_qty)  from stock_move
                inner join stock_picking on stock_move.picking_id = stock_picking.id
                inner join stock_picking_type on stock_picking.picking_type_id = stock_picking_type.id
                inner join product_product on stock_move.product_id = product_product.id
                inner join product_template on product_template.id = product_product.product_tmpl_id 
                where stock_move.state = 'done' and stock_move.company_id=%s and stock_picking_type.code = 'outgoing' 
                and stock_move.create_date between (now() - interval '30 day') and now()
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
    def top_products_last_three_months(self):
        """ Returns top ten products and done quantity for last 3 months."""
        company_id = self.env.company.id
        query = '''select product_template.name,sum(product_uom_qty)  from stock_move
                    inner join stock_picking on stock_move.picking_id = stock_picking.id
                    inner join stock_picking_type on stock_picking.picking_type_id = stock_picking_type.id
                    inner join product_product on stock_move.product_id = product_product.id
                    inner join product_template on product_template.id = product_product.product_tmpl_id 
                    where stock_move.state = 'done' and stock_move.company_id=%s and stock_picking_type.code ='outgoing' 
                    and stock_move.create_date between (now() - interval '3 month') and now()
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
    def top_products_last_year(self):
        """ Returns top ten products and done quantity for last year."""
        company_id = self.env.company.id
        query = '''select product_template.name,sum(product_uom_qty)  from stock_move
                        inner join stock_picking on stock_move.picking_id = stock_picking.id
                        inner join stock_picking_type on stock_picking.picking_type_id = stock_picking_type.id
                        inner join product_product on stock_move.product_id = product_product.id
                        inner join product_template on product_template.id = product_product.product_tmpl_id 
                        where stock_move.state = 'done' and stock_move.company_id=%s and 
                        stock_picking_type.code = 'outgoing' and 
                        stock_move.create_date between (now() - interval '1 year') and now()
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
    def get_stock_moves(self):
        """ Returns location name and quantity_done of stock moves graph"""
        company_id = self.env.company.id
        query = ('''select stock_location.complete_name, count(stock_move.id) from stock_move 
            inner join stock_location on stock_move.location_id = stock_location.id where stock_move.state = 'done' 
            and stock_move.company_id = %s group by stock_location.complete_name''' % company_id)
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
        """ Returns location name and quantity_done of stock moves graph last
        ten days."""
        company_id = self.env.company.id
        query = ('''select stock_location.name,sum(stock_move_line.quantity) from stock_move_line
                        inner join stock_location on stock_move_line.location_id = stock_location.id
                        where stock_move_line.state = 'done' and stock_move_line.company_id = %s
                        and stock_move_line.create_date between (now() - interval '10 day') and now()
                        group by stock_location.name''' % company_id)
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
        """ Returns location name and quantity_done of stock moves graph for
        current month."""
        company_id = self.env.company.id
        query = ('''select stock_location.name,sum(stock_move_line.quantity) from stock_move_line
                    inner join stock_location on stock_move_line.location_id = stock_location.id
                    where stock_move_line.state = 'done' and stock_move_line.company_id = %s
                    and stock_move_line.create_date between (now() - interval '1 months') and now()
                    group by stock_location.name''' % company_id)
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
    def last_three_month(self, post):
        """ Returns location name and quantity_done of stock moves graph for
        last three months."""
        company_id = self.env.company.id
        query = ('''select stock_location.name,sum(stock_move_line.quantity) from stock_move_line
                        inner join stock_location on stock_move_line.location_id = stock_location.id
                        where stock_move_line.state = 'done' and stock_move_line.company_id = %s
                        and stock_move_line.create_date between (now() - interval '3 months') and now()
                        group by stock_location.name''' % company_id)
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
        """ Returns location name and quantity_done of stock moves graph for
        last year."""
        company_id = self.env.company.id
        query = ('''select stock_location.name,sum(stock_move_line.quantity) from stock_move_line
                       inner join stock_location on stock_move_line.location_id = stock_location.id
                       where stock_move_line.state = 'done' and stock_move_line.company_id = %s 
                       and stock_move_line.create_date between (now() - interval '12 months') and now()
                        group by stock_location.name''' % company_id)
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
    def get_dead_of_stock(self):
        """ Returns product name and dead quantity of dead stock graph."""
        company_id = self.env.company.id
        sett_dead_stock_bool = self.env['ir.config_parameter'].sudo(). \
            get_param("inventory_stock_dashboard_odoo.dead_stock_bol", default="")
        sett_dead_stock_quantity = self.env['ir.config_parameter'].sudo().get_param(
            "inventory_stock_dashboard_odoo.dead_stock",
            default="")
        sett_dead_stock_type = self.env['ir.config_parameter'].sudo().get_param(
            "inventory_stock_dashboard_odoo.dead_stock_type",
            default="")
        if sett_dead_stock_bool == "True":
            if sett_dead_stock_quantity:
                out_stock_value = int(sett_dead_stock_quantity)
                query = '''select product_product.id,stock_quant.quantity from product_product
                inner join stock_quant on product_product.id = stock_quant.product_id
                where stock_quant.company_id = %s and product_product.create_date not between (now() - interval '%s %s')
                and now() and product_product.id NOT IN (select product_id from stock_move
                inner join stock_picking on stock_move.picking_id = stock_picking.id
                inner join stock_picking_type on stock_picking.picking_type_id = stock_picking_type.id
                where stock_move.company_id = %s and stock_picking_type.code = 'outgoing' and 
                stock_move.state = 'done'   and stock_move.create_date between (now() - interval '%s %s') and now()
                group by product_id)''' % \
                        (company_id, out_stock_value, sett_dead_stock_type, company_id, out_stock_value,
                         sett_dead_stock_type)
                self._cr.execute(query)
                result = self._cr.fetchall()
                total_quantity = []
                product_name = []
                for record in result:
                    if record[1] > 0:
                        complete_name = self.env['product.product'].browse(record[0]).display_name
                        product_name.append(complete_name)
                        total_quantity.append(record[1])
                value = {
                    'product_name': product_name,
                    'total_quantity': total_quantity
                }
                return value
