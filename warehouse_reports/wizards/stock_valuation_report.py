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

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.json import json_default


class StockValuationReport(models.TransientModel):
    """Wizard for stock valuation report with PDF and Excel output formats."""

    _name = "stock.valuation.report"
    _description = "Stock Valuation Report"

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
    from_date = fields.Datetime(
        string="Date From",
        help="Filter stock valuation entries from this date",
        required=False,
    )
    to_date = fields.Datetime(
        string="To Date",
        help="Filter stock valuation entries up to this date",
        required=False,
        default=fields.Datetime.now,
    )
    company_id = fields.Many2one(
        'res.company',
        string="Company",
        default=lambda self: self.env.company,
        help="Filter by company",
    )

    @api.constrains('from_date', 'to_date')
    def _check_date_range(self):
        """Validate that To Date is greater than or equal to From Date."""
        for rec in self:
            if rec.from_date and rec.to_date and rec.to_date < rec.from_date:
                raise ValidationError(
                    self.env._('To Date must be greater than or equal to From Date.')
                )

    def _get_stock_valuations(self):
        """Fetch stock valuation entries dynamically using SQL parameters."""
        lang = self.env.context.get('lang', 'en_US')
        params = []
        if self.product_category_id:
            query = """ WITH RECURSIVE CategoryHierarchy AS (
                        SELECT id, name, parent_id FROM product_category WHERE id = %s
                        UNION ALL
                        SELECT c.id, c.name, c.parent_id FROM product_category c
                        JOIN CategoryHierarchy ch ON c.parent_id = ch.id
                        )
                        SELECT CategoryHierarchy.id as category_id,
                        CategoryHierarchy.name->>%s as category_name,
                        stock_move.date as create_date, product_template.name->>%s as name,
                        stock_move.reference as description, res_company.name as company_name,
                        stock_move.product_id as product_id, stock_move.id as move_id,
                        stock_move.product_uom_qty as quantity,
                        COALESCE(stock_move.price_unit, 0.0) as unit_cost,
                        (stock_move.product_uom_qty * COALESCE(stock_move.price_unit, 0.0)) as value
                        FROM CategoryHierarchy
                        JOIN product_category on CategoryHierarchy.id = product_category.id
                        JOIN product_template on product_category.id = product_template.categ_id
                        JOIN product_product on product_template.id = product_product.product_tmpl_id
                        JOIN stock_move on product_product.id = stock_move.product_id
                        JOIN res_company on stock_move.company_id = res_company.id AND stock_move.state = 'done'
                        WHERE product_category.id IN (SELECT id FROM CategoryHierarchy)"""
            params.extend([self.product_category_id.id, lang, lang])
        else:
            query = """ SELECT product_category.id as category_id,
                        product_category.name->>%s as category_name,
                        stock_move.date as create_date, product_template.name->>%s as name,
                        stock_move.reference as description, res_company.name as company_name,
                        stock_move.product_id as product_id, stock_move.id as move_id,
                        stock_move.product_uom_qty as quantity,
                        COALESCE(stock_move.price_unit, 0.0) as unit_cost,
                        (stock_move.product_uom_qty * COALESCE(stock_move.price_unit, 0.0)) as value
                        FROM product_category
                        JOIN product_template on product_category.id = product_template.categ_id
                        JOIN product_product on product_template.id = product_product.product_tmpl_id
                        JOIN stock_move on product_product.id = stock_move.product_id
                        JOIN res_company on stock_move.company_id = res_company.id AND stock_move.state = 'done'
                        WHERE 1=1"""
            params.extend([lang, lang])

        if self.product_id:
            query += " AND stock_move.product_id = %s"
            params.append(self.product_id.id)
        if self.company_id:
            query += " AND stock_move.company_id = %s"
            params.append(self.company_id.id)
        if self.from_date and self.to_date and self.from_date == self.to_date:
            query += " AND stock_move.date <= %s"
            params.append(self.to_date)
        else:
            if self.from_date:
                query += " AND stock_move.date >= %s"
                params.append(self.from_date)
            if self.to_date:
                query += " AND stock_move.date <= %s"
                params.append(self.to_date)

        query += " ORDER BY stock_move.date DESC"

        self.env.cr.execute(query, tuple(params))
        res = self.env.cr.dictfetchall()

        # SVL layer fallback for unit_cost and value
        move_ids = [r['move_id'] for r in res if r.get('move_id')]
        svl_data = {}
        if move_ids and 'stock.valuation.layer' in self.env:
            svl_records = self.env['stock.valuation.layer'].search_read(
                [('stock_move_id', 'in', move_ids)],
                ['stock_move_id', 'unit_cost', 'value']
            )
            for svl in svl_records:
                move_id = svl['stock_move_id'][0]
                if move_id not in svl_data:
                    svl_data[move_id] = svl

        comp_str = str(self.company_id.id) if self.company_id else '1'
        for rec in res:
            move_id = rec.get('move_id')
            if move_id in svl_data:
                rec['unit_cost'] = svl_data[move_id].get('unit_cost', rec['unit_cost'])
                rec['value'] = svl_data[move_id].get('value', rec['value'])
            for k, v in rec.items():
                if isinstance(v, dict):
                    rec[k] = v.get(lang) or v.get(comp_str) or next(iter(v.values()), '')

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
            'stock_valuation': self._get_stock_valuations(),
        }

    def action_print_pdf_report(self):
        """Pass data to the PDF template and print."""
        data = self._get_report_data()
        return self.env.ref(
            'warehouse_reports.stock_valuation_report'
        ).report_action(None, data=data)

    def action_print_xls_report(self):
        """Pass data to the Excel report action."""
        data = self._get_report_data()
        return {
            'type': 'ir.actions.report',
            'report_type': 'xlsx',
            'data': {
                'model': 'stock.valuation.report',
                'output_format': 'xlsx',
                'options': json.dumps(data, default=json_default),
                'report_name': 'Stock Valuation Report',
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
        sheet.set_column(0, 9, 24)
        head = workbook.add_format(
            {'align': 'center', 'bold': True, 'font_size': '20px'}
        )
        txt = workbook.add_format({'align': 'center'})
        sheet.merge_range('B2:E3', 'STOCK VALUATION REPORT', head)
        sheet.merge_range('C4:D4', data['company_name'], txt)
        sheet.write('A8', 'SL No.', txt)
        sheet.write('B8', 'Date', txt)
        sheet.write('C8', 'Product Name', txt)
        sheet.write('D8', 'Description', txt)
        sheet.write('E8', 'Product Category', txt)
        sheet.write('F8', 'Company Name', txt)
        sheet.write('G8', 'Quantity', txt)
        sheet.write('H8', 'Unit Cost', txt)
        sheet.write('I8', 'Value', txt)
        records = data['stock_valuation']
        row = 9
        flag = 1
        for record in records:
            sheet.write(row, 0, flag, txt)
            sheet.write(row, 1, str(record.get('create_date')) if record.get('create_date') else '')
            sheet.write(row, 2, record.get('name') or '')
            sheet.write(row, 3, record.get('description') or '', txt)
            sheet.write(row, 4, record.get('category_name') or '', txt)
            sheet.write(row, 5, record.get('company_name') or '', txt)
            sheet.write(row, 6, record.get('quantity', 0.0), txt)
            sheet.write(row, 7, record.get('unit_cost', 0.0), txt)
            sheet.write(row, 8, record.get('value', 0.0), txt)
            flag += 1
            row += 1
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
