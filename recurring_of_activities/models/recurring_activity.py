# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Fathima Mazlin AM (odoo@cybrosys.com)
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
###############################################################################
from datetime import timedelta, date
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class RecurringActivity(models.Model):
    """It handles the activity scheduled in recurring mode."""
    _name = 'recurring.activity'
    _description = 'Recurring Activity'

    name = fields.Char(string='Name', help='Enter the name of the recurring '
                       'activity', required=True)
    activity_type_id = fields.Many2one(
        'mail.activity.type', string='Activity', help='Which activity you '
        'want to schedule the recurring', required=True)
    user_id = fields.Many2one('res.users', string='Assigned to',
                              help='Who are the responsible person to assign'
                                   ' the activity')
    summary = fields.Char(string='Summary', help='Discussion proposal',
                          required=True)
    note = fields.Text(string='Note', help='Any kind of notes if you want to '
                                           'share with the activity')
    period = fields.Selection([('day', 'Days'), ('week', 'Weeks'),
                               ('month', 'Months'), ('year', 'Years')],
                              string='Repeat Every',
                              help='Number of period to be recurring the '
                                   'activity',
                              default="day", required=True)
    create_date = fields.Date(string='Activity Create Date',
                              help='Create date of the activity',
                              default=fields.Date.today)
    next_activity_date = fields.Date(string='Next Activity Date',
                                     help='Remaining the next activity day',
                                     copy=False)
    archive_date = fields.Date(string='Recurring Deadline',
                               help='The date after which this rule will be'
                                    ' archived and no more recurrent activity '
                                    'will be created', required=True)
    monday = fields.Boolean(string='Monday',
                            help='You will choose this day it'
                                 ' repeat every monday in a week ')
    tues = fields.Boolean(string='Tuesday',
                          help='You will choose this day it'
                               ' repeat every Tuesday in a week ')
    wed = fields.Boolean(string='Wednesday',
                         help='You will choose this day it'
                              ' repeat every Wednesday in a week ')
    thus = fields.Boolean(string='Thursday',
                          help='You will choose this day it'
                               ' repeat every Thursday in a week ')
    fri = fields.Boolean(string='Friday',
                         help='You will choose this day it'
                              ' repeat every Friday in a week ')
    sat = fields.Boolean(string='Saturday',
                         help='You will choose this day it'
                              ' repeat every Saturday in a week ')
    sun = fields.Boolean(string='Sunday',
                         help='You will choose this day it'
                              ' repeat every Sunday in a week ')
    action = fields.Reference(selection=[('sale.order', 'Sale Orders'),
                                         ('purchase.order', 'Purchase Orders'),
                                         ('res.partner', 'Contact'),
                                         ('account.journal', 'Journal'),
                                         ('res.partner', 'Employees'),
                                         ('crm.lead', 'Lead/Opportunity'),
                                         ('product.template', 'Product'),
                                         ('product.product', 'Product Variant'),
                                         ('project.task', 'Task'),
                                         ],
                              string='Action',
                              help='Choose the reference document you want to '
                                   'set a recurring activity.')
    year_date = fields.Integer(string='Date',
                               help='Periodicity of the recurring activity '
                                    'in year')
    year_months = fields.Selection([('1', 'January'), ('2', 'February'),
                                    ('3', 'March'), ('4', 'April'),
                                    ('5', 'May'),
                                    ('6', 'June'), ('7', 'July'),
                                    ('8', 'August'), ('9', 'September'),
                                    ('10', 'October'), ('11', 'November'),
                                    ('12', 'December')], string='Month',
                                   help='You can choose e month.It repeat every'
                                        ' the chose month')
    month_by = fields.Selection([('first', 'The First Day'),
                                 ('last', 'The Last Day'),
                                 ('date', 'Date of Month'),
                                 ],
                                string='Day of Month',
                                help='Choose the month base recurring activity',
                                defualt='date')
    date_of_month = fields.Integer(string='Date of Month',
                                   help='Repeat the activity every date of the'
                                        ' chose month', default=1)

    def _get_weekdays(self):
        """Get a list of selected weekdays based on user input."""
        weekdays = []
        if self.monday:
            weekdays.append('Mon')
        if self.tues:
            weekdays.append('Tue')
        if self.wed:
            weekdays.append('Wed')
        if self.thus:
            weekdays.append('Thu')
        if self.fri:
            weekdays.append('Fri')
        if self.sat:
            weekdays.append('Sat')
        if self.sun:
            weekdays.append('Sun')
        return weekdays

    def _get_next_recurring_dates(self):
        """Calculate the next recurring activity dates based on defined
        rules."""
        next_dates = []
        # Calculate the next date based on the selected options
        current_date = date.today()
        if current_date < self.archive_date:
            if self.period == 'day':
                next_dates.append(current_date)
            elif self.period == 'week':
                weekdays = self._get_weekdays()
                if not weekdays:
                    raise ValidationError('Please choose a specific day for '
                                          'the recurring activity.')
                while current_date <= self.archive_date:
                    if current_date.strftime('%a') in weekdays:
                        next_dates.append(current_date.strftime("%Y-%m-%d"))
                    current_date += timedelta(days=1)
            elif self.period == 'month':
                if self.month_by == 'first':
                    next_month_date = (current_date + relativedelta(months=1)
                                       ).replace(day=1)
                    next_dates.append(next_month_date)
                elif self.month_by == 'last':
                    # Calculate the last day of the current month
                    last_day_date_current_month = current_date.replace(
                        day=1) + relativedelta(months=1, days=-1)
                    # If the current date is before the last day, its start the
                    # current month
                    if current_date <= last_day_date_current_month:
                        next_dates.append(last_day_date_current_month)
                    else:
                        # Otherwise, set recurrence start last day of the
                        # next month
                        next_month_date = (current_date + relativedelta(
                            day=31)).replace(day=1)
                        last_day_date_next_month = (next_month_date +
                                                    relativedelta(
                                                        months=1, days=-1))
                        next_dates.append(last_day_date_next_month)
                elif self.month_by == 'date':
                    try:
                        next_month_date = (current_date + relativedelta())
                        selected_date = next_month_date.replace(
                            day=self.date_of_month)
                        next_dates.append(selected_date)
                    except Exception as e:
                        raise ValidationError(f"Error: {e}. Invalid date of"
                                              f" the month specified.")
                else:
                    raise ValidationError('Please select a recurring activity '
                                          'type for the month.')
            elif self.period == 'year':
                if not self.year_date or not self.year_months:
                    raise ValidationError("Both Date and month are "
                                          "required for yearly recurrence.")
                month_integer = int(self.year_months)
                # Get the current month
                current_month = self.create_date.month
                # Calculate the next date for yearly recurrence
                if current_month <= month_integer:
                    # If the current month is on or before the specified month,
                    # set the next_year_date in the same year
                    next_year_date = self.create_date.replace(
                        month=month_integer)
                else:
                    # If the current month is after the specified month,
                    # set the next_year_date in the next year
                    next_year_date = self.create_date.replace(
                        month=month_integer, year=self.create_date.year + 1)
                next_month_date = next_year_date.replace(day=self.year_date)
                next_dates.append(next_month_date)
        else:
            next_dates.append(self.archive_date)
        if next_dates:
            self.next_activity_date = next_dates[
                0]  # Set the next activity date
        return next_dates

    def create_recurring_activities(self):
        """Create recurring activities based on calculated dates."""
        records = self.env['recurring.activity'].search([])
        for rec in records:
            next_dates = rec._get_next_recurring_dates()
            # Create recurring activities for each next date
            self.env['mail.activity'].create({
                'activity_type_id': rec.activity_type_id.id,
                'user_id': rec.user_id.id,
                'date_deadline': next_dates[0],
                'note': rec.note,
                'summary': rec.summary,
                'res_model_id': rec.env['ir.model']._get_id(rec.action._name),
                'res_id': rec.action.id,
            })

    def create_recurring_activities_record(self):
        """Create recurring activities based on calculated dates."""
        next_dates = self._get_next_recurring_dates()
        # Create recurring activities for each next date
        self.env['mail.activity'].create({
            'activity_type_id': self.activity_type_id.id,
            'user_id': self.user_id.id,
            'date_deadline': next_dates[0],
            'note': self.note,
            'summary': self.summary,
            'res_model_id': self.env['ir.model']._get_id(self.action._name),
            'res_id': self.action.id,
        })

    @api.model
    def create(self, vals_list):
        """
        Create and schedule recurring activities when a new record is created.
        :param vals_list: List of field values for the new record.
        :return: Created record.
        """
        res = super().create(vals_list)
        if not vals_list['action']:
            raise ValidationError("Please choose the record for the recurring activity.")
        res.create_recurring_activities_record()
        return res

    @api.constrains('create_date', 'archive_date')
    def _compute_archive_date(self):
        """This method is used to check whether the 'archive_date' is greater
        than or equal to the 'create_date' for each record. If 'archive_date'
        is less than 'create_date', it raises a validation error with the
        message "The dealing should be greater than the created date." """
        for record in self:
            if record.archive_date < record.create_date:
                raise ValidationError("The dealing should be grater than the created date")
