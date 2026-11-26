# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
###############################################################################
from odoo import fields, models


class PrinterDetails(models.Model):
    """Model storing details of synchronized PrintNode printers."""
    _name = "printer.details"
    _description = "Printer Details"
    _rec_name = 'printers_name'

    id_of_printer = fields.Char(string="Printer ID", help="Identifier of the printer in PrintNode.")
    printers_name = fields.Char(string="Printer Name", help="Name of the printer in PrintNode.")
    printer_description = fields.Char(string="Printer Description",
                                      help="Description of the printer reported by PrintNode.")
    state = fields.Char(string="Status", help="Current operational status of the printer.")
