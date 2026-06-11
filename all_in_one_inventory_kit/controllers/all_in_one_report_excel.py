# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

import json
from odoo import http
from odoo.http import content_disposition, request, \
    serialize_exception as _serialize_exception
from odoo.tools import html_escape
from datetime import datetime, timedelta


class XLSXReportController(http.Controller):
    """Controller for handling XLSX report generation and download in Odoo."""

    @http.route('/xlsx_reports', type='http', auth='user', methods=['POST'],
                csrf=False)
    def get_report_xlsx(self, model, options, output_format, report_name,
                        report_data=None):
        """Endpoint to generate and download an XLSX report."""
        uid = request.session.uid
        report_obj = request.env[model].with_user(uid)
        token = 'dummy-because-api-expects-one'
        try:
            if output_format == 'xlsx':
                response = request.make_response(
                    None,
                    headers=[
                        ('Content-Type', 'application/vnd.ms-excel'),
                        ('Content-Disposition',
                         content_disposition(report_name + '.xlsx'))
                    ]
                )
                try:
                    report_obj.get_xlsx_report(options, response, report_data)
                except Exception:
                    report_obj.get_xlsx_report(json.loads(options), response)
                response.set_cookie('fileToken', token)
                return response
        except Exception as e:
            se = _serialize_exception(e)
            error = {
                'code': 200,
                'message': 'Odoo Server Error',
                'data': se
            }
            return request.make_response(html_escape(json.dumps(error)))

    @http.route('/get_operation_types', auth='public', type='json')
    def get_operation_types(self):
        no_transfer = {}
        stock_picking_type = request.env['stock.picking.type'].search([])
        stock_picking = request.env['stock.picking'].search([])
        stock = []
        length = []
        names = []
        late = {}
        query = '''select stock_picking.picking_type_id, count(stock_picking.
                picking_type_id) from stock_picking
                    inner join stock_picking_type on stock_picking.picking_type_id = 
                    stock_picking_type.id
                    where stock_picking.company_id = %s and
                    stock_picking.state in ('assigned', 'waiting', 'confirmed') and 
                    (has_deadline_issue = true or 
                    date_deadline <= now() or scheduled_date <= now())
                    group by stock_picking.picking_type_id''' % request.env.company.id
        request._cr.execute(query)
        lates = request._cr.dictfetchall()
        for rec in lates:
            late.update({rec.get('picking_type_id'): rec.get('count')})
        waiting = {}
        backorder = {}
        operation_type_name = {}
        for type in stock_picking_type:
            names.append(type.name)
            orders = stock_picking.filtered(
                lambda r: r.picking_type_id.id == type.id)
            stock.append(len(orders))
            length_stock_picking = len(orders)
            length.append(len(stock_picking.filtered(
                lambda r: r.picking_type_id.id == type.id)))
            no_transfer.update({type.id: length_stock_picking})
            operation_type_name.update({type.id: type.name})
            if len(orders) > 0:
                if len(orders.filtered(lambda r: r.state == 'confirmed')) > 0:
                    waiting.update({type.id: len(
                        orders.filtered(lambda r: r.state == 'confirmed'))})
                if len(orders.mapped('backorder_id')) > 0:
                    backorder.update(
                        {type.id: len(orders.mapped('backorder_id'))})
        return no_transfer, late, waiting, operation_type_name, backorder

    @http.route('/get_the_top_products', auth='public', type='json')
    def get_the_top_products(self):
        company_id = request.env.company.id
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
        request._cr.execute(query)
        top_product = request._cr.dictfetchall()
        total_quantity = []
        product_name = []
        for record in top_product[:10]:
            total_quantity.append(record.get('sum'))
            product_name.append((record.get('name', {}).get('en_US') if isinstance(record.get('name'), dict) else record.get('name')))
        value = {'products': product_name, 'count': total_quantity}
        return value

    @http.route('/get_stock_moves', auth='public', type='json')
    def get_stock_moves(self):
        """rpc method of stock moves graph
            Returns location name and quantity_done"""
        company_id = request.env.company.id
        query = ('''select stock_location.complete_name, count(stock_move.id) 
                    from stock_move inner join stock_location on stock_move.
                    location_id = stock_location.id where stock_move.state = 'done' 
                and stock_move.company_id = %s group by stock_location.complete_name
                ''' % company_id)
        request._cr.execute(query)
        stock_move = request._cr.dictfetchall()
        count = []
        complete_name = []
        for record in stock_move:
            count.append(record.get('count'))
            complete_name.append(record.get('complete_name'))
        value = {'name': complete_name, 'count': count}
        return value

    @http.route('/get_stock_moves', auth='public', type='json')
    def get_stock_moves(self):
        company_id = request.env.company.id
        query = ('''select stock_location.complete_name, count(stock_move.id) 
                        from stock_move inner join stock_location on stock_move.
                        location_id = stock_location.id where stock_move.state = 'done' 
                    and stock_move.company_id = %s group by stock_location.complete_name
                    ''' % company_id)
        request._cr.execute(query)
        stock_move = request._cr.dictfetchall()
        count = []
        complete_name = []
        for record in stock_move:
            count.append(record.get('count'))
            complete_name.append(record.get('complete_name'))
        value = {'name': complete_name, 'count': count}
        return value

    @http.route('/get_product_moves', auth='public', type='json')
    def get_product_moves(self):
        """rpc method of product moves graph
            Returns product move product and quantity_done"""
        company_id = request.env.company.id
        query = ('''select product_template.name,sum(stock_move_line.quantity)
         from stock_move_line
                inner join product_product on stock_move_line.product_id = 
                product_product.id
                inner join product_template on product_product.product_tmpl_id =
                 product_template.id
                where stock_move_line.company_id = %s group by
                 product_template.name''' % company_id)
        request._cr.execute(query)
        products_quantity = request._cr.dictfetchall()
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
        request._cr.execute(category_query)
        category = request._cr.dictfetchall()
        category_id = []
        category_name = []
        for record in category:
            category_id.append(record.get('id'))
            category_name.append(record.get('name'))
        value1 = {'category_id': category_id, 'category_name': category_name}
        return value, value1

    @http.route('/get_product_category', auth='public', type='json')
    def get_product_category(self):
        """rpc method of product category graph
        Returns product categories and category having on hand product quantity"""
        category_ids = request.env['product.category'].search([])
        category_name = []
        product_count = []
        for rec in category_ids:
            name = rec.name
            category_name.append(name)
            count = rec.product_count
            product_count.append(count)
        value = {'name': category_name, 'count': product_count}
        return value

    @http.route('/product_move_by_category', auth='public', type='json')
    def product_move_by_category(self, args):
        """rpc method of product moves by category
            Returns category name and quantity_done"""
        category_id = int(args)
        company_id = request.env.company.id
        query = ('''select product_template.name,sum(stock_move_line.quantity) 
        from stock_move_line inner join product_product on stock_move_line.
        product_id = product_product.id inner join product_template on 
        product_product.product_tmpl_id = product_template.id inner join 
        product_category on product_template.categ_id = product_category.id
        where stock_move_line.company_id = %s and product_category.id = %s 
        group by product_template.name''' %
                 (company_id, category_id))
        request._cr.execute(query)
        product_move = request._cr.dictfetchall()
        quantity_done = []
        name = []
        for record in product_move:
            quantity_done.append(record.get('sum'))
            name.append((record.get('name', {}).get('en_US') if isinstance(record.get('name'), dict) else record.get('name')))
        value = {
            'name': name,
            'count': quantity_done,
        }
        return value

    @http.route('/get_locations', auth='public', type='json')
    def get_locations(self):
        """rpc method of product location table
               Returns locations and location having on hand product quantity"""
        stock_quant_ids = request.env['stock.quant'].search([])
        locations = stock_quant_ids.mapped('location_id')
        value = {}
        for rec in locations:
            loc_stock_quant = stock_quant_ids.filtered(
                lambda x: x.location_id == rec)
            on_hand_quantity = sum(
                loc_stock_quant.mapped('inventory_quantity_auto_apply'))
            value[rec.name] = on_hand_quantity
        return value

    @http.route('/get_out_of_stock', auth='public', type='json')
    def get_out_of_stock(self):
        """rpc method of out of stock graph
        Returns products and quantity"""
        company_id = request.env.company.id
        sett_out_stock_bool = request.env['ir.config_parameter'].sudo(). \
            get_param("inventory_stock_dashboard_odoo.out_of_stock", default="")
        sett_out_stock_quantity = request.env['ir.config_parameter'].sudo(). \
            get_param("inventory_stock_dashboard_odoo.out_of_stock_quantity",
                      default="")
        if sett_out_stock_bool == "True":
            if sett_out_stock_quantity:
                out_stock_value = int(sett_out_stock_quantity)
                query = '''select product_template.name,sum(stock_quant.quantity)
                     from stock_quant inner join product_product on stock_quant.
                     product_id = product_product.id inner join product_template on 
                     product_product.product_tmpl_id = product_template.id  where 
                     stock_quant.quantity < %s and stock_quant.company_id = %s group
                     by product_template.name''' \
                        % (out_stock_value, company_id)
                request._cr.execute(query)
                result = request._cr.fetchall()
                total_quantity = []
                for record in result:
                    total_quantity.append(record[1])
                product_name = []
                for record in result:
                    product_name.append(record[0])
                value = {
                    'product_name': product_name,
                    'total_quantity': total_quantity
                }
                return value

    @http.route('/get_dead_of_stock', auth='public', type='json')
    def get_dead_of_stock(self):
        """rpc method of dead of stock graph
        Returns product name and dead quantity"""
        company_id = request.env.company.id
        sett_dead_stock_bool = request.env['ir.config_parameter'].sudo(). \
            get_param("inventory_stock_dashboard_odoo.dead_stock_bol",
                      default="")
        sett_dead_stock_quantity = request.env[
            'ir.config_parameter'].sudo().get_param(
            "inventory_stock_dashboard_odoo.dead_stock",
            default="")
        sett_dead_stock_type = request.env['ir.config_parameter'].sudo().get_param(
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
                request._cr.execute(query)
                result = request._cr.fetchall()
                total_quantity = []
                product_name = []
                for record in result:
                    if record[1] > 0:
                        complete_name = request.env['product.product'].browse(
                            record[0]).display_name
                        product_name.append(complete_name)
                        total_quantity.append(record[1])
                value = {
                    'product_name': product_name,
                    'total_quantity': total_quantity
                }
                return value

    @http.route('/top_products_last_ten', auth='public', type='json')
    def top_products_last_ten(self):
        """rpc method of top products graph for last 10 days
        Returns top ten products and done quantity"""
        company_id = request.env.company.id
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
        request._cr.execute(query)
        top_product = request._cr.dictfetchall()
        total_quantity = []
        product_name = []
        for record in top_product[:10]:
            total_quantity.append(record.get('sum'))
            product_name.append((record.get('name', {}).get('en_US') if isinstance(record.get('name'), dict) else record.get('name')))
        value = {'products': product_name, 'count': total_quantity}
        return value

    @http.route('/top_products_last_thirty', auth='public', type='json')
    def top_products_last_thirty(self):
        """rpc method of top products graph for last 30 days
        Returns top ten products and done quantity"""
        company_id = request.env.company.id
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
        request._cr.execute(query)
        top_product = request._cr.dictfetchall()
        total_quantity = []
        product_name = []
        for record in top_product[:10]:
            total_quantity.append(record.get('sum'))
            product_name.append((record.get('name', {}).get('en_US') if isinstance(record.get('name'), dict) else record.get('name')))
        value = {'products': product_name, 'count': total_quantity}
        return value

    @http.route('/top_products_last_three_months', auth='public', type='json')
    def top_products_last_three_months(self):
        """RPC method of top products graph select last 3 months
        Returns top ten products and done quantity"""
        company_id = request.env.company.id
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
        request._cr.execute(query, (company_id, start_three_months_ago, now))
        top_product = request._cr.dictfetchall()
        total_quantity = []
        product_name = []
        for record in top_product[:10]:
            total_quantity.append(record.get('sum'))
            product_name.append((record.get('name', {}).get('en_US') if isinstance(record.get('name'), dict) else record.get('name')))
        value = {'products': product_name, 'count': total_quantity}
        return value

    @http.route('/top_products_last_year', auth='public', type='json')
    def top_products_last_year(self):
        """RPC method of top products graph select last year
        Returns top ten products and done quantity"""
        company_id = request.env.company.id
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
        request._cr.execute(query, (company_id, start_last_year, end_last_year))
        top_product = request._cr.dictfetchall()
        total_quantity = []
        product_name = []
        for record in top_product[:10]:
            total_quantity.append(record.get('sum'))
            product_name.append((record.get('name', {}).get('en_US') if isinstance(record.get('name'), dict) else record.get('name')))
        value = {'products': product_name, 'count': total_quantity}
        return value

    @http.route('/stock_move_last_ten_days', auth='public', type='json')
    def stock_move_last_ten_days(self, post):
        """rpc method of stock moves graph select last ten days
            Returns location name and quantity_done"""
        company_id = request.env.company.id
        query = ('''select stock_location.name,sum(stock_move_line.quantity) 
                from stock_move_line inner join stock_location on 
                stock_move_line.location_id = stock_location.id where 
                stock_move_line.state = 'done' and stock_move_line.company_id =
                 %s and stock_move_line.create_date between (now() - interval 
                 '10 day') and now() group by stock_location.name'''
                 % company_id)
        request._cr.execute(query)
        location_quantity = request._cr.dictfetchall()
        quantity_done = []
        name = []
        for record in location_quantity:
            quantity_done.append(record.get('sum'))
            name.append(record.get('name'))
        value = {'name': name, 'count': quantity_done}
        return value

    @http.route('/this_month', auth='public', type='json')
    def this_month(self, post):
        """RPC method of stock moves graph select this month
        Returns location name and quantity_done"""
        company_id = request.env.company.id
        now = datetime.now()
        start_this_month = datetime(now.year, now.month, 1)
        end_this_month = now
        query = '''
        SELECT stock_location.name, SUM(stock_move_line.quantity)
        FROM stock_move_line
        INNER JOIN stock_location ON stock_move_line.location_id = stock_location.id
        WHERE stock_move_line.state = 'done'
          AND stock_move_line.company_id = %s
          AND stock_move_line.create_date BETWEEN %s AND %s
        GROUP BY stock_location.name
        '''
        request._cr.execute(query, (company_id, start_this_month, end_this_month))
        location_quantity = request._cr.dictfetchall()
        quantity_done = []
        name = []
        for record in location_quantity:
            quantity_done.append(record.get('sum'))
            name.append(record.get('name'))
        value = {'name': name, 'count': quantity_done}
        return value

    @http.route('/last_three_month', auth='public', type='json')
    def last_three_month(self, post):
        """rpc method of stock moves graph select 3 month
            Returns location name and quantity_done"""
        company_id = request.env.company.id
        query = ('''select stock_location.name,sum(stock_move_line.quantity) 
        from stock_move_line inner join stock_location on stock_move_line.
        location_id = stock_location.id where stock_move_line.state = 
        'done' and stock_move_line.company_id = %s and stock_move_line.
        create_date between (now() - interval '3 months') and now() group by 
        stock_location.name''' % company_id)
        request._cr.execute(query)
        location_quantity = request._cr.dictfetchall()
        quantity_done = []
        name = []
        for record in location_quantity:
            quantity_done.append(record.get('sum'))
            name.append(record.get('name'))
        value = {'name': name, 'count': quantity_done}
        return value

    @http.route('/last_year', auth='public', type='json')
    def last_year(self, post):
        """RPC method of stock moves graph select last year
        Returns location name and quantity_done"""
        company_id = request.env.company.id
        now = datetime.now()
        start_last_year = datetime(now.year - 1, 1, 1)
        end_last_year = datetime(now.year - 1, 12, 31, 23, 59, 59)
        query = '''
        SELECT stock_location.name, SUM(stock_move_line.quantity) 
        FROM stock_move_line
        INNER JOIN stock_location ON stock_move_line.location_id = stock_location.id
        WHERE stock_move_line.state = 'done'
          AND stock_move_line.company_id = %s
          AND stock_move_line.create_date BETWEEN %s AND %s
        GROUP BY stock_location.name
        '''
        request._cr.execute(query, (company_id, start_last_year, end_last_year))
        location_quantity = request._cr.dictfetchall()
        quantity_done = []
        name = []
        for record in location_quantity:
            quantity_done.append(record.get('sum'))
            name.append(record.get('name'))
        value = {'name': name, 'count': quantity_done}
        return value

    @http.route('/inventory_report', auth='public', type='json')
    def inventory_report(self, post=None):
            """ Inventory report """
            if post:
                report_values = request.env['dynamic.inventory.report'].search(
                    [('id', '=', post[0])])
                data = {
                    'report_type': report_values.report_type,
                     }

                if report_values.date_from:
                    data.update({
                        'date_from': report_values.date_from,
                    })
                if report_values.date_to:
                    data.update({
                        'date_to': report_values.date_to,
                    })
                filters = request.get_filter(post)
                lines = request._get_report_values(data).get('INVENTORY')
                return {
                    'name': "Inventory Orders",
                    'type': 'ir.actions.client',
                    'tag': 's_r',
                    'orders': data,
                    'filters': filters,
                    'report_lines': lines,
                }








