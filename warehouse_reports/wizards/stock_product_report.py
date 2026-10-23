# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
import io
import json
import xlsxwriter

from odoo import fields, models
from odoo.tools.json import json_default


class StockProductReport(models.TransientModel):
    """Wizard for printing product stock reports in PDF and Excel formats."""

    _name = "stock.product.report"
    _description = "Stock Product Report"

    product_id = fields.Many2one(
        'product.product',
        string="Product",
        help="Filter by specific product",
    )
    product_category_id = fields.Many2one(
        'product.category',
        string="Product Category",
        required=False,
        help="Filter by product category",
    )
    company_id = fields.Many2one(
        'res.company',
        string="Company",
        default=lambda self: self.env.company,
        help="Filter by company",
    )

    def _get_stock_products(self):
        """Fetch stock products dynamically using SQL parameters based on set filters."""
        lang = self.env.context.get('lang', 'en_US')
        comp_str = str(self.company_id.id) if self.company_id else '1'
        params = []
        # Note: product_category.name and product_template.name are PostgreSQL JSONB
        # translatable text columns. Numeric quantities (qty_available, free_qty,
        # incoming_qty, outgoing_qty) are NOT queried using SQL JSON operators;
        # they are computed via product.product ORM methods below.
        if self.product_category_id:
            query = """ WITH RECURSIVE CategoryHierarchy AS (
                        SELECT id, name, parent_id FROM product_category WHERE id = %s
                        UNION ALL
                        SELECT c.id, c.name, c.parent_id FROM product_category c
                        JOIN CategoryHierarchy ch ON c.parent_id = ch.id
                        )
                        SELECT CategoryHierarchy.id as category_id,
                        COALESCE(CategoryHierarchy.name->>%s, CategoryHierarchy.name->>'en_US', '') as category_name,
                        COALESCE(product_template.name->>%s, product_template.name->>'en_US', '') as product_name,
                        product_product.id as product_id
                        FROM CategoryHierarchy
                        JOIN product_category on CategoryHierarchy.id = product_category.id
                        JOIN product_template on product_category.id = product_template.categ_id
                        JOIN product_product on product_template.id = product_product.product_tmpl_id
                        WHERE 1=1"""
            params.extend([self.product_category_id.id, lang, lang])
        else:
            query = """ SELECT product_category.id as category_id,
                        COALESCE(product_category.name->>%s, product_category.name->>'en_US', '') as category_name,
                        COALESCE(product_template.name->>%s, product_template.name->>'en_US', '') as product_name,
                        product_product.id as product_id
                        FROM product_category
                        JOIN product_template on product_category.id = product_template.categ_id
                        JOIN product_product on product_template.id = product_product.product_tmpl_id
                        WHERE 1=1"""
            params.extend([lang, lang])

        if self.product_id:
            query += " AND product_product.id = %s"
            params.append(self.product_id.id)

        if self.company_id:
            query += " AND (product_template.company_id IS NULL OR product_template.company_id = %s)"
            params.append(self.company_id.id)

        self.env.cr.execute(query, tuple(params))
        res = self.env.cr.dictfetchall()

        product_ids = [rec['product_id'] for rec in res if rec.get('product_id')]
        products = self.env['product.product'].browse(product_ids)
        if self.company_id:
            products = products.with_company(self.company_id)
        product_map = {p.id: p for p in products}

        for rec in res:
            for k, v in list(rec.items()):
                if isinstance(v, dict):
                    rec[k] = v.get(lang) or v.get(comp_str) or next(iter(v.values()), '')
            prod = product_map.get(rec.get('product_id'))
            rec['qty_available'] = prod.qty_available if prod else 0.0
            rec['free_qty'] = prod.free_qty if prod else 0.0
            rec['incoming_qty'] = prod.incoming_qty if prod else 0.0
            rec['outgoing_qty'] = prod.outgoing_qty if prod else 0.0

        return res

    def _get_report_data(self):
        """Prepare common dictionary payload for PDF and Excel reports."""
        return {
            'product_name': (
                self.product_id.product_tmpl_id.name if self.product_id else ''
            ),
            'Product Category': (
                self.product_category_id.display_name if self.product_category_id else ''
            ),
            'company_name': self.company_id.name if self.company_id else '',
            'company_street': self.company_id.street if self.company_id else '',
            'state': (
                self.company_id.state_id.name
                if self.company_id and self.company_id.state_id else ''
            ),
            'country': (
                self.company_id.country_id.name
                if self.company_id and self.company_id.country_id else ''
            ),
            'company_email': self.company_id.email if self.company_id else '',
            'stock_product': self._get_stock_products(),
        }

    def action_print_pdf_report(self):
        """Pass data to the PDF template and print."""
        data = self._get_report_data()
        return self.env.ref(
            'warehouse_reports.stock_product_report'
        ).report_action(None, data=data)

    def action_print_xls_report(self):
        """Pass data to the Excel report action."""
        data = self._get_report_data()
        return {
            'type': 'ir.actions.report',
            'report_type': 'xlsx',
            'data': {
                'model': 'stock.product.report',
                'output_format': 'xlsx',
                'options': json.dumps(data, default=json_default),
                'report_name': 'Stock Product Report',
            },
        }

    def get_xlsx_report(self, data, response):
        """Customize Excel file and write data to response.

        :param data: Dictionary containing results
        :param response: Response from the controller
        """
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet()
        sheet.set_column(0, 8, 24)
        head = workbook.add_format(
            {'align': 'center', 'bold': True, 'font_size': '20px'}
        )
        txt = workbook.add_format({'align': 'center'})
        sheet.merge_range('B2:D3', 'STOCK REPORT', head)
        sheet.merge_range('B4:D4', data['company_name'], txt)
        sheet.write('A8', 'SL No.', txt)
        sheet.write('B8', 'Product Name', txt)
        sheet.write('C8', 'Product Category', txt)
        sheet.write('D8', 'On Hand Quantity', txt)
        sheet.write('E8', 'Quantity Unreserved', txt)
        sheet.write('F8', 'Incoming Quantity', txt)
        sheet.write('G8', 'Outgoing Quantity', txt)
        records = data['stock_product']
        row = 9
        flag = 1
        for record in records:
            sheet.write(row, 0, flag, txt)
            sheet.write(row, 1, record['product_name'] or '', txt)
            sheet.write(row, 2, record['category_name'] or '', txt)
            sheet.write(row, 3, record['qty_available'], txt)
            sheet.write(row, 4, record['free_qty'], txt)
            sheet.write(row, 5, record['incoming_qty'], txt)
            sheet.write(row, 6, record['outgoing_qty'], txt)
            flag += 1
            row += 1
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
