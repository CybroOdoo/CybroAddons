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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import http, fields
from odoo.http import request

class UniversityWebsite(http.Controller):

    @http.route('/apply', website=True, type='http', auth='public', csrf=False)
    def apply_page(self, **kw):
        """Render the university application page."""
        return request.render('theme_university.university_apply_page')

    @http.route('/academics', website=True, type='http', auth='public', csrf=False)
    def academics_page(self, **kw):
        """Render the academics overview page."""
        return request.render('theme_university.university_academics_page')

    @http.route('/events', website=True, type='http', auth='public', csrf=False)
    def events_page(self, **kw):
        """Render the upcoming university events page."""
        Event = request.env['event.event'].sudo()
        events = Event.search([('date_end', '>=', fields.Datetime.now())], order='date_begin', limit=10)
        return request.render('theme_university.university_events_page', {'events': events})

    @http.route('/campus-life', website=True, type='http', auth='public', csrf=False)
    def campus_life_page(self, **kw):
        """Render the campus life page."""
        return request.render('theme_university.university_campus_life_page')

    @http.route('/research', website=True, type='http', auth='public', csrf=False)
    def research_page(self, **kw):
        """Render the research page."""
        return request.render('theme_university.university_research_page')

    @http.route('/about', website=True, type='http', auth='public', csrf=False)
    def about_page(self, **kw):
        """Render the about page."""
        return request.render('theme_university.university_about_page')

    @http.route('/academics/undergraduate', website=True, type='http', auth='public', csrf=False)
    def undergraduate_page(self, **kw):
        """Render the undergraduate programs page."""
        return request.render('theme_university.university_undergraduate_page')

    @http.route('/academics/graduate', website=True, type='http', auth='public', csrf=False)
    def graduate_page(self, **kw):
        """Render the graduate programs page."""
        return request.render('theme_university.university_graduate_page')

    @http.route('/academics/online-learning', website=True, type='http', auth='public', csrf=False)
    def online_learning_page(self, **kw):
        """Render the online learning page."""
        return request.render('theme_university.university_online_page')

    @http.route('/research/centers', website=True, type='http', auth='public', csrf=False)
    def research_centers_page(self, **kw):
        """Render the research centers page."""
        return request.render('theme_university.university_research_centers_page')

    @http.route('/campus-life/housing-dining', website=True, type='http', auth='public', csrf=False)
    def housing_dining_page(self, **kw):
        """Render the housing and dining page."""
        return request.render('theme_university.university_housing_dining_page')

    @http.route('/campus-life/clubs-orgs', website=True, type='http', auth='public', csrf=False)
    def clubs_orgs_page(self, **kw):
        """Render the clubs and organizations page."""
        return request.render('theme_university.university_clubs_orgs_page')

    @http.route('/campus-life/athletics', website=True, type='http', auth='public', csrf=False)
    def athletics_page(self, **kw):
        """Render the athletics page."""
        return request.render('theme_university.university_athletics_page')

    @http.route('/campus-life/health-wellness', website=True, type='http', auth='public', csrf=False)
    def health_wellness_page(self, **kw):
        """Render the health and wellness page."""
        return request.render('theme_university.university_health_wellness_page')

    @http.route('/rebuild_menus', type='http', auth='user', website=True)
    def rebuild_university_menus(self, **kw):
        """Rebuild the university website navigation menus."""
        website = request.env['website'].get_current_website()
        main_menu = website.menu_id
        if not main_menu:
            return "Error: Website has no main menu configured."
        menu_env = request.env['website.menu'].sudo()
        
        # Helper to create menu
        def _create_menu(name, url, parent, seq):
            # Check if it exists to avoid duplicates
            existing = menu_env.search([('name', '=', name), ('url', '=', url), ('website_id', '=', website.id)])
            if existing:
                existing.write({'parent_id': parent.id, 'sequence': seq})
                return existing[0]
            return menu_env.create({
                'name': name,
                'url': url,
                'parent_id': parent.id,
                'sequence': seq,
                'website_id': website.id,
            })
        # Create Home if missing
        _create_menu('Home', '/', main_menu, 10)

        # Academics
        academics = _create_menu('Academics', '/academics', main_menu, 20)
        _create_menu('Academics', '/academics', academics, 10)
        _create_menu('Graduate', '/academics/graduate', academics, 20)
        _create_menu('Undergraduate', '/academics/undergraduate', academics, 30)
        _create_menu('Online Learning', '/academics/online-learning', academics, 40)
        _create_menu('Research Centers', '/research/centers', academics, 50)

        # Campus Life
        campus = _create_menu('Campus Life', '/campus-life', main_menu, 30)
        _create_menu('Campus Life', '/campus-life', campus, 10)
        _create_menu('Housing & Dining', '/campus-life/housing-dining', campus, 20)
        _create_menu('Health & Wellness', '/campus-life/health-wellness', campus, 30)
        _create_menu('Clubs & Organizations', '/campus-life/clubs-orgs', campus, 40)
        _create_menu('Athletics', '/campus-life/athletics', campus, 50)

        # Research, About, Events
        _create_menu('Research', '/research', main_menu, 40)
        _create_menu('About', '/about', main_menu, 50)
        _create_menu('Events', '/events', main_menu, 60)

        # Contact
        _create_menu('Contact Us', '/contactus', main_menu, 70)

        # Remove native Odoo events menu to avoid duplication
        native_events = menu_env.search([('url', '=', '/event'), ('website_id', 'in', (website.id, False))])
        if native_events:
            native_events.unlink()

        return "Menus successfully rebuilt! Please go back to your homepage."