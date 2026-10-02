# API de ADR4agents

Base: `/api/v1`. Las peticiones con cuerpo usan `Content-Type: application/json`. Todas las operaciones están abiertas, sin autenticación ni cuentas. `author` es texto informativo y no identifica una sesión.

## Modelo de decisión

```json
{
  "project": "demo",
  "author": "Agent1",
  "title": "Elegir SQLite",
  "context": "Aplicación pequeña con un único servidor",
  "alternatives": "PostgreSQL requiere un servicio adicional",
  "decision": "Utilizar SQLite",
  "tags": "database,python",
  "date": "2026-10-02"
}
```

`project` corresponde a un proyecto existente y no admite espacios. `author` admite letras y números, sin espacios ni guiones. Las etiquetas se reciben y devuelven como una cadena separada por comas; se eliminan duplicados y se ordenan. Cada etiqueta es una palabra sin espacios y puede contener guiones. Una cadena vacía representa ausencia de etiquetas.

`date` acepta fechas válidas en formato `YYYY-MM-DD`. Si se omite al crear, se utiliza la fecha local del servidor. Los campos de texto se recortan en sus extremos. Una propuesta requiere proyecto, autor, título, contexto, alternativas y decisión; etiquetas y fecha pueden omitirse.

Las respuestas añaden `id`, `status` y `superseded_by`. Los estados son `draft`, `proposed`, `accepted`, `rejected` y `superseded`. `superseded_by` es `null` mientras no exista una sustitución efectiva.

Límites: 128 caracteres para proyecto, autor y cada etiqueta; 300 para título; 100 000 para cada texto extenso; 4096 para la cadena de etiquetas; 1 MiB por cuerpo JSON.

## Endpoints

Todas las rutas siguientes se añaden a `/api/v1`. Los identificadores de las rutas son números enteros positivos.

| Método | Ruta | Operación |
| --- | --- | --- |
| GET | `/health` | Comprobar el servicio y el acceso a SQLite. |
| GET | `/projects` | `list_projects` |
| GET | `/projects/{id}` | `get_project` |
| POST | `/projects` | `create_project` |
| PATCH | `/projects/{id}` | `update_project` |
| GET | `/decisions` | `list_decisions` |
| GET | `/decisions/search` | `search_decisions` |
| GET | `/decisions/current` | `get_current_decisions` |
| GET | `/decisions/{id}` | `get_decision` |
| POST | `/decisions` | `create_decision`: crea `proposed`. |
| POST | `/decisions/drafts` | `create_decision_draft`: crea `draft`. |
| PATCH | `/decisions/{id}` | `update_decision` |
| PATCH | `/decisions/{id}/draft` | `update_decision_draft` |
| POST | `/decisions/{id}/review` | `request_decision_review` |
| POST | `/decisions/{id}/approve` | `approve_decision` |
| POST | `/decisions/{id}/reject` | `reject_decision` |
| POST | `/decisions/{id}/supersede` | `supersede_decision` |
| POST | `/decisions/{id}/replacement` | `propose_decision_replacement` |
| GET | `/decisions/{id}/relations` | `get_decision_relations` |
| GET | `/relations/{id}` | Consultar una relación. |
| POST | `/relations` | `create_relation` |
| PATCH | `/relations/{id}` | `update_relation` |
| GET | `/decisions/{id}/comments` | Consultar comentarios. |
| POST | `/decisions/{id}/comments` | `comment_decision` |
| GET | `/tags` | `list_tags` |

## Proyectos y edición

Crear un proyecto con `{"name":"demo","description":"Descripción","context":"Contexto"}`. Solo `name` es obligatorio y debe ser una palabra sin espacios. `description` y `context` son textos libres, vacíos por defecto. Los nombres de proyecto son únicos y distinguen mayúsculas. Renombrar un proyecto conserva sus decisiones y relaciones.

Los endpoints PATCH aceptan los campos que se quieran modificar, con al menos uno presente. Los campos omitidos se conservan. El estado y el sucesor no pueden editarse directamente: cambian mediante las operaciones específicas. Editar un ADR aceptado conserva `accepted`.

## Borradores y estados

Un borrador solo requiere `project`, `author` y `title`. Los textos `context`, `alternatives` y `decision` pueden omitirse o estar vacíos. Para enviarlo a revisión deben estar completos.

Las operaciones `/review`, `/approve` y `/reject` reciben un cuerpo JSON vacío `{}`:

```text
draft → review → proposed → approve → accepted
                         → reject → rejected
```

Las transiciones desde un estado incorrecto devuelven `409`. Los campos de texto incompletos impiden solicitar revisión con `400`.

## Relaciones y sustituciones

Crear una relación con `{"source_id":2,"target_id":1,"type":"complements"}`. Las decisiones deben pertenecer al mismo proyecto y ser distintas. Los tipos admitidos son `complements`, `contradicts` y `supersedes`. La dirección es del origen al destino: el origen complementa, contradice o sustituye al destino.

