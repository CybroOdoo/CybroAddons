# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Prathyunnan R (odoo@cybrosys.com)
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
from printnodeapi.gateway import Gateway
from odoo import fields, models, _
from odoo.exceptions import ValidationError


class ResConfigSettings(models.TransientModel):
    """This class is Inheriting the model res.config.setting.
     add some extra fields and functions for the model."""
    _inherit = 'res.config.settings'

    api_key_print_node = fields.Char(string="API Key",
                                     related='company_id.api_key_print_node',
                                     help='API Key of the print-node',
                                     readonly=False)
    available_printers_id = fields.Many2one('printer.details',
                                            related='company_id.available_printers_id',
                                            help='Available printers',
                                            readonly=False)
    printers_ids = fields.Many2many('printer.details',
                                    string='Printers Details',
                                    related='company_id.printers_ids',
                                    help='Printers Details', readonly=False)
    is_multiple_printers = fields.Boolean(string='Multiple Printers',
                                          help='Enable if you have Multiple '
                                               'Printers', readonly=False,
                                          related='company_id.is_multiple_printers')

    def action_check_printers(self):
        """Check the available printer"""
        print_node_api = self.env.company.api_key_print_node
        try:
            gateway = Gateway(url="https://api.printnode.com",
                              apikey=print_node_api)
            computer_id = int(gateway.computers()[0].id)
            if computer_id:
                for printer in gateway.printers(computer=computer_id):
                    prints = self.env['printer.details'].search(
                        [('id_of_printer', '=', printer.id)])
                    if not prints:
                        self.env['printer.details'].create({
                            'id_of_printer': printer.id,
                            'printers_name': printer.name,
                            'printer_description': printer.description,
                            'state': printer.state,
                        })
            else:
                raise ValidationError(_('Please Connect a Computer First '))
        except ValidationError:
            raise
        except Exception:
            raise ValidationError(_("Please provide valid credentials"))
