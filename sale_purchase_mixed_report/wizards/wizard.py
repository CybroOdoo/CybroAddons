# -*- coding: utf-8 -*-
################################################################################
#
#   Cybrosys Technologies Pvt. Ltd.
#
#   Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#   Author: Mohammed Ajmal P (odoo@cybrosys.com)
#
#   You can modify it under the terms of the GNU AFFERO
#   GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#   This program is distributes in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#   GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#   You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#   (AGPL v3) along this program.
#   If not, see <http://www.gnu.org/license/>.
#
################################################################################
import io
import json

import datetime
from odoo import fields, models
from odoo.exceptions import ValidationError
from odoo.tools import date_utils

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


class SalePurchasePrintReport(models.TransientModel):
    """Fields and functions for the wizard for filtering"""
    _name = 'wizard.sale.purchase.report'
    _description = 'Sale Purchase Report Print'

    date_from = fields.Datetime('Date From')
    date_to = fields.Datetime('Date To')
    partner_ids = fields.Many2many(
        'res.partner', string='Partners',
        domain=lambda self: [('company_id', 'in',
                              [False, self.env.company.id])])
    sale_order_ids = fields.Many2many(
        'sale.order', string='Sale Orders',
        domain=lambda self: [('company_id', 'in',
                              [False, self.env.company.id])]
    )
    purchase_order_ids = fields.Many2many(
        'purchase.order', string='Purchase  Orders', domain=lambda self: [
            ('company_id', 'in', [False, self.env.company.id])]
    )

    def print_pdf_report(self):
        """Button function to print PDF Report"""
        if self.date_from and self.date_to and self.date_from > self.date_to:
            raise ValidationError('From Date must be less than of To Date!!!')
        data = {
            'model': self._name,
            'form': self.read()[0],
        }
        return self.env.ref(
            'sale_purchase_mixed_report.action_report_sale_purchase'
        ).report_action(self, data=data)

    def print_xlsx_report(self):
        """Button function to print Xlsx Report"""
        if self.date_from and self.date_to and self.date_from > self.date_to:
            raise ValidationError('From Date must be less than of To Date!!!')
        data = {
            'model': self._name,
            'form': self.read()[0],
        }
        return {
            'type': 'ir.actions.report',
            'data': {'model': self._name,
                     'options': json.dumps(data,
                                           default=date_utils.json_default),
                     'output_format': 'xlsx_controller',
                     'report_name': 'Sales Purchase Report',
                     },
            'report_type': 'xlsx_controller',
        }

    def get_xlsx_report(self, data, response):
        """Create and add data to the excel sheet"""
        company_id = self.env.company
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet()
        head_format = workbook.add_format({
            'align': 'center',
            'bold': True,
            'font_size': '10px'
        })
        data_format = workbook.add_format({
            'font_size': '10px'
        })
        sheet.write(0, 0, 'Order Date', head_format)
        sheet.write(0, 1, 'Order Type', head_format)
        sheet.write(0, 2, 'Order Ref', head_format)
        sheet.write(0, 3, 'Partner', head_format)
        sheet.write(0, 4, 'Product', head_format)
        sheet.write(0, 5, 'Product Type', head_format)
        sheet.write(0, 6, 'Qty Ordered', head_format)
        sheet.write(0, 7, 'Qty Delivered/Received', head_format)
        sheet.write(0, 8, 'Qty To Deliver/To Receive', head_format)
        sheet.write(0, 9, 'Qty Invoiced/Billed', head_format)
        sheet.write(0, 10, 'UOM', head_format)
        sheet.write(0, 11, 'Unit Price', head_format)
        sheet.write(0, 12, 'Total Price', head_format)
        sheet.write(0, 13, 'Currency', head_format)
        sheet.write(0, 14, 'Order State', head_format)
        where_sale = """so.company_id = %s""" % (
            company_id.id)
        where_purchase = """po.company_id = %s""" % (
            company_id.id)
        if data['form']['date_from']:
            where_sale += """AND so.date_order >= '%s'""" % (
                data['form']['date_from'])
            where_purchase += """AND po.date_order >= '%s'""" % (
                data['form']['date_from'])
        if data['form']['date_to']:
            where_sale += """AND so.date_order <= '%s'""" % (
                data['form']['date_to'])
            where_purchase += """AND po.date_order <= '%s'""" % (
                data['form']['date_to'])
        if data['form']['partner_ids']:
            if len(data['form']['partner_ids']) == 1:
                where_sale += """AND so.partner_id = %s""" % (
                    data['form']['partner_ids'][0])
                where_purchase += """AND po.partner_id = %s""" % (
                    data['form']['partner_ids'][0])
            else:
                where_sale += """AND so.partner_id in %s""" % (
                    str(tuple(data['form']['partner_ids'])))
                where_purchase += """AND po.partner_id in %s""" % (
                    str(tuple(data['form']['partner_ids'])))
        if data['form']['sale_order_ids']:
            if len(data['form']['sale_order_ids']) == 1:
                where_sale += """AND so.id = %s""" % (
                    data['form']['sale_order_ids'][0])
            else:
                where_sale += """AND so.id in %s""" % (
                    str(tuple(data['form']['sale_order_ids'])))
        if data['form']['purchase_order_ids']:
            if len(data['form']['purchase_order_ids']) == 1:
                where_purchase += """AND po.id = %s""" % (
                    data['form']['purchase_order_ids'][0])
            else:
                where_purchase += """AND po.id in %s""" % (
                    str(tuple(data['form']['purchase_order_ids'])))
        self.env.cr.execute("""
            select macro.id as id,
                macro.order_type as order_type,
                macro.order_state as order_state,
                macro.order_date as order_date,
                macro.partner_id as partner_id,
                macro.product_id as product_id,
                macro.order_ref as order_ref,
                macro.unit_price_sale as unit_price_sale,
                macro.unit_price_purchase as unit_price_purchase,
                macro.price_total_sale as price_total_sale,
                macro.price_total_purchase as price_total_purchase,
                macro.price_subtotal_sale as price_subtotal_sale,
                macro.price_subtotal_purchase as price_subtotal_purchase,
                macro.product_type as product_type,
                macro.qty_invoiced as qty_invoiced,
                macro.qty_billed as qty_billed,
                macro.qty_ordered_to as qty_ordered_to,
                macro.qty_ordered_by as qty_ordered_by,
                macro.qty_delivered as qty_delivered,
                macro.qty_received as qty_received,
                macro.qty_to_deliver as qty_to_deliver,
                macro.qty_to_receive as qty_to_receive,
                macro.company_id as company_id,
                macro.currency_id as currency_id,
                macro.product_uom as product_uom
                from((
                    with currency_rate as (%s)""" % self.env[
            'res.currency']._select_companies_rates() +
                            """
                               select 
                               po.id as id,
                               po.date_order as order_date,
                               po.partner_id as partner_id,
                               po.company_id as company_id,
                               po.currency_id,
                               t.uom_id as product_uom,
                               po.state as order_state,
                               case when po.is_purchase_order=True then 
                               'Purchase' else '' end as order_type,
                               l.product_id as product_id,
                               t.detailed_type as product_type, 
                               po.name as order_ref,
                               0 as unit_price_sale,
                               case when l.product_id is not null then 
                               sum(l.price_unit) 
                               else 0 end as unit_price_purchase,
                               0 as price_total_sale,
                               sum(l.price_total / coalesce(po.currency_rate, 1.0))::decimal(16,2) * currency_table.rate as price_total_purchase,
                               0 as price_subtotal_sale,
                               sum(l.price_subtotal / coalesce(po.currency_rate, 1.0))::decimal(16, 2) * currency_table.rate as price_subtotal_purchase,
                               case when l.product_id is not null then 
                               sum(l.product_qty/ u.factor * u2.factor) else 0 
                               end as qty_ordered_to, 
                               case when l.product_id is not null then
                               sum(l.qty_received / u.factor * u2.factor) else 0
                               end as qty_received, 
                               case when l.product_id is not null then 
                               sum(l.qty_invoiced / u.factor * u2.factor) 
                               else 0 end as qty_billed,
                               case when l.product_id is not null then 
                               sum((l.product_qty - l.qty_received) / u.factor * u2.factor)
                               else 0 end as qty_to_receive,
                               0 as qty_ordered_by,
                               0 as qty_delivered,
                               0 as qty_invoiced,
                               0 as qty_to_deliver
                               from
                               (purchase_order_line l 
                               join purchase_order po on (l.order_id=po.id)
                               join res_partner partner on 
                               (po.partner_id=partner.id)
                               left join product_product p on 
                               (l.product_id=p.id)
                               left join product_template t on 
                               (p.product_tmpl_id=t.id)
                               left join uom_uom u on (l.product_uom=u.id)
                               left join uom_uom u2 on (t.uom_id=u2.id))
                               left join currency_rate cr on 
                               (cr.currency_id = po.currency_id 
                               and cr.company_id = po.company_id and cr.date_start <= coalesce(po.date_order, now()) and
                               (cr.date_end is null or cr.date_end > coalesce(po.date_order, now())))
                               left join {currency_table} on 
                               currency_table.company_id = po.company_id
                               """.format(
                                currency_table=self.env[
                                    'res.currency']._get_query_currency_table(
                                    {'multi_company': True,
                                     'date': {
                                         'date_to': fields.Date.today()}}), ) +
                            """
                                           where %s
                                           group by
                                           po.partner_id,
                                           po.date_order,
                                           l.product_id,
                                           t.uom_id,
                                           t.detailed_type,
                                           po.id,
                                           currency_table.rate,
                                           t.purchase_method
                                           order by l.product_id)
                                        UNION ALL
                                           (select 
                                           so.id as id,
                                           so.date_order as order_date,
                                           so.partner_id as partner_id,
                                           so.company_id as company_id,
                                           so.currency_id,
                                           t.uom_id as product_uom,
                                           so.state as order_state,
                                           case when so.is_sale_order=True then 
                                           'Sale' else '' end as order_type,
                                           s.product_id as product_id,
                                           t.detailed_type as product_type,
                                           so.name as order_ref,
                                           case when s.product_id is not null 
                                           then sum(s.price_unit)
                                           else 0 end as unit_price_sale,
                                           0 as unit_price_purchase,
                                           case when s.product_id is not null 
                                           then sum(s.price_total / case coalesce(so.currency_rate, 0)
                                           when 0  then 1.0 else 
                                           so.currency_rate end) else 0 end 
                                           as price_total_sale,
                                           0 as price_total_purchase,
                                           case when s.product_id is not null 
                                           then sum(s.price_subtotal / case coalesce(so.currency_rate, 0)
                                           when 0  then 1.0 else 
                                           so.currency_rate end) else
                                           0 end as price_subtotal_sale,
                                           0 as price_subtotal_purchase,
                                           0 as qty_ordered_to,
                                           0 as qty_received,
                                           0 as qty_billed,
                                           0 as qty_to_receive,
                                           case when s.product_id is not null 
                                           then sum(s.product_uom_qty / u.factor * u2.factor) else 0 end as 
                                           qty_ordered_by,
                                           case when s.product_id is not null 
                                           then sum(s.qty_delivered / u.factor * u2.factor) else 0 end as
                                           qty_delivered,
                                           case when s.product_id is not null 
                                           then sum(s.qty_invoiced / u.factor * u2.factor) else 0 end as
                                           qty_invoiced,
                                           case when s.product_id is not null 
                                           then sum((s.product_uom_qty - s.qty_delivered) / u.factor * u2.factor)
                                           else 0 end as qty_to_deliver
                                           from
                                           (sale_order_line s
                                           join sale_order so on (s.order_id=so.id)
                                           join res_partner partner on 
                                           (so.partner_id=partner.id)
                                           left join product_product p on 
                                           (s.product_id=p.id)
                                           left join product_template t on 
                                           (p.product_tmpl_id=t.id)
                                           left join uom_uom u on 
                                           (s.product_uom=u.id)
                                           left join uom_uom u2 on 
                                           (t.uom_id=u2.id))
                                           where %s
                                           group by
                                           so.partner_id,
                                           so.date_order,
                                           s.product_id,
                                           t.uom_id,
                                           t.detailed_type,
                                           so.id
                                           order by s.product_id))
                                        macro
                                        group by
                                        macro.partner_id,
                                        macro.order_date,
                                        macro.order_state,
                                        macro.product_id,
                                        macro.id,
                                        macro.order_ref,
                                        macro.order_type,
                                        macro.unit_price_sale,
                                        macro.unit_price_purchase,
                                        macro.product_type,
                                        macro.qty_invoiced,
                                        macro.qty_billed,
                                        macro.qty_delivered,
                                        macro.qty_received,
                                        macro.qty_ordered_to,
                                        macro.qty_ordered_by,
                                        macro.qty_to_deliver,
                                        macro.qty_to_receive,
                                        macro.price_total_sale,
                                        macro.price_total_purchase,
                                        macro.price_subtotal_sale,
                                        macro.price_subtotal_purchase,
                                        macro.company_id,
                                        macro.currency_id,
                                        macro.product_uom
                                        order by macro.product_id    
           """ % (where_purchase, where_sale))
        rec = self.env.cr.fetchall()
        j = 1
        k = 0
        for i in range(0, len(rec)):
            product_id = self.env['product.product'].browse(rec[i][5])
            uom_id = self.env['uom.uom'].browse(rec[i][24])
            # currency_id = self.env['res.currency'].browse(rec[i][23])
            currency_id = company_id.currency_id
            partner_id = self.env['res.partner'].browse(rec[i][4])
            sheet.set_column(j, k, 15)
            sheet.write(j, 0, datetime.datetime.strftime(rec[i][3], '%m/%d/%Y'),
                        data_format)
            sheet.write(j, 1, rec[i][1], data_format)
            sheet.write(j, 2, rec[i][6], data_format)
            sheet.write(j, 3, partner_id.name, data_format)
            sheet.write(j, 4, product_id.display_name, data_format)
            sheet.write(j, 5, rec[i][13], data_format)
            sheet.write(j, 6, rec[i][17] if rec[i][1] == 'Sale' else rec[i][16],
                        data_format)
            sheet.write(j, 7, rec[i][18] if rec[i][1] == 'Sale' else rec[i][19],
                        data_format)
            sheet.write(j, 8, rec[i][20] if rec[i][1] == 'Sale' else rec[i][21],
                        data_format)
            sheet.write(j, 9, rec[i][14] if rec[i][1] == 'Sale' else rec[i][15],
                        data_format)
            sheet.write(j, 10, uom_id.name, data_format)
            sheet.write(j, 11, rec[i][7] if rec[i][1] == 'Sale' else rec[i][8],
                        data_format)
            sheet.write(j, 12, rec[i][9] if rec[i][1] == 'Sale' else rec[i][10],
                        data_format)
            sheet.write(j, 13, currency_id.name, data_format)
            sheet.write(j, 14, dict(
                self.env['sale.order']._fields['state'].selection).get(
                rec[i][2]) if rec[i][1] == 'Sale' else dict(
                self.env['purchase.order']._fields['state'].selection).get(
                rec[i][2]), data_format)
            j += 1
            k += 1
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
