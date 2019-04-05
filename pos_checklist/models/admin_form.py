# -*- coding: utf-8 -*-
from odoo import models, fields, api
import datetime
from datetime import datetime


class ToDoList(models.Model):

    _name = 'todo.list'
    _rec_name = "accountant"

    accountant = fields.Many2one('hr.employee', string='Cashier')
    img_view = fields.Binary()
    todo_menu = fields.One2many('todo.menu.line', 'connect_id', string="To DO List")
    note = fields.Text('Comments', translate=True)

    @api.onchange('accountant')
    def onchange_accountant(self):
        for i in self:
            result = i.env['hr.employee'].search([('id', '=', i.accountant.id)])
            for k in result:
                i.img_view = k.image


    @api.multi
    def add_day_cron(self):
        print('Day Cron')
        for data in self.env['todo.list'].search([]):
            days = []
            dates = datetime.today()
            result = self.env['todo.activity'].search([('activity_type', '=', 'day')])
            for i in result:
                vals = (0, 0, {
                    'todo_name': i.id,
                    'todo_type': 'day',
                    'todo_date': dates,
                })
                days.append(vals)
            data.update({'todo_menu': days})

    @api.multi
    def add_week_cron(self):
        print('Week Cron')
        for data in self.env['todo.list'].search([]):
            weeks = []
            dates = datetime.today()
            result = self.env['todo.activity'].search([('activity_type', '=', 'week')])
            for i in result:
                vals = (0, 0, {
                    'todo_name': i.id,
                    'todo_type': 'week',
                    'todo_date': dates,
                })
                weeks.append(vals)
            data.update({'todo_menu': weeks})

    @api.multi
    def add_month_cron(self):
        print('Month Cron')
        for data in self.env['todo.list'].search([]):
            months = []
            dates = datetime.today()
            result = self.env['todo.activity'].search([('activity_type', '=', 'month')])
            for i in result:
                vals = (0, 0, {
                    'todo_name': i.id,
                    'todo_type': 'month',
                    'todo_date': dates,
                })
                months.append(vals)
            data.update({'todo_menu': months})


class ToDoListLine(models.Model):
    _name = 'todo.menu.line'

    connect_id = fields.Many2one('todo.list', string='Description', required=True)
    todo_name = fields.Many2one('todo.activity',string='Title', required=True, readonly=True)
    todo_type = fields.Selection([
        ('day', 'Daily'),
        ('week', 'Weekly'),
        ('month', 'Monthly')
    ],readonly=True)
    todo_date = fields.Date(string="date", readonly=False)
    todo_checked = fields.Boolean(string='Status', readonly=True)
    colour_check = fields.Boolean(string='check', compute='get_colour')

    @api.multi
    def action_check_bool(self):
        for i in self:
            i.todo_checked = True

    @api.multi
    def get_colour(self):
        current_date = datetime.today()
        for i in self:
            date_object = datetime.strptime(i.todo_date, '%Y-%m-%d')
            difference = current_date - date_object
            if i.todo_type == 'day':
                if difference.days >= 1 and not i.todo_checked:
                    i.colour_check = True
                elif difference.days <= 1 and not i.todo_checked:
                    i.colour_check = False

            if i.todo_type == 'week':
                if difference.days >= 7 and not i.todo_checked:
                    i.colour_check = True
                elif difference.days <= 7 and not i.todo_checked:
                    i.colour_check = False

            if i.todo_type == 'month':
                if difference.days >= 30 and not i.todo_checked:
                    i.colour_check = True
                elif difference.days <= 30 and not i.todo_checked:
                    i.colour_check = False


class Activities(models.Model):

    _name = 'todo.activity'
    _rec_name = 'activity_description'

    activity_description = fields.Char(string='Description', required=True)
    activity_type = fields.Selection([
        ('day', 'Daily'),
        ('week', 'Weekly'),
        ('month', 'Monthly')
    ], required=True)


class CashierEmployee(models.Model):

    _inherit = 'hr.employee'

    is_cashier = fields.Boolean(string='Is Cashier', default=False)

    @api.constrains('is_cashier')
    def constrain_is_cashier(self):
        for rec in self:
            if rec.is_cashier:
                vals = {
                    'accountant': rec.id,
                    'img_view': rec.image,
                }
                cashier = rec.env['todo.list'].sudo().create(vals)