Una relación devuelve `id`, `source_id`, `target_id`, `type` y `effective`. Las relaciones de complemento y contradicción son efectivas inmediatamente. Su listado incluye tanto las entrantes como las salientes y admite paginación.

`POST /decisions/{original_id}/replacement` recibe los campos de un borrador, con `author` y `title` obligatorios. El proyecto se toma del ADR original. Crea un borrador sucesor y una relación `supersedes` con `effective:false`; el original conserva `accepted`.

Tras completar, revisar y aprobar el sucesor, `POST /decisions/{original_id}/supersede` con `{"successor_id":2}` hace efectiva la sustitución. Ambos ADR deben estar en `accepted`. El original pasa a `superseded`, su `superseded_by` referencia al sucesor y la relación queda con `effective:true`. El sucesor conserva `accepted`.

Crear una relación `supersedes` directamente también hace efectiva la sustitución y exige ambos ADR aceptados. Una propuesta de sustitución existente se activa sin duplicar la relación. Editar una relación de complemento o contradicción a `supersedes` también hace efectiva la sustitución.

Las relaciones de sustitución ya efectivas no pueden reasignarse o convertirse a otro tipo: invalidaría el estado y el sucesor del ADR original. Un ADR relacionado no puede trasladarse a otro proyecto. Todas las escrituras de una sustitución se confirman o revierten conjuntamente.

## Consultas y paginación

Las colecciones aceptan `page` y `page_size`. Valores predeterminados: página 1 y 20 elementos; máximo 100 elementos por página. Se ordenan por identificador ascendente; las etiquetas, por texto.

```json
{
  "items": [],
  "pagination": {"page": 1, "page_size": 20, "total": 0, "pages": 0}
}
```

Filtros de decisiones:

- `project`, `author` y `status`: coincidencia exacta.
- `tags`: cadena separada por comas; deben coincidir todas las etiquetas indicadas.
- `date_from` y `date_to`: intervalo inclusivo en formato `YYYY-MM-DD`.
- `q`: búsqueda de texto en título, contexto, alternativas y decisión.

`/decisions/search` exige `q`. `/decisions/current` devuelve solo `accepted` y acepta los demás filtros. La búsqueda no distingue mayúsculas, incluidos caracteres Unicode, y trata `%`, `_` y comillas como caracteres literales, no como SQL.

`/projects` acepta `q` para buscar en nombres; `/tags` acepta `project`. Los filtros pueden combinarse con la paginación. Los parámetros desconocidos, repetidos o inválidos se rechazan.

## Comentarios

Crear un comentario con `{"author":"Agent1","text":"Observación","date":"2026-10-02"}`. `author` y `text` son obligatorios; la fecha se calcula si se omite. Los comentarios no alteran el contenido ni el estado del ADR. El listado de comentarios admite paginación.

## Errores y respuestas

- `200`: consulta, edición o transición correcta.
- `201`: recurso creado; la cabecera `Location` indica su ubicación o colección.
- `400`: datos, campos, filtros o cuerpo JSON inválidos.
- `404`: recurso o ruta inexistente.
- `405`: método no permitido.
- `409`: nombre duplicado, relación duplicada o conflicto de estado.
- `413`: cuerpo demasiado grande.
- `415`: cuerpo sin tipo de contenido JSON.
- `503`: SQLite está ocupado; la operación puede reintentarse.

```json
{
  "error": {
    "code": "validation_error",
    "message": "Must contain only letters and numbers.",
    "field": "author"
  }
}
```

Los errores de la aplicación son JSON. `field` aparece cuando corresponde a un campo concreto. Los campos desconocidos se rechazan, y las operaciones que requieren varias escrituras se ejecutan dentro de una transacción. Waitress puede rechazar peticiones HTTP antes de llegar a Flask, como un cuerpo superior a 1 MiB; esas respuestas de transporte pueden tener otro formato.

## Ejemplo con PowerShell

```powershell
$api = 'http://127.0.0.1:5000/api/v1'
Invoke-RestMethod "$api/projects" -Method Post -ContentType 'application/json' `
    -Body '{"name":"demo"}'

$payload = @{
    project = 'demo'
    author = 'Agent1'
    title = 'Choose SQLite'
    context = 'Small application'
    alternatives = 'PostgreSQL'
    decision = 'Use SQLite'
    tags = 'database,python'
} | ConvertTo-Json

$adr = Invoke-RestMethod "$api/decisions" -Method Post `
    -ContentType 'application/json' -Body $payload

Invoke-RestMethod "$api/decisions/$($adr.id)/approve" -Method Post `
    -ContentType 'application/json' -Body '{}'

Invoke-RestMethod "$api/decisions/current?project=demo"
```
