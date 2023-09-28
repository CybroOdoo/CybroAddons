# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Rahul C K (odoo@cybrosys.com)
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
###############################################################################
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """This is for validating the birthdate"""
    _inherit = 'res.config.settings'

    birthday_discount = fields.Boolean(string="Birthday Discount",
                                       related="pos_config_id."
                                               "birthday_discount",
                                       help="Enable this field to enable "
                                            "birthday discount feature",
                                       readonly=False)
    discount = fields.Float(string="Discount",
                            help="Percentage of birthday discount",
                            related="pos_config_id.discount", readonly=False)
    first_order = fields.Boolean(string="Only Apply the discount on the first "
                                        "order on Birthday",
                                 help="Restrict discount to apply only on "
                                      "first order on birthday",
                                 related="pos_config_id.first_order",
                                 readonly=False)
