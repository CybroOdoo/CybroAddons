# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
from odoo import api, exceptions, fields, models, Command


class DashboardMenu(models.Model):
    """Model to manage dashboard configurations and their associated cards."""
    _name = 'dashboard.menu'
    _description = 'Dashboard Menu'

    name = fields.Char(string='Menu Name', required=True, help='Name of the dashboard menu.')
    sequence = fields.Integer(string='Sequence', default=10, help='Sequence order of the menu.')
    action_id = fields.Reference(
        string='Action',
        selection=[
            ('ir.actions.act_window', 'Window Action'),
            ('ir.actions.report', 'Report Action'),
            ('ir.actions.server', 'Server Action')
        ],
        help="The action to execute when clicking on the menu item."
    )
    parent_id = fields.Many2one(
        'ir.ui.menu',
        domain=[('action', '=', False)],
        string='Parent Menu',
        help='Parent menu item.'
    )
    menu_id = fields.Many2one('ir.ui.menu', string='Menu Item', help='Linked UI menu item.')
    child_ids = fields.One2many('dashboard.menu', 'parent_id', string='Child Menus', help='Child menus of this dashboard.')
    dashboard_name = fields.Char(string='Dashboard Name', required=True, help='Name of the dashboard.')
    description = fields.Text(string='Description', help='Description of the dashboard.')
    card_ids = fields.One2many('dashboard.card', 'dashboard_menu_id', string='Cards', copy=True, help='Cards belonging to this dashboard.')
    default_filter_id = fields.Many2one('ir.filters', string='Default Filter', help='Default filter applied.')
    start_date = fields.Date(string='Start Date', help='Start date.')
    end_date = fields.Date(string='End Date', help='End date.')
    layout = fields.Selection(
        selection=[('grid', 'Grid'), ('list', 'List')],
        string='Layout',
        default='grid',
        help='Layout type for the dashboard.'
    )
    refresh_interval = fields.Integer(string='Refresh Interval (seconds)', help='Interval to refresh dashboard data.')
    background_color = fields.Char(string='Background Color', default='#ffffff', help='Background color of the dashboard.')
    font = fields.Selection(
        selection=[('Roboto', 'Roboto'), ('Open Sans', 'Open Sans'), ('Lato', 'Lato')],
        string='Font',
        default='Roboto',
        help='Font family for the dashboard.'
    )
    theme_id = fields.Many2one('dashboard.theme.group', string='Theme', help='Theme applied to this dashboard.')
    dark_mode_enabled = fields.Boolean(
        string='Dark Mode Enabled',
        default=False,
        help="Persisted dark-mode state for this dashboard. Toggled live by the Light/Dark switch in the dashboard header; sets the initial state on load."
    )
    custom_css = fields.Text(string='Custom CSS', help='Custom CSS for the dashboard.')
    custom_js = fields.Text(string='Custom JavaScript', help='Custom JavaScript for the dashboard.')
    icon = fields.Binary(string='Icon', help='Icon for the dashboard menu.')
    background_image = fields.Binary(string='Background Image', help='Background image for the dashboard.')
    custom_title = fields.Char(string='Custom Title', help='Custom title.')
    custom_subtitle = fields.Char(string='Custom Subtitle', help='Custom subtitle.')
    custom_filter_ids = fields.One2many('dashboard.custom.filter', 'dashboard_menu_id', string='Custom Filters', copy=True, help='Custom filters for this dashboard.')
    advanced_date_filter_ids = fields.One2many('dashboard.date.filter', 'dashboard_menu_id', string='Advanced Date Filters', copy=True, help='Advanced date filters.')

    # Fields for the icon configuration
    icon_class = fields.Char(
        string="Icon Class",
        help="Full Font Awesome class, e.g., 'fa-solid fa-user'. Find icons at fontawesome.com",
        default="fa-solid fa-box"
    )
    color_1 = fields.Char(
        string="Color 1",
        default="#71639e",
        help="Start color for gradient, e.g., #FF0000"
    )
    color_2 = fields.Char(
        string="Color 2",
        default="#5a5087",
        help="End color for gradient, e.g., #0000FF"
    )
    gradient_degree = fields.Integer(
        string="Gradient Degree",
        default=135,
        help="Angle of the gradient, e.g., 90"
    )
    icon_style_json = fields.Json(
        string="Icon Preview",
        compute="_compute_icon_style_json",
        store=True,
        help="JSON configuration for icon preview."
    )

    @api.constrains('gradient_degree')
    def _check_gradient_degree(self):
        """
        Validates that the gradient degree is between 0 and 360.
        """
        for rec in self:
            if not (0 <= rec.gradient_degree <= 360):
                raise exceptions.ValidationError("The Gradient Degree must be a number between 0 and 360.")

    @api.depends('icon_class', 'color_1', 'color_2', 'gradient_degree')
    def _compute_icon_style_json(self):
        """ This method runs onchange and populates the JSON field. """
        for rec in self:
            rec.icon_style_json = {
                'class': rec.icon_class,
                'color_1': rec.color_1,
                'color_2': rec.color_2,
                'degree': rec.gradient_degree,
            }

    def get_theme_data(self):
        """Retrieve theme data for rendering the dashboard UI."""
        self.ensure_one()
        if self.theme_id:
            return {
                'background_color': self.theme_id.background_color,
                'card_background_color': self.theme_id.card_background_color,
                'card_text_color': self.theme_id.card_text_color,
                'button_color': self.theme_id.button_color,
                'text_color': self.theme_id.text_color,
                'sidebar_toggle_color': self.theme_id.sidebar_toggle_color,
                'navbar_color': self.theme_id.navbar_color,
                'dashboard_card_color': self.theme_id.dashboard_card_color,
                'card_spacing': self.theme_id.card_spacing,
                'is_gradient': self.theme_id.is_gradient,
                'gradient_color_1': self.theme_id.gradient_color_1,
                'gradient_color_2': self.theme_id.gradient_color_2,
                'gradient_degree': self.theme_id.gradient_degree,
                'background_image': self.theme_id.background_image,
                'background_size': self.theme_id.background_size,
                'id': self.theme_id.id,
            }
        return {}


    @api.model_create_multi
    def create(self, vals_list):
        """Override create to also build the corresponding UI menus and actions."""
        dashboards = super().create(vals_list)
        dashboards._create_menu_and_actions()
        return dashboards

    def unlink(self):
        """Override unlink to remove associated UI menus and actions."""
        for rec in self:
            if rec.menu_id:
                # Find the action linked to this menu
                action = rec.menu_id.action
                if action and action._name == 'ir.actions.client':
                    action.unlink()
                rec.menu_id.unlink()
        return super(DashboardMenu, self).unlink()

    def action_duplicate_dashboard(self, new_name, parent_id):
        """Duplicate the dashboard and its cards."""
        self.ensure_one()
        # Create the copy of the dashboard record
        new_dashboard = self.copy({
            'name': new_name,
            'dashboard_name': new_name,
            'parent_id': parent_id,
        })
        
        # If Odoo's default copy didn't clone the cards (e.g. if copy=False or environment issues),
        # manually clone each card to the new dashboard.
        if not new_dashboard.card_ids and self.card_ids:
            for card in self.card_ids:
                card.copy({'dashboard_menu_id': new_dashboard.id})
        
        return {
            'type': 'ir.actions.client',
            'tag': 'DynamicDashboard',
            'params': {
                'dashboard_menu_id': new_dashboard.id,
            }
        }

    def _create_menu_and_actions(self):
        """Create the client action and menu item for the dashboard."""
        for dashboard in self:
            action = self.env['ir.actions.client'].create({
                'name': dashboard.dashboard_name,
                'tag': 'DynamicDashboard',
                'params': {'dashboard_menu_id': dashboard.id,}
            })
            menu_item  = self.env['ir.ui.menu'].create({
                'name': dashboard.name,
                'parent_id': dashboard.parent_id.id,
                'action': f'ir.actions.client,{action.id}',
                'dashboard_menu_id': dashboard.id
            })
            dashboard.menu_id = menu_item.id

    def action_open_dashboard(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.client',
            'tag': 'DynamicDashboard',
            'params': {'dashboard_menu_id': self.id},
        }

    def action_new_dashboard_dialog(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'dashboard.menu',
            'view_mode': 'form',
            'views': [(False, 'form')],
            'target': 'new',
        }

    def action_edit_record(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'dashboard.menu',
            'res_id': self.id,
            'view_mode': 'form',
            'views': [(False, 'form')],
            'target': 'new',
        }

    def export_dashboard(self):
        """Export all cards in the dashboard to a JSON-compatible list."""
        self.ensure_one()
        export_data = []
        for card in self.card_ids:
            vals = {
                'name': card.name,
                'description': card.description,
                'type': card.type,
                'gs_x': card.gs_x,
                'gs_y': card.gs_y,
                'gs_w': card.gs_w,
                'gs_h': card.gs_h,
                'model_name': card.model_name,
                'domain': card.domain,
            }
            # Handle standard fields
            fields_to_copy = ['semi_circular', 'index_axis', 'legend', 'legend_position', 'legend_alignment', 
                              'legend_label_pointstyle', 'background_color', 'todo_type', 'size', 
                              'chart_type', 'chart_color', 'record_limit', 'table_type', 'table_order', 
                              'show_record_count', 'table_limit', 'view_type', 'activity_type', 'enable_click',
                              'aggregation_method']
            for f in fields_to_copy:
                 # Standard field access on recordset is safe. Unset fields returned as False/initial value.
                 val = card[f]
                 if val:
                      vals[f] = val

            # Handle Relations to be portable
            # Group By
            if card.group_by_field_id:
                vals['group_by_field_name'] = card.group_by_field_id.name
            if card.measure_field_id:
                vals['measure_field_name'] = card.measure_field_id.name
            if card.group_by_2:
                vals['group_by_2_name'] = card.group_by_2.name

            # Table Fields (One2many)
            if card.table_field_line_ids:
                vals['table_field_lines'] = [
                    {'sequence': line.sequence, 'field_name': line.field_id.name}
                    for line in card.table_field_line_ids if line.field_id
                ]
            
            # Todos
            if card.todo_ids:
                vals['todos'] = [
                    {'name': todo.name, 'status': todo.status, 'is_done': todo.is_done}
                    for todo in card.todo_ids
                ]
            
            # Color Group (if applicable, simple link by ID is risky, maybe skip or export name? Let's skip for now or use name if it exists)
            # Assuming basic color group usage
                
            export_data.append(vals)
        return export_data

    def import_dashboard(self, cards_data):
        """Import cards from a JSON-compatible list into this dashboard."""
        self.ensure_one()
        # Find max Y
        max_y = 0
        if self.card_ids:
            # simple calculation
            for c in self.card_ids:
                bottom = c.gs_y + c.gs_h
                if bottom > max_y:
                    max_y = bottom
        
        # Add spacing
        if max_y > 0:
            max_y += 1

        for card_data in cards_data:
            # Resolve Model
            model_name = card_data.get('model_name')
            model_id = False
            if model_name:
                IrModel = self.env['ir.model'].search([('model', '=', model_name)], limit=1)
                if IrModel:
                    model_id = IrModel.id
            
            vals = {
                'dashboard_menu_id': self.id,
                'name': card_data.get('name', 'Imported Card'),
                'description': card_data.get('description', ''),
                'gs_x': card_data.get('gs_x', 0),
                'gs_y': card_data.get('gs_y', 0) + max_y, # Offset
                'model_id': model_id,
            }
            
            # Copy scalars
            fields_to_copy = ['type', 'gs_w', 'gs_h', 'domain', 
                             'semi_circular', 'index_axis', 'legend', 'legend_position', 'legend_alignment', 
                              'legend_label_pointstyle', 'background_color', 'todo_type', 'size', 
                              'chart_type', 'chart_color', 'record_limit', 'table_type', 'table_order', 
                              'show_record_count', 'table_limit', 'view_type', 'activity_type', 'enable_click',
                              'aggregation_method']
            for f in fields_to_copy:
                 if f in card_data:
                     vals[f] = card_data[f]

            # Resolve Fields
            if model_id:
                if card_data.get('group_by_field_name'):
                     F = self.env['ir.model.fields'].search([('model_id', '=', model_id), ('name', '=', card_data['group_by_field_name'])], limit=1)
                     if F: vals['group_by_field_id'] = F.id
                
                if card_data.get('measure_field_name'):
                     F = self.env['ir.model.fields'].search([('model_id', '=', model_id), ('name', '=', card_data['measure_field_name'])], limit=1)
                     if F: vals['measure_field_id'] = F.id

                if card_data.get('group_by_2_name'):
                     F = self.env['ir.model.fields'].search([('model_id', '=', model_id), ('name', '=', card_data['group_by_2_name'])], limit=1)
                     if F: vals['group_by_2'] = F.id

                # Table Lines
                if card_data.get('table_field_lines'):
                    lines_commands = []
                    for line in card_data['table_field_lines']:
                        # Find field
                        f_id = self.env['ir.model.fields'].search([('model_id', '=', model_id), ('name', '=', line['field_name'])], limit=1).id
                        if f_id:
                            lines_commands.append(Command.create({
                                'field_id': f_id,
                                'sequence': line.get('sequence', 10)
                            }))
                    if lines_commands:
                        vals['table_field_line_ids'] = lines_commands

            # Todos
            if card_data.get('todos'):
                vals['todo_ids'] = [
                    Command.create({
                        'name': todo.get('name'),
                        'status': todo.get('status'),
                        'is_done': todo.get('is_done'),
                    }) for todo in card_data['todos']
                ]

            self.env['dashboard.card'].create(vals)
        
        return True



