# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author:  Mruthul Raj (odoo@cybrosys.com)
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
import calendar
from datetime import datetime

from dateutil.relativedelta import relativedelta
from odoo import api, fields, models
from odoo.http import request
from odoo.tools import date_utils


class CRMLead(models.Model):
    """Extends crm.lead for adding more functions in it"""
    _inherit = 'crm.lead'

    monthly_goal = fields.Float(string="Monthly Goal", help="Lead monthly goal")
    achievement_amount = fields.Float(string="Monthly Achievement",
                                      help="Achievement for the month")

    @api.model
    def _get_currency(self):
        """Get the currency symbol and position for the current user's company.
        Returns:
            list: A list containing the currency symbol and its position."""
        currency_array = [self.env.user.company_id.currency_id.symbol,
                          self.env.user.company_id.currency_id.position]
        return currency_array

    @api.model
    def check_user_group(self, kwargs):
        """Checking a user group"""
        user = self.env.user
        if user.has_group('sales_team.group_sale_manager'):
            return True
        else:
            return False

    @api.model
    def get_lead_stage_data(self, kwargs):
        """funnel chart"""
        stage_ids = self.env["crm.stage"].search([])
        crm_list = []
        for stage in stage_ids:
            leads = self.search_count([("stage_id", "=", stage.id)])
            crm_list.append((stage.name, int(leads)))
        return crm_list

    @api.model
    def get_lead_month_pie(self, kwargs):
        """pie chart"""
        month_count = []
        month_value = []
        leads = self.env['crm.lead'].search([])
        for rec in leads:
            month = rec.create_date.month
            if month not in month_value:
                month_value.append(month)
            month_count.append(month)
        month_val = [{'label': calendar.month_name[month],
                      'value': month_count.count(month)} for month in
                     month_value]
        names = [record['label'] for record in month_val]
        counts = [record['value'] for record in month_val]
        month = [counts, names]
        return month

    @api.model
    def get_the_sales_activity(self, kwargs):
        """Sales Activity Pie"""
        self._cr.execute('''SELECT mail_activity_type.name, COUNT(*) FROM 
                            mail_activity 
                            INNER JOIN mail_activity_type ON 
                            mail_activity.activity_type_id = mail_activity_type.id
                            WHERE mail_activity.res_model = 'crm.lead' 
                            GROUP BY mail_activity_type.name''')
        data = self._cr.dictfetchall()
        names = [record['name']['en_US'] for record in data]
        counts = [record['count'] for record in data]
        return [counts, names]

    @api.model
    def get_the_annual_target(self, kwargs):
        """Annual Target: Year To Date Graph"""
        session_user_id = self.env.uid
        self._cr.execute('''SELECT res_users.id, res_users.sales, res_users.sale_team_id, 
                                (SELECT crm_team.invoiced_target FROM crm_team 
                                WHERE crm_team.id = res_users.sale_team_id) as invoiced_target 
                                FROM res_users WHERE res_users.sales IS NOT NULL 
                                AND res_users.id=%s AND res_users.sale_team_id IS NOT NULL;''' % session_user_id)
        data2 = self._cr.dictfetchall()
        sales = [rec['sales'] for rec in data2]
        inv_target = [
            rec['invoiced_target'] if rec['invoiced_target'] is not None else 0
            for rec in data2]
        team_id = data2[-1]['sale_team_id'] if data2 else 0
        target_annual = sum(sales) + sum(inv_target)
        if self.env.user.has_group('sales_team.group_sale_manager'):
            self._cr.execute('''SELECT res_users.id,res_users.sales,
            res_users.sale_team_id, (SELECT crm_team.invoiced_target FROM 
            crm_team WHERE crm_team.id = res_users.sale_team_id) FROM res_users 
            WHERE res_users.id = %s AND res_users.sales is not null;'''
                             % session_user_id)
            data3 = self._cr.dictfetchall()
            sales = []
            inv_target = []
            for rec in data3:
                sales.append(rec['sales'])
                inv_target.append(rec['invoiced_target'])
                if inv_target == [None]:
                    inv_target = [0]
            ytd_target = (sum(sales) + sum(inv_target))
            self._cr.execute('''select sum(expected_revenue) from crm_lead 
            where stage_id=4 and team_id=%s AND Extract(Year FROM date_closed)=
            Extract(Year FROM DATE(NOW()))''' % team_id)
            achieved_won_data = self._cr.dictfetchall()
            achieved_won = [item['sum'] for item in achieved_won_data]
        else:
            self._cr.execute(
                '''SELECT res_users.id,res_users.sales FROM res_users WHERE 
                res_users.id = %s AND res_users.sales is not null;''' %
                session_user_id)
            data4 = self._cr.dictfetchall()
            sales = []
            for rec in data4:
                sales.append(rec['sales'])
            ytd_target = (sum(sales))
            self._cr.execute('''select sum(expected_revenue) from crm_lead 
            where stage_id=4 and user_id=%s AND 
            Extract(Year FROM date_closed)=Extract(Year FROM DATE(NOW()))'''
                             % session_user_id)
            achieved_won_data = self._cr.dictfetchall()
            achieved_won = [item['sum'] for item in achieved_won_data]
        won = achieved_won[0]
        if won is None:
            won = 0
        value = [target_annual, ytd_target, won]
        name = ["Annual Target", "YtD target", "Won"]
        final = [value, name]
        return final

    @api.model
    def get_the_campaign_pie(self, kwargs):
        """Leads Group By Campaign Pie"""
        self._cr.execute('''SELECT campaign_id, COUNT(*),
                            (SELECT name FROM utm_campaign 
                             WHERE utm_campaign.id = crm_lead.campaign_id)
                            FROM crm_lead WHERE campaign_id IS NOT NULL GROUP BY
                             campaign_id''')
        data = self._cr.dictfetchall()
        names = [record.get('name') for record in data]
        counts = [record.get('count') for record in data]
        final = [counts, names]
        return final

    @api.model
    def get_the_source_pie(self, kwargs):
        """Leads Group By Source Pie"""
        self._cr.execute('''SELECT source_id, COUNT(*),
                            (SELECT name FROM utm_source 
                             WHERE utm_source.id = crm_lead.source_id)
                            FROM crm_lead WHERE source_id IS NOT NULL GROUP BY 
                            source_id''')
        data = self._cr.dictfetchall()
        names = [record.get('name') for record in data]
        counts = [record.get('count') for record in data]
        final = [counts, names]
        return final

    @api.model
    def get_the_medium_pie(self, kwargs):
        """Leads Group By Medium Pie"""
        self._cr.execute('''SELECT medium_id, COUNT(*),
                            (SELECT name FROM utm_medium 
                             WHERE utm_medium.id = crm_lead.medium_id)
                            FROM crm_lead WHERE medium_id IS NOT NULL GROUP BY medium_id''')
        data = self._cr.dictfetchall()
        names = [record.get('name') for record in data]
        counts = [record.get('count') for record in data]
        final = [counts, names]
        return final

    @api.model
    def revenue_count_pie(self, kwargs):
        """Total expected revenue and count Pie"""
        session_user_id = self.env.uid

        def fetch_total_revenue(query):
            self._cr.execute(query)
            total_rev_data = self._cr.dictfetchall()
            total_rev = total_rev_data[0]['revenue'] if total_rev_data and \
                                                        total_rev_data[0][
                                                            'revenue'] else 0
            return total_rev

        queries = [
            f"SELECT sum(expected_revenue) as revenue FROM crm_lead WHERE user_id={session_user_id} AND type='opportunity' AND active='true'",
            f"SELECT sum(expected_revenue) as revenue FROM crm_lead WHERE user_id={session_user_id} AND type='opportunity' AND active='false' AND stage_id='4'",
            f"SELECT sum(expected_revenue) as revenue FROM crm_lead WHERE user_id={session_user_id} AND type='opportunity' AND active='false' AND probability='0' AND active='false'"
        ]
        total_expected_revenue, total_won_rev, total_lost_rev = [
            fetch_total_revenue(query) for query in queries]
        exp_revenue_without_won = total_expected_revenue - total_won_rev
        revenue_pie_count = [exp_revenue_without_won, total_won_rev,
                             total_lost_rev]
        revenue_pie_title = ['Expected without Won', 'Won', 'Lost']
        revenue_data = [revenue_pie_count, revenue_pie_title]
        return revenue_data

    @api.model
    def get_upcoming_events(self, kwargs):
        """Upcoming Activities Table"""
        today = fields.date.today()
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
        order by mail_activity.date_deadline asc''' % (today, session_user_id))
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
    def get_top_deals(self, kwargs):
        """Top 10 Deals Table"""
        self._cr.execute('''SELECT crm_lead.user_id,crm_lead.id,
        crm_lead.expected_revenue, crm_lead.name,crm_lead.company_id, 
        (SELECT crm_team.name FROM crm_team
        WHERE crm_lead.team_id = crm_team.id) from crm_lead where 
        crm_lead.expected_revenue is not null and crm_lead.type = 'opportunity' 
        GROUP BY crm_lead.user_id,
        crm_lead.id,crm_lead.expected_revenue,crm_lead.name,crm_lead.company_id
        order by crm_lead.expected_revenue DESC limit 10''')
        data1 = self._cr.fetchall()
        deals = [[self.env['res.users'].browse(rec[0]).name,
                  rec[1], rec[2], rec[3],
                  self.env['res.company'].browse(rec[4]).currency_id.symbol,
                  rec[5], index + 1] for index, rec in enumerate(data1)]
        return {'deals': deals}

    @api.model
    def get_monthly_goal(self, kwargs):
        """Monthly Goal Gauge"""
        uid = request.session.uid
        leads = self.env['crm.lead'].search([
            ('date_deadline', '!=', False), ('user_id', '=', uid),
            ('type', '=', 'opportunity')])
        leads_won = self.env['crm.lead'].search([
            ('date_closed', '!=', False), ('stage_id', '=', 4),
            ('user_id', '=', uid), ('type', '=', 'opportunity')])
        currency_symbol = self.env.company.currency_id.symbol
        achievement = sum(won.expected_revenue for won in leads_won.filtered(
            lambda a: a.date_closed.month == fields.date.today().month and
                      a.date_closed.year == fields.date.today().year))
        total = sum(rec.expected_revenue for rec in leads.filtered(
            lambda t: t.date_deadline.month == fields.date.today().month and
                      t.date_deadline.year == fields.date.today().year))
        self.monthly_goal = total
        self.achievement_amount = achievement
        percent = (achievement * 100 / total) / 100 if total > 0 else 0
        goals = [achievement, total, currency_symbol, percent]
        return {'goals': goals}

    @api.model
    def get_top_sp_revenue(self, kwargs):
        """Top 10 Salesperson revenue Table"""
        user = self.env.user
        self._cr.execute('''SELECT user_id, id, expected_revenue, name, company_id
                            FROM crm_lead 
                            WHERE expected_revenue IS NOT NULL AND user_id = %s
                            GROUP BY user_id, id 
                            ORDER BY expected_revenue DESC 
                            LIMIT 10''' % user.id)
        data1 = self._cr.fetchall()
        top_revenue = [
            [self.env['res.users'].browse(rec[0]).name, rec[1], rec[2],
             rec[3], self.env['res.company'].browse(rec[4]).currency_id.symbol]
            for rec in data1]
        return {'top_revenue': top_revenue}

    @api.model
    def get_country_revenue(self, kwargs):
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
    def get_country_count(self, kwargs):
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
    def get_total_lost_crm(self, option):
        """Lost Opportunity or Lead Graph"""
        month_dict = {}
        for i in range(int(option) - 1, -1, -1):
            last_month = fields.Datetime.now() - relativedelta(months=i)
            text = format(last_month, '%B')
            month_dict[text] = 0
        if option == '1':
            day_dict = {}
            last_day = date_utils.end_of(fields.Date.today(),
                                         "month").strftime("%d")
            for i in range(1, int(last_day), 1):
                day_dict[i] = 0
            self._cr.execute('''select create_date::date,count(id) from crm_lead
            where probability=0 and active=false and create_date between 
            (now() - interval '1 month') and now()
            group by create_date order by create_date;''')
            data = self._cr.dictfetchall()
            for rec in data:
                day_dict[int(rec['create_date'].strftime("%d"))] = rec['count']

            test = {'month': list(day_dict.keys()),
                    'count': list(day_dict.values())}
        else:
            month_string = str(int(option)) + ' Months'
            self._cr.execute('''select extract(month from create_date),count(id)
            from crm_lead where probability=0 and active=false and
            create_date between (now() - interval '%s') and now()
            group by extract(month from create_date) order by extract(
            month from create_date);''' % month_string)
            data = self._cr.dictfetchall()
            for rec in data:
                datetime_object = datetime.strptime(
                    str(int(rec['date_part'])), "%m")
                month_name = datetime_object.strftime("%B")
                month_dict[month_name] = rec['count']
            test = {'month': list(month_dict.keys()),
                    'count': list(month_dict.values())}
        return test

    @api.model
    def get_ratio_based_country(self, kwargs):
        """Top 5 Won vs Lost Ratio based on Country"""
        self._cr.execute('''SELECT (SELECT name FROM res_country WHERE id=country_id),
                            COUNT(country_id)FROM crm_lead
                            WHERE probability=100 AND active=true
                            GROUP BY country_id
                            ORDER BY COUNT(country_id) DESC''')
        data_won = self._cr.fetchall()
        self._cr.execute('''SELECT (SELECT name FROM res_country WHERE id=country_id),
                                COUNT(country_id)
                            FROM crm_lead
                            WHERE probability=0 AND active=false
                            GROUP BY country_id
                            ORDER BY COUNT(country_id) DESC''')
        data_lost = self._cr.fetchall()
        country_wise_ratio = [[won[0], won[1], str(round(won[1] / next(
            (lost[1] for lost in data_lost if lost[0] == won[0]), 1),
                                                         2))] for won in
                              data_won[:5]]
        return {'country_wise_ratio': country_wise_ratio}

    @api.model
    def get_ratio_based_sp(self, kwargs):
        """Top 5 Won vs Lost Ratio based on Sales Person"""
        self._cr.execute('''select user_id,count(user_id) from crm_lead where
        probability=100 and active=true group by user_id order by 
        count(user_id) desc''')
        data_won = self._cr.fetchall()
        self._cr.execute('''select user_id,count(user_id) from crm_lead where 
        probability=0 and active=false group by user_id order by 
        count(user_id) desc''')
        data_lost = self._cr.fetchall()
        won = [[user_id_obj.name, rec[1]] for rec in data_won for user_id_obj in
               self.env['res.users'].browse(rec[0])]
        for won_list in won:
            won_list.append(next((lose[1] for lose in data_lost if
                                  self.env['res.users'].browse(
                                      data_won[won.index(won_list)][0]).name ==
                                  self.env['res.users'].browse(lose[0]).name),
                                 0))
        salesperson_wise_ratio = [[data[0], data[1], data[2],
                                   round(data[1] / data[2], 2) if data[
                                                                      2] != 0 else 0]
                                  for data in won if len(data) == 2]
        salesperson_wise_ratio = sorted(salesperson_wise_ratio,
                                        key=lambda x: x[3], reverse=True)[:5]
        return {'salesperson_wise_ratio': salesperson_wise_ratio}

    @api.model
    def get_ratio_based_sales_team(self, kwargs):
        """Top 5 Won vs Lost Ratio based on Sales Team"""
        self._cr.execute('''select (SELECT name FROM crm_team WHERE crm_team.id 
        = team_id), count(user_id) from crm_lead where probability=100 and 
        active=true group by team_id order by count(team_id) desc''')
        data_won = self._cr.fetchall()
        self._cr.execute('''select (SELECT name FROM crm_team WHERE crm_team.id 
        = team_id), count(user_id) from crm_lead where probability=0 and 
        active=false group by team_id order by count(team_id) desc''')
        data_lost = self._cr.fetchall()
        won = [[rec[0], rec[1]] for rec in data_won]
        for won_list in won:
            won_list.append(
                next((lose[1] for lose in data_lost if lose[0] == won_list[0]),
                     0))
        sales_team_wise_ratio = [[data[0], data[1], data[2],
                                  round(data[1] / data[2], 2) if data[
                                                                     2] != 0 else 0]
                                 for data in won if len(data) == 3]
        sales_team_wise_ratio = sorted(sales_team_wise_ratio,
                                       key=lambda x: x[3], reverse=True)[:5]
        return {'sales_team_wise_ratio': sales_team_wise_ratio}

    @api.model
    def get_lost_lead_by_reason_pie(self, kwargs):
        """Lost Leads by Lost Reason Pie"""
        self._cr.execute('''select lost_reason_id, count(*), (SELECT name FROM 
        crm_lost_reason WHERE id = lost_reason_id) from crm_lead where 
        probability=0 and active=false and type='lead' group by lost_reason_id''')
        data1 = self._cr.dictfetchall()
        name = [rec["name"] if rec["name"] is not None else "Undefined" for rec
                in data1]
        count = [rec["count"] for rec in data1]
        lost_leads = [count, name]
        return lost_leads

    @api.model
    def get_lost_lead_by_stage_pie(self, kwargs):
        """Lost Leads by Stage Pie"""
        self._cr.execute('''select stage_id, count(*),(SELECT name FROM 
        crm_stage WHERE id = stage_id) from crm_lead where probability=0 and 
        active=false and type='lead' group by stage_id''')
        data1 = self._cr.dictfetchall()
        name = [rec["name"] for rec in data1]
        count = [rec["count"] for rec in data1]
        lost_leads_stage = [count, name]
        return lost_leads_stage

    @api.model
    def get_recent_activities(self, kwargs):
        """Recent Activities Table"""
        today = fields.date.today()
        recent_week = today - relativedelta(days=7)
        self._cr.execute('''select mail_activity.activity_type_id,
        mail_activity.date_deadline, mail_activity.summary,
        mail_activity.res_name,(SELECT mail_activity_type.name
        FROM mail_activity_type WHERE mail_activity_type.id = 
        mail_activity.activity_type_id), mail_activity.user_id FROM 
        mail_activity WHERE res_model = 'crm.lead' AND
        mail_activity.date_deadline between '%s' and '%s' GROUP BY 
        mail_activity.activity_type_id, mail_activity.date_deadline,
        mail_activity.summary,mail_activity.res_name,mail_activity.user_id
        order by mail_activity.date_deadline desc''' % (recent_week, today))
        data = self._cr.fetchall()
        activities = [[*record[:5], self.env['res.users'].browse(record[5]).name
                       ] for record in data]
        return {'activities': activities}

    @api.model
    def get_count_unassigned(self, kwargs):
        """Unassigned Leads Count Card"""
        count_unassigned = self.env['crm.lead'].search_count(
            [('user_id', '=', False), ('type', '=', 'lead')])
        return {'count_unassigned': count_unassigned}

    @api.model
    @api.model
    def get_top_sp_by_invoice(self, kwargs):
        """Top 10 Sales Person by Invoice Table"""
        self._cr.execute('''select user_id,sum(amount_total) as total
        from sale_order where invoice_status='invoiced'
        group by user_id order by total desc limit 10''')
        data1 = self._cr.fetchall()
        sales_person_invoice = [[
            self.env['res.users'].browse(rec[0]).name, rec[1],
            self.env['res.users'].browse(rec[0]).company_id.currency_id.symbol,
            idx + 1, ] for idx, rec in enumerate(data1)]
        return {'sales_person_invoice': sales_person_invoice}

    @api.model
    def lead_details_user(self, kwargs):
        """Cards Count and Detail based on User"""
        session_user_id = self.env.uid
        month_count = []
        month_value = []
        leads = self.env['crm.lead'].search([])
        for rec in leads:
            month = rec.create_date.month
            if month not in month_value:
                month_value.append(month)
            month_count.append(month)
        value = []
        for index in range(len(month_value)):
            value = month_count.count(month_value[index])
        self._cr.execute('''SELECT res_users.id,res_users.sales,
        res_users.sale_team_id,(SELECT crm_team.invoiced_target FROM crm_team 
        WHERE crm_team.id = res_users.sale_team_id)
        FROM res_users WHERE res_users.sales is not null and res_users.id=%s
        AND res_users.sale_team_id is not null;''' % session_user_id)
        data2 = self._cr.dictfetchall()
        sales = []
        inv_target = []
        team_id = 0
        for rec in data2:
            sales.append(rec['sales'])
            inv_target.append(rec['invoiced_target'])
            if inv_target == [None]:
                inv_target = [0]
            team_id = rec['sale_team_id']
        target_annual = (sum(sales) + sum(inv_target))
        if self.env.user.has_group('sales_team.group_sale_manager'):
            self._cr.execute('''SELECT res_users.id,res_users.sales,
            res_users.sale_team_id,(SELECT crm_team.invoiced_target FROM 
            crm_team WHERE crm_team.id = res_users.sale_team_id) FROM 
            res_users WHERE res_users.id = %s AND res_users.sales is not 
            null;''' % session_user_id)
            data3 = self._cr.dictfetchall()
            sales = []
            inv_target = []
            for rec in data3:
                sales.append(rec['sales'])
                inv_target.append(rec['invoiced_target'])
                if inv_target == [None]:
                    inv_target = [0]
            ytd_target = (sum(sales) + sum(inv_target))
            self._cr.execute('''select sum(expected_revenue) from crm_lead where
             stage_id=4 and team_id=%s AND Extract(Year FROM date_closed)=
             Extract(Year FROM DATE(NOW()))''' % team_id)
            achieved_won_data = self._cr.dictfetchall()
            achieved_won = [item['sum'] for item in achieved_won_data]
        else:
            self._cr.execute('''SELECT res_users.id,res_users.sales FROM 
            res_users WHERE res_users.id = %s AND res_users.sales is not null;
            ''' % session_user_id)
            data4 = self._cr.dictfetchall()
            sales = []
            for rec in data4:
                sales.append(rec['sales'])
            ytd_target = (sum(sales))
            self._cr.execute('''select sum(expected_revenue) from crm_lead where
             stage_id=4 and user_id=%s AND Extract(Year FROM date_closed)=
             Extract(Year FROM DATE(NOW()))''' % session_user_id)
            achieved_won_data = self._cr.dictfetchall()
            achieved_won = [item['sum'] for item in achieved_won_data]
        won = achieved_won[0]
        if won is None:
            won = 0
        difference = target_annual - won
        self._cr.execute('''select COUNT(id) from crm_lead WHERE 
        crm_lead.user_id = '%s' AND Extract(MONTH FROM crm_lead.date_deadline) 
        = Extract( MONTH FROM DATE(NOW())) AND Extract(Year FROM 
        crm_lead.date_deadline) = Extract(Year FROM DATE(NOW()))
        ''' % session_user_id)
        record = self._cr.dictfetchall()
        rec_ids = [item['count'] for item in record]
        crm_lead_value = rec_ids[0]
        self._cr.execute('''select COUNT(id) from crm_lead WHERE 
        crm_lead.user_id = %s AND crm_lead.type = 'opportunity' AND 
        Extract(MONTH FROM crm_lead.date_deadline) = Extract(MONTH FROM 
        DATE(NOW())) AND Extract(Year FROM crm_lead.date_deadline
        ) = Extract(Year FROM DATE(NOW( )))''' % session_user_id)
        opportunity_data = self._cr.dictfetchall()
        opportunity_data_value = [item['count'] for item in opportunity_data]
        opportunity_value = opportunity_data_value[0]
        self._cr.execute('''select SUM(crm_lead.expected_revenue) from crm_lead 
        WHERE crm_lead.user_id = %s and type='opportunity' and active='true' 
        AND Extract(MONTH FROM crm_lead.date_deadline) = 
        Extract(MONTH FROM DATE(NOW())) AND Extract(Year FROM 
        crm_lead.date_deadline) = Extract(Year FROM DATE(NOW()))'''
                         % session_user_id)
        exp_revenue_data = self._cr.dictfetchall()
        exp_revenue_data_value = [item['sum'] for item in exp_revenue_data]
        exp_revenue_value = exp_revenue_data_value[0]
        if exp_revenue_value is None:
            exp_revenue_value = 0
        self._cr.execute('''select SUM(crm_lead.expected_revenue) from crm_lead 
        WHERE crm_lead.user_id = %s and type='opportunity' and active='true' 
        and stage_id=4 AND Extract(MONTH FROM crm_lead.date_closed) = 
        Extract(MONTH FROM DATE(NOW())) AND Extract(Year FROM 
        crm_lead.date_closed) = Extract(Year FROM DATE(NOW()))
        ''' % session_user_id)
        revenue_data = self._cr.dictfetchall()
        revenue_data_value = [item['sum'] for item in revenue_data]
        revenue_value = revenue_data_value[0]
        if revenue_value is None:
            revenue_value = 0
        ratio_value = []
        if revenue_value == 0:
            ratio_value = 0
        if revenue_value > 0:
            self._cr.execute('''select case when b.count_two = 0 then 0 else (
            CAST(a.count_one as float) / CAST(b.count_two as float))end as 
            final_count from (select COUNT(id) as count_one from crm_lead WHERE
            crm_lead.user_id = '%s' AND crm_lead.active = True AND 
            crm_lead.probability = 100 AND Extract(MONTH FROM 
            crm_lead.date_deadline) = Extract(MONTH FROM DATE(NOW()))
            AND Extract(Year FROM crm_lead.date_open) = Extract(Year 
            FROM DATE(NOW())))a,(select COUNT(id) as count_two from crm_lead 
            WHERE crm_lead.user_id = '%s' AND crm_lead.active = False AND 
            crm_lead.probability = 0 AND Extract(MONTH FROM 
            crm_lead.date_deadline) = Extract(MONTH FROM DATE(NOW())) AND 
            Extract(Year FROM crm_lead.date_deadline) = Extract(Year FROM 
            DATE(NOW())))b''' % (session_user_id, session_user_id))
            ratio_data_value = [row[0] for row in self._cr.fetchall()]
            ratio_value = str(ratio_data_value)[1:-1]
        self._cr.execute('''SELECT active,count(active) FROM crm_lead where 
        type='opportunity' and active = true and probability = 100 and 
        user_id=%s AND Extract(MONTH FROM date_closed) = Extract(MONTH FROM 
        DATE(NOW())) AND Extract(Year FROM date_closed) = Extract(
        Year FROM DATE(NOW())) or type='opportunity' and active = false and 
        probability = 0 and user_id=%s AND Extract(MONTH FROM date_deadline) = 
        Extract(MONTH FROM DATE(NOW())) AND Extract(Year FROM date_deadline) = 
        Extract(Year FROM DATE(NOW())) GROUP BY active
        ''' % (session_user_id, session_user_id))
        record_opportunity = dict(self._cr.fetchall())
        opportunity_ratio_value = 0.0
        if record_opportunity == {}:
            opportunity_ratio_value = 0.0
        else:
            total_opportunity_won = record_opportunity.get(False)
            total_opportunity_lost = record_opportunity.get(True)
            if total_opportunity_won is None:
                total_opportunity_won = 0
            if total_opportunity_lost is None:
                total_opportunity_lost = 0
                opportunity_ratio_value = 0.0
            if total_opportunity_lost > 0:
                opportunity_ratio_value = round(
                    total_opportunity_won / total_opportunity_lost, 2)
        avg = 0
        if crm_lead_value == 1:
            self._cr.execute('''SELECT id, date_conversion, create_date
            FROM crm_lead WHERE date_conversion IS NOT NULL;''')
            data = self._cr.dictfetchall()
            for rec in data:
                date_close = rec['date_conversion']
                date_create = rec['create_date']
                avg = (date_close - date_create).seconds
        if crm_lead_value > 1:
            self._cr.execute('''SELECT id, date_conversion, create_date
            FROM crm_lead WHERE date_conversion IS NOT NULL;''')
            data1 = self._cr.dictfetchall()
            for rec in data1:
                date_close = rec['date_conversion']
                date_create = rec['create_date']
                avg = (date_close - date_create).seconds
        avg_time = 0 if crm_lead_value == 0 else round(avg / crm_lead_value)
        data = {
            'record': crm_lead_value,
            'record_op': opportunity_value,
            'record_rev_exp': exp_revenue_value,
            'record_rev': revenue_value,
            'record_ratio': ratio_value,
            'opportunity_ratio_value': str(opportunity_ratio_value),
            'avg_time': avg_time,
            'count': value,
            'target': target_annual,
            'ytd_target': ytd_target,
            'difference': difference,
            'won': won,
        }
        return data

    @api.model
    def crm_year(self, kwargs):
        """Year CRM Dropdown Filter"""
        session_user_id = self.env.uid
        self._cr.execute('''select COUNT(id) from crm_lead WHERE 
        crm_lead.user_id = '%s' AND Extract(Year FROM crm_lead.date_deadline) = 
        Extract(Year FROM DATE(NOW()))''' % session_user_id)
        record = self._cr.dictfetchall()
        rec_ids = [item['count'] for item in record]
        crm_lead_value = rec_ids[0]
        self._cr.execute('''select COUNT(id) from crm_lead WHERE 
        crm_lead.user_id = %s AND crm_lead.type = 'opportunity' AND 
        Extract(Year FROM crm_lead.date_deadline
        ) = Extract(Year FROM DATE(NOW()))''' % session_user_id)
        opportunity_data = self._cr.dictfetchall()
        opportunity_data_value = [item['count'] for item in opportunity_data]
        opportunity_value = opportunity_data_value[0]
        self._cr.execute('''select SUM(crm_lead.expected_revenue) from crm_lead
        WHERE crm_lead.user_id = %s and type='opportunity' and active='true' AND
        Extract(Year FROM crm_lead.date_deadline) = Extract(Year FROM 
        DATE(NOW()))''' % session_user_id)
        exp_revenue_data = self._cr.dictfetchall()
        exp_revenue_data_value = [item['sum'] for item in exp_revenue_data]
        exp_revenue_value = exp_revenue_data_value[0]
        if exp_revenue_value is None:
            exp_revenue_value = 0
        self._cr.execute('''select SUM(crm_lead.expected_revenue) from crm_lead
        WHERE crm_lead.user_id = %s and type='opportunity' and active='true' and
        stage_id=4 AND Extract(Year FROM crm_lead.date_closed) = Extract(Year
        FROM DATE(NOW()))''' % session_user_id)
        revenue_data = self._cr.dictfetchall()
        revenue_data_value = [item['sum'] for item in revenue_data]
        revenue_value = revenue_data_value[0]
        if revenue_value is None:
            revenue_value = 0
        ratio_value = []
        if revenue_value == 0:
            ratio_value = 0
        if revenue_value > 0:
            self._cr.execute('''select case when b.count_two = 0 then 0 else (
            CAST(a.count_one as float) / CAST(b.count_two as float))end as 
            final_count from (select COUNT(id) as count_one from crm_lead 
            WHERE crm_lead.user_id = '%s' AND crm_lead.active = True AND 
            crm_lead.probability = 100 AND Extract(Year FROM
            crm_lead.date_deadline) = Extract(Year FROM DATE(NOW())))a,
            (select COUNT(id) as count_two from crm_lead WHERE crm_lead.user_id 
            = '%s' AND crm_lead.active = False AND crm_lead.probability 
            = 0 AND Extract(Year FROM
            crm_lead.date_deadline) = Extract(Year FROM DATE(NOW())))b
            ''' % (session_user_id, session_user_id))
            ratio_value = [row[0] for row in self._cr.fetchall()]
            ratio_value = str(ratio_value)[1:-1]
        self._cr.execute('''SELECT active,count(active) FROM crm_lead
        where type='opportunity' and active = true and probability = 100 and 
        user_id=%s AND Extract(Year FROM date_closed) = Extract(Year 
        FROM DATE(NOW())) or type='opportunity' and active = false and 
        probability = 0 and user_id=%s
        AND Extract(Year FROM date_deadline) = Extract(Year FROM DATE(NOW()))
        GROUP BY active''' % (session_user_id, session_user_id))
        record_opportunity = dict(self._cr.fetchall())
        opportunity_ratio_value = 0.0
        if record_opportunity == {}:
            opportunity_ratio_value = 0.0
        else:
            total_opportunity_won = record_opportunity.get(False)
            total_opportunity_lost = record_opportunity.get(True)
            if total_opportunity_won is None:
                total_opportunity_won = 0
            if total_opportunity_lost is None:
                total_opportunity_lost = 0
                opportunity_ratio_value = 0.0
            if total_opportunity_lost > 0:
                opportunity_ratio_value = round(
                    total_opportunity_won / total_opportunity_lost, 2)
        avg = 0
        if crm_lead_value == 1:
            self._cr.execute('''SELECT id, date_conversion, create_date
            FROM crm_lead WHERE date_conversion IS NOT NULL;''')
            data = self._cr.dictfetchall()
            for rec in data:
                date_close = rec['date_conversion']
                date_create = rec['create_date']
                avg = (date_close - date_create).seconds
        if crm_lead_value > 1:
            self._cr.execute('''SELECT id, date_conversion, create_date
            FROM crm_lead WHERE date_conversion IS NOT NULL;''')
            data1 = self._cr.dictfetchall()
            for rec in data1:
                date_close = rec['date_conversion']
                date_create = rec['create_date']
                avg = (date_close - date_create).seconds
        if crm_lead_value == 0:
            record_avg_time = 0
        else:
            record_avg_time = round(avg / crm_lead_value)
        data_year = {
            'record': crm_lead_value,
            'record_op': opportunity_value,
            'record_rev_exp': exp_revenue_value,
            'record_rev': revenue_value,
            'record_ratio': ratio_value,
            'opportunity_ratio_value': str(opportunity_ratio_value),
            'avg_time': record_avg_time,
        }
        return data_year

    @api.model
    def crm_quarter(self, kwargs):
        """Quarter CRM Dropdown Filter"""
        session_user_id = self.env.uid
        self._cr.execute('''select COUNT(id) from crm_lead WHERE 
        crm_lead.user_id = '%s' AND Extract(QUARTER FROM crm_lead.date_deadline)
         = Extract(QUARTER FROM DATE(NOW())) AND Extract(Year FROM 
         crm_lead.date_deadline) = Extract(Year FROM DATE(NOW()))
        ''' % session_user_id)
        record = self._cr.dictfetchall()
        rec_ids = [item['count'] for item in record]
        crm_lead_value = rec_ids[0]
        self._cr.execute('''select COUNT(id) from crm_lead  WHERE 
        crm_lead.user_id = %s AND crm_lead.type = 'opportunity' AND 
        Extract(QUARTER FROM crm_lead.date_deadline) = Extract(QUARTER FROM 
        DATE(NOW())) AND Extract(Year FROM crm_lead.date_deadline
        ) = Extract(Year FROM DATE(NOW( )))''' % session_user_id)
        opportunity_data = self._cr.dictfetchall()
        opportunity_data_value = [item['count'] for item in opportunity_data]
        opportunity_value = opportunity_data_value[0]
        self._cr.execute('''select SUM(crm_lead.expected_revenue) from crm_lead 
        WHERE crm_lead.user_id = %s and type='opportunity' and active='true' 
        AND Extract(QUARTER FROM crm_lead.date_deadline) = 
        Extract(QUARTER FROM DATE(NOW())) AND Extract(Year FROM 
        crm_lead.date_deadline) = Extract(Year FROM DATE(NOW()))'''
                         % session_user_id)
        exp_revenue_data = self._cr.dictfetchall()
        exp_revenue_data_value = [item['sum'] for item in exp_revenue_data]
        exp_revenue_value = exp_revenue_data_value[0]
        if exp_revenue_value is None:
            exp_revenue_value = 0
        self._cr.execute('''select SUM(crm_lead.expected_revenue) from crm_lead 
        WHERE crm_lead.user_id = %s and type='opportunity' and active='true' 
        and stage_id=4 AND Extract(QUARTER FROM crm_lead.date_closed) = 
        Extract(QUARTER FROM DATE(NOW())) AND Extract(Year FROM 
        crm_lead.date_closed) = Extract(Year FROM DATE(NOW()))'''
                         % session_user_id)
        revenue_data = self._cr.dictfetchall()
        revenue_data_value = [item['sum'] for item in revenue_data]
        revenue_value = revenue_data_value[0]
        if revenue_value is None:
            revenue_value = 0
        ratio_value = []
        if revenue_value == 0:
            ratio_value = 0
        if revenue_value > 0:
            self._cr.execute('''select case when b.count_two = 0 then 0 else (
            CAST(a.count_one as float) / CAST(b.count_two as float))end as 
            final_count from (select COUNT(id) as count_one from crm_lead 
            WHERE crm_lead.user_id = '%s' AND crm_lead.active = True AND 
            crm_lead.probability = 100 AND Extract(QUARTER FROM 
            crm_lead.date_deadline) = Extract(QUARTER FROM DATE(NOW())) 
            AND Extract(Year FROM crm_lead.date_open) = Extract(Year 
            FROM DATE(NOW())))a,(select COUNT(id) as count_two from crm_lead 
            WHERE crm_lead.user_id = '%s' AND crm_lead.active = False AND 
            crm_lead.probability = 0 AND Extract(QUARTER FROM 
            crm_lead.date_deadline) = Extract(QUARTER FROM DATE(NOW()))
            AND Extract(Year FROM crm_lead.date_deadline) = Extract(Year 
            FROM DATE(NOW())))b''' % (session_user_id, session_user_id))
            ratio_value = [row[0] for row in self._cr.fetchall()]
            ratio_value = str(ratio_value)[1:-1]
        self._cr.execute('''SELECT active,count(active) FROM crm_lead
        where type='opportunity' and active = true and probability = 100 and 
        user_id=%s AND Extract(QUARTER FROM date_closed) = 
        Extract(QUARTER FROM DATE(NOW())) AND Extract(Year FROM date_closed) 
        = Extract(Year FROM DATE(NOW())) or type='opportunity' and active = 
        false and probability = 0 and user_id=%s AND Extract(QUARTER FROM 
        date_deadline) = Extract(QUARTER FROM DATE(NOW()))
        AND Extract(Year FROM date_deadline) = Extract(Year FROM DATE(NOW()))
        GROUP BY active''' % (session_user_id, session_user_id))
        record_opportunity = dict(self._cr.fetchall())
        opportunity_ratio_value = 0.0
        if record_opportunity == {}:
            opportunity_ratio_value = 0.0
        else:
            total_opportunity_won = record_opportunity.get(False)
            total_opportunity_lost = record_opportunity.get(True)
            if total_opportunity_won is None:
                total_opportunity_won = 0
            if total_opportunity_lost is None:
                total_opportunity_lost = 0
                opportunity_ratio_value = 0.0
            if total_opportunity_lost > 0:
                opportunity_ratio_value = round(
                    total_opportunity_won / total_opportunity_lost, 2)
        avg = 0
        if crm_lead_value == 1:
            self._cr.execute('''SELECT id, date_conversion, create_date
            FROM crm_lead WHERE date_conversion IS NOT NULL;''')
            data = self._cr.dictfetchall()
            for rec in data:
                date_close = rec['date_conversion']
                date_create = rec['create_date']
                avg = (date_close - date_create).seconds
        if crm_lead_value > 1:
            self._cr.execute('''SELECT id, date_conversion, create_date
            FROM crm_lead WHERE date_conversion IS NOT NULL;''')
            data1 = self._cr.dictfetchall()
            for rec in data1:
                date_close = rec['date_conversion']
                date_create = rec['create_date']
                avg = (date_close - date_create).seconds
        if crm_lead_value == 0:
            record_avg_time = 0
        else:
            record_avg_time = round(avg / crm_lead_value)
        data_quarter = {
            'record': crm_lead_value,
            'record_op': opportunity_value,
            'record_rev_exp': exp_revenue_value,
            'record_rev': revenue_value,
            'record_ratio': ratio_value,
            'opportunity_ratio_value': str(opportunity_ratio_value),
            'avg_time': record_avg_time,
        }
        return data_quarter

    @api.model
    def crm_month(self, kwargs):
        """Month CRM Dropdown Filter"""
        session_user_id = self.env.uid

        self._cr.execute('''select COUNT(id) from crm_lead WHERE 
        crm_lead.user_id = '%s' AND Extract(MONTH FROM crm_lead.date_deadline) 
        = Extract(MONTH FROM DATE(NOW())) AND Extract(Year FROM 
        crm_lead.date_deadline) = Extract(Year FROM DATE(NOW()))'''
                         % session_user_id)
        record = self._cr.dictfetchall()
        rec_ids = [item['count'] for item in record]
        crm_lead_value = rec_ids[0]
        self._cr.execute('''select COUNT(id) from crm_lead WHERE 
        crm_lead.user_id = %s AND crm_lead.type = 'opportunity' AND 
        Extract(MONTH FROM crm_lead.date_deadline) = 
        Extract(MONTH FROM DATE(NOW())) AND Extract(Year FROM 
        crm_lead.date_deadline) = Extract(Year FROM DATE(NOW( )))'''
                         % session_user_id)
        opportunity_data = self._cr.dictfetchall()
        opportunity_data_value = [item['count'] for item in opportunity_data]
        opportunity_value = opportunity_data_value[0]
        self._cr.execute('''select SUM(crm_lead.expected_revenue) from crm_lead 
        WHERE crm_lead.user_id = %s and type='opportunity' and active='true' 
        AND Extract(MONTH FROM crm_lead.date_deadline) = 
        Extract(MONTH FROM DATE(NOW())) AND Extract(Year FROM 
        crm_lead.date_deadline) = Extract(Year FROM DATE(NOW()))''' %
                         session_user_id)
        exp_revenue_data = self._cr.dictfetchall()
        exp_revenue_data_value = [item['sum'] for item in exp_revenue_data]
        exp_revenue_value = exp_revenue_data_value[0]
        if exp_revenue_value is None:
            exp_revenue_value = 0
        self._cr.execute('''select SUM(crm_lead.expected_revenue) from 
        crm_lead WHERE crm_lead.user_id = %s and type='opportunity' and 
        active='true' and stage_id=4 AND Extract(MONTH FROM 
        crm_lead.date_closed) = Extract(MONTH FROM DATE(NOW()))
        AND Extract(Year FROM crm_lead.date_closed) = Extract(Year 
        FROM DATE(NOW()))''' % session_user_id)
        revenue_data = self._cr.dictfetchall()
        revenue_data_value = [item['sum'] for item in revenue_data]
        revenue_value = revenue_data_value[0]
        if revenue_value is None:
            revenue_value = 0
        ratio_value = []
        if revenue_value == 0:
            ratio_value = 0
        if revenue_value > 0:
            self._cr.execute('''select case when b.count_two = 0 then 0 else (
            CAST(a.count_one as float) / CAST(b.count_two as float))end as 
            final_count from (select COUNT(id) as count_one from crm_lead
            WHERE crm_lead.user_id = '%s' AND crm_lead.active = True AND
            crm_lead.probability = 100 AND Extract(MONTH FROM 
            crm_lead.date_deadline) = Extract(MONTH FROM DATE(NOW())) 
            AND Extract(Year FROM crm_lead.date_open) = 
            Extract(Year FROM DATE(NOW())))a,(select COUNT(id) as 
            count_two from crm_lead WHERE crm_lead.user_id = '%s'
            AND crm_lead.active = False AND crm_lead.probability = 0 
            AND Extract(MONTH FROM crm_lead.date_deadline) = 
            Extract(MONTH FROM DATE(NOW())) AND Extract(Year FROM 
            crm_lead.date_deadline) = Extract(Year FROM DATE(NOW())))b'''
                             % (session_user_id, session_user_id))
            ratio_value = [row[0] for row in self._cr.fetchall()]
            ratio_value = str(ratio_value)[1:-1]
        self._cr.execute('''SELECT active,count(active) FROM crm_lead
        where type='opportunity' and active = true and probability = 100 and 
        user_id=%s AND Extract(MONTH FROM date_closed) = 
        Extract(MONTH FROM DATE(NOW())) AND Extract(Year FROM date_closed) 
        = Extract(Year FROM DATE(NOW())) or type='opportunity' 
        and active = false and probability = 0 and user_id=%s
        AND Extract(MONTH FROM date_deadline) = Extract(MONTH FROM DATE(NOW()))
        AND Extract(Year FROM date_deadline) = Extract(Year FROM DATE(NOW()))
        GROUP BY active''' % (session_user_id, session_user_id))
        record_opportunity = dict(self._cr.fetchall())
        opportunity_ratio_value = 0.0
        if record_opportunity == {}:
            opportunity_ratio_value = 0.0
        else:
            total_opportunity_won = record_opportunity.get(False)
            total_opportunity_lost = record_opportunity.get(True)
            if total_opportunity_won is None:
                total_opportunity_won = 0
            if total_opportunity_lost is None:
                total_opportunity_lost = 0
                opportunity_ratio_value = 0.0
            if total_opportunity_lost > 0:
                opportunity_ratio_value = round(
                    total_opportunity_won / total_opportunity_lost, 2)
        avg = 0
        if crm_lead_value == 1:
            self._cr.execute('''SELECT id, date_conversion, create_date
            FROM crm_lead WHERE date_conversion IS NOT NULL;''')
            data = self._cr.dictfetchall()
            for rec in data:
                date_close = rec['date_conversion']
                date_create = rec['create_date']
                avg = (date_close - date_create).seconds
        if crm_lead_value > 1:
            self._cr.execute('''SELECT id, date_conversion, create_date
            FROM crm_lead WHERE date_conversion IS NOT NULL;''')
            data1 = self._cr.dictfetchall()
            for rec in data1:
                date_close = rec['date_conversion']
                date_create = rec['create_date']
                avg = (date_close - date_create).seconds
        record_avg_time = 0 if crm_lead_value == 0 else round(
            avg / crm_lead_value)
        data_month = {
            'record': crm_lead_value,
            'record_op': opportunity_value,
            'record_rev_exp': exp_revenue_value,
            'record_rev': revenue_value,
            'record_ratio': ratio_value,
            'opportunity_ratio_value': str(opportunity_ratio_value),
            'avg_time': record_avg_time,
        }
        return data_month

    @api.model
    def crm_week(self, kwargs):
        """Week CRM Dropdown Filter"""
        session_user_id = self.env.uid
        self._cr.execute('''select COUNT(id) from crm_lead WHERE 
        crm_lead.user_id = '%s' AND Extract(MONTH FROM 
        crm_lead.date_deadline) = Extract(MONTH FROM DATE(NOW()))
        AND Extract(Week FROM crm_lead.date_deadline) = 
        Extract(Week FROM DATE(NOW())) AND Extract(Year FROM 
        crm_lead.date_deadline) = Extract(Year FROM DATE(NOW()))'''
                         % session_user_id)
        record = self._cr.dictfetchall()
        rec_ids = [item['count'] for item in record]
        crm_lead_value = rec_ids[0]
        self._cr.execute('''select COUNT(id) from crm_lead WHERE 
        crm_lead.user_id = %s AND crm_lead.type = 'opportunity' AND 
        Extract(MONTH FROM crm_lead.date_deadline) = Extract(MONTH 
        FROM DATE(NOW())) AND Extract(Week FROM crm_lead.date_deadline
        ) = Extract(Week FROM DATE(NOW())) AND Extract(Year 
        FROM crm_lead.date_deadline) = Extract(Year FROM DATE(NOW()))'''
                         % session_user_id)
        opportunity_data = self._cr.dictfetchall()
        opportunity_data_value = [item['count'] for item in opportunity_data]
        opportunity_value = opportunity_data_value[0]
        self._cr.execute('''select SUM(crm_lead.expected_revenue) from crm_lead 
        WHERE crm_lead.user_id = %s and type='opportunity' 
        and active='true' AND Extract(MONTH FROM crm_lead.date_deadline) 
        = Extract(MONTH FROM DATE(NOW())) AND Extract(Week FROM 
        crm_lead.date_deadline) = Extract(Week FROM DATE(NOW())) AND 
        Extract(Year FROM crm_lead.date_deadline) = 
        Extract(Year FROM DATE(NOW()))''' % session_user_id)
        exp_revenue_data = self._cr.dictfetchall()
        exp_revenue_data_value = [item['sum'] for item in exp_revenue_data]
        exp_revenue_value = exp_revenue_data_value[0]
        if exp_revenue_value is None:
            exp_revenue_value = 0
        self._cr.execute('''select SUM(crm_lead.expected_revenue) from 
        crm_lead WHERE crm_lead.user_id = %s and type='opportunity' 
        and active='true' and stage_id=4 AND Extract(
        MONTH FROM crm_lead.date_closed) = Extract(MONTH FROM DATE(NOW()))
        AND Extract(Week FROM crm_lead.date_closed) = 
        Extract(Week FROM DATE(NOW())) AND Extract(Year 
        FROM crm_lead.date_closed) = Extract(Year FROM DATE(NOW()))'''
                         % session_user_id)
        revenue_data = self._cr.dictfetchall()
        revenue_data_value = [item['sum'] for item in revenue_data]
        revenue_value = revenue_data_value[0]
        if revenue_value is None:
            revenue_value = 0
        ratio_value = []
        if revenue_value == 0:
            ratio_value = 0
        if revenue_value > 0:
            self._cr.execute('''select case when b.count_two = 0 then 0 else (
            CAST(a.count_one as float) / CAST(b.count_two as float))end as 
            final_count from (select COUNT(id) as count_one from crm_lead
            WHERE crm_lead.user_id = '%s' AND crm_lead.active = True AND
            crm_lead.probability = 100 AND 
            Extract(MONTH FROM crm_lead.date_deadline) = 
            Extract(MONTH FROM DATE(NOW())) AND 
            Extract(Week FROM crm_lead.date_deadline) = 
            Extract(Week FROM DATE(NOW())) AND 
            Extract(Year FROM crm_lead.date_open
            ) = Extract(Year FROM DATE(NOW())))a,
            (select COUNT(id) as count_two from crm_lead WHERE 
            crm_lead.user_id = '%s' AND crm_lead.active = False AND 
            crm_lead.probability = 0 AND Extract(MONTH 
            FROM crm_lead.date_deadline) = Extract(MONTH FROM DATE(NOW())) 
            AND Extract(Week FROM crm_lead.date_deadline) = 
            Extract(Week FROM DATE(NOW())) AND Extract(Year FROM
            crm_lead.date_deadline) = Extract(Year FROM DATE(NOW())))b
            ''' % (session_user_id, session_user_id))
            ratio_value = [row[0] for row in self._cr.fetchall()]
            ratio_value = str(ratio_value)[1:-1]
        self._cr.execute('''SELECT active,count(active) FROM crm_lead
        where type='opportunity' and active = true and probability = 100 and
        user_id=%s AND Extract(MONTH FROM crm_lead.date_closed) = 
        Extract(MONTH FROM DATE(NOW())) AND Extract(Week FROM 
        crm_lead.date_closed) = Extract(Week FROM DATE(NOW())) AND 
        Extract(Year FROM crm_lead.date_closed) = Extract(Year FROM DATE(NOW()))
        or type='opportunity' and active = false and probability = 0 
        and user_id=%s AND Extract(MONTH FROM crm_lead.date_deadline) 
        = Extract(MONTH FROM DATE(NOW())) AND 
        Extract(Week FROM crm_lead.date_deadline) 
        = Extract(Week FROM DATE(NOW())) AND 
        Extract(Year FROM crm_lead.date_deadline) 
        = Extract(Year FROM DATE(NOW()))GROUP BY active'''
                         % (session_user_id, session_user_id))
        record_opportunity = dict(self._cr.fetchall())
        opportunity_ratio_value = 0.0
        if record_opportunity == {}:
            opportunity_ratio_value = 0.0
        else:
            total_opportunity_won = record_opportunity.get(False)
            total_opportunity_lost = record_opportunity.get(True)
            if total_opportunity_won is None:
                total_opportunity_won = 0
            if total_opportunity_lost is None:
                total_opportunity_lost = 0
                opportunity_ratio_value = 0.0
            if total_opportunity_lost > 0:
                opportunity_ratio_value = round(
                    total_opportunity_won / total_opportunity_lost, 2)
        avg = 0
        if crm_lead_value == 1:
            self._cr.execute('''SELECT id, date_conversion, create_date
            FROM crm_lead WHERE date_conversion IS NOT NULL;''')
            data = self._cr.dictfetchall()
            for rec in data:
                date_close = rec['date_conversion']
                date_create = rec['create_date']
                avg = (date_close - date_create).seconds
        if crm_lead_value > 1:
            self._cr.execute('''SELECT id, date_conversion, create_date
            FROM crm_lead WHERE date_conversion IS NOT NULL;''')
            data1 = self._cr.dictfetchall()
            for rec in data1:
                date_close = rec['date_conversion']
                date_create = rec['create_date']
                avg = (date_close - date_create).seconds
        if crm_lead_value == 0:
            record_avg_time = 0
        else:
            record_avg_time = round(avg / crm_lead_value)
        data_week = {
            'record': crm_lead_value,
            'record_op': opportunity_value,
            'record_rev_exp': exp_revenue_value,
            'record_rev': revenue_value,
            'record_ratio': ratio_value,
            'opportunity_ratio_value': str(opportunity_ratio_value),
            'avg_time': record_avg_time,
        }
        return data_week
