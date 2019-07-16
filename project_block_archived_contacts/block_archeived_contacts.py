# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2015-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#    Author: Jesni Banu(<http://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.

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
from openerp import models, fields, api, _


class ProjectTaskInherit(models.Model):
    _inherit = 'project.task'

    user_id = fields.Many2one('res.users', 'Assigned to', select=True, track_visibility='onchange',
                              domain=[('active', '=', 'True'), ('partner_id.active', '=', 'True')])


class ProjectProjectInherit(models.Model):
    _inherit = 'project.project'

    user_id = fields.Many2one('res.users', 'Project Manager',
                              domain=[('active', '=', 'True'), ('partner_id.active', '=', 'True')])


class ProjectIssueInherit(models.Model):
    _inherit = 'project.issue'

    user_id = fields.Many2one('res.users', 'Assigned to', required=False, select=1, track_visibility='onchange',
                              domain=[('active', '=', 'True'), ('partner_id.active', '=', 'True')])
    partner_id = fields.Many2one('res.partner', 'Contact', select=1,
                                 domain=[('active', '=', 'True')])


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    @api.model
    def _default_user(self):
        return self.env.context.get('user_id', self.env.user.id)

    user_id = fields.Many2one('res.users', string='User', default=_default_user,
                              domain=[('active', '=', 'True'), ('partner_id.active', '=', 'True')])

