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
import calendar
import datetime
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models


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
        converted_count = 0
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
                converted_count += 1
                total_seconds += (record.date_conversion
                                  - record.create_date).total_seconds()

        win_ratio = win_count / active_lead_count if active_lead_count else 0
        opportunity_ratio = won_opportunity_count / active_opportunity_count if active_opportunity_count else 0
        # Average closing time in days
        avg_close_time = round(total_seconds / converted_count / 86400,
                               2) if converted_count else 0

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
        groups = self._read_group([], ['create_date:month_number'],
                                  ['__count'])
        names = [calendar.month_name[int(month)] for month, _count in groups]
        counts = [count for _month, count in groups]
        return [counts, names]

    @api.model
    def get_crm_activities(self, period):
        """Sales Activity Pie"""
        start_date = get_period_start_date(period)
        self.env.cr.execute('''
               SELECT mail_activity.activity_type_id, COUNT(*)
               FROM mail_activity
               INNER JOIN crm_lead
                   ON mail_activity.res_id = crm_lead.id
                   AND mail_activity.res_model = 'crm.lead'
               WHERE crm_lead.create_date >= %s
               GROUP BY mail_activity.activity_type_id
           ''', (start_date,))
        data = self.env.cr.fetchall()
        names = [self._get_activity_type_name(type_id)
                 for type_id, _count in data]
        counts = [count for _type_id, count in data]
        return [counts, names]

    def _get_activity_type_name(self, activity_type_id):
        """Return the activity type name in the user's language, or an
        empty string when the activity has no type"""
        if not activity_type_id:
            return ''
        return self.env['mail.activity.type'].browse(activity_type_id).name

    @api.model
    def get_the_campaign_pie(self, period):
        """Leads Group By Campaign Pie"""
        start_date = get_period_start_date(period)
        self.env.cr.execute('''SELECT campaign_id, COUNT(*),
                               (SELECT name FROM utm_campaign 
                                WHERE utm_campaign.id = crm_lead.campaign_id)
                               FROM crm_lead WHERE create_date >= %s AND campaign_id IS NOT NULL GROUP BY
                                campaign_id''', (start_date,))
        data = self.env.cr.dictfetchall()
        names = [record.get('name') for record in data]
        counts = [record.get('count') for record in data]
        final = [counts, names]
        return final

    @api.model
    def get_the_source_pie(self, period):
        """Leads Group By Source Pie"""
        start_date = get_period_start_date(period)
        self.env.cr.execute('''SELECT source_id, COUNT(*),
                                (SELECT name FROM utm_source 
                                 WHERE utm_source.id = crm_lead.source_id)
                                FROM crm_lead WHERE create_date >= %s AND source_id IS NOT NULL GROUP BY 
                                source_id''', (start_date,))
        data = self.env.cr.dictfetchall()
        names = [record.get('name') for record in data]
        counts = [record.get('count') for record in data]
        final = [counts, names]
        return final

    @api.model
    def get_the_medium_pie(self, period):
        """Leads Group By Medium Pie"""
        start_date = get_period_start_date(period)
        self.env.cr.execute('''SELECT medium_id, COUNT(*),
                                (SELECT name FROM utm_medium 
                                 WHERE utm_medium.id = crm_lead.medium_id)
                                FROM crm_lead WHERE create_date >= %s AND medium_id IS NOT NULL GROUP BY medium_id''',
                         (start_date,))
        data = self.env.cr.dictfetchall()
        names = [record.get('name') for record in data]
        counts = [record.get('count') for record in data]
        final = [counts, names]
        return final

    @api.model
    def get_total_lost_crm(self, period):
        """Lost Opportunity or Lead Graph"""
        month_dict = {}

        # Format the start date to be used in the SQL query
        start_date = get_period_start_date(period)

        if period == 'year':
            num_months = 12
        elif period == 'quarter':
            num_months = 3
        else:
            num_months = 1

            # Initialize the dictionary with month names and counts
        for i in range(num_months):
            current_month = start_date + relativedelta(months=i)
            month_name = current_month.strftime('%B')
            month_dict[month_name] = 0

            # Execute the SQL query to count lost opportunities
        self.env.cr.execute('''SELECT TO_CHAR(create_date, 'Month') AS month, 
                                       COUNT(id) 
                                FROM crm_lead
                                WHERE probability = 0 
                                  AND active = FALSE 
                                  AND create_date >= %s
                                GROUP BY TO_CHAR(create_date, 'Month')
                                ORDER BY TO_CHAR(create_date, 'Month')''',
                         (start_date,))

        data = self.env.cr.dictfetchall()

        # Update month_dict with the results from the query
        for rec in data:
            month_name = rec[
                'month'].strip()  # Strip the month name to remove extra spaces
            if month_name in month_dict:
                month_dict[month_name] = rec['count']

        result = {
            'month': list(month_dict.keys()),
            'count': list(month_dict.values())
        }

        return result

    @api.model
    def get_upcoming_events(self):
        """Upcoming Activities Table"""
        today = fields.Date.today()
        session_user_id = self.env.uid
        self.env.cr.execute('''select mail_activity.activity_type_id,
            mail_activity.date_deadline, mail_activity.summary,
            mail_activity.res_name,(SELECT mail_activity_type.name
            FROM mail_activity_type WHERE mail_activity_type.id = 
            mail_activity.activity_type_id), mail_activity.user_id FROM 
            mail_activity WHERE res_model = 'crm.lead' AND
            mail_activity.date_deadline >= %s and user_id = %s GROUP BY
            mail_activity.activity_type_id, mail_activity.date_deadline,
            mail_activity.summary,mail_activity.res_name,mail_activity.user_id
            order by mail_activity.date_deadline asc''',
                            (today, session_user_id))
        data = self.env.cr.fetchall()
        events = [[record[0], record[1], record[2], record[3],
                   self._get_activity_type_name(record[0]),
                   self.env['res.users'].browse(record[5]).name if record[
                       5] else ''
                   ] for record in data]
        return {'event': events}

    @api.model
    def total_revenue_by_sales(self, period):
        """Total expected revenue and count Pie"""
        session_user_id = self.env.uid
        start_date = get_period_start_date(period)
        self.env.cr.execute('''
            SELECT COALESCE(SUM(crm_lead.expected_revenue)
                       FILTER (WHERE crm_lead.active), 0),
                   COALESCE(SUM(crm_lead.expected_revenue)
                       FILTER (WHERE crm_lead.active AND crm_stage.is_won), 0),
                   COALESCE(SUM(crm_lead.expected_revenue)
                       FILTER (WHERE NOT crm_lead.active
                               AND crm_lead.probability = 0), 0)
            FROM crm_lead
            LEFT JOIN crm_stage ON crm_stage.id = crm_lead.stage_id
            WHERE crm_lead.user_id = %s
              AND crm_lead.type = 'opportunity'
              AND crm_lead.create_date >= %s
        ''', (session_user_id, start_date))
        active_revenue, won_revenue, lost_revenue = self.env.cr.fetchone()
        revenue_pie_count = [active_revenue - won_revenue, won_revenue,
                             lost_revenue]
        revenue_pie_title = ['Expected without Won', 'Won', 'Lost']
        return [revenue_pie_count, revenue_pie_title]

    @api.model
    def get_top_sp_revenue(self, period):
        """Top 10 Salesperson revenue Table"""
        user = self.env.user
        start_date = get_period_start_date(period)
        self.env.cr.execute('''SELECT user_id, id, expected_revenue, name, company_id
                                    FROM crm_lead 
                                    WHERE create_date >= %s AND expected_revenue IS NOT NULL AND user_id = %s
                                    GROUP BY user_id, id
                                    ORDER BY expected_revenue DESC
                                    LIMIT 10''', (start_date, user.id))
        data1 = self.env.cr.fetchall()
        top_revenue = [
            [self.env['res.users'].browse(rec[0]).name, rec[1], rec[2],
             rec[3], (self.env['res.company'].browse(rec[4])
                      or self.env.company).currency_id.symbol]
            for rec in data1]
        return {'top_revenue': top_revenue}

    @api.model
    def get_top_country_revenue(self, period):
        """Top 10 Country Wise Revenue - Heat Map"""
        company_id = self.env.company.id
        self.env.cr.execute('''SELECT country_id, sum(expected_revenue)
                                FROM crm_lead 
                                WHERE expected_revenue IS NOT NULL 
                                AND country_id IS NOT NULL
                                GROUP BY country_id 
                                ORDER BY sum(expected_revenue) DESC 
                                LIMIT 10''')
        data1 = self.env.cr.fetchall()
        country_revenue = [[self.env['res.country'].browse(rec[0]).name,
                            rec[1], self.env['res.company'].browse(
                company_id).currency_id.symbol] for rec in data1]
        return {'country_revenue': country_revenue}

    @api.model
    def get_top_country_count(self, period):
        """Top 10 Country Wise Count - Heat Map"""
        self.env.cr.execute('''SELECT country_id, COUNT(*) 
                                FROM crm_lead 
                                WHERE country_id IS NOT NULL 
                                GROUP BY country_id 
                                ORDER BY COUNT(*) DESC 
                                LIMIT 10''')
        data1 = self.env.cr.fetchall()
        country_count = [[self.env['res.country'].browse(rec[0]).name, rec[1]]
                         for rec in data1]
        return {'country_count': country_count}

    @api.model
    def get_recent_activities(self):
        """Recent Activities Table: activities of the last seven days"""
        today = fields.Date.today()
        recent_week = today - relativedelta(days=7)
        current_user_id = self.env.user.id  # Get the current logged-in user's ID
        # Check if the current user is an administrator
        is_admin = self.env.user.has_group('base.group_system')
        # Build the SQL query with or without user filtering based on role
        if is_admin:
            self.env.cr.execute('''
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
            self.env.cr.execute('''
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

        data = self.env.cr.fetchall()
        activities = [
            [*record[:4], self._get_activity_type_name(record[0]),
             self.env['res.users'].browse(record[5]).name] for record in data]
        return {'activities': activities}
