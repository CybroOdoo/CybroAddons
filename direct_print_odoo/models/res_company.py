# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gokul P I (odoo@cybrosys.com)
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


class ResCompany(models.Model):
    """Inheriting this class to add the Print-node credential need in config
            settings and use the multi company feature"""
    _inherit = 'res.company'

    api_key_print_node = fields.Char(string="API Key",
                                     help='API Key of the print-node')
    available_printers_id = fields.Many2one('printer.details',
                                            string='Available Printers',
                                            help='Available printers in the '
                                                 'connected computer',
                                            config_parameter='direct_print_odoo'
                                                             '.available_printers_id')
    printers_ids = fields.Many2many('printer.details',
                                    string='Printers Details',
                                    help='Multiple Printers can connect and '
                                         'print')
    multiple_printers = fields.Boolean(string='Multiple Printers',
                                       help='Enable if you have Multiple '
                                            'Printers',
                                       config_parameter='direct_print_odoo'
                                                        '.multiple_printers')
