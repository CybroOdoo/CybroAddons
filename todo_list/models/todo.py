# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2021-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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

from datetime import timedelta

from odoo import models, fields, api
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class MailActivity(models.Model):
    _name = 'mail.activity'
    _inherit = ['mail.activity', 'mail.thread']
    _rec_name = 'summary'

    date_deadline = fields.Date('Due Date', index=True, required=True,
                                default=fields.Date.context_today, store=True)
    user_id = fields.Many2one('res.users', string='user', index=True,
                              tracking=True, default=lambda self: self.env.user)
    res_model_id = fields.Many2one(
        'ir.model', 'Document Model',
        index=True, ondelete='cascade', required=True,
        default=lambda self: self.env.ref('todo_list.model_activity_general'))
    res_id = fields.Many2oneReference(string='Related Document ID', index=True,
                                      required=True, model_field='res_model',
                                      default=lambda self: self.env.ref(
                                          'todo_list.general_activities'))
    priority = fields.Selection([
        ('0', 'Normal'),
        ('1', 'Important'),
        ('2', 'Very Important'),
        ('3', 'Urgent'),
    ], default='0', index=True, store=True)
    recurring = fields.Boolean(string="Recurring", store=True)
    state = fields.Selection([
        ('today', 'Today'),
        ('planned', 'Planned'),
        ('done', 'Done'),
        ('overdue', 'Expired'),
        ('cancel', 'Cancelled'), ], 'State',
        compute='_compute_state', store=True)
    interval = fields.Selection(
        [('Daily', 'Daily'),
         ('Weekly', 'Weekly'),
         ('Monthly', 'Monthly'),
         ('Quarterly', 'Quarterly'),
         ('Yearly', 'Yearly')],
        string='Recurring Interval', )
    new_date = fields.Date(string="Next Due Date", store=True)

    def action_done(self):
        """Function done button"""
        self.write({'state': 'done'})
        if self.recurring:
            self.env['mail.activity'].create({
                'res_id': self.res_id,
                'res_model_id': self.res_model_id.id,
                'summary': self.summary,
                'priority': self.priority,
                'date_deadline': self.new_date,
                'recurring': self.recurring,
                'interval': self.interval,
                'activity_type_id': self.activity_type_id.id,
                'new_date': self.get_date(),
                'user_id': self.user_id.id
            })

    def get_date(self):
        """ function for get new due date on new record"""
        date_deadline = self.new_date if self.new_date else self.date_deadline
        new_date = False
        if self.interval == 'Daily':
            new_date = (
                    date_deadline + timedelta(days=1)).strftime(
                DEFAULT_SERVER_DATE_FORMAT)
        elif self.interval == 'Weekly':
            new_date = (
                    date_deadline + timedelta(days=7)).strftime(
                DEFAULT_SERVER_DATE_FORMAT)
        elif self.interval == 'Monthly':
            new_date = (
                    date_deadline + timedelta(days=30)).strftime(
                DEFAULT_SERVER_DATE_FORMAT)
        elif self.interval == 'Quarterly':
            new_date = (
                    date_deadline + timedelta(days=90)).strftime(
                DEFAULT_SERVER_DATE_FORMAT)
        elif self.interval == 'Yearly':
            new_date = (
                    date_deadline + timedelta(days=365)).strftime(
                DEFAULT_SERVER_DATE_FORMAT)
        return new_date

    @api.onchange('interval', 'date_deadline')
    def onchange_recurring(self):
        """ function for show new due date"""
        self.new_date = False
        if self.recurring:
            self.new_date = self.get_date()

    def action_date(self):
        """ Function for automated actions for deadline"""
        today = fields.date.today()
        dates = self.env['mail.activity'].search(
            [('state', 'in', ['today', 'planned']),
             ('date_deadline', '=', today),
             ('recurring', '=', True)])
        for rec in dates:
            self.env['mail.activity'].create(
                {'res_id': rec.res_id,
                 'res_model_id': rec.res_model_id.id,
                 'summary': rec.summary,
                 'priority': rec.priority,
                 'interval': rec.interval,
                 'recurring': rec.recurring,
                 'date_deadline': rec.new_date,
                 'new_date': rec.get_date(),
                 'activity_type_id': rec.activity_type_id.id,
                 'user_id': rec.user_id.id
                 })
            rec.state = 'done'

    def action_cancel(self):
        """ function for cancel button"""
        return self.write({'state': 'cancel'})


class ActivityGeneral(models.Model):
    _name = 'activity.general'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Name')
