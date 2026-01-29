# -*- coding: utf-8 -*-
###################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2019-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Noushid Khan.P (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###################################################################################
from odoo import models, fields


class SendgridEmailTemplate(models.Model):
    """Creates the model sendgrid.email.template to create the email templates
    that needs to be sent through the send grid"""
    _name = "sendgrid.email.template"
    _rec_name = "temp_name"
    _description = "Sendgrid Email Template"

    temp_name = fields.Char(string="Template Name", required=True)
    ver_subject = fields.Char(string="Template Subject", required=True)
    temp_cont = fields.Html(string="Template Content",
                            help="content convert to html code", translate=True,
                            sanitize=False)