# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Ayana KP (odoo@cybrosys.com)
#    Modified by: Broigm - API configuration improvements
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
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class ConnectionApi(models.Model):
    """Configuración de modelos para REST API con mejores controles"""
    _name = 'connection.api'
    _description = 'REST API Configuration'
    _rec_name = 'display_name'

    model_id = fields.Many2one(
        'ir.model',
        string="Model",
        required=True,
        ondelete='cascade',
        domain="[('transient', '=', False)]",
        help="Modelo que será accesible a través de la REST API."
    )

    display_name = fields.Char(
        string="Name",
        compute='_compute_display_name',
        store=True
    )

    # Permisos de métodos HTTP
    is_get = fields.Boolean(
        string='GET (Read)',
        default=True,
        help="Permite operaciones de lectura (GET) en este modelo."
    )

    is_post = fields.Boolean(
        string='POST (Create)',
        default=False,
        help="Permite operaciones de creación (POST) en este modelo."
    )

    is_put = fields.Boolean(
        string='PUT (Update)',
        default=False,
        help="Permite operaciones de actualización (PUT) en este modelo."
    )

    is_delete = fields.Boolean(
        string='DELETE',
        default=False,
        help="Permite operaciones de eliminación (DELETE) en este modelo."
    )

    # Configuraciones adicionales
    active = fields.Boolean(
        string="Active",
        default=True,
        help="Si está desactivado, el modelo no estará disponible en la API."
    )

    allowed_fields = fields.Text(
        string="Allowed Fields",
        help="Lista de campos permitidos separados por comas. Si está vacío, todos los campos son permitidos."
    )

    forbidden_fields = fields.Text(
        string="Forbidden Fields",
        default="__last_update,create_uid,create_date,write_uid,write_date",
        help="Lista de campos prohibidos separados por comas."
    )

    max_records_limit = fields.Integer(
        string="Max Records Limit",
        default=1000,
        help="Límite máximo de registros que se pueden obtener en una sola request GET."
    )

    require_record_id_for_write = fields.Boolean(
        string="Require ID for Write Operations",
        default=True,
        help="Si está marcado, las operaciones PUT/DELETE requieren un ID específico."
    )

    # Campos informativos
    api_endpoint = fields.Char(
        string="API Endpoint",
        compute='_compute_api_endpoint',
        help="URL del endpoint de la API para este modelo."
    )

    description = fields.Text(
        string="Description",
        help="Descripción del propósito de esta configuración de API."
    )

    @api.depends('model_id')
    def _compute_display_name(self):
        """Calcula el nombre para mostrar"""
        for record in self:
            if record.model_id:
                record.display_name = f"API: {record.model_id.name}"
            else:
                record.display_name = "API Configuration"

    @api.depends('model_id')
    def _compute_api_endpoint(self):
        """Calcula la URL del endpoint de la API"""
        for record in self:
            if record.model_id:
                base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url', 'http://localhost:8069')
                record.api_endpoint = f"{base_url}/api/v1/{record.model_id.model}"
            else:
                record.api_endpoint = ""

    @api.constrains('model_id')
    def _check_unique_model(self):
        """Valida que no haya configuraciones duplicadas para el mismo modelo"""
        for record in self:
            if record.model_id:
                existing = self.search([
                    ('model_id', '=', record.model_id.id),
                    ('id', '!=', record.id)
                ])
                if existing:
                    raise ValidationError(
                        _("Ya existe una configuración de API para el modelo %s") % record.model_id.name
                    )

    @api.constrains('max_records_limit')
    def _check_max_records_limit(self):
        """Valida el límite máximo de registros"""
        for record in self:
            if record.max_records_limit <= 0:
                raise ValidationError(_("El límite máximo de registros debe ser mayor a 0"))
            if record.max_records_limit > 10000:
                raise ValidationError(_("El límite máximo de registros no puede exceder 10,000"))

    def get_allowed_fields(self):
        """Obtiene la lista de campos permitidos para este modelo"""
        self.ensure_one()

        if not self.allowed_fields:
            # Si no hay campos específicos permitidos, obtener todos los campos del modelo
            model_obj = self.env[self.model_id.model]
            all_fields = list(model_obj._fields.keys())
        else:
            all_fields = [field.strip() for field in self.allowed_fields.split(',') if field.strip()]

        # Remover campos prohibidos
        forbidden = []
        if self.forbidden_fields:
            forbidden = [field.strip() for field in self.forbidden_fields.split(',') if field.strip()]

        allowed = [field for field in all_fields if field not in forbidden]
        return allowed

    def get_forbidden_fields(self):
        """Obtiene la lista de campos prohibidos"""
        self.ensure_one()

        if not self.forbidden_fields:
            return []

        return [field.strip() for field in self.forbidden_fields.split(',') if field.strip()]

    def is_method_allowed(self, method):
        """Verifica si un método HTTP está permitido"""
        self.ensure_one()

        if not self.active:
            return False

        method_map = {
            'GET': self.is_get,
            'POST': self.is_post,
            'PUT': self.is_put,
            'DELETE': self.is_delete
        }

        return method_map.get(method.upper(), False)

    def action_test_api_endpoint(self):
        """Acción para probar el endpoint de la API (útil para botón en vista)"""
        self.ensure_one()

        if not self.model_id:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': _('No model selected'),
                    'type': 'warning',
                }
            }

        return {
            'type': 'ir.actions.act_url',
            'url': self.api_endpoint,
            'target': 'new',
        }

    @api.model
    def get_api_statistics(self):
        """Obtiene estadísticas de uso de la API"""
        stats = {}

        # Estadísticas por modelo
        api_configs = self.search([('active', '=', True)])
        stats['active_models'] = len(api_configs)
        stats['total_models'] = len(self.search([]))

        # Estadísticas de usuarios con API keys
        users_with_keys = self.env['res.users'].search([('api_key', '!=', False)])
        stats['users_with_api_keys'] = len(users_with_keys)
        stats['total_api_requests'] = sum(users_with_keys.mapped('api_requests_count'))

        return stats

    def toggle_active(self):
        """Alterna el estado activo de la configuración"""
        for record in self:
            record.active = not record.active

    @api.model
    def create_default_configurations(self):
        """Crea configuraciones por defecto para modelos comunes"""
        default_models = [
            ('res.partner', {'is_get': True, 'is_post': True, 'is_put': True, 'is_delete': False}),
            ('product.product', {'is_get': True, 'is_post': True, 'is_put': True, 'is_delete': False}),
            ('sale.order', {'is_get': True, 'is_post': True, 'is_put': True, 'is_delete': False}),
            ('account.move', {'is_get': True, 'is_post': False, 'is_put': False, 'is_delete': False}),
        ]

        created_configs = []
        for model_name, config in default_models:
            model_obj = self.env['ir.model'].search([('model', '=', model_name)], limit=1)
            if model_obj:
                existing = self.search([('model_id', '=', model_obj.id)])
                if not existing:
                    api_config = self.create({
                        'model_id': model_obj.id,
                        'description': f'Default API configuration for {model_obj.name}',
                        **config
                    })
                    created_configs.append(api_config)

        return created_configs
