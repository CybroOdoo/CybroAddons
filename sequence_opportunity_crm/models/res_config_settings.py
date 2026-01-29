# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Ranjith R(odoo@cybrosys.com)
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

###############################################################################
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """
    This class extends the`res.config.settings` and add a boolean field
    """
    _inherit = "res.config.settings"

    sequence_create = fields.Boolean(
        "Creates Automatic Sequence Numbers for CRM Opportunity",
        config_parameter="sequence_opportunity_crm.sequence_create",
        store=True, default=False, help="Creates unique code "
                                        "for each opportunity")
