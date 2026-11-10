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
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from collections import defaultdict
from datetime import datetime, time, timedelta

import pytz
from odoo import api, fields, models
from odoo.exceptions import AccessError
from odoo.tools.misc import format_amount

MONTH_LABELS = ('JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN',
                'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC')
NUMBER_SUFFIXES = ('', 'K', 'M', 'G', 'T', 'P')
# Paid orders count at once; 'paid' is the state until the session is closed
COUNTED_STATES = ('paid', 'done', 'invoiced')


class PosOrder(models.Model):
    """ Inherited pos.order to provide the data of the POS dashboard """
    _inherit = 'pos.order'

    @api.model
    def _dashboard_check_access(self):
        """ The dashboard is reserved to the POS managers, like its menu. """
        if not self.env.user.has_group('point_of_sale.group_pos_manager'):
            raise AccessError(self.env._(
                "Only the Point of Sale managers can read the dashboard."))

    @api.model
    def _dashboard_tz_name(self):
        """ Return the name of the timezone used to bucket the dates. """
        tz_name = self.env.context.get('tz') or self.env.user.tz
        return tz_name if tz_name in pytz.all_timezones_set else 'UTC'

    @api.model
    def _dashboard_order_domain(self):
        """ Domain of the orders counted by the dashboard: the ones of the
        current company that are paid. """
        return [
            ('company_id', '=', self.env.company.id),
            ('state', 'in', COUNTED_STATES),
        ]

    @api.model
    def _dashboard_group(self, domain, groupby, aggregates, model='pos.order',
                         **kwargs):
        """ Group the records of ``model`` with the ORM, so that the access
        rights and the record rules of the user apply, using the timezone of
        the user for the date groupings.

        :return: list of tuples (group values..., aggregates...)
        """
        records = self.env[model].with_context(tz=self._dashboard_tz_name())
        return records._read_group(domain, groupby, aggregates, **kwargs)

    @api.model
    def _dashboard_humanize(self, value):
        """ Shorten a number: 1250 -> '1.25K', 2500000 -> '2.50M'. """
        magnitude = 0
        while abs(value) >= 1000 and magnitude < len(NUMBER_SUFFIXES) - 1:
            magnitude += 1
            value /= 1000.0
        return f'{value:.2f}{NUMBER_SUFFIXES[magnitude]}'

    @api.model
    def _dashboard_local_start(self, unit):
        """ Return the start of today ('day'), of the current month ('month')
        or of the current year ('year') in the timezone of the user, as a
        naive UTC datetime ready to be used in a search domain. """
        tz = pytz.timezone(self._dashboard_tz_name())
        day = datetime.now(tz).date()
        if unit == 'month':
            day = day.replace(day=1)
        elif unit == 'year':
            day = day.replace(month=1, day=1)
        start = tz.localize(datetime.combine(day, time.min))
        return start.astimezone(pytz.UTC).replace(tzinfo=None)

    @api.model
    def _dashboard_today_range(self):
        """ Return the start and the end of today in the timezone of the user,
        as naive UTC datetimes ready to be used in a search domain. """
        tz = pytz.timezone(self._dashboard_tz_name())
        start = self._dashboard_local_start('day')
        end_local = tz.localize(datetime.combine(
            pytz.UTC.localize(start).astimezone(tz).date() + timedelta(days=1),
            time.min))
        return start, end_local.astimezone(pytz.UTC).replace(tzinfo=None)

    @api.model
    def get_department(self, option):
        """ Return the sales of the current company grouped by hour (current
        month), by day (current month) or by month (current year).

        :param str option: pos_hourly_sales, pos_daily_sales or
            pos_monthly_sales
        :return: [amounts, labels of the amounts, name of the grouping]
        """
        self._dashboard_check_access()
        domain = self._dashboard_order_domain()
        if option == 'pos_hourly_sales':
            domain.append(('date_order', '>=',
                           self._dashboard_local_start('month')))
            rows = self._dashboard_group(
                domain, ['date_order:hour_number'], ['amount_total:sum'])
            labels = [str(int(row[0])) for row in rows]
            group_name = self.env._("Hours")
        elif option == 'pos_daily_sales':
            domain.append(('date_order', '>=',
                           self._dashboard_local_start('month')))
            rows = self._dashboard_group(
                domain, ['date_order:day'], ['amount_total:sum'])
            labels = [row[0].strftime('%Y-%m-%d') for row in rows]
            group_name = self.env._("Days")
        else:
            domain.append(('date_order', '>=',
                           self._dashboard_local_start('year')))
            rows = self._dashboard_group(
                domain, ['date_order:month_number'], ['amount_total:sum'])
            labels = [MONTH_LABELS[int(row[0]) - 1] for row in rows]
            group_name = self.env._("Months")
        return [[float(row[1]) for row in rows], labels, group_name]

    @api.model
    def get_details(self):
        """ Return the payment methods, the salespersons and the status of
        the POS of the current company. """
        self._dashboard_check_access()
        company = self.env.company
        currency = company.currency_id

        payment_rows = self._dashboard_group(
            [('pos_order_id.company_id', '=', company.id),
             ('pos_order_id.state', 'in', COUNTED_STATES)],
            ['payment_method_id'], ['amount:sum'], model='pos.payment')
        payment_rows = sorted(payment_rows, key=lambda row: -row[1])
        payments = [
            (method.name, format_amount(self.env, amount, currency))
            for method, amount in payment_rows]

        sales_rows = self._dashboard_group(
            self._dashboard_order_domain() + [('user_id', '!=', False)],
            ['user_id'], ['amount_paid:sum', '__count'])
        sales_rows = sorted(sales_rows, key=lambda row: -row[1])
        salesperson = [
            (user.name, format_amount(self.env, amount, currency), count)
            for user, amount, count in sales_rows]

        status_labels = {
            'opening_control': self.env._("Opening Control"),
            'opened': self.env._("Opened"),
            'closing_control': self.env._("Closing Control"),
        }
        configs = self.env['pos.config'].search(
            [('company_id', '=', company.id)])
        open_sessions = self.env['pos.session'].search([
            ('config_id', 'in', configs.ids),
            ('state', '!=', 'closed'),
        ])
        state_by_config = {
            session.config_id.id: session.state for session in open_sessions}
        sessions = [{
            'session': config.name,
            'status': status_labels.get(
                state_by_config.get(config.id), self.env._("Closed")),
        } for config in configs]
        return {
            'payment_details': payments,
            'salesperson': salesperson,
            'sessions': sessions,
        }

    @api.model
    def get_refund_details(self):
        """ Return the numbers shown in the tiles of the dashboard, with the
        domains the tiles use to open the matching lists, so that a list
        always shows the records counted by its tile. """
        self._dashboard_check_access()
        start, end = self._dashboard_today_range()
        order_domain = self._dashboard_order_domain()
        today_domain = [
            ('date_order', '>=', fields.Datetime.to_string(start)),
            ('date_order', '<', fields.Datetime.to_string(end)),
        ]
        refund_domain = [('amount_total', '<', 0.0)]
        session_domain = [('config_id.company_id', '=', self.env.company.id)]
        total_sale_rows = self._dashboard_group(
            order_domain, [], ['amount_total:sum'])
        total_sale = total_sale_rows[0][0] if total_sale_rows else 0
        return {
            'total_sale': self._dashboard_humanize(float(total_sale or 0)),
            'total_order_count': self.search_count(order_domain),
            'total_refund_count': self.search_count(
                order_domain + refund_domain),
            'total_session': self.env['pos.session'].search_count(
                session_domain),
            'today_refund_total': self.search_count(
                order_domain + refund_domain + today_domain),
            'today_sale': self.search_count(order_domain + today_domain),
            'order_domain': order_domain,
            'refund_domain': refund_domain,
            'today_domain': today_domain,
            'session_domain': session_domain,
        }

    @api.model
    def get_the_top_customer(self):
        """ Return the ten customers who paid the most. """
        self._dashboard_check_access()
        rows = self._dashboard_group(
            self._dashboard_order_domain() + [('partner_id', '!=', False)],
            ['partner_id'], ['amount_paid:sum'],
            order='amount_paid:sum desc', limit=10)
        return [[float(row[1]) for row in rows],
                [row[0].name for row in rows]]

    @api.model
    def _dashboard_top_lines(self, key):
        """ Return the ten products (or product categories) with the largest
        sold quantity, as a list of (record, quantity).

        :param callable key: gets a product.product and returns the record
            the quantity is added to
        """
        rows = self._dashboard_group(
            [('order_id.company_id', '=', self.env.company.id),
             ('order_id.state', 'in', COUNTED_STATES)],
            ['product_id'], ['qty:sum'], model='pos.order.line')
        quantities = defaultdict(float)
        for product, qty in rows:
            quantities[key(product)] += qty
        return sorted(quantities.items(), key=lambda item: -item[1])[:10]

    @api.model
    def get_the_top_products(self):
        """ Return the ten most sold products. """
        self._dashboard_check_access()
        top = self._dashboard_top_lines(lambda product: product.product_tmpl_id)
        return [[float(qty) for _record, qty in top],
                [record.name for record, _qty in top]]

    @api.model
    def get_the_top_categories(self):
        """ Return the ten most sold product categories. """
        self._dashboard_check_access()
        top = self._dashboard_top_lines(
            lambda product: product.product_tmpl_id.categ_id)
        return [[float(qty) for _record, qty in top],
                [record.name for record, _qty in top]]
