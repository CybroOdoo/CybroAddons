# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2017-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#    Author: Jesni Banu(<https://www.cybrosys.com>)
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
from odoo import models, fields, api, _


class ProjectCode(models.Model):
    _inherit = 'project.project'

    project_code = fields.Char(string='Project Code', required=True)


class ProjectCodeTask(models.Model):
    _inherit = 'project.task'

    @api.model
    def create(self, vals):
        if vals['project_id']:
            obj = self.env['project.project'].browse(vals['project_id'])
            if obj.project_code:
                vals['name'] = obj.project_code + '/' + vals['name']
        return super(ProjectCodeTask, self).create(vals)

    @api.multi
    def write(self, vals):
        if vals.get('project_id'):
            obj = self.env['project.project'].browse(vals.get('project_id'))
            if obj.project_code:
                if vals.get('name'):
                    vals['name'] = obj.project_code + '/' + vals['name']
                else:
                    if '/' in self.name:
                        s = self.name.index('/')
                        s += 1
                        self.name = self.name[s:]
                    vals['name'] = obj.project_code + '/' + self.name
            else:
                if not vals.get('name'):
                    if '/' in self.name:
                        s = self.name.index('/')
                        s += 1
                        vals['name'] = self.name[s:]
        elif vals.get('name'):
            vals['name'] = self.project_id.project_code + '/' + vals['name']
        return super(ProjectCodeTask, self).write(vals)
