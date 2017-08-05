# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2017-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#    Author: Nilmar Shereef(<http://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from odoo import models, fields, api


class ProjectTaskInherit(models.Model):
    _inherit = 'project.task'

    @api.model
    def create(self, vals):
        result = super(ProjectTaskInherit, self).create(vals)
        if result['issue_id']:
            result['issue_id'].task_id = result['id']
        return result

    issue_id = fields.Many2one('project.issue', string='Issue Reference')


class ProjectIssueInherit(models.Model):
    _inherit = 'project.issue'

    task_id = fields.Many2one('project.task', string='Task Reference')

    @api.model
    def create(self, vals):
        result = super(ProjectIssueInherit, self).create(vals)
        if result['task_id']:
            result['task_id'].issue_id = result['id']
        return result
