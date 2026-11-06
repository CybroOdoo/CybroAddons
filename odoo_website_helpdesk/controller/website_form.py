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
#############################################################################
import json
import logging

from odoo import http
from odoo.exceptions import UserError, ValidationError
from odoo.http import request

from odoo.addons.website.controllers.form import WebsiteForm

_logger = logging.getLogger(__name__)


class WebsiteFormInherit(WebsiteForm):
    """Create a helpdesk ticket from the website form"""

    # An empty @http.route() keeps the routes of the parent method
    # (/website/form/<model_name>, csrf and captcha settings).
    @http.route()
    def website_form(self, model_name='', **kwargs):
        """Create the ticket of the helpdesk form"""
        if model_name != 'ticket.helpdesk':
            return super().website_form(model_name=model_name, **kwargs)
        try:
            with request.env.cr.savepoint():
                ticket = self._create_helpdesk_ticket(kwargs)
        except (ValidationError, UserError) as error:
            return self._json_response(
                {'error': str(error.args[0] if error.args else error)})
        except Exception:
            _logger.exception("Helpdesk website form failed")
            return self._json_response({'error': self.env._(
                'The ticket could not be created. Please try again or '
                'contact us.')})
        request.session['ticket_number'] = ticket.name
        request.session['ticket_id'] = ticket.id
        request.session['form_builder_model_model'] = 'ticket.helpdesk'
        request.session['form_builder_model'] = 'Helpdesk Ticket'
        request.session['form_builder_id'] = ticket.id
        return self._json_response({'id': ticket.id})

    def _json_response(self, data):
        """JSON answer read by the website form"""
        return request.make_response(
            json.dumps(data),
            headers=[('Content-Type', 'application/json')])

    def _get_record_ids(self, model, value):
        """Ids of the existing records among the posted ids"""
        values = value if isinstance(value, list) else [value]
        ids = [int(item) for text in values
               for item in str(text or '').split(',') if item.strip().isdigit()]
        return request.env[model].sudo().browse(ids).exists()

    def _get_ticket_partner(self, kwargs):
        """The logged in customer, or the contact of the email"""
        if not request.env.user._is_public():
            return request.env.user.partner_id
        email = (kwargs.get('email_from') or '').strip()
        if not email:
            raise UserError(self.env._('Please enter your email address.'))
        partner = request.env['res.partner'].sudo().search(
            [('email', '=ilike', email)], limit=1)
        return partner or request.env['res.partner'].sudo().create({
            'name': kwargs.get('customer_name') or email,
            'phone': kwargs.get('phone'),
            'email': email,
        })

    def _create_helpdesk_ticket(self, kwargs):
        """Create the ticket and its attachments"""
        if not (kwargs.get('subject') or '').strip() or not (
                kwargs.get('description') or '').strip():
            raise UserError(self.env._('Please enter the subject and the '
                                       'description of your ticket.'))
        partner = self._get_ticket_partner(kwargs)
        vals = {
            'customer_name': kwargs.get('customer_name'),
            'subject': kwargs.get('subject'),
            'description': kwargs.get('description'),
            'email': kwargs.get('email_from') or partner.email,
            'phone': kwargs.get('phone'),
            'customer_id': partner.id,
            'ticket_type_id': self._get_record_ids(
                'helpdesk.type', kwargs.get('ticket_type_id'))[:1].id,
            'category_id': self._get_record_ids(
                'helpdesk.category', kwargs.get('category'))[:1].id,
        }
        if kwargs.get('priority') in ('0', '1', '2', '3', '4'):
            vals['priority'] = kwargs['priority']
        if request.env['ir.config_parameter'].sudo().get_bool(
                'odoo_website_helpdesk.product_website'):
            products = self._get_record_ids(
                'product.template',
                request.httprequest.form.getlist('product')
                or kwargs.get('product')).filtered('sale_ok')
            vals['product_ids'] = [(6, 0, products.ids)]
        ticket = request.env['ticket.helpdesk'].sudo().create(vals)
        files = request.httprequest.files
        for key, attachment in files.items(multi=True):
            if key.startswith('ticket_attachment') and attachment.filename:
                request.env['ir.attachment'].sudo().create({
                    'name': attachment.filename,
                    'res_model': 'ticket.helpdesk',
                    'res_id': ticket.id,
                    'type': 'binary',
                    'raw': attachment.read(),
                })
        return ticket
