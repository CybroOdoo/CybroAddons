################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Fathima Mazlin AM (odoo@cybrosys.com)
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


class ResConfigSettings(models.TransientModel):
    """"Inherited model for adding extra fields"""
    _inherit = 'res.config.settings'

    minimum_working_hour = fields.Float(string='Minimum Working Hours',
                                        help=" Set minimum working hours/day"
                                             " to notify in Email",
                                        config_parameter=
                                        "employee_less_working_"
                                        "hour_notification."
                                        "minimum_working_hour",
                                        default=0.00)
    hr_email = fields.Char(string='HR Email', default="hr@gmail.com",
                           help="  Set HR Manager's Email address to Send the"
                                " Less Hour Worked Employees list to",
                           config_parameter="employee_less_working_hour_"
                                            "notification.hr_email")
