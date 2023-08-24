# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Anfas Faisal K (odoo@cybrosys.info)
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
    """
    This transient model inherits from res.config.settings and adds a boolean
    field `show_create_task` that is used as a configuration parameter to
    control whether the "Create Task" button is visible on the website
    helpdesk page. The`config_parameter` attribute specifies the name
    of the corresponding configuration parameter in the database.
    """
    _inherit = 'res.config.settings'

    show_create_task = fields.Boolean(
        string="Create Tasks",
        config_parameter='odoo_website_helpdesk.show_create_task',
        help='Whether to show the "Create Task" button on the website helpdesk '
             'page. This field is used as a configuration parameter to control '
             'whether the button is visible or not.')
