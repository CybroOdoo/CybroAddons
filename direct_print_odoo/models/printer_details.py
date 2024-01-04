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


class PrinterPrint(models.Model):
    """This class is created for model printer.details. It contains fields
    for the model"""
    _name = "printer.details"
    _description = "Printer Details"
    _rec_name = 'printers_name'

    id_of_printer = fields.Char(string="Printer ID", help="id of printer")
    printers_name = fields.Char(string="Printer Name", help="name of printer")
    printer_description = fields.Char(string="Printer Description",
                                      help="description of printer")
    state = fields.Char(string="Status", help="status of printer")
