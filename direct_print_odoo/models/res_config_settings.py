# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gokul P I (odoo@cybrosys.com)
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
from ast import literal_eval
from printnodeapi.gateway import Gateway
from odoo import api, fields, models ,_
from odoo.exceptions import ValidationError


class ResConfigSettings(models.TransientModel):
    """This class is Inheriting the model res.config.setting.
     add some extra fields and functions for the model.
    Methods:
    get_values(self):
            super the  function for getting the printer details.
    set_values(self):
            super the  function for setting the printer details
    action_check_printers(self):
            checking the available printers in the system"""
    _inherit = 'res.config.settings'

    api_key_print_node = fields.Char(string="API Key",
                                     help='API Key of the printnode')
    available_printers_id = fields.Many2one('printer.details',
                                            config_parameter='direct_print_odoo'
                                                             '.available_printers_id')
    printers_ids = fields.Many2many('printer.details',
                                    string='Printers Details',
                                    help='Printers Details')
    multiple_printers = fields.Boolean(string='Multiple Printers',
                                       help='Enable if you have Multiple '
                                            'Printers',
                                       config_parameter='direct_print_odoo'
                                                        '.multiple_printers')
    @api.model
    def get_values(self):
        """Get the values in the config"""
        res = super(ResConfigSettings, self).get_values()
        res['api_key_print_node'] = self.env[
            'ir.config_parameter'].sudo().get_param('api_key_print_node')
        res['printers_ids'] = self.env[
            'ir.config_parameter'].sudo().get_param(
            'direct_print_odoo.printers_ids')
        params = self.env['ir.config_parameter'].sudo()
        printers_ids = params.get_param('direct_print_odoo.printers_ids',
                                        default=False)
        if printers_ids:
            res.update(
                printers_ids=literal_eval(printers_ids)
            )
        else:
            res.update(
                printers_ids=False
            )
        return res

    @api.model
    def set_values(self):
        """Set the values in the config"""
        self.env['ir.config_parameter'].sudo().set_param('api_key_print_node',
                                                         self.api_key_print_node)
        self.env['ir.config_parameter'].sudo().set_param(
            'direct_print_odoo.printers_ids',
            self.printers_ids.ids)
        super(ResConfigSettings, self).set_values()

    def action_check_printers(self):
        """Check the available printer"""
        print_node_api = self.env['ir.config_parameter'].sudo().get_param(
            'api_key_print_node')
        try:
            gateway = Gateway(url="https://api.printnode.com", apikey=print_node_api)
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
                        raise ValidationError(_('Printer already exists'))
            else:
                raise ValidationError(_('Please Connect a Computer First '))
        except Exception:
            raise ValidationError(_("Please provide valid credentials"))
