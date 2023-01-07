# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo import models, fields


class RiskIncidents(models.Model):
    _name = 'risk.incident'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'risk_incident'

    risk_incident = fields.Char(string='Title', tracking=True, required=True)
    project_id = fields.Many2one('project.project', string='Project',
                                 tracking=True)
    user_id = fields.Many2one('res.users', string='Assigned to',
                              tracking=True, default=lambda self: self.env.user)
    deadline = fields.Date(string='Deadline', tracking=True)
    tag_ids = fields.Many2many('risk.tag', string='Tags', tracking=True)
    partner_id = fields.Many2one('res.partner', string='Customer',
                                 tracking=True)
    state = fields.Selection(
        [('new', 'New'), ('to_do', 'To Do'),
         ('advanced', 'Advanced'), ('progress', 'In Progress'),
         ('done', 'Done'), ('cancel', 'Cancelled')],
        string='Status', default='new', tracking=True,
        group_expand='_group_expand_states')
    note = fields.Text(string='Description')
    incident_image = fields.Binary(string='Incident Image')

    def _group_expand_states(self, state, domain, order):
        return [key for
                key, val in type(self).state.selection]
