# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2020-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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

from odoo import models,fields, api, _


class BlastConfiguration(models.Model):
    _name = 'blast.configuration'

    name = fields.Char('Name')
    best_deal = fields.Many2one('product.product')
    date_start = fields.Datetime(string='Start Date',
                                 default=fields.Datetime.now())
    date_end = fields.Datetime(string='End Date')
    best_products = fields.Many2many('product.product')
    asked_questions_ids = fields.One2many('asked.questions',
                                          'blast_configuration_id',
                                          string="Asked Questions")
