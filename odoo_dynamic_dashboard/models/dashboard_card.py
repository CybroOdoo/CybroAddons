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
import json
import logging
from datetime import date, datetime, timedelta

from google import genai

from odoo import api, fields, models
from odoo.addons.iap.tools import iap_tools
from odoo.exceptions import UserError, ValidationError
from odoo.tools.safe_eval import safe_eval

_logger = logging.getLogger(__name__)


class DashboardJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle datetimes and Odoo records."""
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if hasattr(obj, 'id'):  # Many2one or NewId
            # Handle NewId which might not be an int
            if not isinstance(obj.id, int):
                return 0
            return obj.id
        # Handle NewId directly if passed as value
        if type(obj).__name__ == 'NewId':
            return 0
        try:
            return super().default(obj)
        except TypeError:
            return str(obj)


class DashboardCard(models.Model):
    """Model representing an individual widget/card on a dashboard."""
    _name = 'dashboard.card'
    _description = 'Dashboard Card'

    name = fields.Char(string='Card Title', required=True, help='Title of the dashboard card.')
    description = fields.Char(string='Card Description', required=True, help='Description of the card.')
    semi_circular = fields.Boolean(string='Semi Circular Chart', default=False, help='Display chart as semi-circular.')
    index_axis = fields.Selection(
        selection=[('y', 'Horizontal'), ('x', 'Vertical')],
        default='x',
        string='Index Axis',
        help='Axis direction for charts.'
    )

    # legend attributes
    legend = fields.Boolean(string='Enable Legend', default=True, help='Show legend on the chart.')
    legend_position = fields.Selection(
        string='Position Of The Legend',
        selection=[('bottom', 'Bottom'), ('top', 'Top'), ('left', 'Left'), ('right', 'Right')],
        default='bottom',
        help='Position of the chart legend.'
    )
    legend_alignment = fields.Selection(
        selection=[('start', 'Start'), ('center', 'Center'), ('end', 'End')],
        string='Alignment Of The Legend',
        default='start',
        help='Alignment of the chart legend.'
    )
    legend_label_pointstyle = fields.Selection(
        selection=[
            ('circle', 'Circle'), ('rect', 'Rectangle'),
            ('rectRounded', 'Rectangle Rounded'), ('rectRot', 'Rectangle Rot'),
            ('triangle', 'Triangle')
        ],
        default='circle',
        string='Point Styles',
        help='Point style for the legend labels.'
    )

    model_id = fields.Many2one('ir.model', string='Odoo Model', help='Model used for data.')
    model_name = fields.Char(
        related='model_id.model',
        string='Model Name',
        help='Added model_id model.'
    )
    domain = fields.Char(string='Domain', default='[]', help='Data domain.')

    group_by_field_id = fields.Many2one(
        'ir.model.fields',
        string='Group By',
        domain="[('model_id', '=', model_id), ('ttype', 'not in', ['many2many', 'one2many', 'binary', 'html', 'json', 'image', 'date', 'datetime', 'reference']), ('store', '=', True)]",
        help='Field used for grouping.'
    )
    measure_field_id = fields.Many2one(
        'ir.model.fields',
        string='Measure',
        domain="[('model_id', '=', model_id), ('ttype', 'in', ['integer', 'float', 'monetary']), ('store', '=', True)]",
        help='Field used for measurement.'
    )
    aggregation_method = fields.Selection(
        selection=[
            ('sum', 'Sum'),
            ('avg', 'Average'),
        ('count', 'Count'),
            ('max', 'Maximum'),
            ('min', 'Minimum'),
        ],
        string='Aggregation',
        default='sum',
        help='Aggregation method applied to the measure field.'
    )
    chart_x_axis_data = fields.Char(string='X Axis Data', compute='_compute_chart_data', help='Computed X axis data for chart.')
    chart_y_axis_data = fields.Char(string='Y Axis Data', compute='_compute_chart_data', help='Computed Y axis data for chart.')

    background_color = fields.Char(string='Background Color', default='#ffffff', help='Background color of the card.')
    type = fields.Selection(
        selection=[
            ('chart', 'Chart'), ('block', 'Block'), ('table', 'Table'),
            ('to-do', 'To-do'), ('views', 'Views'), ('activity', 'Activity')
        ],
        string='Type',
        default='block',
        help='Type of the dashboard card.'
    )

    # ---- Optional decorative icon on the card --------------------- #
    icon_class = fields.Char(
        string='Icon Class',
        help="Font Awesome icon class (e.g. 'fa-solid fa-chart-line'). Leave empty to hide the icon on the card.",
    )
    icon_layout = fields.Selection(
        selection=[
            ('left', 'Icon Left, Content Right'),
            ('right', 'Icon Right, Content Left'),
            ('top', 'Icon Top, Content Bottom'),
            ('bottom', 'Icon Bottom, Content Top'),
        ],
        string='Icon Layout',
        default='top',
        help="How the icon and the card's content are arranged side by side."
    )
    icon_color = fields.Char(string='Icon Color', default='#6B7280', help='Hex colour for the icon (e.g. #6B7280).')
    icon_size = fields.Selection(
        selection=[
            ('sm', 'Small'),
            ('md', 'Medium'),
            ('lg', 'Large'),
            ('xl', 'Extra Large'),
        ],
        string='Icon Size',
        default='md',
        help='Size of the decorative icon.'
    )

    todo_type = fields.Selection(
        selection=[
            ('classic', 'Classic Checklist'),
            ('priority', 'Priority Based'),
            ('progress', 'Progress Tracker'),
            ('kanban', 'Kanban Board')
        ],
        string='Todo Type',
        default='classic',
        help='Type of todo data visualization.'
    )

    dashboard_menu_id = fields.Many2one('dashboard.menu', string='Dashboard Menu', help='Linked dashboard menu.')

    group_by_2 = fields.Many2one('ir.model.fields', string='Second Group By', domain="[('model_id', '=', model_id)]", help='Second field used for grouping.')
    size = fields.Selection(
        selection=[('small', 'Small'), ('medium', 'Medium'), ('large', 'Large')],
        string='Size',
        default='small',
        help='Size of the dashboard card.'
    )
    gs_x = fields.Integer(string='Grid Stack X', default=0, help='X coordinate in grid stack.')
    gs_y = fields.Integer(string='Grid Stack Y', default=0, help='Y coordinate in grid stack.')
    gs_w = fields.Integer(string='Grid Stack W', default=3, help='Width in grid stack.')
    gs_h = fields.Integer(string='Grid Stack H', default=2, help='Height in grid stack.')
    chart_type = fields.Selection(
        selection=[
            ('bar', 'Bar'), ('line', 'Line'), ('area', 'Area'),
            ('pie', 'Pie'), ('doughnut', 'Doughnut'), ('polarArea', 'Polar Area'),
            ('radial', 'Radial'), ('scatter', 'Scatter'), ('radar', 'Radar'),
            ('bubble', 'Bubble'), ('flower', 'Flower'), ('funnel', 'Funnel')
        ],
        string='Chart Type',
        default='bar',
        help='Type of the chart to display.'
    )
    color_group_id = fields.Many2one('dashboard.color.group', string='Color Group', help='Select color palette for charts.')
    chart_color = fields.Char(string='Chart Color', default='#366899', help='Color applied to the chart elements.')

    # Table-specific fields
    record_limit = fields.Integer(string='Record Limit', default=10, help='Maximum number of records to display.')
    table_field_line_ids = fields.One2many('dashboard.card.field', 'card_id', string='Table Fields', copy=True, help='Fields displayed in the table.')
    table_type = fields.Selection(
        selection=[
            ('striped', 'Striped Table'),
            ('borderless', 'Borderless Table'),
            ('minimal_line', 'Minimal Line Table'),
            ('data_grid', 'Data Grid Table'),
        ],
        string='Table Type',
        default='striped',
        help='Style of the table display.'
    )

    table_order = fields.Char(string='Order By', default='id desc', help='Field to order records by, e.g., "create_date desc".')

    show_record_count = fields.Boolean(string='Show Record Count', default=True, help='Display total number of records.')

    table_limit = fields.Integer(string='Table Limit', default=10, help='Maximum number of records to display in the table.')
    table_headers = fields.Char(string='Table Headers', compute='_compute_table_data', help='Computed table headers.')
    table_rows = fields.Char(string='Table Rows', compute='_compute_table_data', help='Computed table rows.')

    todo_ids = fields.One2many(comodel_name='dashboard.todo', inverse_name='card_id', string='Todos', copy=True, help='Associated to-do items.')

    view_type = fields.Selection(
        selection=[
            ('kanban', 'Kanban'), ('graph', 'Graph'), ('pivot', 'Pivot'),
            ('list', 'List'), ('calendar', 'Calendar'), ('hierarchy', 'Hierarchy'),
        ],
        string='View Type',
        default='kanban',
        help='Type of view to embed.'
    )

    view_records = fields.Char(string='View Records JSON', compute='_compute_view_data', store=True, help='Serialized view records.')
    view_fields = fields.Char(string='View Fields JSON', compute='_compute_view_data', store=True, help='Serialized view fields.')
    total_view_count = fields.Integer(string='Total Count', compute='_compute_view_data', store=True, help='Total record count for the view.')

    enable_click = fields.Boolean(string='Enable Click', default=True, help='If enabled, clicking a record will open its form view.')

    activity_type = fields.Selection(
        selection=[
            ('timeline', 'Timeline'), ('feed', 'Feed'),
            ('summary', 'Summary'), ('calendar', 'calendar')
        ],
        string='Activity Type',
        default='timeline',
        help='Format of activity display.'
    )

    block_value = fields.Char(string='Block Value', compute='_compute_block_data', help='Computed value for block displays.')

    block_aggregation_method = fields.Selection(
        selection=[
            ('sum', 'Sum'),
            ('avg', 'Average'),
            ('count', 'Count'),
        ],
        string='Block Aggregation',
        default='sum',
        help='Aggregation method used for block type cards.'
    )

    activity_records = fields.Char(
        string='Activity Records JSON',
        compute='_compute_activity_data',
        help='Serialized activity records.'
    )

    total_activity_count = fields.Integer(
        string='Total Activity Count',
        compute='_compute_activity_data',
        help='Total count of activities.'
    )

    @api.model
    def generate_max_cards_from_model(self, model_name, dashboard_menu_id=None, max_cards=12):
        """
        Generate dashboard cards using AI based on the specified model.

        :param model_name: The technical name of the Odoo model.
        :param dashboard_menu_id: ID of the dashboard menu to attach cards to.
        :param max_cards: Maximum number of cards to generate.
        :return: String 'success' if generation completes.
        """
        # 1. Validate and Fetch Model Metadata
        model = self.env.get(model_name)
        if model is None:
            raise UserError("Model '{}' not found.".format(model_name))
        model_label = model._description
        fields_map = model._fields

        # Domain equivalent for group_by_field_id
        excluded_types = [
            'many2many', 'one2many', 'binary', 'html',
            'json', 'image', 'date', 'datetime', 'reference'
        ]

        groupable_xaxis = {
            name: field.string
            for name, field in fields_map.items()
            if field.store and field.type not in excluded_types
        }

        # Domain equivalent for measure_field_id
        numeric_measures = {
            name: field.string
            for name, field in fields_map.items()
            if field.store and field.type in ['integer', 'float', 'monetary']
        }
        if not numeric_measures or not groupable_xaxis:
            raise UserError(
                "Model {} lacks suitable numeric or groupable fields for dashboards.".format(model_name))

        # 2. Configure Gemini API
        icp = self.env['ir.config_parameter'].sudo()

        # 3. Formulate Prompt
        prompt = """
            You are an expert Odoo dashboard configuration generator.
            Generate exactly {max_cards} diverse dashboard cards for the Odoo model '{model_name}' ({model_label}).

            Available Numeric Fields (for Measures): {numeric_measures_json}
            Available Groupable Fields (for X-Axis/Categorization): {groupable_xaxis_json}

            Output strictly as a JSON array of objects.
            Every object MUST have: "name", "description", "type", "gs_w" (Grid Width 1-9), and "gs_h" (Grid Height).

            Allowed "type" values and their specific required fields:
            - "block": Requires "block_aggregation_method" (sum, avg, count), "domain", "measure_field_id". Set gs_w: 3, gs_h: 2.
            - "chart": Requires "chart_type" (bar, pie, line, doughnut), "domain", "group_by_field_id", "aggregation_method", "measure_field_id". Set gs_w: 6, gs_h: 4.
            - "table": Requires "table_type" (striped, data_grid), "domain", "table_columns" (array of 3-5 field names). Set gs_w: 9, gs_h: 5.
            - "to-do": Requires "todo_type" (classic, kanban). Set gs_w: 4, gs_h: 4.
            - "views": Requires "view_type" (list, kanban, pivot), "domain". Set gs_w: 7, gs_h: 5.
            - "activity": Requires "activity_type" (timeline, summary), "domain". Set gs_w: 4, gs_h: 4.

            IMPORTANT DATA QUALITY RULES:
            - Generate cards that are likely to show real data, not empty widgets.
            - Prefer broad but meaningful domains that usually return records for typical databases.
            - Avoid overly restrictive domains that can result in no records.
            - Use valid field names from the provided model metadata.
            - If unsure, use domain "[]" rather than an invalid or too strict filter.

            Generate realistic domains (e.g., "[('state','=','done')]"). Return ONLY raw JSON. Do not use markdown blocks.
            """.format(
            max_cards=max_cards,
            model_name=model_name,
            model_label=model_label,
            numeric_measures_json=json.dumps(numeric_measures),
            groupable_xaxis_json=json.dumps(groupable_xaxis)
        )
        configs = []
        if icp.get_param('odoo_dynamic_dashboard.enable_ai') and icp.get_param(
                'odoo_dynamic_dashboard.ai_service_type') == 'gemini':
            # Gemini setup
            api_key = icp.get_param('odoo_dynamic_dashboard.api_key')
            if not api_key:
                raise UserError("Gemini API key is not configured in the Settings.")
            client = genai.Client(api_key=api_key)
            # Using gemini-1.5-pro for complex reasoning and structured output
            try:
                response = client.models.generate_content(
                    model="gemini-3-flash-preview", contents=prompt
                )
                configs = json.loads(response.text)
                configs = configs[:max_cards]

            except Exception as e:
                _logger.error("Gemini generation failed: {}".format(str(e)))
                raise UserError(
                    "Failed to generate dashboard configurations. Please try again.\nError: {}".format(e))

        else:
            olg_endpoint = icp.get_param('html_editor.olg_api_endpoint', 'https://olg.api.odoo.com')
            db_uuid = icp.get_param('database.uuid')
            try:
                params = {
                    'prompt': prompt,
                    'conversation_history': [],
                    'database_id': db_uuid,
                }

                response = iap_tools.iap_jsonrpc(olg_endpoint + "/api/olg/1/chat", params=params,
                                                 timeout=30)
                if response.get('status') == 'success':
                    configs = json.loads(response.get('content'))
                elif response.get('status') == 'limit_call_reached':
                    return UserError(
                        "You have reached the maximum number of requests for Odoo AI. Try again later.")
                else:
                    return UserError(f"Odoo AI Error: {response.get('status')}")
            except Exception as e:
                return UserError(f"Odoo AI Connection Error: {str(e)}")

        # 5. Prepare for Model Parsing
        ir_model = self.env['ir.model'].search([('model', '=', model_name)], limit=1)
        model_fields = {f.name: f for f in
                        self.env['ir.model.fields'].search([('model_id', '=', ir_model.id)])}

        resolved_configs = []

        # 6. --- GRIDSTACK LAYOUT ENGINE ---
        current_x = 0
        current_y = 0
        current_row_height = 0
        max_grid_width = 9

        default_sizes = {
            'block': {'w': 3, 'h': 2},
            'chart': {'w': 4, 'h': 3},
            'table': {'w': 6, 'h': 3},
            'to-do': {'w': 5, 'h': 4},
            'activity': {'w': 4, 'h': 4},
            'views': {'w': 5, 'h': 4},
        }

        for config in configs:
            try:
                card_type = config.get('type', 'block')

                # Layout Math: Determine width and height (AI provided OR fallback to default)
                fallback = default_sizes.get(card_type, {'w': 4, 'h': 4})
                w = min(int(config.get('gs_w', fallback['w'])), max_grid_width)
                h = max(int(config.get('gs_h', fallback['h'])), 2)

                # Layout Math: Wrap to next row if widget exceeds grid max width
                if current_x + w > max_grid_width:
                    current_x = 0
                    current_y += current_row_height
                    current_row_height = 0

                # Base Dictionary for EVERY card (including grid coords)[{'name': 'Total Sales Amount', 'description': 'Displays the total sales amount from all orders.', 'type': 'block', 'gs_w': 3, 'gs_h': 2, 'block_aggregation_method': 'sum', 'domain': '[]', 'measure_field_id': 'amount_total'}, {'name': 'Average Untaxed Amount', 'description': 'Shows the average untaxed amount of all sales orders.', 'type': 'block', 'gs_w': 3, 'gs_h': 2, 'block_aggregation_method': 'avg', 'domain': '[]', 'measure_field_id': 'amount_untaxed'}, {'name': 'Sales by Status', 'description': 'Breakdown of sales orders by their current status.', 'type': 'chart', 'gs_w': 6, 'gs_h': 4, 'chart_type': 'bar', 'domain': '[]', 'group_by_field_id': 'state', 'aggregation_method': 'count', 'measure_field_id': 'id'}, {'name': 'Sales by Customer', 'description': 'Total sales amount grouped by customer.', 'type': 'chart', 'gs_w': 6, 'gs_h': 4, 'chart_type': 'pie', 'domain': '[]', 'group_by_field_id': 'partner_id', 'aggregation_method': 'sum', 'measure_field_id': 'amount_total'}, {'name': 'Sales Orders Table', 'description': 'A detailed table of all sales orders.', 'type': 'table', 'gs_w': 12, 'gs_h': 5, 'table_type': 'data_grid', 'domain': '[]', 'table_columns': ['id', 'name', 'partner_id', 'amount_total', 'state']}, {'name': 'Pending Orders', 'description': 'List of orders that are pending.', 'type': 'to-do', 'gs_w': 4, 'gs_h': 4, 'todo_type': 'kanban'}, {'name': 'Sales by Salesperson', 'description': 'Total sales amount grouped by salesperson.', 'type': 'chart', 'gs_w': 6, 'gs_h': 4, 'chart_type': 'line', 'domain': '[]', 'group_by_field_id': 'user_id', 'aggregation_method': 'sum', 'measure_field_id': 'amount_total'}, {'name': 'Sales Orders by Campaign', 'description': 'Total sales amount grouped by marketing campaign.', 'type': 'chart', 'gs_w': 6, 'gs_h': 4, 'chart_type': 'doughnut', 'domain': '[]', 'group_by_field_id': 'campaign_id', 'aggregation_method': 'sum', 'measure_field_id': 'amount_total'}, {'name': 'Sales Order Activity Summary', 'description': 'Summary of activities related to sales orders.', 'type': 'activity', 'gs_w': 4, 'gs_h': 4, 'activity_type': 'summary', 'domain': '[]'}, {'name': 'Sales Orders by Payment Terms', 'description': 'Breakdown of sales orders by payment terms.', 'type': 'chart', 'gs_w': 6, 'gs_h': 4, 'chart_type': 'bar', 'domain': '[]', 'group_by_field_id': 'payment_term_id', 'aggregation_method': 'count', 'measure_field_id': 'id'}, {'name': 'Sales Orders by Currency', 'description': 'Total sales amount grouped by currency.', 'type': 'chart', 'gs_w': 6, 'gs_h': 4, 'chart_type': 'pie', 'domain': '[]', 'group_by_field_id': 'currency_id', 'aggregation_method': 'sum', 'measure_field_id': 'amount_total'}, {'name': 'Sales Order Views', 'description': 'View of sales orders in a list format.', 'type': 'views', 'gs_w': 12, 'gs_h': 6, 'view_type': 'list', 'domain': '[]'}]
                card_vals = {
                    'name': config.get('name', f"{model_label} {card_type.capitalize()}"),
                    'description': config.get('description', ''),
                    'type': card_type,
                    'model_id': ir_model.id,
                    'dashboard_menu_id': dashboard_menu_id,
                    'domain': config.get('domain', '[]'),
                    'gs_w': w,
                    'gs_h': h,
                    'gs_x': current_x,
                    'gs_y': current_y,
                }
                # Update layout trackers for the next card
                current_x += w
                current_row_height = max(current_row_height, h)

                # --- Type-Specific Field Mapping ---position: absolute; top: 0; left: 0; right: 0; bottom: 0; z-index: 1100
                if card_type == 'chart':
                    card_vals['chart_type'] = config.get('chart_type', 'bar')
                    card_vals['aggregation_method'] = config.get('aggregation_method', 'sum')

                elif card_type == 'block':
                    card_vals['block_aggregation_method'] = config.get('block_aggregation_method',
                                                                       'sum')

                elif card_type == 'table':
                    card_vals['table_type'] = config.get('table_type', 'striped')
                    if config.get('table_columns'):
                        lines = []
                        for field_name in config['table_columns']:
                            if field_name in model_fields:
                                lines.append((0, 0, {'field_id': model_fields[field_name].id}))
                        if lines:
                            card_vals['table_field_line_ids'] = lines

                elif card_type == 'to-do':
                    card_vals['todo_type'] = config.get('todo_type', 'classic')

                elif card_type == 'views':
                    card_vals['view_type'] = config.get('view_type', 'kanban')

                elif card_type == 'activity':
                    card_vals['activity_type'] = config.get('activity_type', 'timeline')

                # Resolve Many2one Fields (group_by and measures)
                for fkey in ['group_by_field_id', 'measure_field_id']:
                    if config.get(fkey) and config[fkey] in model_fields:
                        card_vals[fkey] = model_fields[config[fkey]].id
                resolved_configs.append(card_vals)

            except Exception as item_error:
                _logger.warning(
                    f"Skipping card due to parsing error: {item_error}. Raw config: {config}")
                continue

        if not resolved_configs:
            raise UserError(
                "AI generated data, but none of the fields matched the model's schema successfully.")
        # 7. Batch Create Records
        created_ids = self.create(resolved_configs)
        return 'success'

    def analyze_card_with_ai(self):
        """Send the card's configuration and computed data to AI and return analytical insights."""
        self.ensure_one()

        card_data = {
            'name': self.name,
            'description': self.description or '',
            'type': self.type,
            'model': self.model_id.model if self.model_id else None,
            'model_label': self.model_id.name if self.model_id else None,
            'domain': self.domain or '[]',
            'record_limit': self.record_limit,
        }

        if self.type == 'chart':
            try:
                x_data = json.loads(self.chart_x_axis_data or '[]')
                y_data = json.loads(self.chart_y_axis_data or '[]')
            except Exception:
                x_data, y_data = [], []
            card_data.update({
                'chart_type': self.chart_type,
                'group_by': self.group_by_field_id.field_description if self.group_by_field_id else None,
                'measure': self.measure_field_id.field_description if self.measure_field_id else None,
                'aggregation': self.aggregation_method,
                'categories': x_data[:30],
                'values': y_data[:30],
            })
        elif self.type == 'block':
            card_data.update({
                'aggregation': self.block_aggregation_method,
                'measure': self.measure_field_id.field_description if self.measure_field_id else None,
                'current_value': self.block_value,
            })
        elif self.type == 'table':
            sample = ''
            if self.table_rows:
                try:
                    rows = json.loads(self.table_rows)
                    flat = rows[0] if rows and isinstance(rows[0], list) else rows
                    sample = json.dumps(flat[:10])
                except Exception:
                    sample = (self.table_rows or '')[:2000]
            card_data.update({
                'limit': self.table_limit,
                'order': self.table_order,
                'sample_rows': sample,
            })
        elif self.type == 'views':
            card_data['view_type'] = self.view_type
        elif self.type == 'activity':
            card_data['activity_type'] = self.activity_type
        elif self.type == 'to-do':
            card_data['todo_type'] = self.todo_type

        prompt = f"""
You are a business intelligence analyst. Analyze the following Odoo dashboard card and provide concise, actionable insights for a business user.

Card configuration and data:
{json.dumps(card_data, indent=2, cls=DashboardJSONEncoder)}

Respond in plain text using exactly this structure (no markdown symbols like ** or ##):

PURPOSE
One or two sentences describing what this card shows.

KEY INSIGHTS
- Three to four short bullet points citing specific numbers, top categories, or notable patterns from the data.

RECOMMENDATIONS
- Two or three short bullet points suggesting concrete actions the business can take based on these insights.

Keep the entire response under 250 words. Be direct, specific, and avoid filler. Do not repeat the configuration back.
"""

        icp = self.env['ir.config_parameter'].sudo()
        if icp.get_param('odoo_dynamic_dashboard.enable_ai') and icp.get_param(
                'odoo_dynamic_dashboard.ai_service_type') == 'gemini':
            api_key = icp.get_param('odoo_dynamic_dashboard.api_key')
            if not api_key:
                raise UserError("Gemini API key is not configured in the Settings.")
            client = genai.Client(api_key=api_key)
            try:
                response = client.models.generate_content(
                    model="gemini-3-flash-preview", contents=prompt
                )
                return response.text
            except Exception as e:
                _logger.error(f"Gemini analysis failed: {str(e)}")
                raise UserError(f"Failed to generate AI analysis.\nError: {e}")

        olg_endpoint = icp.get_param('html_editor.olg_api_endpoint', 'https://olg.api.odoo.com')
        db_uuid = icp.get_param('database.uuid')
        try:
            params = {
                'prompt': prompt,
                'conversation_history': [],
                'database_id': db_uuid,
            }
            response = iap_tools.iap_jsonrpc(olg_endpoint + "/api/olg/1/chat", params=params,
                                             timeout=30)
            if response.get('status') == 'success':
                return response.get('content')
            if response.get('status') == 'limit_call_reached':
                raise UserError(
                    "You have reached the maximum number of requests for Odoo AI. Try again later.")
            raise UserError(f"Odoo AI Error: {response.get('status')}")
        except UserError:
            raise
        except Exception as e:
            raise UserError(f"Odoo AI Connection Error: {str(e)}")

    def _compute_activity_data(self):
        """Compute JSON data for activity widgets."""
        for record in self:
            record.activity_records = "[]"
            record.total_activity_count = 0

    @api.depends('model_id', 'domain', 'measure_field_id', 'aggregation_method', 'type',
                 'record_limit', 'block_aggregation_method')
    @api.depends_context('dashboard_date_filter', 'dashboard_date_start', 'dashboard_date_end',
                         'dashboard_custom_filter_id')
    def _compute_block_data(self):
        """Compute numeric block value based on selected aggregation method."""
        for record in self:
            record.block_value = "0"
            if record.type == 'block' and record.model_id:
                try:
                    Model = self.env[record.model_id.model]
                    domain = safe_eval(record.domain or '[]')

                    # Apply global date filter
                    date_filter_domain = record._get_date_filter_domain()
                    if date_filter_domain:
                        domain += date_filter_domain

                    # Apply custom backend filter
                    custom_filter_domain = record._get_custom_filter_domain()
                    if custom_filter_domain:
                        domain += custom_filter_domain

                    # Respect record limit if set
                    if record.record_limit:
                        limited_records = Model.search(domain, limit=record.record_limit)
                        domain = [('id', 'in', limited_records.ids)]

                    method = record.block_aggregation_method or 'sum'

                    if method == 'count':
                        value = Model.search_count(domain)
                    elif record.measure_field_id:
                        field_name = record.measure_field_id.name
                        # Use _read_group for efficient aggregation (read_group deprecated in 19.0)
                        res = Model._read_group(domain, [], [f"{field_name}:sum"])
                        value = res[0][0] if res else 0

                        if method == 'avg' and value:
                            count = Model.search_count(domain)
                            value = value / count if count else 0
                        elif record.aggregation_method == 'max':
                            res = Model._read_group(domain, [], [f"{field_name}:max"])
                            value = res[0][0] if res else 0
                        elif record.aggregation_method == 'min':
                            res = Model._read_group(domain, [], [f"{field_name}:min"])
                            value = res[0][0] if res else 0

                    # Format the value (monetary, float, etc.)
                    if isinstance(value, (float, int)):
                        if value >= 1000000:
                            record.block_value = f"{value / 1000000:.1f}M"
                        elif value >= 1000:
                            record.block_value = f"{value / 1000:.1f}K"
                        else:
                            record.block_value = f"{value:,.2f}".rstrip('0').rstrip('.')
                    else:
                        record.block_value = str(value)

                except Exception as e:
                    _logger.error(f"Error computing block data for {record.name}: {e}")
                    record.block_value = "Error"

    def _json_serializable(self, obj):
        """Convert datetime/date to string for JSON"""
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if hasattr(obj, 'id'):  # Many2one
            return str(obj.id) if obj else ''
        return str(obj)

    @api.depends('model_id', 'domain', 'view_type', 'type', 'table_field_line_ids', 'record_limit')
    @api.depends_context('dashboard_date_filter', 'dashboard_date_start', 'dashboard_date_end',
                         'dashboard_custom_filter_id')
    def _compute_view_data(self):
        """Fetch and format records for list/kanban views."""
        for record in self:
            record.view_records = "[]"
            record.view_fields = "[]"
            record.total_view_count = 0

            if record.type == 'views' and record.model_id:
                try:
                    Model = self.env[record.model_id.model]
                    domain = safe_eval(record.domain or '[]')

                    limit = record.record_limit or 10

                    # Simple field list - just get basics
                    fields_to_read = ['id', 'display_name']
                    if 'name' in Model._fields:
                        fields_to_read.append('name')
                    if 'create_date' in Model._fields:
                        fields_to_read.append('create_date')

                    # Fetch records
                    records = Model.search_read(
                        domain=domain,
                        fields=fields_to_read,
                        limit=limit
                    )

                    # Simple formatting
                    export_data = []
                    for rec in records:
                        row = {}
                        for key, val in rec.items():
                            if isinstance(val, (list, tuple)) and len(val) == 2:
                                row[key] = str(val[1])
                            elif isinstance(val, (datetime, date)):
                                row[key] = val.isoformat()
                            elif val is False or val is None:
                                row[key] = ""
                            else:
                                row[key] = str(val)
                        export_data.append(row)

                    record.view_records = json.dumps(export_data, cls=DashboardJSONEncoder)
                    record.total_view_count = Model.search_count(domain)

                except Exception as e:
                    _logger.error(f"Error computing view data: {e}")
                    record.view_records = "[]"

    @api.depends('model_id', 'domain', 'type', 'table_field_line_ids', 'table_limit',
                 'record_limit', 'table_order')
    @api.depends_context('dashboard_date_filter', 'dashboard_date_start', 'dashboard_date_end',
                         'dashboard_custom_filter_id')
    def _compute_table_data(self):
        """Compute paginated table records in JSON format."""
        def _to_string(value, field, model, fname):
            if value in (False, None):
                return ""
            t = field.type

            if t in ('char', 'text'):
                return str(value)

            if t in ('integer', 'float', 'monetary'):
                return str(value)

            if t in ('date', 'datetime'):
                return value.isoformat() if hasattr(value,
                                                    'isoformat') else str(value)

            if t == 'boolean':
                return value

            if t == 'selection':
                return dict(model._fields[fname].selection).get(value, value)

            if t == 'many2one':
                return value[1] if isinstance(value, (list, tuple)) else ""

            return str(value)

        for record in self:
            # Defaults
            record.table_headers = "[]"
            record.table_rows = "[]"

            if record.type != 'table' or not record.table_field_line_ids:
                continue

            # Headers (ordered)
            field_lines = record.table_field_line_ids.sorted('sequence')
            headers_data = field_lines.read(['field_name', 'field_label', 'type'])
            # Sanitize NewId for JSON serialization
            for header in headers_data:
                if 'id' in header and not isinstance(header['id'], int):
                    header['id'] = 0  # Fallback for NewId

            record.table_headers = json.dumps(headers_data, cls=DashboardJSONEncoder)

            Model = self.env[record.model_id.model]
            domain = safe_eval(record.domain or '[]')

            # Apply global date filter
            date_filter_domain = record._get_date_filter_domain()
            if date_filter_domain:
                domain = domain + date_filter_domain

            # Apply custom backend filter
            custom_filter_domain = record._get_custom_filter_domain()
            if custom_filter_domain:
                domain = domain + custom_filter_domain

            batch_size = record.table_limit or 10
            total_limit = record.record_limit

            field_names = field_lines.mapped('field_name')

            # Pre-calc field definitions once
            field_defs = {
                name: Model._fields[name]
                for name in field_names
                if name in Model._fields
            }
            total_count = Model.search_count(domain)
            if total_limit:
                total_count = min(total_count, total_limit)
            batches = []

            for offset in range(0, total_count, batch_size):
                try:
                    # Calculate the actual limit for this batch
                    remaining_records = total_count - offset
                    current_batch_size = min(batch_size, remaining_records)
                    rows = Model.search_read(
                        domain=domain,
                        fields=field_names,
                        limit=current_batch_size,
                        offset=offset,
                        order=record.table_order
                    )
                except Exception as e:
                    raise ValidationError(
                        f"Invalid table order configuration: '{record.table_order}'.\n"
                        f"Please check the field name and sort format (e.g. 'name asc', 'id desc')."
                    )

                for row in rows:
                    for fname, field in field_defs.items():
                        row[fname] = _to_string(row.get(fname), field, Model,
                                                fname)
                batches.append(rows)
            record.table_rows = json.dumps(batches, cls=DashboardJSONEncoder)

    def _get_date_filter_domain(self):
        """
        Returns a domain based on the dashboard_date_filter context.
        Applies to the 'create_date' field if it exists in the model.
        
        :return: A list of domain tuples for date filtering.
        """
        filter_type = self.env.context.get('dashboard_date_filter', 'all')

        if filter_type == 'all' or not self.model_id:
            return []

        Model = self.env[self.model_id.model]
        if 'create_date' not in Model._fields:
            return []

        now = datetime.now()

        if filter_type == 'today':
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
            return [('create_date', '>=', start), ('create_date', '<=', end)]

        elif filter_type == 'this_week':
            start = now - timedelta(days=now.weekday())
            start = start.replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=6, hours=23, minutes=59, seconds=59)
            return [('create_date', '>=', start), ('create_date', '<=', end)]

        elif filter_type == 'this_month':
            start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            next_month = start.replace(day=28) + timedelta(days=4)
            end = (next_month - timedelta(days=next_month.day)).replace(hour=23, minute=59,
                                                                        second=59)
            return [('create_date', '>=', start), ('create_date', '<=', end)]

        elif filter_type == 'this_quarter':
            # Calculate start of current quarter
            # Quarter 1: Jan-Mar (1,2,3) -> starts Jan 1
            # Quarter 2: Apr-Jun (4,5,6) -> starts Apr 1
            # Quarter 3: Jul-Sep (7,8,9) -> starts Jul 1
            # Quarter 4: Oct-Dec (10,11,12) -> starts Oct 1
            month = (now.month - 1) // 3 * 3 + 1
            start = now.replace(month=month, day=1, hour=0, minute=0, second=0, microsecond=0)

            # Calculate end of current quarter (end of the month 2 months after start month)
            # Simplest way: go to start of next quarter and subtract 1 second
            if month == 10:
                next_quarter_start = now.replace(year=now.year + 1, month=1, day=1, hour=0,
                                                 minute=0, second=0, microsecond=0)
            else:
                next_quarter_start = now.replace(month=month + 3, day=1, hour=0, minute=0, second=0,
                                                 microsecond=0)

            end = next_quarter_start - timedelta(seconds=1)
            return [('create_date', '>=', start), ('create_date', '<=', end)]

        elif filter_type == 'this_year':
            start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            end = now.replace(month=12, day=31, hour=23, minute=59, second=59, microsecond=999999)
            return [('create_date', '>=', start), ('create_date', '<=', end)]

        elif filter_type == 'custom':
            start_str = self.env.context.get('dashboard_date_start')
            end_str = self.env.context.get('dashboard_date_end')

            if start_str and end_str:
                # Expecting strings like "YYYY-MM-DD"
                try:
                    start_date = datetime.strptime(start_str, '%Y-%m-%d')
                    end_date = datetime.strptime(end_str, '%Y-%m-%d')

                    # Set time to start of day for start date
                    start = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
                    # Set time to end of day for end date
                    end = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)

                    return [('create_date', '>=', start), ('create_date', '<=', end)]
                except (ValueError, TypeError):
                    pass

        return []

    def _get_custom_filter_domain(self):
        """
        Returns a domain based on the dashboard_custom_filter_id context.
        If the filter's model doesn't match the card's model, returns a domain that matches nothing.
        """
        filter_id = self.env.context.get('dashboard_custom_filter_id')
        if not filter_id:
            return []

        try:
            custom_filter = self.env['dashboard.custom.filter'].browse(int(filter_id))
            if not custom_filter.exists():
                return []

            # If models don't match, return a domain that ensures no records are found
            if custom_filter.model_id.id != self.model_id.id:
                # Return a domain that is always False to ensure "No Records Found"
                return [('id', '=', -1)]

            domain_str = custom_filter.domain or '[]'
            return safe_eval(domain_str)
        except Exception as e:
            _logger.error(f"Error applying custom filter: {e}")
            return []

    def get_dashboard_data(self):
        """
        This method fetches and aggregates data based on the card's configuration.
        """
        self.ensure_one()

        if not self.model_name or not self.group_by_field_id:
            _logger.warning(
                f"Dashboard card '{self.name}' is missing a model or a group_by field.")
            return [], None

        if self.aggregation_method != 'count' and not self.measure_field_id:
            _logger.warning(
                f"Dashboard card '{self.name}' requires a measure field for aggregation '{self.aggregation_method}'.")
            return [], None

        try:
            domain = safe_eval(self.domain or '[]')
            # Apply global date filter
            date_filter_domain = self._get_date_filter_domain()
            if date_filter_domain:
                domain += date_filter_domain

            # Apply custom backend filter
            custom_filter_domain = self._get_custom_filter_domain()
            if custom_filter_domain:
                domain = domain + custom_filter_domain


        except (ValueError, SyntaxError) as e:
            _logger.error(
                f"Invalid domain on card '{self.name}': {self.domain}. Error: {e}")
            return [], None

        Model = self.env[self.model_name]
        group_by_field = self.group_by_field_id.name
        groupby_list = [group_by_field]

        measure_field = self.measure_field_id.name
        aggregated_field = measure_field
        agg_spec = f"{measure_field}:{self.aggregation_method}"
        fields_list = [agg_spec]

        try:
            read_group_result = Model._read_group(domain, groupby_list,
                                                  fields_list)
        except Exception as e:
            _logger.error(
                f"Error executing _read_group for card '{self.name}' on model '{self.model_name}': {e}")
            return [], None

        return read_group_result, aggregated_field

    @api.depends('measure_field_id', 'group_by_field_id', 'domain', 'model_id',
                 'aggregation_method', 'type', 'record_limit')
    @api.depends_context('dashboard_date_filter', 'dashboard_date_start', 'dashboard_date_end',
                         'dashboard_custom_filter_id')
    def _compute_chart_data(self):
        """Fetch and aggregate data for rendering charts."""
        for rec in self:
            rec.chart_x_axis_data = json.dumps([], cls=DashboardJSONEncoder)
            rec.chart_y_axis_data = json.dumps([], cls=DashboardJSONEncoder)

            if rec.type == 'chart' and rec.model_id and rec.group_by_field_id:
                try:
                    model_obj = self.env[rec.model_id.model]
                    domain = safe_eval(rec.domain or '[]')

                    # Apply global date filter
                    date_filter_domain = rec._get_date_filter_domain()
                    if date_filter_domain:
                        domain = domain + date_filter_domain

                    # Apply custom backend filter
                    custom_filter_domain = rec._get_custom_filter_domain()
                    if custom_filter_domain:
                        domain = domain + custom_filter_domain

                    _logger.info(f"[_compute_chart_data] Final Domain for {rec.name}: {domain}")

                    groupby_field = rec.group_by_field_id.name

                    measure_field = rec.measure_field_id.name
                    agg_key = f"{measure_field}:{rec.aggregation_method}"

                    if rec.record_limit:
                        ids = model_obj.search(domain,
                                               limit=rec.record_limit).ids
                        domain = [('id', 'in', ids)]

                    # formatted_read_group returns dicts with formatted values
                    # (Many2one as [id, name]); read_group deprecated in 19.0.
                    results = model_obj.formatted_read_group(
                        domain,
                        [groupby_field],
                        [agg_key],
                    )

                    x_vals = []
                    y_vals = []

                    for res in results:
                        label = res.get(groupby_field)
                        if isinstance(label, (list, tuple)):
                            label = label[1]
                        x_vals.append(str(label) if label else "Undefined")

                        value = res.get(agg_key) or res.get(
                            measure_field) or 0.0
                        y_vals.append(float(value))

                    rec.chart_x_axis_data = json.dumps(x_vals, cls=DashboardJSONEncoder)
                    rec.chart_y_axis_data = json.dumps(y_vals, cls=DashboardJSONEncoder)
                except Exception as e:
                    _logger.error("Dashboard Chart Error: %s", str(e))
                    rec.chart_x_axis_data = json.dumps([], cls=DashboardJSONEncoder)
                    rec.chart_y_axis_data = json.dumps([], cls=DashboardJSONEncoder)
