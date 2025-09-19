# -*- coding: utf-8 -*-
import json
import logging
from datetime import datetime
from odoo import http, fields
from odoo.http import request

_logger = logging.getLogger(__name__)


class SwaggerController(http.Controller):
    """Controlador Swagger/OpenAPI con esquemas dinámicos mejorados"""

    @http.route(["/api/v1/docs", "/api/docs"], type="http", auth="none", methods=["GET"], csrf=False)
    def swagger_ui(self, **kwargs):
        """Muestra la interfaz de Swagger UI mejorada"""
        try:
            base_url = self._get_base_url()

            swagger_html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Odoo REST API - Documentation</title>
    <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@5.9.0/swagger-ui.css" />
    <style>
        html {{ box-sizing: border-box; overflow: -moz-scrollbars-vertical; overflow-y: scroll; }}
        body {{ margin: 0; background: #fafafa; font-family: "Helvetica Neue", Helvetica, Arial, sans-serif; }}
        #swagger-ui {{ max-width: 1400px; margin: 0 auto; padding: 20px; }}
        .topbar {{ background-color: #89bf04 !important; }}
        .swagger-ui .info .title {{ color: #89bf04; font-size: 2.2em; }}
        .swagger-ui .info .description {{ font-size: 1.1em; line-height: 1.6; }}
        .auth-banner {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; padding: 15px; border-radius: 8px; margin: 20px 0;
            text-align: center;
        }}
    </style>
</head>
<body>
    <div class="auth-banner">
        <h3>🔐 Autenticación JWT</h3>
        <p>Esta API usa <strong>JWT Bearer Tokens</strong>. Usa el endpoint <code>/auth</code> para obtener tu token.</p>
        <p>Luego agrega: <code>Authorization: Bearer tu_token_aqui</code></p>
    </div>
    <div id="swagger-ui"></div>

    <script src="https://unpkg.com/swagger-ui-dist@5.9.0/swagger-ui-bundle.js"></script>
    <script src="https://unpkg.com/swagger-ui-dist@5.9.0/swagger-ui-standalone-preset.js"></script>
    <script>
        window.onload = function() {{
            const ui = SwaggerUIBundle({{
                url: '{base_url}/api/v1/openapi.json',
                dom_id: '#swagger-ui',
                deepLinking: true,
                presets: [SwaggerUIBundle.presets.apis, SwaggerUIStandalonePreset],
                plugins: [SwaggerUIBundle.plugins.DownloadUrl],
                layout: "StandaloneLayout",
                validatorUrl: null,
                tryItOutEnabled: true,
                supportedSubmitMethods: ['get', 'post', 'put', 'delete'],
                docExpansion: 'list',
                defaultModelsExpandDepth: 2,
                defaultModelExpandDepth: 3,
                requestInterceptor: function(req) {{
                    // Auto-agregar Content-Type para requests que no sean GET
                    if (req.method !== 'GET' && !req.headers['Content-Type']) {{
                        req.headers['Content-Type'] = 'application/json';
                    }}
                    return req;
                }},
                responseInterceptor: function(res) {{
                    // Log responses para debugging
                    if (res.status >= 400) {{
                        console.warn('API Error:', res.status, res.statusText, res.body);
                    }}
                    return res;
                }}
            }});
            window.ui = ui;
        }}
    </script>
</body>
</html>"""

            return request.make_response(swagger_html, headers=[("Content-Type", "text/html; charset=utf-8")])

        except Exception as e:
            _logger.error(f"Error serving Swagger UI: {str(e)}")
            return request.make_response(f"<h1>Error</h1><p>Could not load documentation: {str(e)}</p>", status=500)

    @http.route(["/api/v1/openapi.json"], type="http", auth="none", methods=["GET"], csrf=False)
    def openapi_spec(self, **kwargs):
        """Genera la especificación OpenAPI/Swagger con mejoras"""
        try:
            base_url = self._get_base_url()
            api_configs = []

            try:
                api_configs = request.env["connection.api"].sudo().search([("active", "=", True)])
            except Exception as e:
                _logger.warning(f"Could not load API configurations: {str(e)}")

            # Generar esquemas dinámicos mejorados
            dynamic_schemas = self._generate_enhanced_schemas(api_configs)

            openapi_spec = {
                "openapi": "3.0.3",
                "info": {
                    "title": "Odoo REST API",
                    "description": self._get_enhanced_description(base_url),
                    "version": "2.0.0",
                    "contact": {"name": "API Support", "email": "support@example.com"},
                    "license": {"name": "LGPL-3", "url": "https://www.gnu.org/licenses/lgpl-3.0.html"}
                },
                "servers": [{"url": f"{base_url}/api/v1", "description": "Production server"}],
                "security": [{"BearerAuth": []}],
                "components": {
                    "securitySchemes": {
                        "BearerAuth": {
                            "type": "http",
                            "scheme": "bearer",
                            "bearerFormat": "JWT",
                            "description": "JWT Bearer token obtenido del endpoint /auth"
                        }
                    },
                    "schemas": {
                        **self._get_base_schemas(),
                        **dynamic_schemas
                    },
                    "responses": self._get_common_responses()
                },
                "paths": self._generate_enhanced_paths(api_configs),
                "tags": self._generate_enhanced_tags(api_configs)
            }

            return request.make_response(
                json.dumps(openapi_spec, indent=2, ensure_ascii=False),
                headers=[("Content-Type", "application/json; charset=utf-8")]
            )

        except Exception as e:
            _logger.error(f"Error generating OpenAPI spec: {str(e)}")
            return request.make_response(
                json.dumps({"error": f"Error loading API specification: {str(e)}"}),
                headers=[("Content-Type", "application/json; charset=utf-8")]
            )

    @http.route(['/api/v1/schema/<model_name>'], type='http', auth='none', methods=['GET'], csrf=False)
    def get_model_schema(self, model_name, **kwargs):
        """Obtiene el esquema de un modelo específico"""
        try:
            # Obtener configuración del modelo
            model_obj = request.env['ir.model'].sudo().search([('model', '=', model_name)], limit=1)
            if not model_obj:
                return self._error_response("Modelo no encontrado", 404)

            api_config = request.env['connection.api'].sudo().search([
                ('model_id', '=', model_obj.id),
                ('active', '=', True)
            ], limit=1)

            if not api_config:
                return self._error_response("Modelo no configurado para API REST", 404)

            model_class = request.env[model_name].sudo()
            schema = self._generate_enhanced_model_schema(model_class, api_config)

            response_data = {
                "model": model_name,
                "display_name": model_obj.name,
                "schema": schema,
                "endpoints": {
                    "collection": f"/api/v1/{model_name}",
                    "item": f"/api/v1/{model_name}/{{id}}"
                },
                "available_methods": {
                    "GET": api_config.is_get,
                    "POST": api_config.is_post,
                    "PUT": api_config.is_put,
                    "DELETE": api_config.is_delete
                }
            }

            return request.make_response(
                json.dumps(response_data, indent=2, ensure_ascii=False),
                headers=[("Content-Type", "application/json; charset=utf-8")]
            )

        except Exception as e:
            return request.make_response(
                json.dumps({"error": f"Error getting schema: {str(e)}"}),
                status=500,
                headers=[("Content-Type", "application/json; charset=utf-8")]
            )

    def _get_base_url(self):
        """Obtiene la URL base del servidor"""
        try:
            if request.env:
                return request.env["ir.config_parameter"].sudo().get_param("web.base.url", "http://localhost:8069")
            return request.httprequest.host_url.rstrip('/')
        except:
            return "http://localhost:8069"

    def _get_enhanced_description(self, base_url):
        """Descripción mejorada de la API"""
        return f"""
# Odoo REST API v2.0

API REST completa para Odoo con autenticación JWT y documentación dinámica.

## 🔐 Autenticación

Esta API utiliza **JWT Bearer Tokens** para autenticación:

1. **Obtener token:**
```bash
curl -X POST {base_url}/api/v1/auth \\
  -H "Content-Type: application/json" \\
  -d '{{"username": "DontFucking", "password": "UseTheseCredentials"}}'
```

2. **Usar token en requests:**
```bash
curl -X GET {base_url}/api/v1/models \\
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## 📊 Características

- **Esquemas dinámicos** basados en modelos reales de Odoo
- **Filtrado avanzado** con domain, limit, offset
- **Autenticación JWT** segura con expiración configurable
- **Validación automática** de tipos de datos
- **Documentación interactiva** con Swagger UI

## 🚀 Endpoints Principales

- `POST /auth` - Autenticación y obtención de token
- `POST /refresh` - Renovar token JWT
- `GET /models` - Lista de modelos disponibles
- `GET /health` - Estado de la API
- `GET /schema/{{model}}` - Esquema específico de un modelo

## 📝 Formato de Respuestas

Todas las respuestas siguen un formato consistente:

**Éxito:**
```json
{{
  "success": true,
  "count": 10,
  "data": [...]
}}
```

**Error:**
```json
{{
  "error": true,
  "message": "Descripción del error",
  "status_code": 400,
  "error_code": "ERROR_CODE"
}}
```
"""

    def _get_base_schemas(self):
        """Esquemas base mejorados"""
        return {
            "ErrorResponse": {
                "type": "object",
                "required": ["error", "message", "status_code"],
                "properties": {
                    "error": {"type": "boolean", "example": True},
                    "message": {"type": "string", "example": "Error description"},
                    "status_code": {"type": "integer", "example": 400},
                    "error_code": {"type": "string", "example": "VALIDATION_ERROR"}
                }
            },
            "AuthRequest": {
                "type": "object",
                "required": ["username", "password"],
                "properties": {
                    "username": {"type": "string", "example": "DontFucking"},
                    "password": {"type": "string", "format": "password", "example": "UseTheseCredentials"},
                    "database": {"type": "string", "example": "odoo"},
                    "expires_in_hours": {"type": "integer", "minimum": 1, "maximum": 168, "default": 24, "example": 24}
                }

            },
            "AuthResponse": {
                "type": "object",
                "properties": {
                    "success": {"type": "boolean", "example": True},
                    "message": {"type": "string", "example": "Authentication successful"},
                    "data": {
                        "type": "object",
                        "properties": {
                            "user_id": {"type": "integer", "example": 2},
                            "username": {"type": "string", "example": "DontFucking"},
                            "name": {"type": "string", "example": "Administrator"},
                            "access_token": {"type": "string", "example": "eyJ0eXAiOiJKV1QiLCJhbGc..."},
                            "token_type": {"type": "string", "example": "Bearer"},
                            "expires_in": {"type": "integer", "example": 86400},
                            "database": {"type": "string", "example": "odoo"}
                        }
                    }
                }
            },
            "HealthResponse": {
                "type": "object",
                "properties": {
                    "status": {"type": "string", "enum": ["healthy", "unhealthy"]},
                    "timestamp": {"type": "string", "format": "date-time"},
                    "database": {"type": "string"},
                    "active_models": {"type": "integer"},
                    "version": {"type": "string"},
                    "auth_method": {"type": "string", "example": "JWT Bearer Token"}
                }
            }
        }

    def _get_common_responses(self):
        """Respuestas comunes reutilizables"""
        return {
            "UnauthorizedError": {
                "description": "Token JWT missing, invalid, or expired",
                "content": {
                    "application/json": {
                        "schema": {"$ref": "#/components/schemas/ErrorResponse"},
                        "example": {
                            "error": True,
                            "message": "Token expirado",
                            "status_code": 401,
                            "error_code": "TOKEN_EXPIRED"
                        }
                    }
                }
            },
            "NotFoundError": {
                "description": "Resource not found",
                "content": {
                    "application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}
                }
            },
            "ValidationError": {
                "description": "Invalid request data",
                "content": {
                    "application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}
                }
            }
        }

    def _generate_enhanced_schemas(self, api_configs):
        """Genera esquemas dinámicos mejorados"""
        schemas = {}

        for config in api_configs:
            try:
                if not hasattr(config, 'model_id') or not config.model_id:
                    continue

                model_name = config.model_id.model

                try:
                    model_class = request.env[model_name].sudo()
                except KeyError:
                    _logger.warning(f"Model {model_name} not found")
                    continue

                # Generar esquema mejorado del modelo
                model_schema = self._generate_enhanced_model_schema(model_class, config)
                schemas[f"{model_name}_values"] = model_schema

                # Esquemas de request
                schemas[f"{model_name}_create_request"] = {
                    "type": "object",
                    "required": ["values"],
                    "properties": {
                        "values": {"$ref": f"#/components/schemas/{model_name}_values"},
                        "fields": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Campos específicos a retornar en la respuesta",
                            "example": list(model_schema.get("properties", {}).keys())[:5]
                        }
                    },
                    "example": {
                        "values": self._generate_example_values(model_class, config),
                        "fields": ["id", "display_name"]
                    }
                }

                # Esquema de respuesta de lectura
                read_properties = dict(model_schema.get("properties", {}))
                read_properties.update({
                    "id": {"type": "integer", "description": "ID único del registro", "example": 1},
                    "display_name": {"type": "string", "description": "Nombre para mostrar"}
                })

                schemas[f"{model_name}_read_response"] = {
                    "type": "object",
                    "properties": read_properties
                }

                # Respuesta de colección con metadatos
                schemas[f"{model_name}_collection_response"] = {
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean", "example": True},
                        "count": {"type": "integer", "example": 1},
                        "total": {"type": "integer", "description": "Total de registros (sin limit)"},
                        "offset": {"type": "integer", "description": "Registros omitidos"},
                        "limit": {"type": "integer", "description": "Límite aplicado"},
                        "data": {
                            "type": "array",
                            "items": {"$ref": f"#/components/schemas/{model_name}_read_response"}
                        }
                    }
                }

            except Exception as e:
                _logger.error(f"Error generating enhanced schema for model {config.model_id.model}: {str(e)}")
                continue

        return schemas

    def _generate_enhanced_model_schema(self, model_class, config):
        """Genera esquema mejorado para un modelo específico"""
        properties = {}
        required = []

        try:
            allowed_fields = self._get_allowed_fields(config)
            forbidden_fields = self._get_forbidden_fields(config)

            for field_name, field_obj in model_class._fields.items():
                if field_name in forbidden_fields:
                    continue

                if allowed_fields and field_name not in allowed_fields:
                    continue

                field_schema = self._odoo_field_to_enhanced_json_schema(field_obj, field_name, model_class)
                if field_schema:
                    properties[field_name] = field_schema

                    if getattr(field_obj, 'required', False):
                        required.append(field_name)

        except Exception as e:
            _logger.warning(f"Error processing enhanced model fields: {str(e)}")

        schema = {
            "type": "object",
            "properties": properties
        }

        if required:
            schema["required"] = required

        return schema

    def _odoo_field_to_enhanced_json_schema(self, field_obj, field_name, model_class):
        """Convierte un campo de Odoo a esquema JSON mejorado"""
        field_type = type(field_obj).__name__

        base_schema = {
            "description": getattr(field_obj, 'help', '') or getattr(field_obj, 'string', field_name)
        }

        # Mapeo de tipos mejorado
        type_mapping = {
            'Char': {"type": "string"},
            'Text': {"type": "string"},
            'Html': {"type": "string", "format": "html"},
            'Boolean': {"type": "boolean"},
            'Integer': {"type": "integer"},
            'Float': {"type": "number", "format": "float"},
            'Monetary': {"type": "number", "format": "currency"},
            'Date': {"type": "string", "format": "date"},
            'Datetime': {"type": "string", "format": "date-time"},
            'Binary': {"type": "string", "format": "binary"},
            'Selection': {"type": "string"},
            'Many2one': {"type": "integer"},
            'One2many': {"type": "array", "items": {"type": "integer"}},
            'Many2many': {"type": "array", "items": {"type": "integer"}},
        }

        schema = type_mapping.get(field_type, {"type": "string"})
        schema.update(base_schema)

        # Mejoras específicas por tipo de campo
        if field_type == 'Char' and hasattr(field_obj, 'size') and field_obj.size:
            schema["maxLength"] = field_obj.size

        # Campos Selection con opciones reales
        if field_type == 'Selection' and hasattr(field_obj, 'selection'):
            try:
                if callable(field_obj.selection):
                    try:
                        # Intentar obtener opciones dinámicas
                        options = field_obj.selection(model_class, field_name)
                        if options:
                            schema["enum"] = [opt[0] for opt in options if opt[0]]
                            schema["example"] = options[0][0] if options else None
                            schema["x-options"] = [{"value": opt[0], "label": opt[1]} for opt in options]
                    except:
                        schema["description"] += " (opciones dinámicas)"
                else:
                    options = [opt[0] for opt in field_obj.selection if opt[0]]
                    if options:
                        schema["enum"] = options
                        schema["example"] = options[0]
                        schema["x-options"] = [{"value": opt[0], "label": opt[1]} for opt in field_obj.selection]
            except Exception as e:
                _logger.warning(f"Error getting selection options for {field_name}: {str(e)}")

        # Campos relacionales con información del modelo relacionado
        if field_type == 'Many2one':
            comodel_name = getattr(field_obj, 'comodel_name', None)
            if comodel_name:
                schema.update({
                    "description": f"ID del registro relacionado del modelo {comodel_name}",
                    "x-related-model": comodel_name,
                    "minimum": 1
                })

        # Campos One2many y Many2many
        if field_type in ['One2many', 'Many2many']:
            comodel_name = getattr(field_obj, 'comodel_name', None)
            if comodel_name:
                schema["description"] = f"Lista de IDs de registros del modelo {comodel_name}"
                schema["x-related-model"] = comodel_name
                schema["items"]["minimum"] = 1

        # Mejores ejemplos basados en el nombre del campo
        if "example" not in schema:
            schema["example"] = self._get_smart_example(field_name, schema.get("type"), field_type)

        # Propiedades adicionales
        if hasattr(field_obj, 'required') and field_obj.required:
            schema["x-required"] = True

        if hasattr(field_obj, 'readonly') and field_obj.readonly:
            schema["readOnly"] = True

        return schema

    def _get_smart_example(self, field_name, json_type, odoo_type):
        """Genera ejemplos inteligentes basados en el nombre del campo"""
        field_lower = field_name.lower()

        # Ejemplos específicos por nombre de campo
        smart_examples = {
            'name': 'Ejemplo de nombre',
            'email': 'usuario@ejemplo.com',
            'phone': '+34123456789',
            'mobile': '+34987654321',
            'website': 'https://ejemplo.com',
            'url': 'https://ejemplo.com',
            'street': 'Calle Ejemplo 123',
            'city': 'Madrid',
            'zip': '28001',
            'description': 'Descripción detallada del elemento',
            'note': 'Nota adicional',
            'comment': 'Comentario del usuario',
            'reference': 'REF-001',
            'code': 'COD123',
            'login': 'usuario',
            'password': 'contraseña_segura',
            'price': 99.99,
            'amount': 100.0,
            'quantity': 1,
            'qty': 5,
        }

        # Buscar coincidencias en el nombre del campo
        for pattern, example in smart_examples.items():
            if pattern in field_lower:
                return example

        # Ejemplos por tipo JSON
        type_examples = {
            "string": f"Valor de {field_name}",
            "integer": 1,
            "number": 10.5,
            "boolean": True,
            "array": [1, 2, 3]
        }

        return type_examples.get(json_type, None)

    def _generate_example_values(self, model_class, config):
        """Genera valores de ejemplo para un modelo"""
        example_values = {}

        try:
            allowed_fields = self._get_allowed_fields(config)
            forbidden_fields = self._get_forbidden_fields(config)

            for field_name, field_obj in model_class._fields.items():
                if field_name in forbidden_fields:
                    continue
                if allowed_fields and field_name not in allowed_fields:
                    continue
                if field_name in ['id', 'create_date', 'write_date', 'create_uid', 'write_uid']:
                    continue

                field_type = type(field_obj).__name__
                example = self._get_smart_example(field_name,
                                                 self._get_json_type_for_odoo_field(field_type),
                                                 field_type)
                if example is not None:
                    example_values[field_name] = example

        except Exception as e:
            _logger.warning(f"Error generating example values: {str(e)}")

        return example_values

    def _get_json_type_for_odoo_field(self, odoo_type):
        """Mapeo simple de tipo Odoo a tipo JSON"""
        mapping = {
            'Char': 'string', 'Text': 'string', 'Html': 'string', 'Selection': 'string',
            'Integer': 'integer', 'Many2one': 'integer',
            'Float': 'number', 'Monetary': 'number',
            'Boolean': 'boolean',
            'One2many': 'array', 'Many2many': 'array'
        }
        return mapping.get(odoo_type, 'string')

    def _generate_enhanced_paths(self, api_configs):
        """Genera paths mejorados con parámetros adicionales"""
        paths = {
            "/auth": {
                "post": {
                    "tags": ["Authentication"],
                    "summary": "Authenticate and get JWT token",
                    "description": "Autentica credenciales y devuelve un JWT token para usar en requests subsiguientes",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/AuthRequest"}
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Authentication successful",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/AuthResponse"}
                                }
                            }
                        },
                        "401": {"$ref": "#/components/responses/UnauthorizedError"}
                    },
                    "security": []
                }
            },
            "/refresh": {
                "post": {
                    "tags": ["Authentication"],
                    "summary": "Refresh JWT token",
                    "description": "Genera un nuevo JWT token usando el token actual",
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "expires_in_hours": {"type": "integer", "default": 24}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Token refreshed successfully",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/AuthResponse"}
                                }
                            }
                        },
                        "401": {"$ref": "#/components/responses/UnauthorizedError"}
                    }
                }
            },
            "/health": {
                "get": {
                    "tags": ["System"],
                    "summary": "API health check",
                    "description": "Verifica el estado de salud de la API y conexiones",
                    "responses": {
                        "200": {
                            "description": "API is healthy",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/HealthResponse"}
                                }
                            }
                        },
                        "503": {
                            "description": "API is unhealthy",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/HealthResponse"}
                                }
                            }
                        }
                    },
                    "security": []
                }
            }
        }

        # Generar paths para cada modelo configurado
        for config in api_configs:
            try:
                if not hasattr(config, 'model_id') or not config.model_id:
                    continue

                model_name = config.model_id.model
                model_display_name = config.model_id.name

                collection_path = f"/{model_name}"
                item_path = f"/{model_name}/{{id}}"
                schema_path = f"/schema/{model_name}"

                # Endpoint para obtener esquema del modelo
                paths[schema_path] = {
                    "get": {
                        "tags": ["Schemas"],
                        "summary": f"Get {model_display_name} schema",
                        "description": f"Obtiene el esquema completo del modelo {model_display_name}",
                        "responses": {
                            "200": {"description": "Schema retrieved successfully"},
                            "404": {"$ref": "#/components/responses/NotFoundError"}
                        },
                        "security": []
                    }
                }

                if collection_path not in paths:
                    paths[collection_path] = {}
                if item_path not in paths:
                    paths[item_path] = {}

                # GET endpoints con parámetros mejorados
                if config.is_get:
                    paths[collection_path]["get"] = {
                        "tags": [model_name],
                        "summary": f"Get all {model_display_name} records",
                        "description": f"Obtiene registros del modelo {model_display_name} con filtrado avanzado",
                        "parameters": [
                            {
                                "name": "domain",
                                "in": "query",
                                "description": "Filtros en formato Odoo domain",
                                "schema": {"type": "string"},
                                "example": "[['active', '=', True]]"
                            },
                            {
                                "name": "fields",
                                "in": "query",
                                "description": "Campos específicos a retornar (separados por comas)",
                                "schema": {"type": "string"},
                                "example": "id,name,email"
                            },
                            {
                                "name": "limit",
                                "in": "query",
                                "description": "Número máximo de registros",
                                "schema": {"type": "integer", "minimum": 1, "maximum": config.max_records_limit},
                                "example": 10
                            },
                            {
                                "name": "offset",
                                "in": "query",
                                "description": "Número de registros a omitir",
                                "schema": {"type": "integer", "minimum": 0},
                                "example": 0
                            },
                            {
                                "name": "order",
                                "in": "query",
                                "description": "Ordenamiento (ej: 'name asc', 'create_date desc')",
                                "schema": {"type": "string"},
                                "example": "name asc"
                            }
                        ],
                        "responses": {
                            "200": {
                                "description": "List of records",
                                "content": {
                                    "application/json": {
                                        "schema": {"$ref": f"#/components/schemas/{model_name}_collection_response"}
                                    }
                                }
                            },
                            "401": {"$ref": "#/components/responses/UnauthorizedError"}
                        }
                    }

                    paths[item_path]["get"] = {
                        "tags": [model_name],
                        "summary": f"Get specific {model_display_name} record",
                        "description": f"Obtiene un registro específico del modelo {model_display_name}",
                        "parameters": [
                            {
                                "name": "id",
                                "in": "path",
                                "required": True,
                                "description": "ID del registro",
                                "schema": {"type": "integer", "minimum": 1}
                            },
                            {
                                "name": "fields",
                                "in": "query",
                                "description": "Campos específicos a retornar",
                                "schema": {"type": "string"}
                            }
                        ],
                        "responses": {
                            "200": {
                                "description": "Record found",
                                "content": {
                                    "application/json": {
                                        "schema": {"$ref": f"#/components/schemas/{model_name}_collection_response"}
                                    }
                                }
                            },
                            "404": {"$ref": "#/components/responses/NotFoundError"},
                            "401": {"$ref": "#/components/responses/UnauthorizedError"}
                        }
                    }

                # POST endpoint
                if config.is_post:
                    paths[collection_path]["post"] = {
                        "tags": [model_name],
                        "summary": f"Create new {model_display_name} record",
                        "description": f"Crea un nuevo registro en el modelo {model_display_name}",
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": f"#/components/schemas/{model_name}_create_request"}
                                }
                            }
                        },
                        "responses": {
                            "201": {
                                "description": "Record created successfully",
                                "content": {
                                    "application/json": {
                                        "schema": {"$ref": f"#/components/schemas/{model_name}_collection_response"}
                                    }
                                }
                            },
                            "400": {"$ref": "#/components/responses/ValidationError"},
                            "401": {"$ref": "#/components/responses/UnauthorizedError"}
                        }
                    }

                # PUT endpoint
                if config.is_put:
                    paths[item_path]["put"] = {
                        "tags": [model_name],
                        "summary": f"Update {model_display_name} record",
                        "description": f"Actualiza un registro existente del modelo {model_display_name}",
                        "parameters": [
                            {
                                "name": "id",
                                "in": "path",
                                "required": True,
                                "description": "ID del registro a actualizar",
                                "schema": {"type": "integer", "minimum": 1}
                            }
                        ],
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": f"#/components/schemas/{model_name}_create_request"}
                                }
                            }
                        },
                        "responses": {
                            "200": {
                                "description": "Record updated successfully",
                                "content": {
                                    "application/json": {
                                        "schema": {"$ref": f"#/components/schemas/{model_name}_collection_response"}
                                    }
                                }
                            },
                            "404": {"$ref": "#/components/responses/NotFoundError"},
                            "400": {"$ref": "#/components/responses/ValidationError"},
                            "401": {"$ref": "#/components/responses/UnauthorizedError"}
                        }
                    }

                # DELETE endpoint
                if config.is_delete:
                    paths[item_path]["delete"] = {
                        "tags": [model_name],
                        "summary": f"Delete {model_display_name} record",
                        "description": f"Elimina un registro del modelo {model_display_name}",
                        "parameters": [
                            {
                                "name": "id",
                                "in": "path",
                                "required": True,
                                "description": "ID del registro a eliminar",
                                "schema": {"type": "integer", "minimum": 1}
                            }
                        ],
                        "responses": {
                            "200": {
                                "description": "Record deleted successfully",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "success": {"type": "boolean", "example": True},
                                                "message": {"type": "string", "example": "Record deleted successfully"},
                                                "deleted_record": {
                                                    "type": "object",
                                                    "properties": {
                                                        "id": {"type": "integer"},
                                                        "display_name": {"type": "string"}
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            },
                            "404": {"$ref": "#/components/responses/NotFoundError"},
                            "401": {"$ref": "#/components/responses/UnauthorizedError"}
                        }
                    }

            except Exception as e:
                _logger.warning(f"Error generating enhanced paths for model: {str(e)}")
                continue

        return paths

    def _generate_enhanced_tags(self, api_configs):
        """Genera tags mejorados para agrupar endpoints"""
        tags = [
            {"name": "Authentication", "description": "Autenticación JWT y gestión de tokens"},
            {"name": "System", "description": "Endpoints del sistema (salud, estado)"},
            {"name": "Schemas", "description": "Esquemas de modelos disponibles"}
        ]

        for config in api_configs:
            if hasattr(config, 'model_id') and config.model_id:
                available_methods = []
                if config.is_get: available_methods.append("GET")
                if config.is_post: available_methods.append("POST")
                if config.is_put: available_methods.append("PUT")
                if config.is_delete: available_methods.append("DELETE")

                tags.append({
                    "name": config.model_id.model,
                    "description": f"Operaciones CRUD para {config.model_id.name} - Métodos: {', '.join(available_methods)}",
                    "externalDocs": {
                        "description": "Esquema del modelo",
                        "url": f"/api/v1/schema/{config.model_id.model}"
                    }
                })

        return tags

    def _get_allowed_fields(self, config):
        """Obtiene campos permitidos de la configuración"""
        if not hasattr(config, 'allowed_fields') or not config.allowed_fields:
            return None
        return [f.strip() for f in config.allowed_fields.split(',') if f.strip()]

    def _get_forbidden_fields(self, config):
        """Obtiene campos prohibidos de la configuración"""
        default_forbidden = ['__last_update', 'create_uid', 'create_date', 'write_uid', 'write_date']
        if not hasattr(config, 'forbidden_fields') or not config.forbidden_fields:
            return default_forbidden
        return [f.strip() for f in config.forbidden_fields.split(',') if f.strip()]
