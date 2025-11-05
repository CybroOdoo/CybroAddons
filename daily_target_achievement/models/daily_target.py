# !/usr/bin/env python
# -*- coding: utf-8 -*-

import time
from datetime import datetime
import babel

from odoo import fields, models, api, _, tools
from odoo import exceptions
from odoo.exceptions import Warning, UserError


class DailyTarget(models.Model):
    _name = 'daily.target'
    _description = 'Daily Target'
    _order = "id desc"

    name = fields.Char(string='Reference', readonly=True)
    target_amount = fields.Float(string='Target', compute='calculate_target')
    achieve_amount = fields.Float(string='Achievement', readonly=True, copy=False)
    invoice_id = fields.Many2one('account.invoice', string='Invoice')
    user_id = fields.Many2one('res.users', string='Sales Person', copy=False)
    date = fields.Date(string='Date', default=lambda self: fields.Date.today())
    to_date = fields.Date(string='To Date', default=lambda self: fields.Date.today())
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.user.company_id)
    internal_note = fields.Text(string='Internal Note')
    target_id = fields.One2many('daily.target.line', 'target_id', string='Target')
    state = fields.Selection([('draft', 'Draft'),
                              ('open', 'Open'),
                              ('done', 'Done'),
                              ('cancel', 'Cancel')], string='State', default='draft', copy=False)

    @api.model
    def create(self, values):
        """
        Over writted this method to give the name for record
        :param values:
        :return:
        """
        res = super(DailyTarget, self).create(values)
        for this in res:
            ttyme = datetime.fromtimestamp(time.mktime(time.strptime(this.date, "%Y-%m-%d")))
            locale = res.env.context.get('lang') or 'en_US'
            this.name = 'Target of  ' + this.user_id.name + ' _ ' + tools.ustr(
                babel.dates.format_date(date=ttyme, format='MMMM-y', locale=locale))

        return res

    @api.one
    def action_open_target(self):
        """
        This method is used to change the record state to open
        """
        obj_config = self.env['daily.target'].search([('state', '=', 'open')])
        for i in obj_config:
            if self.user_id == i.user_id:
                raise exceptions.Warning(_("Warning"), _(
                    "You have already created a incentive program for this sales person"))
        self.state = 'open'

    @api.one
    def calculate_target(self):
        """This method is used to calculate the target of the salesperson from lines"""
        target_total = 0
        if self.target_id:
            for i in self.target_id:
                target_total = target_total + i.target
        self.target_amount = target_total

    @api.one
    def action_target_cancel(self):
        """
        This method is used to change the record state to cancel
        """
        self.state = 'cancel'

    @api.one
    def target_done(self):
        """
        This method is used to change the record state to Done
        """
        self.state = 'done'

    @api.constrains('user_id')
    def _checking_another_config(self):
        """
        Only one record is in open state to avoid further mistake
        """
        obj_config = self.env['daily.target'].search([('state', '=', 'open')])
        for i in obj_config:
            if self.user_id == i.user_id:
                raise exceptions.Warning(_("Warning"), _(
                    "You have already created a incentive program for current sales person"))

    @api.multi
    def unlink(self):
        """
        will not able to delete a record which is in open or done state
        :return:
        """
        for rec in self:
            if rec.state in ('open', 'done'):
                raise UserError(_("You can not delete a Target Program that are in Open/Done State"))
        return super(DailyTarget, self).unlink()


class DailyTargetLine(models.Model):
    _name = 'daily.target.line'
    _description = 'Daily Target Line'
    _order = "id desc"

    date_today = fields.Date(string='Date', default=lambda self: fields.Date.today())
    amount = fields.Float(string='Amount', readonly=True)
    target = fields.Float(string='Target')
    target_id = fields.Many2one('daily.target', string='Target Program')
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.user.company_id)
