# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Hridhya D (<https://www.cybrosys.com>)
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
from odoo import fields, models


class VisaApplication(models.Model):
    """This class VisaApplication is to view applied Visa"""
    _name = 'visa.application'
    _description = 'Visa Application'

    name = fields.Char(string='name', readonly=True, help="Name")
    visa_approvals_ids = fields.One2many('visa.approval',
                                         'visa_application_no_id',
                                         string="Visa Approvals",
                                         readonly=True, help="Visa Approvals")
    company_id = fields.Many2one('res.company', string='Company',
                                 help="If set, corresponding record are shown "
                                      "for this specific company")
