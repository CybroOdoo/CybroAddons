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
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class MapViewConfigWizard(models.TransientModel):
    """Wizard to configure and add map views to selected models and actions."""
    _name = 'map.view.config.wizard'
    _description = 'Map View Configuration Wizard'
    _rec_name = 'model_id'

    # Model and Action Selection
    model_id = fields.Many2one('ir.model', string='Model', required=True,
                               help='Select the model to add map view to')
    model_name = fields.Char(related='model_id.model', string='Model Technical Name')
    action_ids = fields.Many2many('ir.actions.act_window', string='Actions', required=True,
                                  domain="[('res_model', '=', model_name)]",
                                  help='Select one or more actions to add map view to')
    
    # Map View Configuration
    partner_field_id = fields.Many2one(comodel_name='ir.model.fields', string='Partner Field',
                                     help='Many2one field pointing to res.partner (e.g., partner_id).'
                                          'Leave empty if the model has direct latitude/longitude fields.')
    partner_field_ids = fields.Many2many('ir.model.fields', string='Available Partner Fields',
                                         compute='_compute_partner_field_ids',
                                         help='Partner fields available for the selected model')
    lat_field = fields.Char(string='Latitude Field', default='partner_latitude',
                            help='Field name for latitude (default: partner_latitude)')
    lng_field = fields.Char(string='Longitude Field', default='partner_longitude',
                            help='Field name for longitude (default: partner_longitude)')
    address_field = fields.Char(string='Address Field', default='contact_address',
                                help='Field name for address display (default: contact_address)')

    # View positioning
    view_position = fields.Selection([
        ('after_list', 'After List View'),
        ('after_form', 'After Form View'),
        ('after_kanban', 'After Kanban View'),
        ('end', 'At the End'),
    ], string='View Position', default='after_form', required=True,
       help='Where to insert the map view in the view switcher')

    @api.depends('model_id')
    def _compute_partner_field_ids(self):
        """Compute available partner fields for the selected model"""
        for record in self:
            if record.model_id:
                # Find all Many2one fields pointing to res.partner
                partner_fields = self.env['ir.model.fields'].search([
                    ('model_id', '=', record.model_id.id),
                    ('ttype', '=', 'many2one'),
                    ('relation', '=', 'res.partner')
                ])
                record.partner_field_ids = partner_fields
            else:
                record.partner_field_ids = False

    def _get_partner_field_selection(self):
        """Return selection list of partner fields"""
        if self.model_id:
            partner_fields = self.env['ir.model.fields'].search([
                ('model_id', '=', self.model_id.id),
                ('ttype', '=', 'many2one'),
                ('relation', '=', 'res.partner')
            ])
            return [(field.name, field.field_description) for field in partner_fields]
        return []

    @api.onchange('model_id')
    def _onchange_model_id(self):
        """Reset actions and partner field when model changes"""
        self.action_ids = [(5, 0, 0)]  # Clear all selections
        self.partner_field_id = False

    def action_create_map_view(self):
        """Create the map view and update the actions"""
        self.ensure_one()
        
        if not self.model_id or not self.action_ids:
            raise UserError(_('Please select both Model and at least one Action.'))
        
        # Build the map view XML
        view_arch = self._build_map_view_arch()
        
        # Create the ir.ui.view record
        view_name = f"{self.model_id.model}.map.view"
        existing_view = self.env['ir.ui.view'].search([
            ('name', '=', view_name),
            ('model', '=', self.model_id.model),
            ('type', '=', 'map')
        ], limit=1)
        
        if existing_view:
            # Update existing view
            existing_view.write({'arch': view_arch})
        else:
            # Create new view
            self.env['ir.ui.view'].create({
                'name': view_name,
                'model': self.model_id.model,
                'type': 'map',
                'arch': view_arch,
            })
        
        # Update all selected actions' view_mode
        for action in self.action_ids:
            self._update_action_view_mode(action)
            
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }


    def _build_map_view_arch(self):
        """Build the XML architecture for the map view"""
        # Build attributes
        attrs = []
        if self.partner_field_id:
            attrs.append(f'partner_field="{self.partner_field_id.name}"')
        if self.lat_field and self.lat_field != 'partner_latitude':
            attrs.append(f'lat_field="{self.lat_field}"')
        if self.lng_field and self.lng_field != 'partner_longitude':
            attrs.append(f'lng_field="{self.lng_field}"')
        if self.address_field and self.address_field != 'contact_address':
            attrs.append(f'address_field="{self.address_field}"')

        
        attrs_str = ' ' + ' '.join(attrs) if attrs else ''
        
        # Build the arch
        arch = f'''<?xml version="1.0"?>
<map{attrs_str}>
    <field name="display_name"/>
</map>'''
        
        return arch

    def _update_action_view_mode(self, action):
        """Update the action's view_mode to include 'map' and shift view bindings"""
        current_view_mode = action.view_mode or ''
        view_modes = [vm.strip() for vm in current_view_mode.split(',') if vm.strip()]
        
        # Remove 'map' if it already exists
        view_modes = [vm for vm in view_modes if vm != 'map']
        
        target_mode = None
        # Insert 'map' at the specified position
        if self.view_position == 'after_list':
            if 'tree' in view_modes:
                idx = view_modes.index('tree') + 1
                view_modes.insert(idx, 'map')
                target_mode = 'tree'
            elif 'list' in view_modes:
                idx = view_modes.index('list') + 1
                view_modes.insert(idx, 'map')
                target_mode = 'list'
            else:
                view_modes.append('map')
        elif self.view_position == 'after_form' and 'form' in view_modes:
            idx = view_modes.index('form') + 1
            view_modes.insert(idx, 'map')
            target_mode = 'form'
        elif self.view_position == 'after_kanban' and 'kanban' in view_modes:
            idx = view_modes.index('kanban') + 1
            view_modes.insert(idx, 'map')
            target_mode = 'kanban'
        else:
            # Default: add at the end
            view_modes.append('map')
        
        # Update the action string
        action.write({
            'view_mode': ','.join(view_modes)
        })
        
        # Force explicit ordering using Odoo's ir.actions.act_window.view table 
        # so it doesn't fall back to the very end of the list when other explicit views exist.
        if target_mode:
            target_view_binding = self.env['ir.actions.act_window.view'].search([
                ('act_window_id', '=', action.id),
                ('view_mode', '=', target_mode)
            ], limit=1)
            
            if target_view_binding:
                view_name = f"{self.model_id.model}.map.view"
                map_view = self.env['ir.ui.view'].search([
                    ('name', '=', view_name),
                    ('model', '=', self.model_id.model),
                    ('type', '=', 'map')
                ], limit=1)
                
                if map_view:
                    target_seq = target_view_binding.sequence
                    higher_bindings = self.env['ir.actions.act_window.view'].search([
                        ('act_window_id', '=', action.id),
                        ('sequence', '>', target_seq)
                    ])
                    for bdg in higher_bindings:
                        bdg.write({'sequence': bdg.sequence + 1})
                        
                    map_binding = self.env['ir.actions.act_window.view'].search([
                        ('act_window_id', '=', action.id),
                        ('view_mode', '=', 'map')
                    ], limit=1)
                    if map_binding:
                        map_binding.write({'sequence': target_seq + 1, 'view_id': map_view.id})
                    else:
                        self.env['ir.actions.act_window.view'].create({
                            'act_window_id': action.id,
                            'view_id': map_view.id,
                            'view_mode': 'map',
                            'sequence': target_seq + 1,
                        })
