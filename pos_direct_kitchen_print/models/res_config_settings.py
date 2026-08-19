# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
import logging

from odoo import fields, models
from odoo.tools.translate import _
from printnodeapi.auth import ApiError, NetworkError
from printnodeapi.gateway import Gateway

_logger = logging.getLogger(__name__)


class ResConfigSettings(models.TransientModel):
    """
    This class is Inheriting the model res.config.setting.
    add some extra fields and functions for the model.
    Methods:
    get_values(self): super the  function for getting the printer details.
    set_values(self): super the  function for setting the printer details
    action_check_printers(self): checking the available printers in the system
    """
    _inherit = 'res.config.settings'

    api_key_print_node = fields.Char(string="API Key",
                                     config_parameter='pos_direct_kitchen_print.api_key_print_node',
                                     help='API Key of the print-node')
    available_printers_id = fields.Many2one('printer.details',
                                            string="Available Printers",
                                            config_parameter='pos_direct_kitchen_print.available_printers_id',
                                            help='Available printers',
                                            readonly=False)

    def _printer_notification(self, message, notification_type='warning'):
        """Return a client notification for printer check feedback."""
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('PrintNode Printer Check'),
                'message': message,
                'type': notification_type,
                'sticky': notification_type in ('danger', 'warning'),
            }
        }

    def action_check_printers(self):
        """Check the available printer"""
        print_node_api = self.api_key_print_node
        if not print_node_api:
            return self._printer_notification(
                _('Please provide a PrintNode API Key first.'))

        try:
            gateway = Gateway(url="https://api.printnode.com",
                              apikey=print_node_api)
            computers = gateway.computers()
            if not computers:
                return self._printer_notification(_(
                    'No computers found in your PrintNode account. Please '
                    'connect a computer first.'))

            computer_id = int(computers[0].id)
            printers = gateway.printers(computer=computer_id)
            if not printers:
                return self._printer_notification(
                    _('No printers found for the connected computer.'))

            for printer in printers:
                prints = self.env['printer.details'].search(
                    [('id_of_printer', '=', printer.id)])
                if not prints:
                    self.env['printer.details'].create({
                        'id_of_printer': printer.id,
                        'printers_name': printer.name,
                        'printer_description': printer.description,
                        'state': printer.state,
                    })
            return self._printer_notification(
                _('Available printers have been checked successfully.'),
                notification_type='success')
        except (ApiError, NetworkError) as error:
            _logger.warning("PrintNode printer check failed: %s", error)
            return self._printer_notification(
                _('Connection failed: %s') % str(error),
                notification_type='danger')
        except (TypeError, ValueError) as error:
            _logger.warning("Invalid PrintNode printer response: %s", error)
            return self._printer_notification(
                _('Invalid response received from PrintNode.'),
                notification_type='danger')
