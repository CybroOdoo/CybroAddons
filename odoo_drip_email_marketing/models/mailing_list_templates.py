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


class MailingListTemplates(models.Model):
    """Creates the model mailing.list.templates"""
    _name = 'mailing.list.templates'
    _description = 'Mailing list templates'

    name = fields.Char(string="Name", help="Name of the mailing list template")
    days_after = fields.Integer(string="Days After",
                                help="Number of days after which the "
                                     "template will be send")
    template_id = fields.Many2one('drip.template', string="Drip Template",
                                  help="The template to be sent")
    mailing_id = fields.Many2one('mailing.list', string="Mailing List",
                                 help="Mailing list")
