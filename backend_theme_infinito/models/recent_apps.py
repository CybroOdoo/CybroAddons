# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo import api,fields, models


class RecentApps(models.Model):
    """
    Model representing recent applications accessed by users in the system.
    """

    _name = 'recent.apps'
    _description = 'Recent Apps'

    name = fields.Char(compute='_compute_icon', store=True)
    app_id = fields.Integer()
    icon = fields.Binary(compute='_compute_icon', store=True)
    type = fields.Char(compute='_compute_type', store=True)
    user_id = fields.Many2one('res.users')

    @api.depends('app_id')
    def _compute_type(self):
        """
        Compute method to determine the type of the recent app based on its
        associated menu.

        This method computes the type of the recent app by retrieving its
        associated menu,
        extracting the type information from the menu's web icon, and
        updating the 'type'
        field accordingly.

        """
        menu_ui = self.env['ir.ui.menu']
        for rec in self:
            app = menu_ui.browse(rec.app_id)
            la = str(app.web_icon)
            spl_word = '.'
            res = la.split(spl_word, 1)
            if len(res) > 1:
                splitString = res[1]
                rec.type = splitString
            else:
                # Handle the case where splitting doesn't result in two parts
                # You might want to set a default value or raise an error, depending on your requirements
                # For now, I'll set rec.type to an empty string
                rec.type = ""

    @api.depends('app_id')
    def _compute_icon(self):
        """
       Compute method to determine the icon for the recent app based on its associated menu.

       This method computes the icon for the recent app by retrieving its associated menu,
       extracting the icon information from the menu's web icon, and updating the 'icon'
       field accordingly. It also updates the 'name' field with the name of the associated menu.

       """
        menu_ui = self.env['ir.ui.menu']
        for rec in self:
            app = menu_ui.browse(rec.app_id)
            rec.icon = app._compute_web_icon_data(app.web_icon)
            rec.name = app.name
