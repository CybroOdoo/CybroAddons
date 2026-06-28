# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Technologies (<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
import babel.dates
from dateutil.relativedelta import relativedelta
from odoo import _, api, fields, models
from odoo.tools.safe_eval import datetime


def _month_label(month_number, lang):
    """Return the localized month name (e.g. 'June' / 'Junio') for the
    given month number (1-12) and the user's language."""
    from datetime import date as _date
    return babel.dates.format_date(
        _date(2000, month_number, 1), format='MMMM', locale=lang or 'en_US',
    )


def get_period_start_date(period):
    """Returns the start date for the given period"""
    today = datetime.datetime.now()

    if period == 'month':
        start_date = today.replace(day=1)
    elif period == 'quarter':
        current_month = today.month
        start_month = ((current_month - 1) // 3) * 3 + 1
        start_date = today.replace(month=start_month, day=1)
    elif period == 'year':
        start_date = today.replace(month=1, day=1)
    elif period == 'week':
        start_date = today - datetime.timedelta(days=today.weekday())
    else:
        raise ValueError("Invalid period specified")

    return start_date.date()


class CRMLead(models.Model):
    """Extends crm.lead for adding more functions in it"""
    _inherit = 'crm.lead'

    @api.model
    def get_data(self, period):
        """Returns data to the dashboard tiles"""
        period_days = get_period_start_date(period)

        crm_model = self.search([('create_date', '>=', period_days)])

        lead_count = 0
        opportunity_count = 0
        win_count = 0
        active_lead_count = 0
        active_opportunity_count = 0
        won_opportunity_count = 0
        total_seconds = 0
        expected_revenue = 0
        revenue = 0
        unassigned_leads = 0

        for record in crm_model:
            if record.type == 'lead':
                lead_count += 1
                if not record.user_id:
                    unassigned_leads += 1

            if record.type == 'opportunity':
                opportunity_count += 1
                expected_revenue += record.expected_revenue
                if record.active:
                    if record.probability == 0:
                        active_opportunity_count += 1
                    elif record.probability == 100:
                        won_opportunity_count += 1
                        if record.stage_id.is_won:
                            revenue += record.expected_revenue

            if record.active:
                if record.probability == 0:
                    active_lead_count += 1
                elif record.probability == 100:
                    win_count += 1

            if record.date_conversion:
                total_seconds += (
                        record.date_conversion - record.create_date).seconds

        win_ratio = win_count / active_lead_count if active_lead_count else 0
        opportunity_ratio = won_opportunity_count / active_opportunity_count if active_opportunity_count else 0
        avg_close_time = round(total_seconds / len(crm_model.filtered(
            lambda l: l.date_conversion))) if total_seconds else 0

        return {
            'leads': lead_count,
            'opportunities': opportunity_count,
            'exp_revenue': expected_revenue,
            'revenue': revenue,
            'win_ratio': win_ratio,
            'opportunity_ratio': opportunity_ratio,
            'avg_close_time': avg_close_time,
            'unassigned_leads': unassigned_leads,
        }

    @api.model
    def get_lead_stage_data(self, period):
        """funnel chart"""
        period_days = get_period_start_date(period)
        crm_model = self.search([('create_date', '>=', period_days)])
        stage_lead_count = {}

        for lead in crm_model:
            stage_name = lead.stage_id.name
            if stage_name in stage_lead_count:
                stage_lead_count[stage_name] += 1
            else:
                stage_lead_count[stage_name] = 1

        # Convert the dictionary into lists for stages and their counts
        crm_stages = list(stage_lead_count.keys())
        lead_count = list(stage_lead_count.values())

        # Return the data in the expected format
        return [lead_count, crm_stages]

    @api.model
    def get_lead_by_month(self):
        """pie chart"""
        month_count = []
        month_value = []
        for rec in self.search([]):
            month = rec.create_date.month
            if month not in month_value:
                month_value.append(month)
            month_count.append(month)
        lang = self.env.lang or 'en_US'
        month_val = [{'label': _month_label(month, lang),
                      'value': month_count.count(month)} for month in
                     month_value]
        names = [record['label'] for record in month_val]
        counts = [record['value'] for record in month_val]
        month = [counts, names]
        return month

    @api.model
    def get_crm_activities(self, period):
        """Sales Activity Pie"""
        start_date = get_period_start_date(period)
        self._cr.execute('''
               SELECT mail_activity_type.name, COUNT(*)
               FROM mail_activity
               INNER JOIN mail_activity_type
                   ON mail_activity.activity_type_id = mail_activity_type.id
               INNER JOIN crm_lead
                   ON mail_activity.res_id = crm_lead.id
                   AND mail_activity.res_model = 'crm.lead'
               WHERE crm_lead.create_date >= %s
               GROUP BY mail_activity_type.name
           ''', (start_date,))
        data = self._cr.dictfetchall()
        # mail_activity_type.name is a translate=True JSONB field. The original
        # code forced 'en_US' which ignored the user's language. Use the user's
        # lang instead, falling back to en_US if the language isn't installed.
        user_lang = self.env.lang or 'en_US'
        names = [
            (record['name'].get(user_lang)
             or record['name'].get('en_US')
             or next(iter(record['name'].values()), ''))
            for record in data
        ]
        counts = [record['count'] for record in data]
        return [counts, names]

    @api.model
    def get_the_campaign_pie(self, period):
        """Leads Group By Campaign Pie"""
        start_date = get_period_start_date(period)
        self._cr.execute('''SELECT campaign_id, COUNT(*),
                               (SELECT name FROM utm_campaign 
                                WHERE utm_campaign.id = crm_lead.campaign_id)
                               FROM crm_lead WHERE create_date >= %s AND campaign_id IS NOT NULL GROUP BY
                                campaign_id''', (start_date,))
        data = self._cr.dictfetchall()
        names = [record.get('name') for record in data]
        counts = [record.get('count') for record in data]
        final = [counts, names]
        return final

    @api.model
    def get_the_source_pie(self, period):
        """Leads Group By Source Pie"""
        start_date = get_period_start_date(period)
        self._cr.execute('''SELECT source_id, COUNT(*),
                                (SELECT name FROM utm_source 
                                 WHERE utm_source.id = crm_lead.source_id)
                                FROM crm_lead WHERE create_date >= %s AND source_id IS NOT NULL GROUP BY 
                                source_id''', (start_date,))
        data = self._cr.dictfetchall()
        names = [record.get('name') for record in data]
        counts = [record.get('count') for record in data]
        final = [counts, names]
        return final

    @api.model
    def get_the_medium_pie(self, period):
        """Leads Group By Medium Pie"""
        start_date = get_period_start_date(period)
        self._cr.execute('''SELECT medium_id, COUNT(*),
                                (SELECT name FROM utm_medium 
                                 WHERE utm_medium.id = crm_lead.medium_id)
                                FROM crm_lead WHERE create_date >= %s AND medium_id IS NOT NULL GROUP BY medium_id''',
                         (start_date,))
        data = self._cr.dictfetchall()
        names = [record.get('name') for record in data]
        counts = [record.get('count') for record in data]
        final = [counts, names]
        return final

    @api.model
    def get_total_lost_crm(self, period):
        """Lost Opportunity or Lead Graph"""
        # Initialize the dictionary with month names and counts (localized)
        start_date = get_period_start_date(period)

        if period == 'year':
            num_months = 12
        elif period == 'quarter':
            num_months = 3
        else:
            num_months = 1

        lang = self.env.lang or 'en_US'
        month_dict = {}
        for i in range(num_months):
            current_month = start_date + relativedelta(months=i)
            # Group by month number (locale-independent) so the SQL doesn't
            # return month names in the cluster's default locale.
            month_num = current_month.month
            month_name = _month_label(month_num, lang)
            month_dict[month_num] = {'label': month_name, 'count': 0}

        # Execute the SQL query: group by month NUMBER (not name) so the
        # result is independent of the cluster locale.
        self._cr.execute('''SELECT EXTRACT(MONTH FROM create_date)::int AS month_num,
                                       COUNT(id) AS count
                                FROM crm_lead
                                WHERE probability = 0
                                  AND active = FALSE
                                  AND create_date >= %s
                                GROUP BY month_num
                                ORDER BY month_num''',
                         (start_date,))

        data = self._cr.dictfetchall()

        # Update month_dict with the results from the query
        for rec in data:
            month_num = rec['month_num']
            if month_num in month_dict:
                month_dict[month_num]['count'] = rec['count']

        # Preserve original response shape: ordered list of month labels and
        # parallel list of counts.
        ordered = sorted(month_dict.items(), key=lambda kv: kv[0])
        result = {
            'month': [entry['label'] for _, entry in ordered],
            'count': [entry['count'] for _, entry in ordered],
        }

        return result

    @api.model
    def get_upcoming_events(self):
        """Upcoming Activities Table"""
        today = fields.Date.today()
        session_user_id = self.env.uid
        self._cr.execute('''select mail_activity.activity_type_id,
            mail_activity.date_deadline, mail_activity.summary,
            mail_activity.res_name,(SELECT mail_activity_type.name
            FROM mail_activity_type WHERE mail_activity_type.id = 
            mail_activity.activity_type_id), mail_activity.user_id FROM 
            mail_activity WHERE res_model = 'crm.lead' AND 
            mail_activity.date_deadline >= '%s' and user_id = %s GROUP BY 
            mail_activity.activity_type_id, mail_activity.date_deadline,
            mail_activity.summary,mail_activity.res_name,mail_activity.user_id
            order by mail_activity.date_deadline asc''' % (
        today, session_user_id))
        data = self._cr.fetchall()
        events = [[record[0], record[1], record[2], record[3],
                   record[4] if record[4] else '',
                   self.env['res.users'].browse(record[5]).name if record[
                       5] else ''
                   ] for record in data]
        return {
            'event': events,
            'cur_lang': self.env.context.get('lang')
        }

    @api.model
    def total_revenue_by_sales(self, period):
        """Total expected revenue and count Pie"""
        session_user_id = self.env.uid
        start_date = get_period_start_date(period)
        # SQL query template
        query_template = """
            SELECT sum(expected_revenue) as revenue 
            FROM crm_lead 
            WHERE user_id = %s 
            AND type = 'opportunity' 
            AND active = %s 
            {conditions}
        """

        # Query conditions for different cases
        conditions = [
            "",  # Active opportunities
            "AND stage_id = '4'",  # Won opportunities
            "AND probability = '0'",  # Lost opportunities
        ]

        # Active status for each condition
        active_status = ['true', 'false', 'false']

        # Fetch total revenue for each condition
        revenues = []
        for cond, active in zip(conditions, active_status):
            self._cr.execute(query_template.format(conditions=cond),
                             (session_user_id, active))
            revenue = self._cr.fetchone()[0] or 0
            revenues.append(revenue)

        # Calculate expected revenue without won
        exp_revenue_without_won = revenues[0] - revenues[1]

        # Prepare the data for the pie chart. Labels are translated via _()
        # so they follow the current user's language.
        revenue_pie_count = [exp_revenue_without_won, revenues[1], revenues[2]]
        revenue_pie_title = [
            _('Expected without Won'),
            _('Won'),
            _('Lost'),
        ]

        return [revenue_pie_count, revenue_pie_title]


    @api.model
    def get_top_sp_revenue(self,period):
        """Top 10 Salesperson revenue Table"""
        user = self.env.user
        start_date = get_period_start_date(period)
        self._cr.execute('''SELECT user_id, id, expected_revenue, name, company_id
                                    FROM crm_lead 
                                    WHERE create_date >= '%s' AND expected_revenue IS NOT NULL AND user_id = %s
                                    GROUP BY user_id, id 
                                    ORDER BY expected_revenue DESC 
                                    LIMIT 10''' % (start_date,user.id,))
        data1 = self._cr.fetchall()
        top_revenue = [
            [self.env['res.users'].browse(rec[0]).name, rec[1], rec[2],
             rec[3], self.env['res.company'].browse(rec[4]).currency_id.symbol]
            for rec in data1]
        return {'top_revenue': top_revenue}

    @api.model
    def get_top_country_revenue(self, period):
        """Top 10 Country Wise Revenue - Heat Map"""
        company_id = self.env.company.id
        self._cr.execute('''SELECT country_id, sum(expected_revenue)
                                FROM crm_lead 
                                WHERE expected_revenue IS NOT NULL 
                                AND country_id IS NOT NULL
                                GROUP BY country_id 
                                ORDER BY sum(expected_revenue) DESC 
                                LIMIT 10''')
        data1 = self._cr.fetchall()
        country_revenue = [[self.env['res.country'].browse(rec[0]).name,
                            rec[1], self.env['res.company'].browse(
                company_id).currency_id.symbol] for rec in data1]
        return {'country_revenue': country_revenue}

    @api.model
    def get_top_country_count(self, period):
        """Top 10 Country Wise Count - Heat Map"""
        self._cr.execute('''SELECT country_id, COUNT(*) 
                                FROM crm_lead 
                                WHERE country_id IS NOT NULL 
                                GROUP BY country_id 
                                ORDER BY COUNT(*) DESC 
                                LIMIT 10''')
        data1 = self._cr.fetchall()
        country_count = [[self.env['res.country'].browse(rec[0]).name, rec[1]]
                         for rec in data1]
        return {'country_count': country_count}

    @api.model
    def get_recent_activities(self, kwargs):
        """Recent Activities Table"""
        today = fields.Date.today()
        recent_week = today - relativedelta(days=7)
        current_user_id = self.env.user.id  # Get the current logged-in user's ID
        # Check if the current user is an administrator
        is_admin = self.env.user.has_group('base.group_system')
        # Build the SQL query with or without user filtering based on role
        if is_admin:
            self._cr.execute('''
                    SELECT mail_activity.activity_type_id,
                           mail_activity.date_deadline,
                           mail_activity.summary,
                           mail_activity.res_name,
                           (SELECT mail_activity_type.name
                            FROM mail_activity_type
                            WHERE mail_activity_type.id = mail_activity.activity_type_id),
                           mail_activity.user_id
                    FROM mail_activity
                    WHERE res_model = 'crm.lead'
                      AND mail_activity.date_deadline BETWEEN %s AND %s
                    GROUP BY mail_activity.activity_type_id,
                             mail_activity.date_deadline,
                             mail_activity.summary,
                             mail_activity.res_name,
                             mail_activity.user_id
                    ORDER BY mail_activity.date_deadline DESC
                ''', (recent_week, today))
        else:
            self._cr.execute('''
                    SELECT mail_activity.activity_type_id,
                           mail_activity.date_deadline,
                           mail_activity.summary,
                           mail_activity.res_name,
                           (SELECT mail_activity_type.name
                            FROM mail_activity_type
                            WHERE mail_activity_type.id = mail_activity.activity_type_id),
                           mail_activity.user_id
                    FROM mail_activity
                    WHERE res_model = 'crm.lead'
                      AND mail_activity.date_deadline BETWEEN %s AND %s
                      AND mail_activity.user_id = %s
                    GROUP BY mail_activity.activity_type_id,
                             mail_activity.date_deadline,
                             mail_activity.summary,
                             mail_activity.res_name,
                             mail_activity.user_id
                    ORDER BY mail_activity.date_deadline DESC
                ''', (recent_week, today, current_user_id))

        data = self._cr.fetchall()
        activities = [
            [*record[:5], self.env['res.users'].browse(record[5]).name] for
            record in data]
        return {'activities': activities}
