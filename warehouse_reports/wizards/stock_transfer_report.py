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


class StockTransferReport(models.TransientModel):
    """Wizard for stock transfer reports in PDF and Excel formats."""

    _name = "stock.transfer.report"
    _description = "Stock Transfer Report"

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
    picking_type_id = fields.Many2one(
        'stock.picking.type',
        string="Operation Type",
        help="Filter by operation type",
    )
    partner_id = fields.Many2one(
        'res.partner',
        string="Customer/Vendor",
        help="Filter by customer or vendor",
    )
    from_date = fields.Datetime(
        string="Date From",
        help="Filter stock transfers from this date",
        required=False,
    )
    to_date = fields.Datetime(
        string="To Date",
        help="Filter stock transfers up to this date",
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

    def _get_stock_transfers(self):
        """Fetch stock transfers dynamically using SQL parameters based on set filters."""
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
                        stock_picking.name as picking_name,
                        product_template.name->>%s as product_name,
                        stock_picking.scheduled_date, stock_picking.date_deadline,
                        stock_picking.date_done, stock_picking.origin,
                        stock_location.complete_name as complete_name,
                        stock_picking.picking_type_id,
                        res_company.name as company_name, COALESCE(stock_picking.state, 'draft') as state
                        FROM CategoryHierarchy
                        JOIN product_category on CategoryHierarchy.id = product_category.id
                        JOIN product_template on product_category.id = product_template.categ_id
                        JOIN product_product on product_template.id = product_product.product_tmpl_id
                        JOIN stock_move on product_product.id = stock_move.product_id
                        JOIN stock_picking on stock_move.picking_id = stock_picking.id
                        JOIN stock_picking_type on stock_picking.picking_type_id = stock_picking_type.id
                        JOIN res_company on stock_picking.company_id = res_company.id
                        JOIN stock_location on stock_move.location_id = stock_location.id
                        WHERE product_category.id IN (SELECT id FROM CategoryHierarchy)"""
            params.extend([self.product_category_id.id, lang, lang])
        else:
            query = """ SELECT product_category.id as category_id,
                        product_category.name->>%s as category_name,
                        stock_picking.name as picking_name,
                        product_template.name->>%s as product_name,
                        stock_picking.scheduled_date, stock_picking.date_deadline,
                        stock_picking.date_done, stock_picking.origin,
                        stock_location.complete_name as complete_name,
                        stock_picking.picking_type_id,
                        res_company.name as company_name, COALESCE(stock_picking.state, 'draft') as state
                        FROM product_category
                        JOIN product_template on product_category.id = product_template.categ_id
                        JOIN product_product on product_template.id = product_product.product_tmpl_id
                        JOIN stock_move on product_product.id = stock_move.product_id
                        JOIN stock_picking on stock_move.picking_id = stock_picking.id
                        JOIN stock_picking_type on stock_picking.picking_type_id = stock_picking_type.id
                        JOIN res_company on stock_picking.company_id = res_company.id
                        JOIN stock_location on stock_move.location_id = stock_location.id
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
        if self.picking_type_id:
            query += " AND stock_picking.picking_type_id = %s"
            params.append(self.picking_type_id.id)
        if self.partner_id:
            query += " AND stock_picking.partner_id = %s"
            params.append(self.partner_id.id)
        if self.company_id:
            query += " AND stock_picking.company_id = %s"
            params.append(self.company_id.id)
        if self.from_date and self.to_date and self.from_date == self.to_date:
            query += " AND stock_picking.scheduled_date <= %s"
            params.append(self.to_date)
        else:
            if self.from_date:
                query += " AND stock_picking.scheduled_date >= %s"
                params.append(self.from_date)
            if self.to_date:
                query += " AND stock_picking.scheduled_date <= %s"
                params.append(self.to_date)

        query += " ORDER BY stock_picking.scheduled_date DESC"

        self.env.cr.execute(query, tuple(params))
        res = self.env.cr.dictfetchall()

        picking_type_ids = [rec['picking_type_id'] for rec in res if rec.get('picking_type_id')]
        picking_types = self.env['stock.picking.type'].browse(picking_type_ids)
        pt_map = {pt.id: pt.display_name for pt in picking_types}

        comp_str = str(self.company_id.id) if self.company_id else '1'
        for rec in res:
            for k, v in list(rec.items()):
                if isinstance(v, dict):
                    rec[k] = v.get(lang) or v.get(comp_str) or next(iter(v.values()), '')
            rec['display_name'] = pt_map.get(rec.get('picking_type_id'), '')

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
            'stock_picking': self._get_stock_transfers(),
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
            'warehouse_reports.stock_transfer_report'
        ).report_action(None, data=data)

    def action_print_xls_report(self):
        """Pass data to the Excel report action."""
        data = self._get_report_data()
        return {
            'type': 'ir.actions.report',
            'report_type': 'xlsx',
            'data': {
                'model': 'stock.transfer.report',
                'output_format': 'xlsx',
                'options': json.dumps(data, default=json_default),
                'report_name': 'Stock Transfer Report',
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
        sheet.set_column(0, 10, 24)
        head = workbook.add_format(
            {'align': 'center', 'bold': True, 'font_size': '20px'}
        )
        txt = workbook.add_format({'align': 'center'})
        sheet.merge_range('B2:I3', 'STOCK TRANSFER REPORT', head)
        sheet.merge_range('D4:F4', data['company_name'], txt)
        sheet.write('A8', 'SL No.', txt)
        sheet.write('B8', 'Reference', txt)
        sheet.write('C8', 'Product', txt)
        sheet.write('D8', 'Scheduled Date', txt)
        sheet.write('E8', 'Deadline', txt)
        sheet.write('F8', 'Effective Date', txt)
        sheet.write('G8', 'Source Document', txt)
        sheet.write('H8', 'Location', txt)
        sheet.write('I8', 'Operation Type', txt)
        sheet.write('J8', 'Company Name', txt)
        sheet.write('K8', 'Status', txt)
        records = data['stock_picking']
        row = 9
        flag = 1
        for record in records:
            sched_date = (
                str(record['scheduled_date']) if record.get('scheduled_date') else ''
            )
            deadline = (
                str(record['date_deadline']) if record.get('date_deadline') else ''
            )
            date_done = (
                str(record['date_done']) if record.get('date_done') else ''
            )
            sheet.write(row, 0, flag, txt)
            sheet.write(row, 1, record['picking_name'] or '', txt)
            sheet.write(row, 2, record['product_name'] or '', txt)
            sheet.write(row, 3, sched_date, txt)
            sheet.write(row, 4, deadline, txt)
            sheet.write(row, 5, date_done, txt)
            sheet.write(row, 6, record['origin'] or '', txt)
            sheet.write(row, 7, record['complete_name'] or '', txt)
            sheet.write(row, 8, record['display_name'] or '', txt)
            sheet.write(row, 9, record['company_name'] or '', txt)
            sheet.write(row, 10, state.get(record['state'], record['state']), txt)
            flag += 1
            row += 1
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
