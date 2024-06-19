# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Ranjith R(<https://www.cybrosys.com>)
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
###########################################################################
from odoo import http, fields
from odoo.http import request


class WebsiteForm(http.Controller):
    """ Class to create a routes to website form for labor supply creation"""

    @http.route(['/labour_supply'], type='http', auth='user',
                website=True)
    def labour_supply(self):
        """ Function to render template to website"""
        if request.env.user._is_admin():
            customers = request.env['res.users'].sudo().search([])
        else:
            customers = request.env.user
        values = {'customer': customers}
        return request.render(
            'manpower_supply_management.online_labour_supply_form', values)

    @http.route(['/labour_supply/submit'], type='http', auth='user',
                website=True)
    def create_labour_supply(self, **post):
        """ Function to render template and pass value to website"""
        if (post.get('from_date') > post.get('to_date') or post.get(
                'from_date') < str(fields.Date.today()) or
                post.get('from_date') < str(fields.Date.today())):
            if request.env.user._is_admin():
                customers = request.env['res.users'].sudo().search([])
            else:
                customers = request.env.user
            values = {'customer': customers, 'alert': True}
            return request.render(
                'manpower_supply_management.online_labour_supply_form', values)
        else:
            skills = request.env['skill.details'].sudo().search([])
            order = request.env['labour.supply'].sudo().create({
                'customer_id': post.get('customer_id'),
                'from_date': post.get('from_date'),
                'to_date': post.get('to_date')
            })
            return request.render(
                'manpower_supply_management.labour_on_supply_form'
                , {'labour_supplies': order, 'skills': skills})

    @http.route(['/labour_on_supply/add'], type='http', auth='user',
                website=True)
    def create_labour_on_supply(self, **post):
        """ Function to render template and pass value to website"""
        if (post.get('from_date') > post.get('to_date') or post.get(
                'from_date') < str(fields.Date.today()) or
                post.get('from_date') < str(fields.Date.today())):
            skills = request.env['skill.details'].sudo().search([])
            order = request.env['labour.supply'].sudo().browse(
                int(post.get('labour_supply')))
            return request.render(
                'manpower_supply_management.labour_on_supply_form'
                , {'labour_supplies': order, 'skills': skills, 'alert': True})
        else:
            skills = request.env['skill.details'].sudo().search([])
            request.env['labour.on.skill'].sudo().create({
                'skill_id': post.get('skill'),
                'from_date': post.get('from_date'),
                'to_date': post.get('to_date'),
                'number_of_labour_required': post.get('required_number'),
                'labour_supply_id': post.get('labour_supply')})
            labour_supply_record = request.env['labour.supply'].sudo().browse(
                int(post.get('labour_supply')))
            return request.render(
                'manpower_supply_management.labour_on_supply_form',
                {'labour_supplies': labour_supply_record, 'skills': skills})

    @http.route(['/labour_on_supply/complete'], type='http', auth='user',
                website=True)
    def create_labour_on_supply_completed(self):
        """ Function to render template to website"""
        return request.render("manpower_supply_management.tmp_form_success")
