# 🧪 Tests Unitarios - REST API Odoo

Este directorio contiene una suite completa de tests unitarios para verificar el funcionamiento del módulo REST API de Odoo.

## 📁 Estructura de Tests

```
tests/
├── __init__.py                 # Inicializador del paquete de tests
├── conftest.py                 # Configuración de pytest y fixtures
├── test_runner.py              # Script ejecutable para correr tests
├── test_rest_api_auth.py       # Tests de autenticación JWT
├── test_rest_api_cors.py       # Tests de CORS y OPTIONS
├── test_rest_api_crud.py       # Tests de operaciones CRUD
├── test_rest_api_errors.py     # Tests de manejo de errores
└── README_TESTS.md             # Esta documentación
```

## 🚀 Métodos de Ejecución

### 1. **Usando el Framework de Odoo (Recomendado)**

```bash
# Navegar al directorio de Odoo
cd /path/to/odoo

# Ejecutar todos los tests del módulo
inv test --modules rest_api_odoo

# O usando odoo-bin directamente
python3 odoo-bin --test-enable --test-tags rest_api_odoo --stop-after-init
```

### 2. **Usando el Script Test Runner**

```bash
# Navegar al directorio del módulo
cd odoo/custom/src/cybroaddons/rest_api_odoo

# Ejecutar todos los tests
./tests/test_runner.py

# Ejecutar test específico
./tests/test_runner.py --module test_rest_api_auth

# Ejecutar con salida verbose
./tests/test_runner.py --verbose

# Ejecutar con coverage
./tests/test_runner.py --coverage

# Usar framework de Odoo
./tests/test_runner.py --odoo
```

### 3. **Usando pytest Directamente**

```bash
# Instalar dependencias de testing
pip install pytest pytest-cov requests

# Ejecutar todos los tests
cd tests/
pytest -v

# Ejecutar test específico
pytest test_rest_api_auth.py -v

# Ejecutar con coverage
pytest --cov=../controllers --cov-report=term-missing

# Ejecutar solo tests rápidos
pytest -m "not slow"
```

### 4. **Usando el entorno Doodba**

```bash
# Desde el directorio raíz del proyecto
inv test --cur-file /odoo/custom/src/cybroaddons/rest_api_odoo/tests/test_rest_api_auth.py

# O para todos los tests del módulo
inv test --modules rest_api_odoo
```

## 📊 Tipos de Tests Incluidos

### 🔐 **Tests de Autenticación** (`test_rest_api_auth.py`)
- ✅ Autenticación exitosa con credenciales válidas
- ✅ Autenticación fallida con credenciales inválidas
- ✅ Manejo de datos faltantes o JSON inválido
- ✅ Validación de JWT tokens
- ✅ Manejo de tokens expirados
- ✅ Endpoint de refresh token
- ✅ Health check endpoint
- ✅ Listado de modelos disponibles

### 🌐 **Tests de CORS** (`test_rest_api_cors.py`)
- ✅ Headers CORS en respuestas de autenticación
- ✅ Peticiones OPTIONS para preflight
- ✅ Headers CORS en respuestas de API
- ✅ Headers CORS en respuestas de error
- ✅ Compatibilidad con axios
- ✅ Headers de autenticación alternativos
- ✅ Exposición correcta de headers

### 📝 **Tests de CRUD** (`test_rest_api_crud.py`)
- ✅ GET: Obtener todos los registros
- ✅ GET: Obtener registro específico
- ✅ GET: Filtro por campos específicos
- ✅ GET: Filtro con domain
- ✅ GET: Paginación (limit/offset)
- ✅ GET: Ordenamiento
- ✅ POST: Crear nuevos registros
- ✅ PUT: Actualizar registros existentes
- ✅ DELETE: Eliminar registros
- ✅ Manejo de métodos no permitidos
- ✅ Acceso a modelos no configurados

