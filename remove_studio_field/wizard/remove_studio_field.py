# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    This program is under the terms of the Odoo Proprietary License v1.0
#    (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NON INFRINGEMENT. IN NO EVENT SHALL
#    THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,DAMAGES OR OTHER
#    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,ARISING
#    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
###############################################################################
"""
The module helps to remove fields added from Odoo UI or Studio.
"""
import logging

from odoo import fields, models, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class RemoveStudioField(models.TransientModel):
    """
    Wizard to select studio fields(x_studio_) and remove them.
    Methods:
        action_remove_studio_field():
            Delete the selected studio fields.
    """
    _name = 'remove.studio.field'
    _description = 'Remove Studio Fields'

    field_ids = fields.Many2many(
        'ir.model.fields', string='Studio Fields', required=True,
        domain="[('name', 'like', 'x_studio_')]",
        help='You can select the fields which are added through Odoo Studio.')

    def action_remove_studio_field(self):
        """ Search for the selected fields(x_studio_) in views. If any of the
        field is used in any view an error is thrown with the fields and
        corresponding views. If the selected fields are not used in any views,
        remove them.
        Raises: UserError: If any of the selected fields is/are still present
        in any view.
        Returns:
            dict: dictionary to show the success notification.
        """
        error_popup_message = ''
        for field in self.field_ids:
            # Broaden search to all views to catch usage in related fields/paths
            domain = [('arch_db', 'like', field.name)]
            views = self.env['ir.ui.view'].search(domain)
            
            if views:
                error_popup_message = '\n'.join([
                    error_popup_message,
                    _('Field: %s', field.display_name),
                    _('Views: %s') % ', '.join(views.mapped('display_name'))
                ])

        if error_popup_message:
            raise UserError('\n'.join([
                _("Cannot delete the fields that are still present in views:"),
                error_popup_message,
                _("\nPlease remove these fields from the views above before attempting to delete them.")
            ]))

        # Using ORM unlink is safer as it handles registry cleanup and 
        # additional Odoo integrity checks.
        try:
            self.field_ids.unlink()
        except Exception as error:
            raise UserError(f'An error occurred! {error}') from error
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('The selected fields are deleted.'),
                'sticky': False,
                'type': 'success',
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }
