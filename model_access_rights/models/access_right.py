# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#    Author: Rahul CK(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO GENERAL
#    PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC
#    LICENSE (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from odoo import api, fields, models


class AccessRight(models.Model):
    """This class is used to detect, which all options want to hide from the
    specified group and model"""
    _name = 'access.right'
    _inherit = 'mail.thread'
    _description = 'Manage Modules Access Control'
    _rec_name = 'model_id'

    model_id = fields.Many2one('ir.model', ondelete='cascade',
                               required=True, string="Model",
                               help="Select the model")
    groups_id = fields.Many2one('res.groups', required=True,
                                string="Groups", help="Select the group")
    is_delete = fields.Boolean(string="Delete", help="Hide the delete option")
    is_export = fields.Boolean(string="Export",
                               help="Hide the 'Export All'"
                                    " option from list view")
    is_create_or_update = fields.Boolean(string="Create/Update",
                                         help="Hide the create option "
                                              "from list as well as form view")
    is_archive = fields.Boolean(string="Archive/UnArchive",
                                help="Hide the archive option")

    @api.model
    def hide_buttons(self, args):
        """Returns the visibility settings for buttons per model and group."""
        user = self.env['res.users'].browse(args[0])
        model_name = args[1]
        access_right_rec = self.sudo().search_read([
            ('model_id.model', '=', model_name),
            ('groups_id', 'in', user.groups_id.ids)
        ], ['is_delete', 'is_export', 'is_create_or_update', 'is_archive'])

        if access_right_rec:
            rec = access_right_rec[0]  # If multiple, first match wins
            return {
                'is_delete': rec['is_delete'],
                'is_export': rec['is_export'],
                'is_create_or_update': rec['is_create_or_update'],
                'is_archive': rec['is_archive']
            }
        return {
            'is_delete': False,
            'is_export': False,
            'is_create_or_update': False,
            'is_archive': False
        }