### 🚨 **Tests de Errores** (`test_rest_api_errors.py`)
- ✅ Falta de token de autenticación
- ✅ Tokens inválidos o mal formados
- ✅ Modelos no existentes
- ✅ Métodos HTTP no permitidos
- ✅ JSON inválido en requests
- ✅ Datos faltantes en POST/PUT
- ✅ Registros no encontrados
- ✅ Errores de validación
- ✅ Headers CORS en errores
- ✅ Manejo de errores internos

## 🔧 Configuración Pre-Tests

### 1. **Asegurar que PyJWT esté instalado:**
```bash
pip install PyJWT>=2.8.0
```

### 2. **Verificar que el módulo esté instalado en Odoo:**
```bash
# Instalar/actualizar el módulo
inv install --modules rest_api_odoo

# O usando interface web de Odoo
# Apps > rest_api_odoo > Install/Upgrade
```

### 3. **Configurar modelo de prueba (automático):**
Los tests automáticamente crean configuraciones de API para `res.partner` y `res.users` durante el setup.

## 📈 Interpretación de Resultados

### ✅ **Test Exitoso:**
```
test_rest_api_auth.py::TestRestApiAuth::test_auth_endpoint_success PASSED
```

### ❌ **Test Fallido:**
```
test_rest_api_auth.py::TestRestApiAuth::test_auth_endpoint_success FAILED
FAILED test_rest_api_auth.py::TestRestApiAuth::test_auth_endpoint_success - AssertionError: ...
```

### 📊 **Reporte de Coverage:**
```
controllers/rest_api_odoo.py    95%   12-15, 67
controllers/jwt_auth.py         87%   143-145
```

## 🐛 Troubleshooting

### **Error: "PyJWT not found"**
```bash
pip install PyJWT>=2.8.0
```

### **Error: "Database does not exist"**
```bash
# Crear base de datos de test
inv resetdb --dbname test
```

### **Error: "Module not installed"**
```bash
inv install --modules rest_api_odoo
```

### **Error: "Authentication failed"**
```bash
# Verificar que el usuario admin existe y tiene la contraseña correcta
# Los tests usan admin/admin por defecto
```

### **Error: "CORS headers missing"**
```bash
# Verificar que las correcciones de CORS se aplicaron correctamente
# Revisar el archivo rest_api_odoo.py línea 20-27
```

## 🎯 Coverage Objetivo

El objetivo es mantener **>90% de coverage** en:
- `controllers/rest_api_odoo.py`
- `controllers/jwt_auth.py`

## 🔄 Integración Continua

Para usar en CI/CD, agregar al pipeline:

```yaml
# .gitlab-ci.yml o .github/workflows/tests.yml
test_rest_api:
  script:
    - pip install PyJWT pytest pytest-cov
    - inv test --modules rest_api_odoo
  coverage: '/TOTAL.*\\s+(\\d+%)$/'
```

## 📝 Agregar Nuevos Tests

Para agregar nuevos tests:

1. **Crear archivo de test:**
   ```python
   # tests/test_nueva_funcionalidad.py
   from odoo.tests.common import HttpCase

   class TestNuevaFuncionalidad(HttpCase):
       def test_nueva_funcion(self):
           # Tu test aquí
           pass
   ```

2. **Agregar al __init__.py:**
   ```python
   from . import test_nueva_funcionalidad
   ```

3. **Ejecutar el nuevo test:**
   ```bash
   ./tests/test_runner.py --module test_nueva_funcionalidad
   ```

## 🎉 Ejecución Exitosa

Una ejecución completa exitosa debería mostrar:

```
========= test session starts =========
collected 45 items

test_rest_api_auth.py ........... [24%]
test_rest_api_cors.py ........... [48%]
test_rest_api_crud.py ........... [71%]
test_rest_api_errors.py ......... [100%]

========= 45 passed in 12.34s =========
```

¡Con estos tests puedes verificar completamente que todas las correcciones funcionan correctamente! 🚀