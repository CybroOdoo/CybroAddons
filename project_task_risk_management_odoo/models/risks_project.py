# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo import fields, models


class Risks(models.Model):
    """ Model for Risk Projects """
    _name = 'risks.project'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'risk_name'

    risk_name = fields.Char(string='Name', tracking=True, help='Risk Name')
    code = fields.Char(string='Code', tracking=True, help='Risk code')
    risk_quantification = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High')], default='low', string='Risk Quantification',
        help='Risk qualification types',
        tracking=True)
    category_id = fields.Many2one('risk.category', string='Category',
                                  help='Select Category',
                                  tracking=True)
    risk_type = fields.Many2one('risk.type', string='Risk Type', tracking=True,
                                help='Risk Type')
    risk_response = fields.Many2one('risk.response', string='Risk Response',
                                    help='Risk response',
                                    tracking=True)
    tag_ids = fields.Many2many('risk.tag', string='Tags', help='Risk tags')
    note = fields.Text(string='Internal Notes', tracking=True, help='Risk Note')
