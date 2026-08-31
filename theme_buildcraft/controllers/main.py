# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
from odoo import http
from odoo.http import request
from werkzeug.exceptions import NotFound


class ThemeBuildCraft(http.Controller):
    @http.route(['/about'], type='http', auth="public", website=True)
    def about_page(self, **kw):
        return request.render('theme_buildcraft.aboutus_template')

    @http.route(['/services'], type='http', auth="public", website=True)
    def services_page(self, **kw):
        return request.render('theme_buildcraft.services_template')

    @http.route(['/projects'], type='http', auth="public", website=True)
    def projects_page(self, **kw):
        projects = request.env['buildcraft.project'].sudo().search([('is_published', '=', True)])
        return request.render('theme_buildcraft.projects_template', {'projects': projects})

    @http.route(['/project/<int:project_id>'], type='http', auth="public", website=True)
    def project_detail(self, project_id, **kw):
        project = request.env['buildcraft.project'].sudo().browse(project_id)
        if not project.exists() or not project.is_published:
            raise NotFound()
        related_projects = request.env['buildcraft.project'].sudo().search([
            ('is_published', '=', True),
            ('id', '!=', project.id),
            ('category', '=', project.category),
        ], limit=3)
        if len(related_projects) < 3:
            extra = request.env['buildcraft.project'].sudo().search([
                ('is_published', '=', True),
                ('id', '!=', project.id),
                ('id', 'not in', related_projects.ids),
            ], limit=3 - len(related_projects))
            related_projects |= extra
        return request.render('theme_buildcraft.project_detail_template', {
            'project': project,
            'related_projects': related_projects,
        })

    @http.route(['/team'], type='http', auth="public", website=True)
    def team_page(self, **kw):
        return request.render('theme_buildcraft.team_template')

    @http.route(['/contactus/submit'], type='http', auth="public", methods=['POST'], website=True, csrf=True)
    def contactus_submit(self, **kw):
        first_name = kw.get('contact_first_name', '')
        last_name = kw.get('contact_last_name', '')
        contact_name = f"{first_name} {last_name}".strip()
        email_from = kw.get('email_from', '')
        phone = kw.get('phone', '')
        project_type = kw.get('project_type', '')
        budget = kw.get('budget', '')
        description = kw.get('description', '')

        body = f"Project Type: {project_type}\nBudget: {budget}\n\nDetails:\n{description}"

        request.env['crm.lead'].sudo().create({
            'name': f"Website Contact: {contact_name}" if contact_name else "Website Contact",
            'contact_name': contact_name,
            'email_from': email_from,
            'phone': phone,
            'description': body,
        })

        return request.redirect('/contactus?submitted=1')
