# -*- coding: utf-8 -*-
import jwt
import base64
import secrets
import logging
from datetime import datetime, timedelta
from odoo import fields
from odoo.http import request

_logger = logging.getLogger(__name__)


class JWTAuthMixin:
    """Mixin para autenticación JWT reutilizable"""

    def _get_jwt_secret(self):
        """Obtiene la clave secreta para JWT desde configuración del sistema"""
        secret = request.env['ir.config_parameter'].sudo().get_param('rest_api.jwt_secret')
        if not secret:
            # Generar y guardar una nueva clave secreta
            try:
                secret = base64.b64encode(secrets.token_bytes(32)).decode('utf-8')
            except (ImportError, AttributeError):
                # Fallback si secrets no está disponible
                import uuid
                import hashlib
                secret = hashlib.sha256(str(uuid.uuid4()).encode()).hexdigest()

            request.env['ir.config_parameter'].sudo().set_param('rest_api.jwt_secret', secret)
            _logger.info("Generated new JWT secret key")

        return secret

    def _generate_jwt_token(self, user_id, expires_in_hours=24):
        """
        Genera un JWT token para el usuario
        Args:
            user_id: ID del usuario
            expires_in_hours: Horas hasta expiración (default: 24h)
        Returns:
            str: JWT token o None si hay error
        """
        try:
            now = datetime.utcnow()
            payload = {
                'user_id': user_id,
                'iat': now,  # Issued at
                'exp': now + timedelta(hours=expires_in_hours),  # Expiration
                'iss': 'odoo-rest-api',  # Issuer
                'aud': 'odoo-client',     # Audience
                'jti': f"{user_id}_{int(now.timestamp())}"  # JWT ID
            }

            secret = self._get_jwt_secret()
            token = jwt.encode(payload, secret, algorithm='HS256')

            _logger.info(f"Generated JWT token for user {user_id}, expires in {expires_in_hours}h")
            return token

        except Exception as e:
            _logger.error(f"Error generating JWT token: {str(e)}")
            return None

    def _validate_jwt_token(self, token):
        """
        Valida un JWT token
        Args:
            token: Token JWT (puede incluir 'Bearer ' al inicio)
        Returns:
            tuple: (success: bool, user_id: int or None, error_message: str or None)
        """
        if not token:
            return False, None, "Token no proporcionado"

        # Limpiar token (remover 'Bearer ' si está presente)
        if token.startswith('Bearer '):
            token = token[7:]
        elif token.startswith('bearer '):
            token = token[7:]

        try:
            secret = self._get_jwt_secret()

            # Decodificar y validar token
            payload = jwt.decode(
                token,
                secret,
                algorithms=['HS256'],
                audience='odoo-client',
                issuer='odoo-rest-api'
            )

            user_id = payload.get('user_id')
            if not user_id:
                return False, None, "Token inválido: user_id no encontrado"

            # Verificar que el usuario existe y está activo
            user = request.env['res.users'].sudo().browse(user_id)
            if not user.exists():
                return False, None, "Usuario no encontrado"

            if not user.active:
                return False, None, "Usuario inactivo"

            # Configurar contexto de sesión
            request.session.uid = user_id
            if hasattr(request, 'env'):
                request.env.user = user

            # Log successful authentication
            _logger.debug(f"JWT authentication successful for user {user_id} ({user.login})")

            return True, user_id, None

        except jwt.ExpiredSignatureError:
            _logger.warning("JWT token expired")
            return False, None, "Token expirado"
        except jwt.InvalidTokenError as e:
            _logger.warning(f"Invalid JWT token: {str(e)}")
            return False, None, f"Token inválido: {str(e)}"
        except jwt.InvalidAudienceError:
            _logger.warning("JWT token has invalid audience")
            return False, None, "Token inválido: audiencia incorrecta"
        except jwt.InvalidIssuerError:
            _logger.warning("JWT token has invalid issuer")
            return False, None, "Token inválido: emisor incorrecto"
        except Exception as e:
            _logger.error(f"Error validating JWT token: {str(e)}")
            return False, None, "Error interno validando token"

    def _decode_jwt_payload(self, token):
        """
        Decodifica un JWT token sin validar (útil para debugging)
        Args:
            token: Token JWT
        Returns:
            dict: Payload del token o None si hay error
        """
        try:
            if token.startswith('Bearer '):
                token = token[7:]

            # Decodificar sin verificar (solo para obtener payload)
            payload = jwt.decode(token, options={"verify_signature": False})
            return payload
        except Exception as e:
            _logger.error(f"Error decoding JWT payload: {str(e)}")
            return None

    def _get_token_info(self, token):
        """
        Obtiene información de un JWT token
        Args:
            token: Token JWT
        Returns:
            dict: Información del token
        """
        payload = self._decode_jwt_payload(token)
        if not payload:
            return None

        try:
            exp_timestamp = payload.get('exp')
            iat_timestamp = payload.get('iat')

            info = {
                'user_id': payload.get('user_id'),
                'issued_at': datetime.fromtimestamp(iat_timestamp) if iat_timestamp else None,
                'expires_at': datetime.fromtimestamp(exp_timestamp) if exp_timestamp else None,
                'issuer': payload.get('iss'),
                'audience': payload.get('aud'),
                'jwt_id': payload.get('jti'),
                'is_expired': datetime.utcnow() > datetime.fromtimestamp(exp_timestamp) if exp_timestamp else True
            }

            return info
        except Exception as e:
            _logger.error(f"Error getting token info: {str(e)}")
            return None
