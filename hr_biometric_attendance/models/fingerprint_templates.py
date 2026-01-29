# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
from odoo import fields, models


class FingerprintTemplates(models.Model):
    """Inherit the model to add field"""
    _name = 'fingerprint.templates'
    _description = 'Finger Print Templates for Employee'

    employee_id = fields.Many2one('hr.employee', string='Employee',
                                  help='The Employee ')
    finger_id = fields.Char(string='Finger Id',
                            help='The Number that refers the Finger')
    filename = fields.Char(string='Finger File Name',
                           help='File Name of the Uploaded Finger Print')
    finger_template = fields.Binary(string='Finger Template',
                                    help='The Uploaded Finger Print file')
