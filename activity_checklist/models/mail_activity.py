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
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models


class MailActivity(models.Model):
    """Creates the model mail.activity"""
    _inherit = 'mail.activity'
    _rec_name = 'summary'

    def _default_res_id(self):
        general_activity = self.env.ref(
            'activity_checklist.general_activities',
            raise_if_not_found=False
        )
        return general_activity.id if general_activity else False

    date_deadline = fields.Date(string='Due Date', index=True, required=True,
                                default=fields.Date.context_today,
                                help="Deadline date")
    user_id = fields.Many2one('res.users', string='User', index=True,
                              default=lambda self: self.env.user,
                              help="User of the activity")
    res_model_id = fields.Many2one(
        'ir.model', string='Document Model',
        index=True, ondelete='cascade', required=True,
        help="Corresponding model")
    res_id = fields.Many2oneReference(string='Related Document ID', index=True,
                                      required=True, model_field='res_model',
                                      help="ID of the related document",
                                      default=_default_res_id)
    priority = fields.Selection([
        ('0', 'Normal'),
        ('1', 'Important'),
        ('2', 'Very Important'),
        ('3', 'Urgent'),
    ], default='0', index=True, store=True, string="Priority",
        help="Priority of the activity")
    recurring = fields.Boolean(string="Recurring",
                               help="Whether the activity is recurring or not")
    interval = fields.Selection(
        [('Daily', 'Daily'),
         ('Weekly', 'Weekly'),
         ('Monthly', 'Monthly'),
         ('Quarterly', 'Quarterly'),
         ('Yearly', 'Yearly')],
        string='Recurring Interval', help="Recurring interval of the activity")
    new_date = fields.Date(string="Next Due Date",
                           help="Next due date of the activity")

    @api.model
    def default_get(self, fields_list):
        """Set the default model to Activity General."""
        res = super().default_get(fields_list)
        if 'res_model_id' in fields_list and not res.get('res_model_id'):
            model = self.env['ir.model'].search(
                [('model', '=', 'activity.general')],
                limit=1
            )
            if model:
                res['res_model_id'] = model.id
        if 'res_id' in fields_list and not res.get('res_id'):
            general_activity = self.env.ref(
                'activity_checklist.general_activities',
                raise_if_not_found=False
            )
            if general_activity:
                res['res_id'] = general_activity.id
        return res

    def action_done(self):
        """Mark activity as done and update chatter activity"""
        for rec in self:
            if rec.recurring:
                next_deadline = (rec.new_date or rec.get_date() or
                                 rec.date_deadline or fields.Date.today())
                new_next_date = False
                if rec.interval:
                    date_for_interval = fields.Date.to_date(next_deadline)
                    if rec.interval == 'Daily':
                        new_next_date = date_for_interval + relativedelta(days=1)
                    elif rec.interval == 'Weekly':
                        new_next_date = date_for_interval + relativedelta(weeks=1)
                    elif rec.interval == 'Monthly':
                        new_next_date = date_for_interval + relativedelta(months=1)
                    elif rec.interval == 'Quarterly':
                        new_next_date = date_for_interval + relativedelta(months=3)
                    elif rec.interval == 'Yearly':
                        new_next_date = date_for_interval + relativedelta(years=1)
                self.env['mail.activity'].create({
                    'res_id': rec.res_id,
                    'res_model_id': rec.res_model_id.id,
                    'summary': rec.summary,
                    'priority': rec.priority,
                    'date_deadline': next_deadline,
                    'recurring': rec.recurring,
                    'interval': rec.interval,
                    'activity_type_id': rec.activity_type_id.id,
                    'new_date': new_next_date,
                    'user_id': rec.user_id.id,
                })
            rec.action_feedback()

    def get_date(self):
        """ function for get new due date on new record"""
        date_deadline = self.new_date if self.new_date else self.date_deadline
        if not date_deadline or not self.interval:
            return False
        date_deadline = fields.Date.to_date(date_deadline)
        if self.interval == 'Daily':
            return date_deadline + relativedelta(days=1)
        elif self.interval == 'Weekly':
            return date_deadline + relativedelta(weeks=1)
        elif self.interval == 'Monthly':
            return date_deadline + relativedelta(months=1)
        elif self.interval == 'Quarterly':
            return date_deadline + relativedelta(months=3)
        elif self.interval == 'Yearly':
            return date_deadline + relativedelta(years=1)
        return False

    @api.onchange('interval', 'date_deadline', 'recurring')
    def _onchange_new_date(self):
        """ function for show new due date"""
        self.new_date = False
        if self.recurring:
            self.new_date = self.get_date()

    def action_date(self):
        """ Function for automated actions for deadline"""
        today = fields.Date.today()
        dates = self.env['mail.activity'].search([
            ('date_deadline', '<=', today),
            ('recurring', '=', True),
        ])
        for rec in dates:
            next_deadline = (rec.new_date or rec.get_date() or
                             rec.date_deadline or today)
            new_next_date = False
            if rec.interval:
                date_for_interval = fields.Date.to_date(next_deadline)
                if rec.interval == 'Daily':
                    new_next_date = date_for_interval + relativedelta(days=1)
                elif rec.interval == 'Weekly':
                    new_next_date = date_for_interval + relativedelta(weeks=1)
                elif rec.interval == 'Monthly':
                    new_next_date = date_for_interval + relativedelta(months=1)
                elif rec.interval == 'Quarterly':
                    new_next_date = date_for_interval + relativedelta(months=3)
                elif rec.interval == 'Yearly':
                    new_next_date = date_for_interval + relativedelta(years=1)
            self.env['mail.activity'].create({
                'res_id': rec.res_id,
                'res_model_id': rec.res_model_id.id,
                'summary': rec.summary,
                'priority': rec.priority,
                'interval': rec.interval,
                'recurring': rec.recurring,
                'date_deadline': next_deadline,
                'new_date': new_next_date,
                'activity_type_id': rec.activity_type_id.id,
                'user_id': rec.user_id.id,
            })
            rec.action_feedback()

    def action_cancel(self):
        """Cancel activity and remove it from related document chatter"""
        for rec in self:
            rec.unlink()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Activities',
            'res_model': 'mail.activity',
            'view_mode': 'kanban,list,form',
            'target': 'current',
        }

    def action_open_origin(self):
        """Open the related document of the activity"""
        self.ensure_one()
        if self.res_model and self.res_id:
            return {
                'type': 'ir.actions.act_window',
                'res_model': self.res_model,
                'res_id': self.res_id,
                'view_mode': 'form',
                'target': 'current',
            }


class ActivityGeneral(models.Model):
    """Creates the model activity.general"""
    _name = 'activity.general'
    _description = 'Activity General'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name', help="Name of the activity")
