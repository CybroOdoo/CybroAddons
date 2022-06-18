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

from odoo import fields, models, api


class SalePurchasePdfReport(models.AbstractModel):
    """Class for PDF Report"""
    _name = 'report.sale_purchase_mixed_report.report_sale_purchase'
    _description = 'Sale Purchase mixed Pdf Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        """Returns PDF Report Values to template"""
        company_id = self.env.company
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
                macro.company_id as company_id,
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
                               case 
                               when po.state='draft' then 'draft_rfq'
                               when po.state='sent' then 'rfq_sent'
                               when po.state='to_approve' then 'to_approve'
                               when po.state='purchase' then 'purchase'
                               when po.state='done' then 'done' else
                               'cancel' end as order_state,
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
                               sum(l.qty_received / u.factor * u2.factor) 
                               else 0 end as qty_received, 
                               case when l.product_id is not null then 
                               sum(l.qty_invoiced / u.factor * u2.factor) 
                               else 0 end as qty_billed,
                               0 as qty_ordered_by,
                               0 as qty_delivered,
                               0 as qty_invoiced
                               from
                               (purchase_order_line l 
                               join purchase_order po on (l.order_id=po.id)
                               join res_partner partner on (po.partner_id=partner.id)
                               left join product_product p on (l.product_id=p.id)
                               left join product_template t on (p.product_tmpl_id=t.id)
                               left join uom_uom u on (l.product_uom=u.id)
                               left join uom_uom u2 on (t.uom_id=u2.id))
                               left join currency_rate cr on 
                               (cr.currency_id = po.currency_id 
                               and cr.company_id = po.company_id and 
                               cr.date_start <= coalesce(po.date_order, now()) 
                               and (cr.date_end is null or cr.date_end > coalesce(po.date_order, now())))
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
                                           currency_table.rate
                                           order by l.product_id)
                                        UNION ALL
                                           (select 
                                           so.id as id,
                                           so.date_order as order_date,
                                           so.partner_id as partner_id,
                                           so.company_id as company_id,
                                           so.currency_id,
                                           t.uom_id as product_uom,
                                           case 
                                           when so.state='draft' then 'draft_sale'
                                           when so.state='sent' then 'sent_sale'
                                           when so.state='sale' then 'sale'
                                           when so.state='done' then 'done' else
                                           'cancel' end as order_state,
                                           case when so.is_sale_order=True then 
                                           'Sale' else '' end as order_type,
                                           s.product_id as product_id,
                                           t.detailed_type as product_type,
                                           so.name as order_ref,
                                           case when s.product_id is not null 
                                           then sum(s.price_unit)
                                           else 0 end as unit_price_sale,
                                           0 as unit_price_purchase,
                                           case when s.product_id is not null then
                                           sum(s.price_total / case coalesce(so.currency_rate, 0)
                                           when 0  then 1.0 else so.currency_rate end) else
                                           0 end as price_total_sale,
                                           0 as price_total_purchase,
                                           case when s.product_id is not null then
                                           sum(s.price_subtotal / case coalesce(so.currency_rate, 0)
                                           when 0  then 1.0 else so.currency_rate end) else
                                           0 end as price_subtotal_sale,
                                           0 as price_subtotal_purchase,
                                           0 as qty_ordered_to,
                                           0 as qty_received,
                                           0 as qty_billed,
                                           case when s.product_id is not null 
                                           then sum(s.product_uom_qty / u.factor * u2.factor) else 0 end as 
                                           qty_ordered_by,
                                           case when s.product_id is not null 
                                           then sum(s.qty_delivered / u.factor * u2.factor) else 0 end as
                                           qty_delivered,
                                           case when s.product_id is not null 
                                           then sum(s.qty_invoiced / u.factor * u2.factor) else 0 end as
                                           qty_invoiced
                                           from
                                           (sale_order_line s
                                           join sale_order so on 
                                           (s.order_id=so.id)
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
                                        macro.price_total_sale,
                                        macro.price_total_purchase,
                                        macro.price_subtotal_sale,
                                        macro.price_subtotal_purchase,
                                        macro.company_id,
                                        macro.currency_id,
                                        macro.product_uom
                                        order by macro.product_id""" % (
                                where_purchase, where_sale))
        rec = self.env.cr.fetchall()
        return {
            'docs': rec,
            'date_from': data['form']['date_from'],
            'date_to': data['form']['date_to'],
        }
