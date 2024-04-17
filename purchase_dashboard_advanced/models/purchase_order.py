# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Bhagyadev KP (odoo@cybrosys.com)
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
################################################################################
import calendar
from odoo import api, models


class PurchaseOrder(models.Model):
    """Model representing purchase orders and related analytics.Inherits from
    'purchase.order' model."""
    _inherit = 'purchase.order'

    @api.model
    def get_purchase_data(self):
        """Returns data to the orm call to display the data in the tiles
        :return: Dictionary with purchase data
        :rtype: dict"""
        orders = self.env['purchase.order'].search([('state', 'in', [
            'purchase', 'done'])])
        priority_orders = self.env['purchase.order'].search([
            ('priority', '=', '1')])
        vendor = list(set(rec.partner_id for rec in orders))
        return {
            'purchase_orders': len(orders),
            'purchase_amount': sum(rec.amount_total for rec in orders),
            'priority_orders': len(priority_orders),
            'vendors': len(vendor)
        }

    def get_yearly_data(self):
        """Get yearly purchase data.
        :return: Dictionary with yearly purchase data
        :rtype: dict"""
        company = self.env.company.id
        query = """
               SELECT COUNT(*) as po_count, SUM(amount_total) as po_sum
               FROM purchase_order
               WHERE company_id = %s
                   AND state IN ('purchase', 'done')
                   AND date_order >= date_trunc('year', now())
           """
        self.env.cr.execute(query, (company,))
        data = self.env.cr.dictfetchall()
        query_priority = """
               SELECT COUNT(*) as priority_count
               FROM purchase_order po
               WHERE company_id = %s
                   AND state IN ('purchase', 'done')
                   AND EXTRACT(YEAR from date_order) = EXTRACT(YEAR from now())
                   AND priority = '1'
           """
        self.env.cr.execute(query_priority, (company,))
        priority_orders = self.env.cr.dictfetchall()
        query_vendors = """
               SELECT COUNT(DISTINCT partner_id) as vendor_count
               FROM purchase_order
               WHERE company_id = %s
                   AND state IN ('purchase', 'done')
                   AND date_order < date_trunc('year', now())
           """
        self.env.cr.execute(query_vendors, (company,))
        result = self.env.cr.dictfetchall()
        if result:
            previous_vendors = result[0]['vendor_count']
        else:
            previous_vendors = 0
        query_current_vendors = """
               SELECT COUNT(DISTINCT partner_id) as vendor_count
               FROM purchase_order
               WHERE company_id = %s
                   AND state IN ('purchase', 'done')
                   AND date_order BETWEEN date_trunc('year', now()) AND now()
           """
        self.env.cr.execute(query_current_vendors, (company,))
        result = self.env.cr.dictfetchall()
        if result:
            current_vendors = result[0]['vendor_count']
        else:
            current_vendors = 0
        new_vendors = current_vendors - previous_vendors
        yearly = {
            'purchase_orders': data[0]['po_count'],
            'purchase_amount': data[0]['po_sum'] or 0,
            'priority_orders': priority_orders[0]['priority_count'],
            'vendors': new_vendors or 0,
        }
        return yearly

    def get_monthly_data(self):
        """Get monthly purchase data.
        :return: Dictionary with monthly purchase data
        :rtype: dict"""
        company = self.env.company.id
        query = """
            SELECT COUNT(*), SUM(amount_total)
            FROM purchase_order po
            WHERE company_id = %s
                AND state IN ('purchase', 'done')
                AND EXTRACT(YEAR from date_order) = EXTRACT(YEAR from 
                CURRENT_DATE)
                AND EXTRACT(MONTH from date_order) = EXTRACT(MONTH from 
                CURRENT_DATE)
        """
        self.env.cr.execute(query, (company,))
        data = self.env.cr.dictfetchall()
        query = """
            SELECT COUNT(*)
            FROM purchase_order po
            WHERE company_id = %s
                AND EXTRACT(YEAR from date_order) = EXTRACT(YEAR from 
                CURRENT_DATE)
                AND EXTRACT(MONTH from date_order) = EXTRACT(MONTH from
                 CURRENT_DATE) 
                AND priority = '1'
        """
        self.env.cr.execute(query, (company,))
        priority_orders = self.env.cr.dictfetchall()
        query = """
            SELECT DISTINCT partner_id
            FROM purchase_order po
            WHERE company_id = %s
                AND state IN ('purchase','done')
                AND EXTRACT(month from date_order) < EXTRACT(month FROM
                 CURRENT_DATE)
        """
        self.env.cr.execute(query, (company,))
        previous_vendors = self.env.cr.dictfetchall()
        previous = []
        if len(previous_vendors) > 1:
            previous = [rec['partner_id'] for rec in previous_vendors]
        else:
            previous.append(rec for rec in previous_vendors)
        query = """
            SELECT DISTINCT partner_id
            FROM purchase_order po
            WHERE company_id = %s
                AND state IN ('purchase','done')
                AND EXTRACT(YEAR from date_order) = EXTRACT(YEAR FROM
                 CURRENT_DATE) 
                AND EXTRACT(month from date_order) = EXTRACT(month FROM
                 CURRENT_DATE)
        """
        self.env.cr.execute(query, (company,))
        vendors = self.env.cr.dictfetchall()
        new_vendors = []
        if vendors:
            if len(vendors) > 1:
                for rec in vendors:
                    if rec['partner_id'] not in previous:
                        new_vendors.append(rec['partner_id'])
            else:
                if vendors not in previous:
                    new_vendors.append(vendors[0]['partner_id'])
        monthly = {
            'purchase_orders': data[0]['count'],
            'purchase_amount': data[0]['sum'],
            'priority_orders': priority_orders[0]['count'],
            'vendors': len(new_vendors),
            'vendor_id': new_vendors,
        }
        return monthly

    def get_weekly_data(self):
        """Get weekly purchase data.
        :return: Dictionary with weekly purchase data
        :rtype: dict"""
        company = self.env.company.id
        query = """
            SELECT COUNT(*), SUM(amount_total), COUNT(CASE WHEN priority = '1' 
            THEN 1 ELSE NULL END)
            FROM purchase_order
            WHERE company_id = %s
                AND state IN ('purchase', 'done')
                AND EXTRACT(YEAR from date_order) = EXTRACT(YEAR from 
                CURRENT_DATE)
                AND EXTRACT(WEEK from date_order) = EXTRACT(WEEK from 
                CURRENT_DATE)
        """
        self.env.cr.execute(query, [company])
        data = self.env.cr.fetchone()
        query = """
            SELECT DISTINCT partner_id
            FROM purchase_order
            WHERE company_id = %s
                AND state IN ('purchase', 'done')
                AND EXTRACT(WEEK from date_order) < EXTRACT(WEEK FROM 
                CURRENT_DATE)
        """
        self.env.cr.execute(query, [company])
        previous_vendors = self.env.cr.dictfetchall()
        previous = [rec['partner_id'] for rec in previous_vendors]
        query = """
            SELECT DISTINCT partner_id
            FROM purchase_order
            WHERE company_id = %s
                AND state IN ('purchase', 'done')
                AND EXTRACT(YEAR from date_order) = EXTRACT(YEAR FROM 
                CURRENT_DATE) 
                AND EXTRACT(WEEK from date_order) = EXTRACT(WEEK FROM 
                CURRENT_DATE)
        """
        self.env.cr.execute(query, [company])
        vendors = self.env.cr.dictfetchall()
        new_vendors = [rec['partner_id'] for rec in vendors if rec[
            'partner_id'] not in previous]
        weekly = {
            'purchase_orders': data[0],
            'purchase_amount': data[1],
            'priority_orders': data[2],
            'vendors': len(new_vendors)
        }
        return weekly

    def get_today_data(self):
        """Get purchase data for the current day.
        :return: Dictionary with purchase data for the current day
        :rtype: dict"""
        company = self.env.company.id
        query = """
            SELECT
                COUNT(*) AS purchase_orders,
                SUM(amount_total) AS purchase_amount,
                COUNT(*) FILTER (WHERE priority = '1') AS priority_orders
            FROM purchase_order
            WHERE
                company_id = %s
                AND state IN ('purchase', 'done')
                AND date_order::date = CURRENT_DATE
        """
        self.env.cr.execute(query, (company,))
        today_data = self.env.cr.dictfetchall()[0]
        query = """
            SELECT DISTINCT partner_id
            FROM purchase_order
            WHERE
                company_id = %s
                AND state IN ('purchase', 'done')
                AND date_order::date = CURRENT_DATE
                AND NOT EXISTS (
                    SELECT 1
                    FROM purchase_order
                    WHERE
                        company_id = %s
                        AND state IN ('purchase', 'done')
                        AND date_order::date < CURRENT_DATE
                        AND partner_id = purchase_order.partner_id)"""
        self.env.cr.execute(query, (company, company))
        new_vendors = [r['partner_id'] for r in self.env.cr.dictfetchall()]
        return {
            'purchase_orders': today_data['purchase_orders'],
            'purchase_amount': today_data['purchase_amount'],
            'priority_orders': today_data['priority_orders'],
            'vendors': len(new_vendors),
            'vendor_id': new_vendors,
        }

    @api.model
    def get_select_mode_data(self, args):
        """Get data based on the selected filters
        :param args: Selected filter
        :type args: str
        :return: Data based on the selected filter
        :rtype: dict or False"""
        data = {
            'this_year': self.get_yearly_data,
            'this_month': self.get_monthly_data,
            'this_week': self.get_weekly_data,
            'today': self.get_today_data,
        }.get(args)
        return data() if data else False

    def execute_query(self, query, args):
        """Returns quantity/count regarding the top entities
        :param query: SQL query to be executed
        :type query: str
        :param args: Query parameters
        :type args: str
        :return: Query results
        :rtype: list"""
        self._cr.execute(query)
        results = self._cr.dictfetchall()
        final = []
        if args == 'top_product':
            final = [[record.get('total_quantity') for record in results],
                     [record.get('product_name') for record in results]]
        elif args == 'top_vendor':
            final = [[record.get('count') for record in results],
                     [record.get('name') for record in results]]
        elif args == 'top_rep':
            final = [[record.get('count') for record in results],
                     [record.get('name') for record in results]]
        return final

    @api.model
    def get_top_chart_data(self, args):
        """Get top chart data based on the selected filter.
         :param args: Selected filter
        :type args: str
        :return: Top chart data
        :rtype: list"""
        query = ''
        company_id = self.env.company.id
        if args == 'top_product':
            query = f'''
                SELECT DISTINCT(product_template.name) as product_name,
                SUM(product_qty) as total_quantity 
                FROM purchase_order_line 
                INNER JOIN product_product ON 
                product_product.id=purchase_order_line.product_id 
                INNER JOIN product_template ON 
                product_product.product_tmpl_id = product_template.id 
                WHERE purchase_order_line.company_id = {company_id} 
                GROUP BY product_template.id 
                ORDER BY total_quantity DESC 
                LIMIT 10
            '''
        elif args == 'top_vendor':
            query = f'''
                SELECT partner.name, COUNT(po.id) as count
                FROM purchase_order po
                JOIN res_partner partner ON po.partner_id = partner.id
                WHERE po.company_id = {company_id}
                GROUP BY partner.name
                ORDER BY count DESC 
                LIMIT 10
            '''
        elif args == 'top_rep':
            query = f'''
                SELECT partner.name, COUNT(po.id) as count
                FROM purchase_order po
                JOIN res_users users ON po.user_id = users.id
                JOIN res_partner partner ON users.partner_id = partner.id
                WHERE po.company_id = {company_id}
                GROUP BY partner.name
                ORDER BY count DESC
                LIMIT 10
            '''
        final = self.execute_query(query, args)
        return final

    @api.model
    def get_orders_by_month(self):
        """Get purchase orders grouped by month.
        :return: Purchase orders by month
        :rtype: dict"""
        query = f"""select count(*), EXTRACT(month from date_order) as dates
            from purchase_order po
            where company_id = {self.env.company.id} and state = 'purchase'
            group by dates"""
        self.env.cr.execute(query, (self.env.company.id,))
        cr = self.env.cr.dictfetchall()
        month = []
        for rec in cr:
            month.append(int(rec['dates']))
            rec.update({
                'count': rec['count'],
                'dates': calendar.month_name[int(rec['dates'])],
                'month': int(rec['dates'])
            })
        for rec in range(1, 13):
            if rec not in month:
                cr.append({
                    'count': 0,
                    'dates': calendar.month_name[rec],
                    'month': rec
                })
        cr = sorted(cr, key=lambda i: i['month'])
        return {
            'count': [rec['count'] for rec in cr],
            'dates': [rec['dates'] for rec in cr]
        }

    @api.model
    def purchase_vendors(self):
        """Get a list of purchase vendors.
        :return: List of purchase vendors in the format
        [{'id': vendor_id, 'name': vendor_name}]
        :rtype: list"""
        company_id = self.env.company.id
        query = """
            SELECT partner.id, partner.name
            FROM purchase_order po
            INNER JOIN res_partner partner ON po.partner_id = partner.id
            WHERE po.company_id = %s
            GROUP BY partner.id
        """
        self._cr.execute(query, (company_id,))
        return self._cr.dictfetchall()

    @api.model
    def purchase_vendor_details(self, args):
        """Get purchase details for a specific vendor.
        :param args: Vendor ID
        :type args: int
        :return: Purchase details for the specific vendor
        :rtype: dict"""
        company_id = self.env.company.id
        partner = int(args) if args else 1
        query = """
            SELECT count(po.id),SUM(po.amount_total), EXTRACT(MONTH from 
            po.date_order) as dates 
            FROM purchase_order po 
            JOIN res_partner ON res_partner.id = po.partner_id 
            WHERE po.company_id = %s and po.partner_id = %s 
            GROUP BY dates
        """
        self._cr.execute(query, (company_id, partner))
        partner_orders = self._cr.dictfetchall()
        query_draft = """
            SELECT count(po.id),SUM(po.amount_total), EXTRACT(MONTH from 
            po.date_order) as dates 
            FROM purchase_order po 
            JOIN res_partner ON res_partner.id = po.partner_id 
            WHERE po.state in ('draft', 'sent') and po.company_id = %s and 
            po.partner_id = %s 
            GROUP BY dates"""
        self._cr.execute(query_draft, (company_id, partner))
        draft_orders = self._cr.dictfetchall()
        approve_qry = """
            SELECT count(po.id),SUM(po.amount_total), EXTRACT(MONTH from 
            po.date_order) as dates 
            FROM purchase_order po 
            JOIN res_partner ON res_partner.id = po.partner_id 
            WHERE po.state = 'to approve' and po.company_id = %s and 
            po.partner_id = %s 
            GROUP BY dates"""
        self._cr.execute(approve_qry, (company_id, partner))
        approve_orders = self._cr.dictfetchall()
        cancel_qry = """
            SELECT count(po.id),SUM(po.amount_total), EXTRACT(MONTH from 
            po.date_order) as dates 
            FROM purchase_order po 
            JOIN res_partner ON res_partner.id = po.partner_id 
            WHERE po.state = 'cancel' and po.company_id = %s and po.partner_id 
            = %s 
            GROUP BY dates"""
        self._cr.execute(cancel_qry, (company_id, partner))
        cancel_orders = self._cr.dictfetchall()
        all_orders = {
            'partner_orders': partner_orders, 'draft_orders': draft_orders,
            'approve_orders': approve_orders, 'cancel_orders': cancel_orders}
        for order_type, order_list in all_orders.items():
            order_months = []
            for rec in order_list:
                order_months.append(int(rec.get('dates')))
            for rec in range(1, 13):
                if rec not in order_months:
                    vals = {'sum': 0.0, 'dates': rec, 'count': 0}
                    order_list.append(vals)
            all_orders[order_type] = sorted(
                order_list, key=lambda order: order['dates'])
        value = {
            'purchase_amount': [record.get('sum') for record in
                                partner_orders],
            'po_count': [record.get('count') for record in partner_orders],
            'draft_amount': [record.get('sum') for record in draft_orders],
            'draft_count': [record.get('count') for record in draft_orders],
            'approve_amount': [record.get('sum') for record in approve_orders],
            'approve_count': [record.get('count') for record in
                              approve_orders],
            'cancel_amount': [record.get('sum') for record in cancel_orders],
            'cancel_count': [record.get('count') for record in cancel_orders],
            'dates': [record.get('dates') for record in partner_orders],
        }
        return value

    @api.model
    def get_pending_purchase_data(self):
        """Get pending purchase orders data.
        :return: Data of pending purchase orders
        :rtype: dict"""
        company = self.env.company.id
        query = """
            SELECT po.name, po.id, rp.name as partner_name, po.date_planned, 
            po.amount_total, po.state 
            FROM purchase_order po 
            JOIN purchase_order_line pol ON pol.order_id = po.id 
            JOIN res_partner rp ON rp.id = po.partner_id 
            WHERE po.date_planned < CURRENT_DATE AND pol.qty_received < 
            pol.product_qty AND po.company_id = %s
            GROUP BY po.id, rp.id
        """
        self._cr.execute(query, (company,))
        orders = self._cr.dictfetchall()
        value = {
            'order': [rec['name'] for rec in orders],
            'vendor': [rec['partner_name'] for rec in orders],
            'amount': [rec['amount_total'] for rec in orders],
            'date': [rec['date_planned'] for rec in orders],
            'state': [rec['state'] for rec in orders],
            'data': [list(val for val in rec.values()) for rec in orders]
        }
        return value

    @api.model
    def get_upcoming_purchase_data(self):
        """Get upcoming purchase orders data.
        :return: Data of upcoming purchase orders
        :rtype: dict"""
        company = self.env.company.id
        query = """
            SELECT po.name, po.id, rp.name as partner_name, po.date_planned, 
            po.amount_total, po.state 
            FROM purchase_order po 
            JOIN purchase_order_line pol ON pol.order_id = po.id 
            JOIN res_partner rp ON rp.id = po.partner_id 
            WHERE po.date_planned > CURRENT_DATE AND pol.qty_received < 
            pol.product_qty AND po.company_id = %s
            GROUP BY po.id, rp.id
        """
        self._cr.execute(query, (company,))
        orders = self._cr.dictfetchall()
        value = {
            'order': [rec['name'] for rec in orders],
            'vendor': [rec['partner_name'] for rec in orders],
            'amount': [rec['amount_total'] for rec in orders],
            'date': [rec['date_planned'] for rec in orders],
            'state': [rec['state'] for rec in orders],
            'data': [list(val for val in rec.values()) for rec in orders],
        }
        return value
