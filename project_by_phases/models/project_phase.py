# -*- coding: utf-8 -*-
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
from odoo import api, fields, models


class ProjectPhase(models.Model):
    """Model to create and manage project phases in project module."""
    _name = 'project.phase'
    _description = "Project Phase"
    _order = 'sequence, id'
    _check_company_auto = True

    @api.model
    def _default_company_id(self):
        if self.env.context.get('default_project_id'):
            return self.env['project.project'].browse(
                self.env.context['default_project_id']
            ).company_id
        return self.env.company

    name = fields.Char(string="Name", required=True,
                       help="Provide name for record.")
    project_id = fields.Many2one('project.project', string="Project",
                                 check_company=True,
                                 help="Choose projects from existing records.")
    start_date = fields.Date(string="Start date", help="Select start date")
    responsible_user_id = fields.Many2one('res.users',
                                          string='Responsible User',
                                          required=True,
                                          help="It's a mandatory field, so "
                                               "please select any user from "
                                               "the list.")
    sequence = fields.Integer(string="Sequence", default=10,
                              help="Give a sequence number.")
    end_date = fields.Date(string="End date", help="Select end date.")
    company_id = fields.Many2one('res.company', string='Company',
                                 default=_default_company_id,
                                 compute='_compute_company_id',
                                 store=True,
                                 readonly=False,
                                 help="By default, current login company will "
                                      "be selected here. You can choose other "
                                      "companies also.")
    internal_notes = fields.Html(string="Internal Note",
                                 help="Add internal notes")

    @api.depends('project_id.company_id')
    def _compute_company_id(self):
        for phase in self:
            if phase.project_id and not phase.company_id:
                phase.company_id = phase.project_id.company_id

    @api.onchange('project_id')
    def _onchange_project_id(self):
        if self.project_id:
            self.company_id = self.project_id.company_id

    def get_project_tasks(self):
        """Return action to view tasks associated with the current project
        phase."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Tasks',
            'view_mode': 'list,form',
            'res_model': 'project.task',
            'domain': [('project_phase_id', '=', self.id)],
            'context': {
                'default_project_phase_id': self.id,
                'default_project_id': self.project_id.id,
            },
        }

