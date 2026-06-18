# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
###############################################################################
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class FreeResource(models.TransientModel):
    """Wizard to add the period to get the free resource"""
    _name = 'free.resource'
    _description = 'Free Resource'

    date_from = fields.Date(
        string="Start Date",
        help="Start date of period for receiving the Free Resource")
    date_to = fields.Date(
        string="End Date",
        help="End date of period for receiving the Free Resource")

    @api.constrains('date_from', 'date_to')
    def _check_date_to_after_date_from(self):
        """Ensure the end date is later than the start date."""
        for record in self:
            if (record.date_from and record.date_to and
                    record.date_to <= record.date_from):
                raise ValidationError(_(
                    "The end date must be after the start date."))

    def get_free_resource(self):
        """Get the list of free resource at the given period"""
        # Find all portal users who are followers, collaborators, or assignees of any project or task
        followers = self.env['mail.followers'].search([('res_model', 'in', ['project.project', 'project.task'])])
        collaborators = self.env['project.collaborator'].search([])
        assigned_tasks = self.env['project.task'].search([('user_ids', '!=', False)])
        
        allowed_partners = followers.mapped('partner_id') | collaborators.mapped('partner_id') | assigned_tasks.mapped('user_ids.partner_id')
        allowed_portal_users = allowed_partners.user_ids.filtered(lambda u: u.share and u.active)
        portal_user_ids = allowed_portal_users.ids

        base_domain = [('active', '=', True), '|', ('share', '=', False), ('id', 'in', portal_user_ids)]

        if self.date_from and self.date_to:
            busy_resource_ids = self.env['project.task'].get_free_resource_ids(
                self.date_from, self.date_to, exclude_task_id=None)
            if busy_resource_ids:
                domain = [('id', 'not in', busy_resource_ids)] + base_domain
            else:
                domain = base_domain
        else:
            domain = base_domain

        return {
            'name': 'Free Resources' if self.date_from and self.date_to else 'All Resources',
            'view_mode': 'list,form',
            'target': 'main',
            'res_model': 'res.users',
            'views': [
                (self.env.ref('project_resource.res_users_view_list').id, 'list'),
                (self.env.ref('project_resource.res_users_view_form').id, 'form')
            ],
            'type': 'ir.actions.act_window',
            'domain': domain,
        }
