# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models, fields


class SupportPackageProduct(models.Model):
    _inherit = "product.template"

    is_support = fields.Boolean(string='Is Support Package', default=False)


class SupportPackage(models.Model):
    _inherit = 'project.project'

    is_support_package = fields.Boolean(string='Support Package', default=False)
    support_count = fields.Char(string='Number of Tickets')
    support_duration = fields.Float(string='Maximum Duration')
    support_validity_number = fields.Char(string='Package Validity')
    validity_rule = fields.Selection([
        ('days', 'Day(s)'),
        ('months', 'Month(s)'),
        ('years', 'Year(s)')], default='months')
    package_validity = fields.Integer(string='Validity',
                                      store=True, readonly=False,
                                      compute='_compute_package_validity')
    privacy_visibility_support = fields.Selection([
        ('followers', 'Invited internal users'),
        ('employees', 'All internal users')], string='Visibility',
        required=True, default='employees')
    allowed_internal_user_support_ids = fields.Many2many(
        'res.users',
        default=lambda self: self.env.user,
        string="Allowed Internal Users",
        domain=[('share', '=', False)])

    @api.model
    def create(self, vals):
        """Create service product of the project"""
        package = super(SupportPackage, self).create(vals)
        if package.is_support_package:
            package.privacy_visibility = 'employees'
            package.label_tasks = 'Customers'
            categ = self.env['product.category'].search(
                [('name', '=', 'Services')])
            project = {
                'name': vals.get('name'),
                'sale_ok': True,
                'purchase_ok': True,
                'is_support': True,
                'type': 'service',
                'categ_id': int(categ.id),
                'service_policy': 'delivered_manual',
            }
            product_id = self.env['product.template'].create(project)
            product_id.service_tracking = 'task_global_project'
            product_id.project_id = package.id
        return package

    @api.onchange('privacy_visibility_support')
    def _onchange_privacy_visibility_support(self):
        if self.is_support_package:
            self.privacy_visibility = self.privacy_visibility_support

    @api.onchange('allowed_internal_user_ids_support')
    def _onchange_allowed_internal_user_ids_support(self):
        if self.is_support_package:
            self.allowed_internal_user_ids = self.allowed_internal_user_ids_support

    @api.onchange('is_support_package')
    def _onchange_is_support_package(self):
        if self.is_support_package:
            self.label_tasks = 'Customers'
            self.allow_billable = True
        else:
            self.label_tasks = 'Tasks'

    @api.depends('support_validity_number', 'validity_rule')
    def _compute_package_validity(self):
        """Find package_validity in days"""
        for rec in self:
            if rec.is_support_package:
                if rec.validity_rule == 'days':
                    rec.package_validity = int(rec.support_validity_number)
                elif rec.validity_rule == 'months':
                    rec.package_validity = int(rec.support_validity_number) * 30
                elif rec.validity_rule == 'years':
                    rec.package_validity = int(
                        rec.support_validity_number) * 365
