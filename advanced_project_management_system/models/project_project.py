# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
import json
from odoo import api, fields, models, _


class ProjectProject(models.Model):
    """ Added project documents,checklist,stage updates"""
    _inherit = 'project.project'

    project_category_id = fields.Many2one('project.category',
                                          string='Project Category',
                                          help="For adding project category ")
    document_count = fields.Integer(string='Documents',
                                    compute='_compute_document_count',
                                    help="For getting the document count")
    project_stage_id = fields.Many2one('project.project.stage',
                                       tracking=True, string='Stage',
                                       help="Project stages")
    project_checklist_info_ids = fields.One2many('project.checklist.info',
                                                 'project_id',
                                                 help="Project checklist details",
                                                 string='Checklist')
    checklist_progress = fields.Float(string="Progress",
                                        help="For checklist progress bar ")
    checklist_template_ids = fields.Many2many('project.checklist.template',
                                              string='checklist template',
                                              help="For getting checklist "
                                                   "template")
    issue_count = fields.Integer(string="Project issue",
                                 help="For getting project issue ",
                                 compute="_compute_issue_count")
    shortcut_ids = fields.One2many('project.shortcut', 'project_id',
                                   string='Shortcuts')
    url_shortcut = fields.Char(string="URL Shortcut",
                               compute="_compute_url_shortcut",
                               help="Enter the URL shortcut.")
    is_active = fields.Boolean(string="Is Active", store=True,
                               help="Check this box if the URL is active.")
    url_link = fields.Char(string="URL Link", help="Enter the URL link.")
    url_name = fields.Char(string="URL Name",
                           help="Enter the name associated with the URL.")

    def open_project_creation_wizard(self):
        """ Open the project creation wizard """
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'project.project',
            'view_mode': 'form',
            'view_id': self.env.ref(
                'advanced_project_management_system.project.project.view.form.'
                'simplified').id,
            'target': 'current',
        }

    @api.depends('url_link', 'url_name')
    def _compute_url_shortcut(self):
        """ Compute the URL shortcut and its activation status """
        for project in self:
            if project.url_link:
                project.is_active = True
                project.url_shortcut = project.url_link
            else:
                project.url_shortcut = "Add Link"
                project.is_active = False

    def open_url_shortcut(self):
        """ Open the URL shortcut """
        for project in self:
            if project.url_shortcut:
                return {
                    'name': self.url_name,
                    'type': 'ir.actions.act_url',
                    'url': project.url_shortcut,
                    'target': 'self',
                }

    def button_document(self):
        """ Return document kanban for the project"""
        return {
            'name': 'Documents',
            'type': 'ir.actions.act_window',
            'res_model': 'ir.attachment',
            'view_mode': 'kanban,form',
            'res_id': self._origin.id,
            'domain': [
                ('res_id', '=', self._origin.id),
                ('res_model', '=', 'project.project')
            ],
        }

    def _compute_document_count(self):
        """ Compute document count and return """
        for rec in self:
            attachment_ids = self.env['ir.attachment'].search(
                [('res_model', '=', 'project.project'),
                 ('res_id', '=', rec.id)])
            rec.document_count = len(attachment_ids)

    def project_multi_stage_update(self):
        """ Return wizard to update the project stage"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Mass Update',
            'view_mode': 'form',
            'target': 'new',
            'res_model': 'project.stage.update',
        }

    @api.onchange('checklist_template_ids')
    def _onchange_checklist_template_ids(self):
        """ Updating checklist"""
        check_list_id = self.env['project.checklist.template'].browse(
            self.checklist_template_ids.ids)
        if check_list_id:
            for checklist_id in check_list_id.checklist_ids.ids:
                self.update({
                    'project_checklist_info_ids':
                        [(0, 0, {
                            'checklist_id': checklist_id
                        })]
                })

    def _compute_issue_count(self):
        """ For getting project issue count"""
        for rec in self:
            issue_id = self.env['project.issue'].search(
                [('project_id', '=', rec.id)])
            rec.issue_count = len(issue_id)

    def button_issue(self):
        """Return project issues"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Project Issues',
            'view_mode': 'tree,form',
            'res_model': 'project.issue',
            'domain': [('project_id', '=', self.id)]
        }

    def _get_stat_buttons(self):
        """ Get statistical buttons for the project """
        self.ensure_one()
        buttons = super(ProjectProject, self)._get_stat_buttons()
        if self.user_has_groups('project.group_project_user'):
            buttons.append({
                'icon': 'area-chart',
                'text': _('Burnup Chart'),
                'action_type': 'action',
                'action': 'advanced_project_management_system.action_project_task_burnup_chart_report',
                'additional_context': json.dumps({
                    'active_id': self.id,
                }),
                'show': True,
                'sequence': 60,
            })
        if self.user_has_groups('project.group_project_user'):
            buttons.append({
                'icon': 'line-chart',
                'text': _('Velocity Chart'),
                'action_type': 'action',
                'action': 'advanced_project_management_system.action_project_velocity_chart_report',
                'additional_context': json.dumps({
                    'active_id': self.id,
                }),
                'show': True,
                'sequence': 60,
            })
        return buttons

    def action_project_task_burnup_chart_report(self):
        """ Open the Burnup Chart report for the project """
        action = self.env['ir.actions.act_window']._for_xml_id(
            'advanced_project_management_system'
            '.action_project_task_burnup_chart_report')
        action['display_name'] = _("%(name)s's Burnup Chart", name=self.name)
        return action

    def action_project_velocity_chart_report(self):
        """ Open the Velocity Chart report for the project """
        action = self.env['ir.actions.act_window']._for_xml_id(
            'advanced_project_management_system'
            '.action_project_velocity_chart_report')
        action['display_name'] = _("%(name)s's Velocity Chart",
                                   name=self.name)
        return action

    def action_open_shortcut(self):
        """ Open the shortcut creation form """
        view_id = self.env.ref(
            'advanced_project_management_system.project_shortcut_view_form').id
        return {
            'name': 'Add Custom Project Shortcut',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'project.shortcut',
            'views': [(view_id, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'new',
        }
