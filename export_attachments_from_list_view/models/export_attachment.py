# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Mohammed Dilshad Tk (odoo@cybrosys.com)
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
from odoo import api, fields, models


class ExportAttachment(models.Model):
    """Create an export attachment dynamic action"""
    _name = 'export.attachment'
    _description = 'Export Attachment'
    _rec_name = 'action_name'

    action_name = fields.Char(string='Action Name',
                              help='Add the document export action name.',
                              required=True)
    applied_model_id = fields.Many2one('ir.model',
                                       string="Applies To",
                                       help='Select the model in which you '
                                            'want to apply this action.',
                                       )
    enabled_value = fields.Boolean(string="Create Action",
                                   help="Enabling and hiding the"
                                        "Create Action button", default=True,
                                   copy=False)
    states = fields.Selection([('draft', 'Draft'),
                               ('running', 'Running'), ('cancel', 'Cancelled')],
                              string='State', help='State of the action',
                              default="draft", copy=False)
    created_action_names = fields.Char(string="Created Action Names",
                                       compute="_compute_created_action_names",
                                       help='If the name is visible to the line'
                                            ' its created the action. If its '
                                            'not its deleted the action',)

    @api.depends('action_name')
    def _compute_created_action_names(self):
        """Computation of adding the action names"""
        for attachments in self:
            actions = self.env['ir.actions.act_window'].search(
                [('name', '=', attachments.action_name)])
            attachments.created_action_names = ', '.join(actions.mapped('name'))

    def action_create(self):
        """When clicking the Add Action button to crete the action in
                appropriate model"""
        self.enabled_value = False
        self.states = 'running'
        self.env['ir.actions.act_window'].create({
            'name': self.action_name,
            'res_model': 'attachment.download.confirmation',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'binding_model_id': self.env['ir.model']._get(
                self.applied_model_id.model).id,
            'target': 'new',
            'view_id':
                self.env.ref('export_attachments_from_list_view.'
                             'attachment_download_confirmation_view_form').id,
            'binding_view_types': 'list'
        })

    def action_unlink(self):
        """ Remove the contextual actions created for the server actions. """
        self.states = 'cancel'
        for attachment in self:
            actions = self.env['ir.actions.act_window'].search(
                [('name', '=', attachment.action_name)])
            actions.unlink()
        self.enabled_value = True
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
