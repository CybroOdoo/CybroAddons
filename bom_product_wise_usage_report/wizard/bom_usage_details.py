# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author:  Cybrosys Techno Solutions (odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0
#    (OPL-1) It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#    DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
#    OTHERWISE,ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE
#    USE OR OTHER DEALINGS IN THE SOFTWARE.
#
################################################################################
from datetime import datetime, time

from odoo import fields, models, _
from odoo.exceptions import ValidationError


class BomUsageReport(models.TransientModel):
    """Model in which fields are added to generate PDF reports regarding usage
    of products in different Bill of Materials while manufacturing process."""
    _name = 'bom.usage.details'
    _description = " For Generating Products Pdf Reports used in BOM "

    product_ids = fields.Many2many('product.product',
                                  string='Products',
                                  domain=lambda self:
                                  self._get_product_domain(),
                                  help="Select the products that used in BOM")
    from_date = fields.Date(string='From Date', help="Starting date of report")
    to_date = fields.Date(string='To Date', default=fields.Date.today,
                          help="Ending date of report")
    un_build_orders = fields.Boolean(string='Reduce un build orders',
                                     help="Remove the un build orders in "
                                          "report")
    byproducts = fields.Boolean(string='Show byproducts',
                                help="Show the Byproducts of BOM in report")

    def _get_product_domain(self):
        """Domain is passed dynamically such that the products is filtered and
        only the products in the company is shown in field."""
        return [('company_id', 'in', [False, self.env.company.id])]

    def action_get_report(self):
        """Button action to get the report data and pass to the report."""
        if (self.to_date and self.from_date) and str(self.from_date) >= str(
                self.to_date):
            raise ValidationError(_("Please check from date and to date"))
        un_build_dict = {}
        product_list = tuple(self.product_ids.ids)
        from_date = self.from_date
        to_date = self.to_date
        if self.from_date:
            from_date = datetime.combine(from_date, time.min)
        if self.to_date:
            to_date = datetime.combine(to_date, time.max)
        un_build = self.un_build_orders
        company_id = self.env.company.id
        body = []
        heading = []
        query = """SELECT DISTINCT mrp_production.product_id AS
                    parent_product_id,
                    stock_move.product_id AS child_product_id,
                    SUM(stock_move.product_qty) AS child_product_used,
                    mrp_production.product_uom_id AS uom
                    FROM mrp_production
                    INNER JOIN stock_move ON 
                    mrp_production.id = 
                        stock_move.raw_material_production_id
                    WHERE mrp_production.id IN (SELECT
                            DISTINCT raw_material_production_id
                            FROM stock_move
                            WHERE raw_material_production_id IS NOT NULL)
                            AND mrp_production.state = 'done' AND 
                                stock_move.product_id IN %s AND
                            mrp_production.company_id = %s"""
        query_from_date = """ AND mrp_production.write_date >=  %s"""
        query_to_date = """ AND mrp_production.write_date <= %s """
        query_finish = """ GROUP BY mrp_production.product_id,
                                stock_move.product_id,mrp_production.
                                product_uom_id"""
        un_build_query = """SELECT
                                DISTINCT mrp_unbuild.product_id AS 
                                    parent_product_id,
                                stock_move.product_id AS child_product_id,
                                SUM(stock_move.product_qty) AS 
                                    child_quantity_used
                                FROM stock_move
                                INNER JOIN mrp_unbuild ON stock_move.unbuild_id 
                                    = mrp_unbuild.id
                                WHERE stock_move.state = 'done'
                                AND stock_move.unbuild_id IN  (SELECT
                                    DISTINCT unbuild_id
                                    FROM stock_move
                                    WHERE stock_move.product_id IN %s AND 
                                        stock_move.unbuild_id IS NOT NULL)"""
        un_build_query_from_date = """ AND mrp_unbuild.write_date >= %s """
        un_build_query_to_date = """ AND mrp_unbuild.write_date <= %s """
        un_build_query_finish = """GROUP BY mrp_unbuild.product_id,
                                    stock_move.product_id"""
        if not product_list:
            product_list = self.env['product.product'].search([]).mapped('id')
            product_list = tuple(product_list)
        if not from_date and not to_date:
            self.env.cr.execute(query + query_finish, (product_list,
                                                       company_id))
            query_data = self.env.cr.dictfetchall()
            if un_build:
                self.env.cr.execute(un_build_query + un_build_query_finish,
                                    (product_list,))
                un_build_dict = self.env.cr.dictfetchall()
        elif not from_date and to_date:
            self.env.cr.execute(query + query_to_date + query_finish,
                                (product_list, company_id, to_date))
            query_data = self.env.cr.dictfetchall()
            if un_build:
                self.env.cr.execute(un_build_query + un_build_query_to_date +
                                    un_build_query_finish,
                                    (product_list, to_date))
                un_build_dict = self.env.cr.dictfetchall()
        elif from_date and not to_date:
            self.env.cr.execute(query + query_from_date + query_finish,
                                (product_list, company_id,
                                 from_date))
            query_data = self.env.cr.dictfetchall()
            if un_build:
                self.env.cr.execute(un_build_query + un_build_query_from_date +
                                    un_build_query_finish, (product_list,
                                                            from_date))
                un_build_dict = self.env.cr.dictfetchall()
        else:
            self.env.cr.execute(query + query_from_date + query_to_date +
                                query_finish, (product_list, company_id,
                                               from_date, to_date))
            query_data = self.env.cr.dictfetchall()
            if un_build:
                self.env.cr.execute(
                    un_build_query + un_build_query_from_date +
                    un_build_query_to_date + un_build_query_finish,
                    (product_list, from_date, to_date))
                un_build_dict = self.env.cr.dictfetchall()
        for data in query_data:
            product_dict = {
                'parent_product_id': data['parent_product_id'],
                'parent_product_name': self.env['product.product'].sudo().
                search([('id', '=', data['parent_product_id'])]).display_name,
                'child_quantity_used': data['child_product_used'],
                'uom': self.env['uom.uom'].sudo().search([('id', '=',
                                                           data['uom'])]).name,
                'child_product_name': self.env[
                    'product.product'].sudo().search(
                    [('id', '=', data['child_product_id'])]).display_name,
                'child_product_id': data['child_product_id'],
            }
            if un_build:
                for rec in un_build_dict:
                    if data['child_product_id'] == rec['child_product_id'] and \
                            data['parent_product_id'] == rec['parent_product_id']:
                        product_dict['child_quantity_used'] = (
                                data['child_product_used'] -
                                rec['child_quantity_used'])
                        break
            if not product_dict['child_quantity_used'] < 1:
                body += [product_dict]
                heading.append({
                    'child_product_name':
                        self.env['product.product'].sudo().search(
                            [('id', '=',
                              data['child_product_id'])]).display_name
                })
        data = {
            'heading': heading,
            'body': body,
            'from_date': from_date,
            'to_date': to_date,
        }
        if not body:
            raise ValidationError(_("No data is available"))
        return self.env.ref(
            'bom_product_wise_usage_report.action_bom_usage_report'). \
            sudo().report_action(None, data=data)