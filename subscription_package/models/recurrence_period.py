# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo import models, fields


class RecurrencePeriod(models.Model):
    """This class is used to create new model recurrence period"""
    _name = "recurrence.period"
    _description = "Recurrence Period "

    name = fields.Char(string="Name")
    duration = fields.Float(string="Duration")
    unit = fields.Selection([('hours', 'hours'),
                             ('days', 'Days'), ('weeks', 'Weeks'),
                             ('months', 'Months'), ('years', 'Years')],
                            string='Unit')


class SubPackages(models.Model):
    """ This function is used to inherit subscription packages"""
    _inherit = 'subscription.package'

    recurrence_period_id = fields.Many2one("recurrence.period",
                                           string="Recurrence Period")
