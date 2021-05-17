# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models, fields


class ProjectTemplate(models.Model):
    _name = 'support.package.template'
    _description = 'Support Package Template'
    _rec_name = 'name'

    name = fields.Char(string="Name of Package")
    count = fields.Char(string='Number of Tickets', readonly=False)
    duration = fields.Float(
        string='Ticket Duration', readonly=False,
        help="Maximum allowed duration for a single ticket in hours")
    validity_number = fields.Char(string='Support Package Validity',
                                  readonly=False)
    validity_rule = fields.Selection([
        ('days', 'Day(s)'),
        ('months', 'Month(s)'),
        ('years', 'Year(s)')], readonly=False, default='months')
    package_validity = fields.Integer(string='Package Validity', store=True,
                                      readonly=False,
                                      compute='_compute_package_validity')

    @api.depends('validity_number', 'validity_rule')
    def _compute_package_validity(self):
        """Find package validity in days"""
        for rec in self:
            if rec.validity_rule == 'days':
                rec.package_validity = int(rec.validity_number)
            elif rec.validity_rule == 'months':
                rec.package_validity = int(rec.validity_number) * 30
            elif rec.validity_rule == 'years':
                rec.package_validity = int(rec.validity_number) * 365

    def button_create_package(self):
        """Button to convert template to project"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Project Support Package',
            'view_mode': 'form',
            'res_model': 'project.project'
        }
