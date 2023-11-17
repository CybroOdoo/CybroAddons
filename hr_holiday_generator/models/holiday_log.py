# -*- coding: utf-8 -*-
###############################################################################
#
#  Cybrosys Technologies Pvt. Ltd.
#
#  Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#  Author: Anusha C (odoo@cybrosys.com)
#
#  You can modify it under the terms of the GNU LESSER
#  GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#  You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#  (LGPL v3) along with this program.
#  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import fields, models


class HolidayLog(models.Model):
    """The model is for showing the holiday logs"""
    _name = "holiday.log"
    _description = "Holiday Logs"

    name = fields.Char(string="Name", help="name of the public holiday")
    start_date = fields.Datetime(string="Start Date",
                                 help="Start date of the public holiday")
    end_date = fields.Datetime(string="End Date",
                               help="End date of the public holiday")
    description = fields.Char(string="Description",
                              help="Description of the public holiday")
