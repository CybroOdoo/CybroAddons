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


class DripMailingHistory(models.Model):
    """Creates the model drip.mailing.history"""
    _name = 'drip.mailing.history'
    _description = 'Drip Mailing History'

    name = fields.Char(string="Name", help="Name of the drip")
    contact_id = fields.Many2one('mailing.contact', string="Contact",
                                 help="Contact of the mailing")
    mailing_id = fields.Many2one('mailing.list', string="Mailing List",
                                 help="Mailing list of mailing")
    template_id = fields.Many2one('drip.template', string="Drip Template",
                                  help="Drip Template of the mailing")
    send_date = fields.Date(string="Send Date", help="Date of the mailing")
    company_id = fields.Many2one('res.company', string="Company",
                                 help="Current company",
                                 default=lambda self: self.env.company)
