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
"""Sale Purchase Report"""
from odoo import fields, models, tools


class SalePurchaseReport(models.Model):
    """Fields and Functions for graph and pivot view"""
    _name = 'sale.purchase.report'
    _description = 'Sale Purchase Report'
    _order = 'order_date desc'
    _auto = False

    product_tmpl_id = fields.Many2one('product.template', string='Product',
                                      readonly=True)
    product_id = fields.Many2one('product.product', string='Variant',
                                 readonly=True)
    partner_id = fields.Many2one('res.partner', string='Partner', readonly=True)
    product_type = fields.Selection(
        [('cosnsu', 'Consumable'), ('service', 'Service'),
         ('product', 'Product')])
    category_id = fields.Many2one('product.category', 'Product Category',
                                  readonly=True)
    qty_invoiced = fields.Float(string='Qty Invoiced', readonly=True)
    qty_billed = fields.Float(string='Qty Billed', readonly=True)
    qty_delivered = fields.Float(string='Qty Delivered', readonly=True)
    qty_received = fields.Float(string='Qty Received', readonly=True)
    qty_ordered_by = fields.Float('Qty Ordered by Customer', readonly=True)
    qty_ordered_to = fields.Float('Qty Ordered to Vendor', readonly=True)
    qty_to_deliver = fields.Float('Qty to Deliver', readonly=True)
    qty_to_receive = fields.Float('Qty to Receive', readonly=True)
    qty_to_invoice = fields.Float('Qty to Invoice', readonly=True)
    qty_to_bill = fields.Float('Qty to Bill', readonly=True)
    unit_price_sale = fields.Float(string='Unit Price Sale', readonly=True)
    unit_price_purchase = fields.Float(string='Unit Price Purchase',
                                       readonly=True)
    order_type = fields.Char('Order Type', readonly=True)
    order_date = fields.Datetime('Order Date', readonly=True)
    order_ref = fields.Char('Order Reference', readonly=True)
    order_state = fields.Selection(
        [('draft_sale', 'Quotation'), ('draft_rfq', 'RFQ'),
         ('sent_sale', 'Quotation Sent'), ('rfq_sent', 'RFQ Sent'),
         ('to_approve', 'To Approve'),
         ('sale', 'Sale Order'), ('purchase', 'Purchase Order'),
         ('done', 'Done'),
         ('cancel', 'Cancelled')], string='Order Status')
    company_id = fields.Many2one('res.company', 'Company', readonly=True)
    price_total_sale = fields.Float('Total Sale', readonly=True)
    price_total_purchase = fields.Float('Total Purchase', readonly=True)
    price_subtotal_sale = fields.Float('Untaxed Total Sale', readonly=True)
    price_subtotal_purchase = fields.Float('Untaxed Total Purchase',
                                           readonly=True)
    user_id = fields.Many2one('res.users', 'Representative', readonly=True)
    currency_id = fields.Many2one('res.currency', 'Currency', readonly=True)
    weight_sale = fields.Float('Gross Weight Sale', readonly=True)
    weight_purchase = fields.Float('Gross Weight Purchase', readonly=True)
    volume_sale = fields.Float('Volume Sale', readonly=True)
    volume_purchase = fields.Float('Volume Purchase', readonly=True)
    product_uom = fields.Many2one('uom.uom', 'Unit of Measure', required=True)

    def init(self):
        tools.drop_view_if_exists(self._cr, 'sale_purchase_report')
        self._cr.execute("""
            CREATE or REPLACE VIEW sale_purchase_report as(
                select macro.id as id,
                macro.order_type as order_type,
                macro.order_state as order_state,
                macro.order_date as order_date,
                macro.partner_id as partner_id,
                macro.product_id as product_id,
                macro.product_tmpl_id as product_tmpl_id,
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
                macro.qty_to_invoice as qty_to_invoice,
                macro.qty_to_bill as qty_to_bill,
                macro.qty_to_deliver as qty_to_deliver,
                macro.qty_to_receive as qty_to_receive,
                macro.company_id as company_id,
                macro.currency_id as currency_id,
                macro.product_uom as product_uom,
                macro.category_id as category_id,
                macro.user_id as user_id,
                macro.weight_sale as weight_sale,
                macro.weight_purchase as weight_purchase,
                macro.volume_sale as volume_sale,
                macro.volume_purchase as volume_purchase
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
                            t.categ_id as category_id,
                            t.uom_id as product_uom,
                            po.user_id as user_id,
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
                            p.product_tmpl_id as product_tmpl_id, 
                            t.detailed_type as product_type, 
                            po.name as order_ref,
                            0 as unit_price_sale,
                            case when l.product_id is not null then 
                            sum(l.price_unit) else 0 end as unit_price_purchase,
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
                            case when t.purchase_method = 'purchase' then 
                            sum(l.product_qty / u.factor * u2.factor) - sum(l.qty_invoiced / u.factor * u2.factor) 
                            else sum(l.qty_received / u.factor * u2.factor) - sum(l.qty_invoiced / u.factor * u2.factor) 
                            end as qty_to_bill,
                            case when l.product_id is not null then 
                            sum((l.product_qty - l.qty_received) / u.factor * u2.factor)
                            else 0 end as qty_to_receive,
                            0 as weight_sale,
                            sum(p.weight * l.product_qty / u.factor * u2.factor) as weight_purchase,
                            0 as volume_sale,
                            sum(p.volume * l.product_qty / u.factor * u2.factor) as volume_purchase,
                            0 as qty_ordered_by,
                            0 as qty_delivered,
                            0 as qty_invoiced,
                            0 as qty_to_invoice,
                            0 as qty_to_deliver
                            from
                            (purchase_order_line l 
                            join purchase_order po on (l.order_id=po.id)
                            join res_partner partner on 
                            (po.partner_id=partner.id)
                            left join product_product p on (l.product_id=p.id)
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
                                        group by
                                        po.partner_id,
                                        p.product_tmpl_id,
                                        po.date_order,
                                        l.product_id,
                                        t.uom_id,
                                        t.detailed_type,
                                        po.id,
                                        currency_table.rate,
                                        t.purchase_method,
                                        t.categ_id
                                        order by l.product_id)
                                     UNION ALL
                                        (select 
                                        so.id as id,
                                        so.date_order as order_date,
                                        so.partner_id as partner_id,
                                        so.company_id as company_id,
                                        so.currency_id,
                                        t.categ_id as category_id,
                                        t.uom_id as product_uom,
                                        so.user_id as user_id,
                                        case 
                                        when so.state='draft' then 'draft_sale'
                                        when so.state='sent' then 'sent_sale'
                                        when so.state='sale' then 'sale'
                                        when so.state='done' then 'done' else
                                        'cancel' end as order_state,
                                        case when so.is_sale_order=True then 
                                        'Sale' else '' end as order_type,
                                        s.product_id as product_id,
                                        p.product_tmpl_id as product_tmpl_id,
                                        t.detailed_type as product_type,
                                        so.name as order_ref,
                                        case when s.product_id is not null then 
                                        sum(s.price_unit) else 0 end 
                                        as unit_price_sale,
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
                                        0 as qty_to_bill,
                                        0 as qty_to_receive,
                                        case when s.product_id is not null then 
                                        sum(p.weight * s.product_uom_qty / u.factor * u2.factor) else 0 end as weight_sale,
                                        0 as weight_purchase,
                                        case when s.product_id is not null then
                                        sum(p.volume * s.product_uom_qty / u.factor * u2.factor) else 0 end as volume_sale,
                                        0 as volume_purchase,
                                        case when s.product_id is not null then
                                        sum(s.product_uom_qty / u.factor * u2.factor) else 0 end as 
                                        qty_ordered_by,
                                        case when s.product_id is not null then
                                        sum(s.qty_delivered / u.factor * u2.factor) else 0 end as
                                        qty_delivered,
                                        case when s.product_id is not null then
                                        sum(s.qty_invoiced / u.factor * u2.factor) else 0 end as
                                        qty_invoiced,
                                        case when s.product_id is not null then
                                        sum(s.qty_to_invoice / u.factor * u2.factor) else 0 end as
                                        qty_to_invoice,
                                        case when s.product_id is not null then
                                        sum((s.product_uom_qty - s.qty_delivered) / u.factor * u2.factor)
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
                                        group by
                                        so.partner_id,
                                        p.product_tmpl_id,
                                        so.date_order,
                                        s.product_id,
                                        t.uom_id,
                                        t.detailed_type,
                                        so.id,
                                        t.categ_id
                                        order by s.product_id))
                                     macro
                                     group by
                                     macro.partner_id,
                                     macro.product_tmpl_id,
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
                                     macro.qty_to_invoice,
                                     macro.qty_to_bill,
                                     macro.price_total_sale,
                                     macro.price_total_purchase,
                                     macro.price_subtotal_sale,
                                     macro.price_subtotal_purchase,
                                     macro.company_id,
                                     macro.currency_id,
                                     macro.product_uom,
                                     macro.user_id,
                                     macro.weight_sale,
                                     macro.weight_purchase,
                                     macro.volume_sale,
                                     macro.volume_purchase,
                                     macro.category_id
                                     order by macro.product_id
                                     );
                                     """)
