# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Anfas Faisal K (odoo@cybrosys.info)
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
import base64
import json

from psycopg2 import IntegrityError

from odoo import _
from odoo.addons.website.controllers.form import WebsiteForm
from odoo.exceptions import ValidationError
from odoo.http import request


class WebsiteForm(WebsiteForm):
    """This module extends the functionality of the website form controller
    to handle the creation of new help desk tickets. It provides a new
    controller to display a list of tickets for the current user in their
    portal, and overrides the website form controller's method for handling
    form submissions to create a new help desk ticket instead."""
    def _handle_website_form(self, model_name, **kwargs):
        """Website Help Desk Form"""
        if model_name == 'help.ticket':
            rec_val = {
                'customer_name': kwargs.get('customer_name'),
                'subject': kwargs.get('subject'),
                'description': kwargs.get('description'),
                'email': kwargs.get('email_from'),
                'phone': kwargs.get('phone'),
                'priority': kwargs.get('priority'),
                'stage_id': request.env['ticket.stage'].search(
                    [('name', '=', 'Inbox')], limit=1).id,
            }
            partner = request.env['res.users'].sudo().browse(
                request.session.uid).partner_id
            if partner:
                rec_val['customer_id'] = partner.id
            else:
                rec_val['public_ticket'] = True
            ticket_id = request.env['help.ticket'].sudo().create(rec_val)
            request.session['ticket_number'] = ticket_id.name
            request.session['ticket_id'] = ticket_id.id
            model_record = request.env['ir.model'].sudo().search(
                [('model', '=', model_name)])
            data = self.extract_data(model_record, request.params)
            if 'ticket_attachment' in request.params \
                    or request.httprequest.files or data.get('attachments'):
                attached_files = data.get('attachments')
                for attachment in attached_files:
                    attached_file = attachment.read()
                    request.env['ir.attachment'].sudo().create({
                        'name': attachment.filename,
                        'res_model': 'help.ticket',
                        'res_id': ticket_id.id,
                        'type': 'binary',
                        'datas': base64.encodebytes(attached_file),
                    })
            request.session['form_builder_model_model'] = model_record.model
            request.session['form_builder_model'] = model_record.name
            request.session['form_builder_id'] = ticket_id.id
            return json.dumps({'id': ticket_id.id})
        else:
            model_record = request.env['ir.model'].sudo().search(
                [('model', '=', model_name)])
            if not model_record:
                return json.dumps({
                    'error': _("The form's specified model does not exist")
                })
            try:
                data = self.extract_data(model_record, request.params)
            # If we encounter an issue while extracting data
            except ValidationError as error:
                return json.dumps({'error_fields': error.args[0]})
            try:
                id_record = self.insert_record(request, model_record,
                                               data['record'], data['custom'],
                                               data.get('meta'))
                if id_record:
                    self.insert_attachment(model_record, id_record,
                                           data['attachments'])
                    # in case of an email, we want to send it immediately
                    # instead of waiting for the email queue to process
                    if model_name == 'mail.mail':
                        request.env[model_name].sudo().browse(id_record).send()
            # Some fields have additional SQL constraints that we can't check
            # generically Ex: crm.lead.probability which is a float between 0
            # and 1 TODO: How to get the name of the erroneous field ?
            except IntegrityError:
                return json.dumps(False)
            request.session['form_builder_model_model'] = model_record.model
            request.session['form_builder_model'] = model_record.name
            request.session['form_builder_id'] = id_record
            return json.dumps({'id': id_record})
