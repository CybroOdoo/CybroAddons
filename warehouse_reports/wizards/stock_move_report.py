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


class StockMoveReport(models.TransientModel):
    """Wizard to get the stock move reports.

    Generates both PDF and Excel reports.
    """

    _name = "stock.move.report"
    _description = "Stock Move Report"

    product_id = fields.Many2one(
        'product.product',
        string="Product",
        help="Filter by specific product",
    )
    location_id = fields.Many2one(
        'stock.location',
        string="Location",
        help="Filter by stock location",
    )
    product_category_id = fields.Many2one(
        'product.category',
        string="Product Category",
        required=False,
        help="Filter by product category",
    )
    from_date = fields.Datetime(
        string="Date From",
        help="Filter stock moves from this date",
        required=False,
    )
    to_date = fields.Datetime(
        string="To Date",
        help="Filter stock moves up to this date",
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

    def _get_stock_moves(self):
        """Fetch stock moves dynamically using SQL parameters based on set filters."""
        lang = self.env.context.get('lang', 'en_US')
        params = []
        if self.product_category_id:
            query = """ WITH RECURSIVE CategoryHierarchy AS (
                        SELECT id, name, parent_id FROM product_category WHERE id = %s
                        UNION ALL
                        SELECT c.id, c.name, c.parent_id FROM product_category c
                        JOIN CategoryHierarchy ch ON c.parent_id = ch.id
                        )
                        SELECT stock_move.date, stock_move.reference,
                        stock_location.complete_name as complete_name,
                        stock_location.complete_name as location_name,
                        CategoryHierarchy.name->>%s as category_name,
                        stock_move.product_uom_qty, res_company.name,
                        stock_move.state, product_template.name->>%s as product_name
                        FROM stock_move
                        JOIN product_product ON stock_move.product_id = product_product.id
                        JOIN stock_location ON stock_move.location_id = stock_location.id
                        JOIN product_template ON product_product.product_tmpl_id = product_template.id
                        JOIN product_category ON product_template.categ_id = product_category.id
                        JOIN CategoryHierarchy ON CategoryHierarchy.id = product_category.id
                        JOIN res_company ON stock_move.company_id = res_company.id
                        WHERE product_category.id IN (SELECT id FROM CategoryHierarchy)"""
            params.extend([self.product_category_id.id, lang, lang])
        else:
            query = """ SELECT stock_move.date, stock_move.reference,
                        stock_location.complete_name as complete_name,
                        stock_location.complete_name as location_name,
                        product_category.name->>%s as category_name,
                        stock_move.product_uom_qty, res_company.name,
                        stock_move.state, product_template.name->>%s as product_name
                        FROM stock_move
                        JOIN product_product ON stock_move.product_id = product_product.id
                        JOIN stock_location ON stock_move.location_id = stock_location.id
                        JOIN product_template ON product_product.product_tmpl_id = product_template.id
                        JOIN product_category ON product_template.categ_id = product_category.id
                        JOIN res_company ON stock_move.company_id = res_company.id
                        WHERE 1=1"""
            params.extend([lang, lang])

        if self.product_id:
            query += " AND stock_move.product_id = %s"
            params.append(self.product_id.id)
        if self.location_id:
            loc_ids = tuple(
                self.env['stock.location'].search([
                    ('id', 'child_of', self.location_id.id),
                ]).ids
            )
            if loc_ids:
                query += " AND (stock_move.location_id IN %s OR stock_move.location_dest_id IN %s)"
                params.extend([loc_ids, loc_ids])
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

        comp_str = str(self.company_id.id) if self.company_id else '1'
        for rec in res:
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
            'location': (
                self.location_id.complete_name if self.location_id else ''
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
            'stock_move': self._get_stock_moves(),
        }

    def action_print_pdf_report(self):
        """Pass data to the PDF template and print."""
        state = {
            'draft': 'Draft',
            'waiting': 'Waiting Another Operation',
            'confirmed': 'Waiting',
            'assigned': 'Ready',
            'done': 'Done',
            'cancel': 'Cancelled',
        }
        data = self._get_report_data()
        data['status'] = state
        return self.env.ref(
            'warehouse_reports.stock_move_report'
        ).report_action(None, data=data)

    def action_print_xls_report(self):
        """Pass data to the Excel report action."""
        data = self._get_report_data()
        return {
            'type': 'ir.actions.report',
            'report_type': 'xlsx',
            'data': {
                'model': 'stock.move.report',
                'output_format': 'xlsx',
                'options': json.dumps(data, default=json_default),
                'report_name': 'Stock Move Report',
            },
        }

    def get_xlsx_report(self, data, response):
        """Customize Excel file and write data to response.

        :param data: Dictionary containing results
        :param response: Response from the controller
        """
        state = {
            'draft': 'Draft',
            'waiting': 'Waiting Another Operation',
            'confirmed': 'Waiting',
            'assigned': 'Ready',
            'done': 'Done',
            'cancel': 'Cancelled',
        }
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet()
        sheet.set_column(0, 8, 24)
        head = workbook.add_format(
            {'align': 'center', 'bold': True, 'font_size': '20px'}
        )
        txt = workbook.add_format({'align': 'center'})
        sheet.merge_range('B2:E3', 'STOCK MOVE REPORT', head)
        sheet.merge_range('C4:D4', data['company_name'], txt)
        sheet.write('A8', 'SL No.', txt)
        sheet.write('B8', 'Date', txt)
        sheet.write('C8', 'Reference', txt)
        sheet.write('D8', 'Product', txt)
        sheet.write('E8', 'Location', txt)
        sheet.write('F8', 'Quantity', txt)
        sheet.write('G8', 'Company', txt)
        sheet.write('H8', 'Product Category', txt)
        sheet.write('I8', 'Status', txt)
        records = data['stock_move']
        row = 9
        flag = 1
        for record in records:
            move_state = state.get(record.get('state', ''), record.get('state', ''))
            sheet.write(row, 0, flag, txt)
            sheet.write(row, 1, str(record.get('date')) if record.get('date') else '')
            sheet.write(row, 2, record.get('reference') or '')
            sheet.write(row, 3, record.get('product_name') or '')
            sheet.write(row, 4, record.get('location_name') or '')
            sheet.write(row, 5, record.get('product_uom_qty', 0.0), txt)
            sheet.write(row, 6, record.get('name') or '')
            sheet.write(row, 7, record.get('category_name') or '')
            sheet.write(row, 8, move_state, txt)
            flag += 1
            row += 1
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
