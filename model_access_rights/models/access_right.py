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
    groups_id = fields.Many2one('res.groups', string="Groups",
                                required=True, help="Select the group")
    is_delete = fields.Boolean(string="Delete", help="Hide the delete option")
    is_export = fields.Boolean(string="Export",
                               help="Hide the 'Export All'"
                                    " option from list view")
    is_create_or_update = fields.Boolean(string="Create/Update",
                                         help="Hide the create option from "
                                              "list as well as form view")
    is_archive = fields.Boolean(string="Archive/UnArchive",
                                help="Hide the archive option")

    @api.model
    def hide_buttons(self, args):
        """This function contains a query  that detects which all options want
        to hide, in which model,and to which user groups"""
        access_right_rec = self.sudo().search_read([],
                                                   ['model_id', 'is_delete',
                                                    'is_export',
                                                    'is_create_or_update',
                                                    'is_archive',
                                                    'groups_id'])
        for rec in access_right_rec:
            model_id = self.env['ir.model'].sudo(). \
                browse(rec['model_id'][0]).model
            if str(model_id) == args[1]:
                groups = self.env['res.users'].browse(args[0]).groups_id.ids
                if rec['groups_id'][0] in groups:
                    data = {
                        'is_delete': rec['is_delete'],
                        'is_export': rec['is_export'],
                        'is_create_or_update': rec['is_create_or_update'],
                        'is_archive': rec['is_archive']
                    }
                    return data
