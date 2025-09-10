# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Ayana KP (odoo@cybrosys.com)
#    Modified by: Broigm - Improvements in authentication and structure
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
import json
import logging
import base64
from datetime import datetime, date, timedelta
from odoo import http
from odoo.http import request
from werkzeug.exceptions import BadRequest, Unauthorized, NotFound, MethodNotAllowed

_logger = logging.getLogger(__name__)


class RestApi(http.Controller):
    """Controlador API REST mejorado con autenticación basada en API Key solamente"""

    def _json_response(self, data, status=200):
        """Genera respuesta JSON estandarizada"""
        response = request.make_response(
            json.dumps(data, ensure_ascii=False, indent=2),
            headers=[('Content-Type', 'application/json')]
        )
        response.status_code = status
        return response

    def _error_response(self, message, status=400, error_code=None):
        """Genera respuesta de error estandarizada"""
        error_data = {
            'error': True,
            'message': message,
            'status_code': status
        }
        if error_code:
            error_data['error_code'] = error_code

        return self._json_response(error_data, status)

    def _authenticate_api_key(self, api_key):
        """
        Autentica usando solo la API key y configura la sesión del usuario
        Returns: (success: bool, user_id: int or None, error_message: str or None)
        """
        if not api_key:
            return False, None, "API Key no proporcionada"

        try:
            user = request.env['res.users'].sudo().search([
                ('api_key', '=', api_key),
                ('active', '=', True)
            ], limit=1)

            if not user:
                return False, None, "API Key inválida o usuario inactivo"

            # Verificar si la API key no ha expirado (si implementas expiración)
            if hasattr(user, 'api_key_expiry') and user.api_key_expiry:
                if user.api_key_expiry < datetime.now():
                    return False, None, "API Key expirada"

            # Configurar la sesión con el usuario autenticado
            request.session.uid = user.id
            request.env.user = user

            return True, user.id, None

        except Exception as e:
            _logger.error(f"Error en autenticación API: {str(e)}")
            return False, None, "Error interno de autenticación"

    def _serialize_record_values(self, records):
        """Serializa los valores de los registros para JSON"""
        if not records:
            return []

        serialized_records = []
        for record in records:
            serialized_record = {}
            for key, value in record.items():
                if isinstance(value, (datetime, date)):
                    serialized_record[key] = value.isoformat()
                elif isinstance(value, bytes):
                    serialized_record[key] = base64.b64encode(value).decode('utf-8')
                elif hasattr(value, '__iter__') and not isinstance(value, (str, dict)):
                    try:
                        serialized_record[key] = list(value) if value else []
                    except:
                        serialized_record[key] = str(value)
                else:
                    serialized_record[key] = value
            serialized_records.append(serialized_record)

        return serialized_records

    def _get_model_config(self, model_name):
        """Obtiene la configuración de la API para un modelo"""
        model_obj = request.env['ir.model'].sudo().search([('model', '=', model_name)], limit=1)
        if not model_obj:
            return None, "Modelo no encontrado"

        api_config = request.env['connection.api'].sudo().search([
            ('model_id', '=', model_obj.id)
        ], limit=1)

        if not api_config:
            return None, "Modelo no configurado para API REST"

        return api_config, None

    def _parse_request_data(self, method):
        """Parsea los datos de la request según el método HTTP"""
        data = {}
        fields = []

        if method == 'GET':
            # Para GET, intentar obtener campos del query string o JSON body
            query_params = dict(request.httprequest.args)

            try:
                if request.httprequest.data:
                    json_data = json.loads(request.httprequest.data)
                    data.update(json_data)
                    if 'fields' in json_data:
                        fields = json_data['fields']
            except json.JSONDecodeError:
                pass

            if not fields and 'fields' in query_params:
                fields = [field.strip() for field in query_params['fields'].split(',')]

        elif method in ['POST', 'PUT']:
            try:
                if request.httprequest.data:
                    data = json.loads(request.httprequest.data)
                    if 'fields' in data:
                        fields = data['fields']
                else:
                    return None, None, "No se proporcionaron datos JSON"
            except json.JSONDecodeError:
                return None, None, "JSON inválido"

        return data, fields, None

    @http.route(['/api/v1/auth'], type='http', auth='none', methods=['POST'], csrf=False)
    def authenticate(self, **kw):
        """Endpoint de autenticación que genera API key"""
        try:
            data = json.loads(request.httprequest.data or '{}')
        except json.JSONDecodeError:
            return self._error_response("JSON inválido", 400)

        username = data.get('username') or request.httprequest.headers.get('username')
        password = data.get('password') or request.httprequest.headers.get('password')
        database = data.get('database') or request.httprequest.headers.get('database', request.env.cr.dbname)

        if not all([username, password]):
            return self._error_response("Username y password son requeridos", 400)

        try:
            # Actualizar sesión con la base de datos
            request.session.update(http.get_default_session(), db=database)

            # Autenticar credenciales
            auth_result = request.session.authenticate(
                database,
                {'login': username, 'password': password, 'type': 'password'}
            )

            if not auth_result:
                return self._error_response("Credenciales inválidas", 401)

            # Generar o recuperar API key
            user = request.env['res.users'].browse(auth_result['uid'])
            api_key = user.generate_api_key()

            response_data = {
                "success": True,
                "message": "Autenticación exitosa",
                "data": {
                    "user_id": user.id,
                    "username": user.login,
                    "name": user.name,
                    "api_key": api_key,
                    "database": database
                }
            }

            return self._json_response(response_data)

        except Exception as e:
            _logger.error(f"Error en autenticación: {str(e)}")
            return self._error_response("Error interno de autenticación", 500)

    @http.route(['/api/v1/<model_name>', '/api/v1/<model_name>/<int:record_id>'],
                type='http', auth='none', methods=['GET', 'POST', 'PUT', 'DELETE'], csrf=False)
    def api_handler(self, model_name, record_id=None, **kw):
        """Endpoint principal de la API REST"""
        method = request.httprequest.method

        # Autenticación usando API key
        api_key = request.httprequest.headers.get('X-API-Key') or request.httprequest.headers.get('api-key')
        success, user_id, error_msg = self._authenticate_api_key(api_key)

        if not success:
            return self._error_response(error_msg, 401, "AUTHENTICATION_FAILED")

        # Obtener configuración del modelo
        api_config, error_msg = self._get_model_config(model_name)
        if not api_config:
            return self._error_response(error_msg, 404, "MODEL_NOT_CONFIGURED")

        # Verificar permisos del método
        method_permissions = {
            'GET': api_config.is_get,
            'POST': api_config.is_post,
            'PUT': api_config.is_put,
            'DELETE': api_config.is_delete
        }

        if not method_permissions.get(method, False):
            return self._error_response(f"Método {method} no permitido para este modelo", 405, "METHOD_NOT_ALLOWED")

        # Parsear datos de la request
        data, fields, error_msg = self._parse_request_data(method)
        if error_msg:
            return self._error_response(error_msg, 400, "INVALID_REQUEST_DATA")

        try:
            return self._handle_request(method, api_config.model_id.model, record_id, data, fields)
        except Exception as e:
            _logger.error(f"Error procesando request {method} para {model_name}: {str(e)}")
            return self._error_response("Error interno del servidor", 500, "INTERNAL_SERVER_ERROR")

    def _handle_request(self, method, model_name, record_id, data, fields):
        """Maneja las diferentes operaciones CRUD"""
        model = request.env[model_name]

        if method == 'GET':
            return self._handle_get(model, record_id, fields)
        elif method == 'POST':
            return self._handle_post(model, data, fields)
        elif method == 'PUT':
            return self._handle_put(model, record_id, data, fields)
        elif method == 'DELETE':
            return self._handle_delete(model, record_id)

    def _handle_get(self, model, record_id, fields):
        """Maneja requests GET"""
        try:
            if record_id:
                # Obtener registro específico
                domain = [('id', '=', record_id)]
                search_fields = fields if fields else []
            else:
                # Obtener todos los registros
                domain = []
                search_fields = fields if fields else ['id', 'display_name']

            records = model.search_read(domain=domain, fields=search_fields)
            serialized_records = self._serialize_record_values(records)

            response_data = {
                "success": True,
                "count": len(serialized_records),
                "data": serialized_records
            }

            return self._json_response(response_data)

        except Exception as e:
            _logger.error(f"Error en GET: {str(e)}")
            return self._error_response("Error obteniendo registros", 500)

    def _handle_post(self, model, data, fields):
        """Maneja requests POST (crear)"""
        if not data.get('values'):
            return self._error_response("Se requiere 'values' para crear registro", 400)

        try:
            new_record = model.create(data['values'])

            # Obtener el registro creado con los campos especificados
            search_fields = fields if fields else ['id', 'display_name']
            record_data = new_record.read(search_fields)[0]
            serialized_record = self._serialize_record_values([record_data])

            response_data = {
                "success": True,
                "message": "Registro creado exitosamente",
                "data": serialized_record[0] if serialized_record else {}
            }

            return self._json_response(response_data, 201)

        except Exception as e:
            _logger.error(f"Error en POST: {str(e)}")
            return self._error_response(f"Error creando registro: {str(e)}", 400)

    def _handle_put(self, model, record_id, data, fields):
        """Maneja requests PUT (actualizar)"""
        if not record_id:
            return self._error_response("ID de registro requerido para actualización", 400)

        if not data.get('values'):
            return self._error_response("Se requiere 'values' para actualizar registro", 400)

        try:
            record = model.browse(record_id)
            if not record.exists():
                return self._error_response("Registro no encontrado", 404)

            record.write(data['values'])

            # Obtener el registro actualizado
            search_fields = fields if fields else ['id', 'display_name']
            record_data = record.read(search_fields)[0]
            serialized_record = self._serialize_record_values([record_data])

            response_data = {
                "success": True,
                "message": "Registro actualizado exitosamente",
                "data": serialized_record[0] if serialized_record else {}
            }

            return self._json_response(response_data)

        except Exception as e:
            _logger.error(f"Error en PUT: {str(e)}")
            return self._error_response(f"Error actualizando registro: {str(e)}", 400)

    def _handle_delete(self, model, record_id):
        """Maneja requests DELETE"""
        if not record_id:
            return self._error_response("ID de registro requerido para eliminación", 400)

        try:
            record = model.browse(record_id)
            if not record.exists():
                return self._error_response("Registro no encontrado", 404)

            # Guardar información del registro antes de eliminarlo
            record_info = {
                "id": record.id,
                "display_name": record.display_name if hasattr(record, 'display_name') else str(record)
            }

            record.unlink()

            response_data = {
                "success": True,
                "message": "Registro eliminado exitosamente",
                "deleted_record": record_info
            }

            return self._json_response(response_data)

        except Exception as e:
            _logger.error(f"Error en DELETE: {str(e)}")
            return self._error_response(f"Error eliminando registro: {str(e)}", 400)

    @http.route(['/api/v1/models'], type='http', auth='none', methods=['GET'], csrf=False)
    def list_available_models(self, **kw):
        """Endpoint para listar modelos disponibles en la API"""
        api_key = request.httprequest.headers.get('X-API-Key') or request.httprequest.headers.get('api-key')
        success, user_id, error_msg = self._authenticate_api_key(api_key)

        if not success:
            return self._error_response(error_msg, 401)

        try:
            api_configs = request.env['connection.api'].sudo().search([])
            models_data = []

            for config in api_configs:
                model_info = {
                    "model": config.model_id.model,
                    "name": config.model_id.name,
                    "methods": {
                        "GET": config.is_get,
                        "POST": config.is_post,
                        "PUT": config.is_put,
                        "DELETE": config.is_delete
                    }
                }
                models_data.append(model_info)

            response_data = {
                "success": True,
                "count": len(models_data),
                "data": models_data
            }

            return self._json_response(response_data)

        except Exception as e:
            _logger.error(f"Error listando modelos: {str(e)}")
            return self._error_response("Error interno del servidor", 500)
