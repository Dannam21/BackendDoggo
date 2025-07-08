# BackendDoggo

La API RESTful **BackendDoggo** está diseñada para gestionar adopciones y eventos de mascotas entre adoptantes y albergues usando FastAPI.

---

## 1. Arquitectura del Sistema

**Visión General**

BackendDoggo se estructura en capas desacopladas:

- **API:** FastAPI + Uvicorn para endpoints HTTP y WebSocket.
- **Lógica de Negocio:** `crud.py` implementa funciones de registro/login, gestión de usuarios, mascotas, citas, matches, adopciones, denegaciones y donaciones.
- **Persistencia:** SQLAlchemy + PostgreSQL con modelos en `models.py`.
- **Autenticación:** JWT con `python-jose`, tokens válidos 30 minutos y dependencias que protegen rutas (en `auth.py`).
- **Almacenamiento de Imágenes:** Endpoints dedicados para subir/descargar archivos estáticos.
- **WebSockets:** Chat en tiempo real para adoptantes y albergues.

---

## 2. Requisitos del Sistema

### Hardware

- **Desarrollo:** 8 GB RAM, 20 GB disco.
- **Producción:** Instancia adecuada (p. ej., t3.medium en AWS).

### Software

- **SO:** Linux, macOS o Windows (WSL2).
- **Lenguajes:** Python ≥ 3.10, Node.js ≥ 20.x.
- **Contenedores:** Docker & Docker Compose (opcional).

### Dependencias (requirements.txt)

```text
fastapi
uvicorn
sqlalchemy
psycopg2
python-jose
passlib[bcrypt]
bcrypt
python-multipart
pytz
websockets
email-validator
scikit-learn
```

---

## 3. Configuración del Entorno de Desarrollo

1. **Clonar el repositorio**
   ```bash
   git clone <url-repo>
   cd dannam21-backenddoggo
   ```
2. **Variables de entorno** Crear un archivo `.env` en la raíz del proyecto con:
   ```ini
   DATABASE_URL=postgresql://user:pass@host:5432/backenddoggo
   SECRET_KEY=<clave_secreta>
   ```
3. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```
4. **Ejecutar la aplicación**
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

---

## 4. Uso de la Aplicación

### Autenticación

- `POST /register/adoptante` – Registra un adoptante y devuelve JWT.
- `POST /login/adoptante` – Autentica adoptante.
- `POST /register/albergue` – Registra un albergue.
- `POST /login/albergue` – Autentica albergue.

### Gestión de Entidades

- **Adoptantes:**
  - `GET /adoptante/me`
  - `PUT /adoptante/{id}`
  - `PATCH /adoptante/{id}`
- **Albergues:**
  - `GET /albergue/me`
  - `PUT /albergue/{id}`
- **Mascotas:**
  - `GET /mascotas`
  - `POST /mascotas`
  - `PUT /mascotas/{id}`
  - `GET /mascotas/{id}`

### Citas

- `POST /calendario/visita` – Agendar visita.
- `POST /calendario/evento` – Agendar evento.
- `GET /calendario/albergue/{albergue_id}`
- `GET /calendario/adoptante/{adoptante_id}`
- `GET /calendario/dia/{fecha}`

### Matches, Adopciones y Denegaciones

- `POST /matches/` – Crear match adoptante-mascota.
- `POST /matches/{adoptante_id}/{mascota_id}/complete` – Confirmar adopción.
- `POST /matches/{adoptante_id}/{mascota_id}/deny` – Denegar match.

### Chat en Tiempo Real

- **WebSocket:** `ws://<host>/ws/chat/{tipo}/{id}`

---

## 5. Referencia de la API

La documentación interactiva Swagger está disponible en `http://localhost:8000/docs`.

### Endpoints Clave

| Método | Ruta                        | Descripción                    |
| ------ | --------------------------- | ------------------------------ |
| POST   | `/register/adoptante`       | Registro adoptante             |
| POST   | `/login/adoptante`          | Login adoptante                |
| GET    | `/adoptante/me`             | Obtener perfil adoptante       |
| POST   | `/register/albergue`        | Registro albergue              |
| POST   | `/login/albergue`           | Login albergue                 |
| GET    | `/albergue/me`              | Obtener perfil albergue        |
| GET    | `/mascotas`                 | Listar mascotas                |
| POST   | `/mascotas`                 | Crear mascota (solo albergue)  |
| PUT    | `/mascotas/{mascota_id}`    | Editar mascota (solo albergue) |
| GET    | `/mascotas/{mascota_id}`    | Detalles de mascota            |
| POST   | `/calendario/visita`        | Agendar visita                 |
| POST   | `/calendario/evento`        | Agendar evento                 |
| POST   | `/matches/`                 | Crear match                    |
| POST   | `/matches/{a}/{m}/complete` | Confirmar adopción             |
| POST   | `/matches/{a}/{m}/deny`     | Denegar match                  |
| WS     | `/ws/chat/{tipo}/{id}`      | Mensajería en tiempo real      |

---

## 6. Modelos de Datos

- **Adoptante, Albergue, Mascota:** Relación muchos-a-muchos a través de `Match`.
- **Calendario:** Tablas para `CitaVisita` y `CitaEvento`.
- **Mensaje:** Incluye `mascota_id` para contexto de chat.
- **Históricos:** `MatchTotal`, `Donacion`, `Adopcion`, `Denegacion`.

---

## 7. Pruebas y Calidad

- **Unitarias:** Usar `pytest` para CRUD y autenticación.
- **Integración:** Tests con `httpx` o `requests`.
- **Manual:** Validar flujos clave en Swagger UI.

---

## 8. Resolución de Problemas

- **Error 401 (Token inválido):** Revisar `SECRET_KEY`, expiración en `auth.py`.
- **Conexión a BD:** Verificar `DATABASE_URL` y que PostgreSQL esté activo.
- **Subida de Archivos:** Comprobar permisos en carpetas de imágenes.
- **WebSocket Desconectado:** Revisar logs y URI de cliente.

---

## 9. Seguridad

- **JWT:** Expiración de 30 min; almacenar seguro en cliente.
- **Hashing:** Contraseñas con BCrypt (`passlib[bcrypt]`).
- **CORS:** Configurar orígenes permitidos en producción.
- **Validación:** Pydantic en `schemas.py`.

---

¡Listo! He corregido los bloques de código y la sintaxis Markdown en todo el README. Avísame si quieres más cambios o detalles adicionales.

