# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Arjun S(odoo@cybrosys.com)
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
###############################################################################
from odoo import fields, models


class DripTemplate(models.Model):
    """Creates the drip.template model"""
    _name = 'drip.template'
    _description = 'Drip Template'

    name = fields.Char(string="Subject", help="Subject of the template",
                       required=True)
    mail_body = fields.Html(string='Mail Body',
                            help="Mail body to send to the customer")
    attachment_ids = fields.Many2many('ir.attachment', string='Attachment',
                                      help='Attachments to be sent along with '
                                           'template')
    company_id = fields.Many2one('res.company', string="Company",
                                 help="Current company",
                                 default=lambda self: self.env.company)
