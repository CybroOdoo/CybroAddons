# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions
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
from odoo import api, fields, models


class ProjectIssue(models.Model):
    """
    Model for recording and tracking issues related to projects and tasks.
    """
    _name = "project.issue"
    _description = 'Project and task issue'

    user_id = fields.Many2one("res.users", string="Assigned to",
                              help="The person who is responsible to solve "
                                   "the issue")
    summary = fields.Text(string='Issue summary', help="Adding project issue")
    email = fields.Char(string="Email", help="Email address")
    project_id = fields.Many2one('project.project', string="Project",
                                 help="To know issue noticed in which project")
    task_id = fields.Many2one('project.task', string="Task",
                              help="To know issue noticed in which task",
                              domain=[('project_id', '=', project_id)])
    priority = fields.Selection([('0', 'Low'), ('1', 'High')], default='0',
                                string="Priority")
    tag_ids = fields.Many2many('project.tags', string='Tags',
                               help='Set the tags')
    partner_id = fields.Many2one('res.partner', string="Contact",
                                 help="Know about the contact details")
    name = fields.Char(string='Number', default='new',
                       help='To track the issue reference')
    description = fields.Text(string='Description',
                              help="To add the issue in detail")
    extra_info = fields.Text(string="Extra Info",
                             help="To add some extra information")
    state = fields.Selection([('new', 'New'), ('progress', 'In Progress'),
                              ('done', 'Done'), ('cancel', 'Cancel')],
                             default='new', string='State',
                             help='Project issue pipeline stages')
    create_date = fields.Datetime(string="Create Date",
                                  help='For tracking the record creation date',
                                  default=fields.Datetime.now())

    @api.model_create_multi
    def create(self, vals_list):
        """
        Overrides create to automatically generate a unique issue reference number
        from the sequence.
        :param vals_list: List of dictionaries of field values.
        :return: Created recordset.
        """
        for vals in vals_list:
            if vals.get('name', 'new') == 'new':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'project.issue')
        res = super(ProjectIssue, self).create(vals_list)
        return res
