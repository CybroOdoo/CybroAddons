# -*- coding: utf-8 -*-
############################################################################-
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
############################################################################-

from odoo import http, SUPERUSER_ID
from odoo.http import request


class ThemeModernPortfolio(http.Controller):
    """Controller for Theme Modern Portfolio."""

    @http.route('/about', type='http', auth='public', website=True)
    def about_page(self):
        """Render the About Us page."""
        return request.render('theme_modern_portfolio.about_page_template')

    @http.route('/projects', type='http', auth='public', website=True)
    def projects_page(self):
        """Render the Projects listing page."""
        return request.render('theme_modern_portfolio.projects_page_template')

    @http.route('/project/<model("portfolio.project"):project>', type='http', auth='public', website=True)
    def project_details_page(self, project):
        """Render the Project detail page."""
        return request.render('theme_modern_portfolio.project_detail_content', {
            'project': project,
        })

    @http.route('/theme_modern_portfolio/get_portfolio_data', type='json', auth='public', website=True)
    def get_portfolio_data(self):
        """Returns the project details and tags for dynamic snippets"""
        tags = request.env['portfolio.project.tag'].search([])
        projects = request.env['portfolio.project'].search([], limit=12)
        return {
            'tags': [{'id': t.id, 'name': t.name} for t in tags],
            'projects': [{
                'id': p.id,
                'name': p.name,
                'description': p.description or '',
                'website_url': p.website_url or '#',
                'image_url': f"/web/image/portfolio.project/{p.id}/image_1920",
                'tag_ids': p.tag_ids.ids
            } for p in projects]
        }

    @http.route('/website/contact/form', type='http', auth="public", methods=['POST'], website=True,
                csrf=False, captcha='website_form')
    def website_contact_form(self, **kwargs):
        """Handle the contact form submission."""
        description = ""
        newsletter = True if kwargs.get("newsletter", 'on') == 'on' else False
        if kwargs.get('name'):
            description += f"Name: {kwargs.get('name')}<br>"
        if kwargs.get('company'):
            description += f"Company: {kwargs.get('company')}<br>"
        if kwargs.get("discuss"):
            description = f"Discuss: {kwargs.get('discuss')}<br>"
        if kwargs.get('timeline'):
            description += f"Timeline: {kwargs.get('timeline')}<br>"
        if kwargs.get('authority'):
            description += "User authorized us to process their personal data.<br>"
        if kwargs.get('source'):
            description += f"Source: {kwargs.get('source')}<br>"
        if kwargs.get('description'):
            description += f"Message: {kwargs.get('description')}<br>"
        subject = f'"{kwargs.get("company")}\'s form submission" {kwargs.get("email_from")}' \
            if kwargs.get('company') else f'"{kwargs.get("email_from")}\'s form submission"'
        body_html = f"This message has been posted on your website!<br>___________<br><br> {description}"
        val = {
            "email_from": kwargs.get("email_from"),
            "subject": subject,
            "reply_to": kwargs.get("email_from"),
            "email_to": kwargs.get("email_to"),
            "body_html": body_html
        }
        request.env['mail.mail'].with_user(SUPERUSER_ID).with_context(
            mail_create_nosubscribe=newsletter,
        ).create(val).send()

        return request.redirect('/contactus-thank-you')
