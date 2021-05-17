# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import datetime
import math
from odoo import api, models, fields, _
from odoo.exceptions import ValidationError


class SupportClientTimesheet(models.Model):
    _inherit = 'account.analytic.line'

    support_count = fields.Integer(string='Ticket Count', store=True,
                                   help="Effective hour of each record",
                                   compute="_compute_support_count")

    @api.depends('unit_amount')
    def _compute_support_count(self):
        """Find count of support in each record"""
        for task in self:
            try:
                task.support_count = math.ceil(task.unit_amount /
                                               task.project_id.support_duration)
            except ZeroDivisionError:
                task.support_count = 0


class SupportClient(models.Model):
    _inherit = 'project.task'

    is_support_package = fields.Boolean(string='Support Package')
    support_count = fields.Integer(string='Number of Tickets')
    count_used = fields.Integer(string='Used Tickets')
    count_remaining = fields.Integer(string='Remaining Tickets')
    support_duration = fields.Float(string='Support Duration', default=1.0)
    package_validity = fields.Integer(string='Support Package Validity',
                                      default=1)

    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    reminder_date = fields.Date(string='Reminder Date')
    this_effective_hours = fields.Float(help="Effective hour in this module",
                                        default=0.0, store=True,
                                        compute_sudo=True,
                                        compute="_compute_this_effective_hours")
    to_renew = fields.Boolean(string="To Renew", default=False)

    @api.model_create_multi
    def create(self, vals_list):
        """update input values with values of this module"""
        for rec in vals_list:
            this_project_id = rec.get('project_id')
            project_id = self.env['project.project'].search([
                ('id', '=', this_project_id)])
            if project_id.is_support_package:
                new_vals_list = [{
                    'is_support_package': project_id.is_support_package,
                    'support_count': project_id.support_count,
                    'support_duration': project_id.support_duration,
                    'planned_hours': (float(project_id.support_count) *
                                      float(project_id.support_duration)),
                    'count_used': 0,
                    'date_deadline': datetime.date.today() + datetime.timedelta(
                        days=project_id.package_validity),
                    'count_remaining': project_id.support_count,
                    'package_validity': project_id.package_validity,
                    'start_date': datetime.date.today(),
                    'end_date': datetime.date.today() + datetime.timedelta(
                        days=project_id.package_validity),
                }]
                vals_list[0].update(new_vals_list[0])
                return super(SupportClient, self).create(vals_list)
            else:
                return super(SupportClient, self).create(vals_list)

    @api.onchange('company_id')
    def _onchange_company_id(self):
        """Function predefines some fields"""
        this_project_id = self.env.context.get('default_project_id')
        project_id = self.env['project.project']. \
            search([('id', '=', this_project_id)])
        if project_id.is_support_package:
            self.count_used = 0
            self.name = project_id.name
            self.start_date = datetime.date.today()
            self.support_duration = project_id.support_duration
            self.package_validity = project_id.package_validity
            self.is_support_package = project_id.is_support_package
            self.end_date = datetime.date.today() + datetime. \
                timedelta(days=project_id.package_validity)
            self.date_deadline = datetime.date.today() + datetime. \
                timedelta(days=project_id.package_validity)
            self.planned_hours = (self.support_count * self.support_duration)
            self.support_count = self.count_remaining = project_id.support_count
        else:
            self.is_support_package = False

    @api.onchange('start_date')
    def _onchange_start_date(self):
        if self.is_support_package:
            self.end_date = self.start_date + datetime.timedelta(
                days=self.package_validity)
            self.date_deadline = self.end_date

    @api.onchange('count_remaining')
    def _onchange_count_remaining(self):
        if self.is_support_package:
            days_left = self.end_date - self.start_date
            for rec in self:
                if rec.count_remaining == 0 or days_left.days <= 0:
                    self.sale_order_id.order_line.qty_delivered = 1
                if not rec.sale_line_id:
                    rec.to_renew = True
                    raise ValidationError(
                        "You cannot add customer from here or because update a"
                        " timesheet without sale order ID ! \n\n You can go to "
                        "sales module to create a sale order and the package"
                        " will be generated automatically.")
                if days_left.days < 0:
                    rec.to_renew = True
                    raise ValidationError(
                        "Package Expired !!! \n\nThis package validity is"
                        " expired, you can create a new sale order to continue"
                        " with the service.")
                if rec.count_remaining < 0:
                    rec.to_renew = True
                    raise ValidationError(
                        "Ticket Limit Exceeded !!! \n\n You can create a new"
                        " sale order to continue with the service.")

    @api.onchange('count_used')
    def _onchange_count_used(self):
        if self.is_support_package:
            days_left = self.end_date - self.start_date
            for rec in self:
                if rec.count_used > rec.support_count:
                    raise ValidationError("Supports Limit Exceeded!")
                if days_left.days <= (int(0.1 * rec.package_validity)) and \
                        rec.count_remaining < (int(0.1 * rec.support_count)):
                    rec.to_renew = True
                    return {'warning': {
                        'title': _("Warning"),
                        'message': _(
                            "%s is having only %d days and %d ticket(s) left"
                            " with this package. Kindly inform the customer to "
                            "renew the package to avail the service without"
                            " break.\n\nThank You !!!",
                            self.partner_id.name, days_left.days,
                            rec.count_remaining),
                    }}
                if days_left.days <= (int(0.1 * rec.package_validity)):
                    rec.to_renew = True
                    return {'warning': {
                        'title': _("Warning"),
                        'message': _(
                            "%s is having only %d days left with this package."
                            " Kindly inform the customer to renew the package"
                            " to avail the service without break."
                            "\n\nThank You !!!",
                            self.partner_id.name, days_left.days),
                    }}
                if rec.count_remaining < (int(0.1 * rec.support_count)):
                    rec.to_renew = True
                    return {'warning': {
                        'title': _("Warning"),
                        'message': _(
                            "%s is having only %d ticket(s) left with this"
                            " package. Kindly inform the customer to renew the"
                            " package to avail the service without break."
                            "\n\nThank You !!!",
                            self.partner_id.name, rec.count_remaining)
                    }}

    def action_renew(self):
        """Button for renewal"""
        product = self.sale_line_id
        product_id = self.env['product.product'].search(
            [('name', '=', product.name)])
        so_id = self.env['sale.order'].create({
            'partner_id': self.partner_id.id,
            'partner_invoice_id': self.partner_id.id,
            'partner_shipping_id': self.partner_id.id,
            'order_line': [(0, 0, {'name': product_id.name,
                                   'product_id': product_id.id,
                                   'product_uom_qty': 1,
                                   'product_uom': product_id.uom_id.id,
                                   'price_unit': product.price_unit,
                                   'tax_id': product_id.taxes_id
                                   })]})
        return {
            'name': _('Sales Orders'),
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'domain': [('id', '=', so_id.id)],
            'view_type': 'form',
            'view_mode': 'tree,form',
        }

    @api.depends('timesheet_ids.unit_amount')
    def _compute_this_effective_hours(self):
        """find effective hours with respect to support duration"""
        for task in self:
            sigma_ciel = 0
            for rec in task.timesheet_ids.mapped('unit_amount'):
                try:
                    ciel_timesheet_ids = math.ceil(rec / task.support_duration)
                except ZeroDivisionError:
                    ciel_timesheet_ids = 0
                sigma_ciel = sigma_ciel + ciel_timesheet_ids
            task.this_effective_hours = round(
                sigma_ciel * task.support_duration, 2)

    @api.depends('effective_hours', 'subtask_effective_hours', 'planned_hours')
    def _compute_remaining_hours(self):
        for task in self:
            if task.is_support_package is False:
                task.remaining_hours = task.planned_hours - \
                                       task.effective_hours - \
                                       task.subtask_effective_hours
            else:
                task.remaining_hours = task.planned_hours - \
                                       task.this_effective_hours - \
                                       task.subtask_effective_hours
                temp_count = 0
                for rec in task.timesheet_ids:
                    temp_count += rec.support_count
                task.count_used = temp_count
                task.count_remaining = task.support_count - task.count_used
