# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
import calendar
from datetime import datetime
from odoo import api, models


class PurchaseOrder(models.Model):
    """
    Inherits the Purchase Order Model and Extends Its Functionality.
    This class extends the Odoo Purchase Order model to provide custom methods
    for retrieving various purchase-related data, including purchase data for
    display in tiles, yearly, monthly, weekly, and today's purchase data,
    top chart data, orders by month, purchase vendors, purchase vendor details,
    pending purchase data, and upcoming purchase data.
    """
    _inherit = 'purchase.order'

    @api.model
    def get_purchase_data(self):
        """
        Get purchase data for display in tiles.
        This method retrieves data related to purchase orders, including
        the count of purchase orders in 'purchase' and 'done' states,
        the total purchase amount, the count of priority orders, and
        the total count of vendors associated with purchase orders.
        Returns:
            dict: A dictionary containing the following purchase data:
                - 'purchase_orders': Count of purchase orders.
                - 'purchase_amount': Total purchase amount.
                - 'priority_orders': Count of priority orders.
                - 'vendors': Total count of vendors.
        """
        orders = self.env['purchase.order'].search_count([('state', 'in', [
            'purchase', 'done'])])
        priority_orders = self.env['purchase.order'].search_count([
            ('priority', '=', '1')])
        vendor_count = self.env['purchase.order'].search_count([
            ('state', 'in', ['purchase', 'done'])])
        return {
            'purchase_orders': orders,
            'purchase_amount': sum(order.amount_total for order in
                                   self.env['purchase.order'].search(
                                       [('state', 'in', ['purchase',
                                                         'done'])])),
            'priority_orders': priority_orders,
            'vendors': vendor_count
        }

    def get_yearly_data(self):
        """
        Get yearly purchase data for the current company.
        Returns:
            dict: A dictionary containing yearly purchase data, including
            purchase orders count, purchase amount, priority orders count, and
            new vendor count compared to the previous year.
        """
        company = self.env.company.id
        current_year = datetime.now().year
        # Query to get purchase orders count and amount for the current year
        query = """
            SELECT COUNT(*) as po_count, SUM(amount_total) as po_sum
            FROM purchase_order
            WHERE company_id = %s
            AND state IN ('purchase', 'done')
            AND EXTRACT(YEAR FROM date_order) = %s
        """
        self.env.cr.execute(query, (company, current_year))
        data = self.env.cr.dictfetchall()
        # Query to get priority purchase orders count for the current year
        query = """
            SELECT COUNT(*) as po_count
            FROM purchase_order
            WHERE company_id = %s
            AND state IN ('purchase', 'done')
            AND EXTRACT(YEAR FROM date_order) = %s
            AND priority = '1'
        """
        self.env.cr.execute(query, (company, current_year))
        priority_orders = self.env.cr.dictfetchall()
        # Query to get vendor count for the previous year
        query = """
            SELECT COUNT(DISTINCT partner_id) as vendor_count
            FROM purchase_order
            WHERE company_id = %s
            AND state IN ('purchase', 'done')
            AND EXTRACT(YEAR FROM date_order) = %s - 1
        """
        self.env.cr.execute(query, (company, current_year))
        previous_vendors = self.env.cr.dictfetchall()[0]['vendor_count']
        # Query to get vendor count for the current year
        query = """
            SELECT COUNT(DISTINCT partner_id) as vendor_count
            FROM purchase_order
            WHERE company_id = %s
            AND state IN ('purchase', 'done')
            AND EXTRACT(YEAR FROM date_order) = %s
        """
        self.env.cr.execute(query, (company, current_year))
        current_vendors = self.env.cr.dictfetchall()[0]['vendor_count']
        # Calculate new vendors compared to the previous year
        new_vendors = current_vendors - previous_vendors
        yearly = {
            'purchase_orders': data[0]['po_count'],
            'purchase_amount': data[0]['po_sum'] or 0,
            'priority_orders': priority_orders[0]['po_count'],
            'vendors': new_vendors or 0,
        }
        return yearly

    def get_monthly_data(self):
        """Get monthly purchase data for the current company.
        Returns:
            dict: A dictionary containing monthly purchase data, including
            purchase orders count, purchase amount, priority orders count,
            vendor count, and new vendor IDs for the current month.
        """
        company = self.env.company.id
        query = """
            SELECT COUNT(*), SUM(amount_total)
            FROM purchase_order po
            WHERE company_id = %s
                AND state IN ('purchase', 'done')
                AND EXTRACT(YEAR from date_order) = 
                EXTRACT(YEAR from CURRENT_DATE)
                AND EXTRACT(MONTH from date_order) = 
                EXTRACT(MONTH from CURRENT_DATE)
        """
        self.env.cr.execute(query, (company,))
        data = self.env.cr.dictfetchall()
        query = """
            SELECT COUNT(*)
            FROM purchase_order po
            WHERE company_id = %s
                AND EXTRACT(YEAR from date_order) = 
                EXTRACT(YEAR from CURRENT_DATE)
                AND EXTRACT(MONTH from date_order) = 
                EXTRACT(MONTH from CURRENT_DATE) 
                AND priority = '1'
        """
        self.env.cr.execute(query, (company,))
        priority_orders = self.env.cr.dictfetchall()
        query = """
            SELECT DISTINCT partner_id
            FROM purchase_order po
            WHERE company_id = %s
                AND state IN ('purchase', 'done')
                AND EXTRACT(month from date_order) <
                 EXTRACT(month FROM CURRENT_DATE)
        """
        self.env.cr.execute(query, (company,))
        previous_vendors = self.env.cr.dictfetchall()
        previous = [rec['partner_id'] for rec in previous_vendors]
        query = """
            SELECT DISTINCT partner_id
            FROM purchase_order po
            WHERE company_id = %s
                AND state IN ('purchase', 'done')
                AND EXTRACT(YEAR from date_order) = 
                EXTRACT(YEAR FROM CURRENT_DATE) 
                AND EXTRACT(month from date_order) = 
                EXTRACT(month FROM CURRENT_DATE)
        """
        self.env.cr.execute(query, (company,))
        vendors = self.env.cr.dictfetchall()
        new_vendors = [rec['partner_id'] for rec in vendors if
                       rec['partner_id'] not in previous]
        monthly = {
            'purchase_orders': data[0]['count'] if data else 0,
            'purchase_amount': data[0]['sum'] if data else 0,
            'priority_orders': priority_orders[0][
                'count'] if priority_orders else 0,
            'vendors': len(new_vendors),
            'vendor_id': new_vendors,
        }
        return monthly

    def get_weekly_data(self):
        """
         Get weekly purchase data for the current company.
         Returns:
             dict: A dictionary containing weekly purchase data, including
             purchase orders count, purchase amount, priority orders count, and
             vendor count.
         """
        company = self.env.company.id
        query = """
            SELECT COUNT(*), SUM(amount_total), COUNT(CASE WHEN priority = '1' 
            THEN 1 ELSE NULL END)
            FROM purchase_order
            WHERE company_id = %s
                AND state IN ('purchase', 'done')
                AND EXTRACT(YEAR from date_order) = 
                EXTRACT(YEAR from CURRENT_DATE)
                AND EXTRACT(WEEK from date_order) = 
                EXTRACT(WEEK from CURRENT_DATE)
        """
        self.env.cr.execute(query, [company])
        data = self.env.cr.fetchone()
        query = """
            SELECT DISTINCT partner_id
            FROM purchase_order
            WHERE company_id = %s
                AND state IN ('purchase', 'done')
                AND EXTRACT(WEEK from date_order) <
                 EXTRACT(WEEK FROM CURRENT_DATE)
        """
        self.env.cr.execute(query, [company])
        previous_vendors = self.env.cr.dictfetchall()
        previous = [rec['partner_id'] for rec in previous_vendors]
        query = """
            SELECT DISTINCT partner_id
            FROM purchase_order
            WHERE company_id = %s
                AND state IN ('purchase', 'done')
                AND EXTRACT(YEAR from date_order) = 
                EXTRACT(YEAR FROM CURRENT_DATE) 
                AND EXTRACT(WEEK from date_order) = 
                EXTRACT(WEEK FROM CURRENT_DATE)
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
        """Get today's purchase data for the current company.
        Returns:
            dict: A dictionary containing today's purchase data, including
            purchase orders count, purchase amount, priority orders count,
            vendor count, and vendor IDs for new vendors today.
        """
        company = self.env.company.id
        # Get data for today
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
        # Get new vendors for today
        query = """
            SELECT DISTINCT po.partner_id
            FROM purchase_order po
            LEFT JOIN purchase_order prior_po
                ON po.partner_id = prior_po.partner_id
                AND prior_po.company_id = %s
                AND prior_po.state IN ('purchase', 'done')
                AND prior_po.date_order::date < CURRENT_DATE
            WHERE
                po.company_id = %s
                AND po.state IN ('purchase', 'done')
                AND po.date_order::date = CURRENT_DATE
                AND prior_po.partner_id IS NULL
        """
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
         Returns:
            dict or False: A dictionary containing the corresponding purchase
            data based on the selected filter or False if the filter is invalid.
        """
        data = {
            'this_year': self.get_yearly_data,
            'this_month': self.get_monthly_data,
            'this_week': self.get_weekly_data,
            'today': self.get_today_data,
        }.get(args)
        return data() if data else False

    def execute_query(self, query, args):
        """ Execute a database query and return the results based on the
        provided arguments.
        Returns:
            list: A list of results based on the query and arguments."""
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
        """
        Get top chart data (e.g., top products, top vendors,
        top representatives).
        Returns:
            list: A list of top chart data, including quantities or counts and
            names.
        """
        company_id = self.env.company.id
        if args == 'top_product':
            query = '''
                SELECT DISTINCT(product_template.name) as product_name,
                SUM(product_qty) as total_quantity 
                FROM purchase_order_line 
                INNER JOIN product_product ON product_product.id = 
                purchase_order_line.product_id 
                INNER JOIN product_template ON product_product.product_tmpl_id =
                product_template.id 
                WHERE purchase_order_line.company_id = %s 
                GROUP BY product_template.id 
                ORDER BY total_quantity DESC 
                LIMIT 10
            ''' % company_id
        elif args == 'top_vendor':
            query = '''
                SELECT partner.name, COUNT(po.id) as count
                FROM purchase_order po
                JOIN res_partner partner ON po.partner_id = partner.id
                WHERE po.company_id = %s
                GROUP BY partner.name
                ORDER BY count DESC 
                LIMIT 10
            ''' % company_id
        elif args == 'top_rep':
            query = '''
                SELECT partner.name, COUNT(po.id) as count
                FROM purchase_order po
                JOIN res_users users ON po.user_id = users.id
                JOIN res_partner partner ON users.partner_id = partner.id
                WHERE po.company_id = %s
                GROUP BY partner.name
                ORDER BY count DESC
                LIMIT 10
            ''' % company_id
        final = self.execute_query(query, args)
        return final

    @api.model
    def get_orders_by_month(self):
        """
        Get monthly purchase orders count for the current company.
        Returns:
            dict: A dictionary containing monthly purchase orders count
        and month names.
        """
        query = """select count(*), EXTRACT(month from date_order) as dates
            from purchase_order po
            where company_id = %s and state = 'purchase'
            group by dates""" % self.env.company.id
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
        """Get a list of purchase vendors for the current company.
        Returns:
            dict: A dictionary containing partner IDs and partner names.
        """
        company_id = self.env.company.id
        query = """
            SELECT partner.id, partner.name
            FROM purchase_order po
            INNER JOIN res_partner partner ON po.partner_id = partner.id
            WHERE po.company_id = %s
            GROUP BY partner.id
        """
        self._cr.execute(query, (company_id,))
        partners = self._cr.dictfetchall()
        partner_ids = [partner['id'] for partner in partners]
        partner_names = [partner['name'] for partner in partners]
        return {'partner_id': partner_ids, 'partner_name': partner_names}

    @api.model
    def purchase_vendor_details(self, args):
        """
        Get vendor analysis data for a specific vendor.
        Returns:
            dict: A dictionary containing purchase amount, purchase order count,
            draft amount, draft order count, approve amount, approve order
            count, cancel amount, cancel order count, and month dates.
        """
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
            GROUP BY dates
        """
        self._cr.execute(query_draft, (company_id, partner))
        draft_orders = self._cr.dictfetchall()
        approve_qry = """
            SELECT count(po.id),SUM(po.amount_total), EXTRACT(MONTH from 
            po.date_order) as dates 
            FROM purchase_order po 
            JOIN res_partner ON res_partner.id = po.partner_id 
            WHERE po.state = 'to approve' and po.company_id = %s and 
            po.partner_id = %s 
            GROUP BY dates
        """
        self._cr.execute(approve_qry, (company_id, partner))
        approve_orders = self._cr.dictfetchall()
        cancel_qry = """
            SELECT count(po.id),SUM(po.amount_total), EXTRACT(MONTH from 
            po.date_order) as dates 
            FROM purchase_order po 
            JOIN res_partner ON res_partner.id = po.partner_id 
            WHERE po.state = 'cancel' and po.company_id = 
            %s and po.partner_id = %s 
            GROUP BY dates
        """
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
            'purchase_amount': [record.get('sum') for record in partner_orders],
            'po_count': [record.get('count') for record in partner_orders],
            'draft_amount': [record.get('sum') for record in draft_orders],
            'draft_count': [record.get('count') for record in draft_orders],
            'approve_amount': [record.get('sum') for record in approve_orders],
            'approve_count': [record.get('count') for record in approve_orders],
            'cancel_amount': [record.get('sum') for record in cancel_orders],
            'cancel_count': [record.get('count') for record in cancel_orders],
            'dates': [record.get('dates') for record in partner_orders],
        }
        return value

    @api.model
    def get_pending_purchase_data(self):
        """
        Get pending purchase orders for the current company.
        Returns:
            dict: A dictionary containing pending purchase order details,
            including order names, vendor names, amounts, dates, and states.
        """
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
        """
        Get upcoming purchase orders for the current company.
        Returns:
        dict: A dictionary containing upcoming purchase order details,
        including order names, vendor names, amounts, dates, and states.
        """
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


class PurchaseOrderLine(models.Model):
    """
        Purchase Order Line Model for Extending Purchase Order Line
        Functionality. This class extends the Odoo Purchase Order Line model
        to add custom methods for product category analysis and retrieval of
        product category data.
        """
    _inherit = 'purchase.order.line'

    @api.model
    def product_categ_analysis(self):
        """
            Perform product category analysis for purchase order lines. This
            method retrieves and analyzes purchase order line data to provide
            information on product categories and their corresponding
            quantities.
            """
        company_id = self.env.user.company_id.id
        # Query to get products quantity by name
        quantity_query = """
                SELECT product_template.name, 
                SUM(pl.product_qty) as total_quantity
                FROM purchase_order_line pl
                JOIN product_product ON pl.product_id = product_product.id
                JOIN product_template ON product_product.product_tmpl_id =
                product_template.id
                WHERE pl.company_id = %s
                GROUP BY product_template.name
            """
        self._cr.execute(quantity_query, (company_id,))
        products_quantity = self._cr.fetchall()
        # Extract name and quantity values from query result
        name, quantity_done = zip(*products_quantity)
        # Query to get category ids and names
        category_query = """
                SELECT pc.id, pc.name
                FROM product_category pc
                JOIN product_template pt ON pt.categ_id = pc.id
                JOIN product_product pp ON pp.product_tmpl_id = pt.id
                JOIN purchase_order_line pl ON pl.product_id = pp.id
                WHERE pl.company_id = %s
                GROUP BY pc.id, pc.name
            """
        self._cr.execute(category_query, (company_id,))
        categories = self._cr.fetchall()
        # Extract category ids and names from query result
        category_ids, category_names = zip(*categories)
        # Create dictionary values to return
        value = {'name': name, 'count': quantity_done}
        new_value = {'category_id': category_ids,
                     'category_name': category_names}
        return value, new_value

    @api.model
    def product_categ_data(self, args):
        """
            Retrieve product category data for a specific category.
            Returns:
                dict: A dictionary containing product data for the specified
                category, including product names and their quantities.
            """
        category_id = int(args or 1)
        company_id = self.env.company.id
        query = """
                SELECT product_template.name, SUM(pl.product_qty)
                FROM purchase_order_line pl
                INNER JOIN product_product ON pl.product_id = product_product.id
                INNER JOIN product_template ON product_product.product_tmpl_id =
                product_template.id
                WHERE pl.company_id = %s AND product_template.categ_id = %s
                GROUP BY product_template.name
            """
        self._cr.execute(query, (company_id, category_id))
        product_move = self._cr.dictfetchall()
        value = {
            'name': [record.get('name') for record in product_move],
            'count': [record.get('sum') for record in product_move],
        }
        return value
