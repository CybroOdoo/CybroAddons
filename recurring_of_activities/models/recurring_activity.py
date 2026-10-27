###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
"""Recurring activity model definitions and scheduling logic."""

import logging
from datetime import date, timedelta

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.exceptions import MissingError, ValidationError

_logger = logging.getLogger(__name__)


class RecurringActivity(models.Model):
    """It handles the activity scheduled in recurring mode."""
    _name = 'recurring.activity'
    _description = 'Recurring Activity'

    name = fields.Char(help='Name of the recurring activity.', required=True)
    activity_type_id = fields.Many2one('mail.activity.type',
                                       string='Activity',
                                       help='Select the activity type to schedule.',
                                       required=True)
    user_id = fields.Many2one('res.users', string='Assigned to',
                              help='The user responsible for this activity.')
    summary = fields.Char(help='Short summary or purpose of the activity.', required=True)
    note = fields.Text(help='Additional notes or instructions for the activity.')
    period = fields.Selection([('day', 'Days'), ('week', 'Weeks'),
                               ('month', 'Months'), ('year', 'Years')],
                              string='Repeat Every',
                              help='Recurrence frequency for the activity.',
                              default="day", required=True)
    start_date = fields.Date(help='Start date of the recurring activity schedule.',
                             default=fields.Date.today)
    next_activity_date = fields.Date(help='Date of the next scheduled activity.',
                                     copy=False)
    archive_date = fields.Date(string='Recurring Deadline',
                               help='The date after which this rule will be'
                                    ' archived and no more recurring activities'
                                    ' will be created.', required=True)
    active = fields.Boolean(default=True,
                            help='By unchecking the active field, you may hide'
                                 ' this record without removing it.')
    monday = fields.Boolean(help='Repeat the activity every Monday.')
    tue = fields.Boolean(string='Tuesday',
                         help='Repeat the activity every Tuesday.')
    wed = fields.Boolean(string='Wednesday',
                         help='Repeat the activity every Wednesday.')
    thu = fields.Boolean(string='Thursday',
                         help='Repeat the activity every Thursday.')
    fri = fields.Boolean(string='Friday',
                         help='Repeat the activity every Friday.')
    sat = fields.Boolean(string='Saturday',
                         help='Repeat the activity every Saturday.')
    sun = fields.Boolean(string='Sunday',
                         help='Repeat the activity every Sunday.')
    action = fields.Reference(selection=[('sale.order', 'Sale Orders'),
                                         ('purchase.order', 'Purchase Orders'),
                                         ('res.partner', 'Contact'),
                                         ('account.journal', 'Journal'),
                                         ('hr.employee', 'Employees'),
                                         ('crm.lead', 'Lead/Opportunity'),
                                         ('product.template', 'Product'),
                                         ('product.product', 'Product Variant'),
                                         ('project.task', 'Task'),
                                         ],
                              help='Choose the target document for the recurring activity.')
    year_date = fields.Integer(string='Date',
                               help='Day of the month for yearly recurrence (1-31).')
    year_months = fields.Selection([('1', 'January'), ('2', 'February'),
                                    ('3', 'March'), ('4', 'April'),
                                    ('5', 'May'),
                                    ('6', 'June'), ('7', 'July'),
                                    ('8', 'August'), ('9', 'September'),
                                    ('10', 'October'), ('11', 'November'),
                                    ('12', 'December')], string='Month',
                                   help='Month of the year for yearly recurrence.')
    month_by = fields.Selection([('first', 'The First Day'),
                                 ('last', 'The Last Day'),
                                 ('date', 'Date of Month'),
                                 ],
                                string='Day of Month',
                                help='Choose whether recurrence is on the first'
                                     ' day, last day, or a specific date of the'
                                     ' month.',
                                default='date')
    date_of_month = fields.Integer(string='Date of Month',
                                   help='Day of the month for monthly recurrence (1-31).',
                                   default=1)

    def _get_weekdays(self):
        """Get a list of selected weekdays based on user input."""
        self.ensure_one()
        weekdays = []
        if self.monday:
            weekdays.append('Mon')
        if self.tue:
            weekdays.append('Tue')
        if self.wed:
            weekdays.append('Wed')
        if self.thu:
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
        self.ensure_one()
        next_dates = []
        # Calculate the next date based on the selected options
        current_date = date.today()
        if current_date < self.archive_date:
            if self.period == 'day':
                next_dates.append(current_date)
            elif self.period == 'week':
                weekdays = self._get_weekdays()
                if not weekdays:
                    raise ValidationError(self.env._('Please choose a specific day for '
                                                     'the recurring activity.'))
                while current_date <= self.archive_date:
                    if current_date.strftime('%a') in weekdays:
                        next_dates.append(current_date)
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
                    if self.date_of_month < 1 or self.date_of_month > 31:
                        raise ValidationError(self.env._(
                            "Invalid date of the month specified.",
                        ))
                    if self.date_of_month >= current_date.day:
                        selected_date = current_date + relativedelta(day=self.date_of_month)
                    else:
                        selected_date = current_date + relativedelta(
                            months=1, day=self.date_of_month,
                        )
                    next_dates.append(selected_date)
                else:
                    raise ValidationError(self.env._(
                        'Please select a recurring activity type for the month.',
                    ))
            elif self.period == 'year':
                if not self.year_date or not self.year_months:
                    raise ValidationError(self.env._(
                        "Both Date and month are required for yearly recurrence.",
                    ))
                if self.year_date < 1 or self.year_date > 31:
                    raise ValidationError(self.env._(
                        "Invalid date of the month specified.",
                    ))
                month_integer = int(self.year_months)
                target_date = current_date + relativedelta(
                    month=month_integer,
                    day=self.year_date,
                )
                if target_date < current_date:
                    target_date = target_date + relativedelta(years=1)
                next_dates.append(target_date)
        else:
            next_dates.append(self.archive_date)
        if next_dates:
            self.next_activity_date = next_dates[0]
        return next_dates

    def create_recurring_activities(self):
        """Create recurring activities based on calculated dates."""
        today = fields.Date.today()
        expired_records = self.search([
            ('archive_date', '<', today),
            ('active', '=', True),
        ])
        if expired_records:
            expired_records.write({'active': False})
        records = self.search([('archive_date', '>=', today)])
        return records.create_recurring_activities_record()

    def create_recurring_activities_record(self):
        """Create recurring activities based on calculated dates."""
        activities_vals = []
        for rec in self:
            try:
                action = rec.action
                if not action or not action.exists():
                    continue
                next_dates = rec._get_next_recurring_dates()
                if not next_dates:
                    continue
                deadline = next_dates[0]
                existing = self.env['mail.activity'].search([
                    ('res_model', '=', action._name),
                    ('res_id', '=', action.id),
                    ('activity_type_id', '=', rec.activity_type_id.id),
                    ('summary', '=', rec.summary),
                    ('date_deadline', '=', deadline),
                ], limit=1)
                if existing:
                    continue
                activities_vals.append({
                    'activity_type_id': rec.activity_type_id.id,
                    'user_id': rec.user_id.id,
                    'date_deadline': deadline,
                    'note': rec.note,
                    'summary': rec.summary,
                    'res_model_id': rec.env['ir.model']._get_id(action._name),
                    'res_id': action.id,
                })
            except (KeyError, ValueError, MissingError):
                continue
        if activities_vals:
            try:
                return self.env['mail.activity'].create(activities_vals)
            except MissingError:
                created_activities = self.env['mail.activity']
                for vals in activities_vals:
                    try:
                        created_activities |= self.env['mail.activity'].create(vals)
                    except MissingError:
                        continue
                return created_activities
        return self.env['mail.activity']

    @api.model_create_multi
    def create(self, vals_list):
        """
        Create and schedule recurring activities when new records are created.

        :param vals_list: List of field values for the new records.
        :return: Created recordset.
        """
        for vals in vals_list:
            if not vals.get('action'):
                raise ValidationError(self.env._("Please choose the record for the "
                                                 "recurring activity."))
            action_val = vals.get('action')
            if isinstance(action_val, str) and ',' in action_val:
                model_name = action_val.split(',')[0]
                if model_name not in self.env:
                    raise ValidationError(self.env._(
                        "The module is not installed, "
                        "so we can't configure any records for this.",
                    ))
            elif hasattr(action_val, '_name'):
                if action_val._name not in self.env:
                    raise ValidationError(self.env._(
                        "The module is not installed, "
                        "so we can't configure any records for this.",
                    ))
        res = super().create(vals_list)
        res.create_recurring_activities_record()
        return res

    @api.model
    def check_model_installed(self, model_name):
        """Check if the given model is installed and accessible in the registry."""
        return model_name in self.env

    @api.constrains('action')
    def _check_action_model_installed(self):
        """Validate that the referenced model is installed in the system."""
        for record in self:
            try:
                action = record.action
                if action and action._name not in self.env:
                    raise ValidationError(self.env._(
                        "The module is not installed, "
                        "so we can't configure any records for this.",
                    ))
            except (KeyError, MissingError) as e:
                _logger.warning("Error checking action model: %s", e)

    @api.constrains('start_date', 'archive_date')
    def _check_archive_date(self):
        """This method is used to check whether the 'archive_date' is greater
        than or equal to the 'start_date' for each record. If 'archive_date'
        is less than 'start_date', it raises a validation error with the
        message "The deadline should be greater than the created date." """
        for record in self:
            if (
                record.archive_date
                and record.start_date
                and record.archive_date < record.start_date
            ):
                raise ValidationError(self.env._(
                    "The deadline should be greater than the created date",
                ))
