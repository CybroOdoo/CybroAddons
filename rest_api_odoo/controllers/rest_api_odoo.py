# -*- coding: utf-8 -*-
import json
import logging
import base64
import ast
from datetime import datetime, date, timedelta
from odoo import http, fields
from odoo.http import request
from .jwt_auth import JWTAuthMixin

_logger = logging.getLogger(__name__)


class RestApi(http.Controller, JWTAuthMixin):
    """Controlador API REST mejorado con JWT y filtrado avanzado"""

    def _json_response(self, data, status=200):
        """Genera respuesta JSON estandarizada con soporte CORS"""
        try:
            cors_headers = [
                ('Content-Type', 'application/json; charset=utf-8'),
                ('Access-Control-Allow-Origin', '*'),
                ('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS'),
                ('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-API-Key, api-key'),
                ('Access-Control-Expose-Headers', 'Content-Type, Authorization'),
                ('Access-Control-Max-Age', '86400')
            ]

            response = request.make_response(
                json.dumps(data, ensure_ascii=False, indent=2, default=str),
                headers=cors_headers
            )
            response.status_code = status
            return response
        except Exception as e:
            _logger.error(f"Error creating JSON response: {str(e)}")
            fallback_data = {
                'error': True,
                'message': 'Error interno creando respuesta JSON',
                'status_code': 500
            }
            cors_headers = [
                ('Content-Type', 'application/json; charset=utf-8'),
                ('Access-Control-Allow-Origin', '*'),
                ('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS'),
                ('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-API-Key, api-key')
            ]
            return request.make_response(
                json.dumps(fallback_data, indent=2),
                status=500,
                headers=cors_headers
            )

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

    def _serialize_record_values(self, records):
        """Serializa los valores de los registros para JSON"""
        if not records:
            return []

        serialized_records = []
        for record in records:
            serialized_record = {}
            for key, value in record.items():
                try:
                    if isinstance(value, (datetime, date)):
                        serialized_record[key] = value.isoformat()
                    elif isinstance(value, bytes):
                        serialized_record[key] = base64.b64encode(value).decode('utf-8')
                    elif isinstance(value, tuple) and len(value) == 2:
                        # Para relaciones Many2one que vienen como (id, name)
                        serialized_record[key] = list(value)
                    elif hasattr(value, '__iter__') and not isinstance(value, (str, dict, bytes)):
                        try:
                            serialized_record[key] = list(value) if value else []
                        except:
                            serialized_record[key] = str(value)
                    else:
                        serialized_record[key] = value
                except Exception as e:
                    _logger.warning(f"Error serializing field {key}: {str(e)}")
                    serialized_record[key] = str(value) if value is not None else None

            serialized_records.append(serialized_record)

        return serialized_records

    def _get_model_config(self, model_name):
        """Obtiene la configuración de la API para un modelo"""
        try:
            model_obj = request.env['ir.model'].sudo().search([('model', '=', model_name)], limit=1)
            if not model_obj:
                return None, "Modelo no encontrado"

            api_config = request.env['connection.api'].sudo().search([
                ('model_id', '=', model_obj.id),
                ('active', '=', True)
            ], limit=1)

            if not api_config:
                return None, "Modelo no configurado para API REST"

            return api_config, None
        except Exception as e:
            _logger.error(f"Error getting model config for {model_name}: {str(e)}")
            return None, f"Error obteniendo configuración del modelo: {str(e)}"

    def _parse_request_data(self, method):
        """Parsea los datos de la request con parámetros avanzados"""
        data = {}
        fields = []
        domain = []
        limit = None
        offset = None
        order = None

        try:
            if method == 'GET':
                query_params = dict(request.httprequest.args)

                # Parsear domain
                if 'domain' in query_params:
                    try:
                        domain = ast.literal_eval(query_params['domain'])
                        if not isinstance(domain, list):
                            domain = []
                    except:
                        _logger.warning("Invalid domain format, ignoring")
                        domain = []

                # Parsear fields
                if 'fields' in query_params:
                    fields = [field.strip() for field in query_params['fields'].split(',') if field.strip()]

                # Parsear limit
                if 'limit' in query_params:
                    try:
                        limit = int(query_params['limit'])
                        if limit <= 0:
                            limit = None
                    except:
                        pass

                # Parsear offset
                if 'offset' in query_params:
                    try:
                        offset = int(query_params['offset'])
                        if offset < 0:
                            offset = None
                    except:
                        pass

                # Parsear order
                if 'order' in query_params:
                    order = query_params['order'].strip()
                    if not order:
                        order = None

                # También intentar JSON body para GET (opcional)
                try:
                    if request.httprequest.data:
                        json_data = json.loads(request.httprequest.data.decode('utf-8'))
                        data.update(json_data)
                        if 'fields' in json_data and not fields:
                            fields = json_data['fields']
                        if 'domain' in json_data and not domain:
                            domain = json_data['domain']
                except:
                    pass

            elif method in ['POST', 'PUT']:
                try:
                    if request.httprequest.data:
                        data = json.loads(request.httprequest.data.decode('utf-8'))
                        if 'fields' in data:
                            fields = data['fields']
                    else:
                        return None, None, None, None, None, None, "No se proporcionaron datos JSON"
                except (json.JSONDecodeError, UnicodeDecodeError) as e:
                    return None, None, None, None, None, None, f"JSON inválido: {str(e)}"

            return data, fields, domain, limit, offset, order, None
        except Exception as e:
            _logger.error(f"Error parsing request data: {str(e)}")
            return None, None, None, None, None, None, f"Error procesando datos de la request: {str(e)}"

    @http.route(['/api/v1/auth'], type='http', auth='none', methods=['POST', 'OPTIONS'], csrf=False)
    def authenticate(self, **kw):
        """Endpoint de autenticación que genera JWT token"""
        # Manejar peticiones OPTIONS para CORS preflight
        if request.httprequest.method == 'OPTIONS':
            return self._handle_cors_preflight()

        try:
            if request.httprequest.data:
                data = json.loads(request.httprequest.data.decode('utf-8'))
            else:
                data = {}
        except (json.JSONDecodeError, UnicodeDecodeError):
            return self._error_response("JSON inválido", 400)

        username = data.get('username') or request.httprequest.headers.get('username')
        password = data.get('password') or request.httprequest.headers.get('password')
        database = data.get('database') or request.httprequest.headers.get('database') or request.env.cr.dbname
        expires_in = data.get('expires_in_hours', 24)

        if not all([username, password]):
            return self._error_response("Username y password son requeridos", 400)

        # Validar expires_in
        if not isinstance(expires_in, int) or expires_in < 1 or expires_in > 168:  # Max 7 días
            expires_in = 24

        try:
            # Autenticar credenciales - Método correcto para Odoo 18.0
            # Usar el env actual para buscar y verificar el usuario
            try:
                # Cambiar temporalmente la base de datos si es necesario
                original_db = request.env.cr.dbname
                if database != original_db:
                    # Para tests, usar la base de datos actual
                    database = original_db

                # Buscar usuario con sudo para evitar restricciones de acceso
                user_obj = request.env['res.users'].sudo()
                user = user_obj.search([
                    '|', ('login', '=', username), ('email', '=', username)
                ], limit=1)

                if user and user._check_credentials(password, {}):
                    uid = user.id
                else:
                    uid = False
            except Exception:
                uid = False

            if not uid:
                return self._error_response("Credenciales inválidas", 401)

            # Generar JWT token
            user = request.env['res.users'].browse(uid)
            token = self._generate_jwt_token(uid, expires_in)

            if not token:
                return self._error_response("Error generando token de acceso", 500)

            response_data = {
                "success": True,
                "message": "Autenticación exitosa",
                "data": {
                    "user_id": user.id,
                    "username": user.login,
                    "name": user.name,
                    "access_token": token,
                    "token_type": "Bearer",
                    "expires_in": expires_in * 3600,  # En segundos
                    "database": database
                }
            }

            return self._json_response(response_data)

        except Exception as e:
            _logger.error(f"Error en autenticación: {str(e)}")
            return self._error_response("Error interno de autenticación", 500)

    @http.route(['/api/v1/refresh'], type='http', auth='none', methods=['POST'], csrf=False)
    def refresh_token(self, **kw):
        """Endpoint para refrescar un JWT token"""
        try:
            success, user_id, error_msg = self._authenticate_request()
            if not success:
                return self._error_response(error_msg, 401, "TOKEN_INVALID")

            # Generar nuevo token
            try:
                data = json.loads(request.httprequest.data.decode('utf-8')) if request.httprequest.data else {}
                expires_in = data.get('expires_in_hours', 24)
                if not isinstance(expires_in, int) or expires_in < 1 or expires_in > 168:
                    expires_in = 24
            except:
                expires_in = 24

            new_token = self._generate_jwt_token(user_id, expires_in)
            if not new_token:
                return self._error_response("Error generando nuevo token", 500)

            user = request.env['res.users'].browse(user_id)
            response_data = {
                "success": True,
                "message": "Token renovado exitosamente",
                "data": {
                    "access_token": new_token,
                    "token_type": "Bearer",
                    "expires_in": expires_in * 3600,
                    "user_id": user.id,
                    "username": user.login
                }
            }

            return self._json_response(response_data)

        except Exception as e:
            _logger.error(f"Error refreshing token: {str(e)}")
            return self._error_response("Error interno renovando token", 500)

    def _authenticate_request(self):
        """
        Autentica la request usando JWT token
        Returns: (success: bool, user_id: int or None, error_message: str or None)
        """
        # Buscar token en headers
        auth_header = request.httprequest.headers.get('Authorization')
        if not auth_header:
            # Fallback a headers alternativos para compatibilidad
            token = request.httprequest.headers.get('X-API-Key') or request.httprequest.headers.get('api-key')
            if token:
                auth_header = f"Bearer {token}"

        if not auth_header:
            return False, None, "Token de autorización no proporcionado (use Authorization: Bearer <token>)"

        return self._validate_jwt_token(auth_header)

    @http.route(['/api/v1/<model_name>', '/api/v1/<model_name>/<int:record_id>'],
                type='http', auth='none', methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'], csrf=False)
    def api_handler(self, model_name, record_id=None, **kw):
        """Endpoint principal de la API REST con JWT y filtrado avanzado"""
        method = request.httprequest.method

        # Manejar peticiones OPTIONS para CORS preflight
        if method == 'OPTIONS':
            return self._handle_cors_preflight()

        # Autenticación usando JWT
        success, user_id, error_msg = self._authenticate_request()
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

        # Parsear datos de la request con parámetros avanzados
        data, fields, domain, limit, offset, order, error_msg = self._parse_request_data(method)
        if error_msg:
            return self._error_response(error_msg, 400, "INVALID_REQUEST_DATA")

        try:
            return self._handle_request(method, api_config.model_id.model, record_id, data, fields, domain, limit, offset, order, api_config)
        except Exception as e:
            _logger.error(f"Error procesando request {method} para {model_name}: {str(e)}")
            return self._error_response("Error interno del servidor", 500, "INTERNAL_SERVER_ERROR")

    def _handle_request(self, method, model_name, record_id, data, fields, domain, limit, offset, order, api_config=None):
        """Maneja las diferentes operaciones CRUD con parámetros avanzados"""
        try:
            model = request.env[model_name]

            if method == 'GET':
                return self._handle_get(model, record_id, fields, domain, limit, offset, order, api_config)
            elif method == 'POST':
                return self._handle_post(model, data, fields)
            elif method == 'PUT':
                return self._handle_put(model, record_id, data, fields)
            elif method == 'DELETE':
                return self._handle_delete(model, record_id)
        except Exception as e:
            _logger.error(f"Error in _handle_request: {str(e)}")
            raise

    def _handle_get(self, model, record_id, fields, domain, limit, offset, order, api_config=None):
        """Maneja requests GET con filtrado avanzado"""
        try:
            # Aplicar límites de la configuración
            max_limit = getattr(api_config, 'max_records_limit', 1000) if api_config else 1000
            if limit and limit > max_limit:
                limit = max_limit

            if record_id:
                # Obtener registro específico
                search_domain = [('id', '=', record_id)]
                search_fields = fields if fields else []
                records = model.search_read(domain=search_domain, fields=search_fields)
                total_count = len(records)

                response_data = {
                    "success": True,
                    "count": len(records),
                    "total": total_count,
                    "data": self._serialize_record_values(records)
                }
            else:
                # Obtener registros con filtros
                search_domain = domain if domain else []
                search_fields = fields if fields else ['id', 'display_name']

                # Contar total sin límite para metadatos
                try:
                    total_count = model.search_count(search_domain)
                except:
                    total_count = None

                # Búsqueda con parámetros
                search_params = {
                    'domain': search_domain,
                    'fields': search_fields
                }

                if limit:
                    search_params['limit'] = limit
                if offset:
                    search_params['offset'] = offset
                if order:
                    search_params['order'] = order

                records = model.search_read(**search_params)

                response_data = {
                    "success": True,
                    "count": len(records),
                    "data": self._serialize_record_values(records)
                }

                # Agregar metadatos de paginación
                if total_count is not None:
                    response_data["total"] = total_count
                if offset:
                    response_data["offset"] = offset
                if limit:
                    response_data["limit"] = limit

                # Información de paginación
                if limit and total_count is not None:
                    current_offset = offset or 0
                    has_more = (current_offset + limit) < total_count
                    response_data["has_more"] = has_more
                    if has_more:
                        response_data["next_offset"] = current_offset + limit

            return self._json_response(response_data)

        except Exception as e:
            _logger.error(f"Error en GET: {str(e)}")
            return self._error_response(f"Error obteniendo registros: {str(e)}", 500)

    def _handle_post(self, model, data, fields):
        """Maneja requests POST (crear)"""
        if not data.get('values'):
            return self._error_response("Se requiere 'values' para crear registro", 400)

        try:
            new_record = model.create(data['values'])

            # Obtener el registro creado con los campos especificados
            search_fields = fields if fields else ['id', 'display_name']
            record_data = new_record.read(search_fields)[0]

            response_data = {
                "success": True,
                "message": "Registro creado exitosamente",
                "count": 1,
                "data": self._serialize_record_values([record_data])
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

            response_data = {
                "success": True,
                "message": "Registro actualizado exitosamente",
                "count": 1,
                "data": self._serialize_record_values([record_data])
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
        success, user_id, error_msg = self._authenticate_request()
        if not success:
            return self._error_response(error_msg, 401)

        try:
            api_configs = request.env['connection.api'].sudo().search([('active', '=', True)])
            models_data = []

            for config in api_configs:
                model_info = {
                    "model": config.model_id.model,
                    "name": config.model_id.name,
                    "description": config.description or f"API REST para el modelo {config.model_id.name}",
                    "methods": {
                        "GET": config.is_get,
                        "POST": config.is_post,
                        "PUT": config.is_put,
                        "DELETE": config.is_delete
                    },
                    "max_records_limit": config.max_records_limit,
                    "endpoints": {
                        "collection": f"/api/v1/{config.model_id.model}",
                        "item": f"/api/v1/{config.model_id.model}/{{id}}",
                        "schema": f"/api/v1/schema/{config.model_id.model}"
                    }
                }
                models_data.append(model_info)

            # Agregar información de documentación
            base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url', 'http://localhost:8069')
            response_data = {
                "success": True,
                "count": len(models_data),
                "data": models_data,
                "documentation": {
                    "swagger_ui": f"{base_url}/api/v1/docs",
                    "openapi_spec": f"{base_url}/api/v1/openapi.json"
                },
                "authentication": {
                    "type": "JWT Bearer Token",
                    "header": "Authorization: Bearer <token>",
                    "auth_endpoint": f"{base_url}/api/v1/auth",
                    "refresh_endpoint": f"{base_url}/api/v1/refresh"
                }
            }

            return self._json_response(response_data)

        except Exception as e:
            _logger.error(f"Error listando modelos: {str(e)}")
            return self._error_response("Error interno del servidor", 500)

    @http.route(['/api/v1/health'], type='http', auth='none', methods=['GET'], csrf=False)
    def health_check(self, **kwargs):
        """Endpoint de verificación de salud de la API"""
        try:
            # Verificar conexión a BD
            request.env.cr.execute("SELECT 1")

            # Verificar configuraciones activas
            active_configs = len(request.env["connection.api"].sudo().search([("active", "=", True)]))

            # Verificar configuración JWT
            jwt_secret = request.env['ir.config_parameter'].sudo().get_param('rest_api.jwt_secret')

            health_status = {
                "status": "healthy",
                "timestamp": fields.Datetime.now().isoformat(),
                "database": request.env.cr.dbname,
                "active_models": active_configs,
                "version": "2.0.0",
                "auth_method": "JWT Bearer Token",
                "jwt_configured": bool(jwt_secret),
                "features": {
                    "dynamic_schemas": True,
                    "advanced_filtering": True,
                    "jwt_authentication": True,
                    "pagination": True,
                    "field_selection": True
                }
            }

            return self._json_response(health_status)

        except Exception as e:
            error_status = {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": fields.Datetime.now().isoformat()
            }
            return request.make_response(
                json.dumps(error_status),
                status=503,
                headers=[("Content-Type", "application/json; charset=utf-8")]
            )

    @http.route(['/api', '/api/'], type='http', auth='none', methods=['GET'], csrf=False)
    def api_root(self, **kw):
        """Endpoint raíz de la API que proporciona información básica"""
        try:
            base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url', 'http://localhost:8069')

            api_info = {
                "message": "Bienvenido a la REST API de Odoo v2.0",
                "version": "2.0.0",
                "status": "active",
                "documentation": f"{base_url}/api/v1/docs",
                "features": [
                    "JWT Bearer Token Authentication",
                    "Dynamic Schema Generation",
                    "Advanced Filtering with Domain",
                    "Pagination Support",
                    "Field Selection",
                    "Interactive Swagger Documentation"
                ],
                "endpoints": {
                    "auth": f"{base_url}/api/v1/auth",
                    "refresh": f"{base_url}/api/v1/refresh",
                    "models": f"{base_url}/api/v1/models",
                    "health": f"{base_url}/api/v1/health",
                    "docs": f"{base_url}/api/v1/docs",
                    "openapi": f"{base_url}/api/v1/openapi.json"
                },
                "authentication": {
                    "type": "JWT Bearer Token",
                    "header": "Authorization",
                    "format": "Bearer <token>",
                    "expires_in_hours": "configurable (default: 24h)"
                }
            }

            return self._json_response(api_info)
        except Exception as e:
            _logger.error(f"Error en api_root: {str(e)}")
            return self._error_response("Error interno del servidor", 500)

    def _handle_cors_preflight(self):
        """Maneja peticiones OPTIONS para CORS preflight"""
        cors_headers = [
            ('Content-Type', 'application/json; charset=utf-8'),
            ('Access-Control-Allow-Origin', '*'),
            ('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS'),
            ('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-API-Key, api-key'),
            ('Access-Control-Expose-Headers', 'Content-Type, Authorization'),
            ('Access-Control-Max-Age', '86400')
        ]

        return request.make_response('', headers=cors_headers, status=200)
