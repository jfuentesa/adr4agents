# Interfaz web

Ejecutar `src\start_app.bat` y abrir **http://127.0.0.1:5000/**. La web y la API se sirven desde la misma aplicación Flask con Waitress; no hace falta iniciar otro servidor para el frontend.

La interfaz usa HTML y CSS con plantillas Jinja y JavaScript sencillo para confirmar el rechazo de propuestas y las sustituciones. Las operaciones siguen funcionando sin JavaScript. Las vistas llaman a las mismas funciones de negocio que la API, conservando sus validaciones y reglas de estados.

## Pantallas

- **Decisiones:** tarjetas con los totales por estado, búsqueda en los textos, filtros por proyecto, estado, autor, etiquetas y fechas, y paginación de 20 elementos. Los totales respetan los filtros excepto el estado, para comparar todos los estados. El ID selecciona la vista previa; el título abre el detalle.
- **Detalle:** contexto, alternativas, decisión, etiquetas, sucesor, comentarios y relaciones. Presenta las acciones válidas para el estado actual.
- **Crear y editar:** proyecto, autor y título obligatorios. Los borradores admiten textos incompletos; las propuestas requieren contexto, alternativas y decisión. La edición conserva el estado. Una fecha vacía se asigna automáticamente al crear y conserva la existente al editar.
- **Proyectos:** listado, búsqueda, creación y edición. El cambio de nombre conserva las decisiones asociadas.
- **Relaciones:** elegir origen, destino y tipo dentro del mismo proyecto. La dirección es origen → destino. Una relación nueva `supersedes` sustituye al destino con el origen y exige ambos aceptados; una sustitución efectiva no puede reasignarse.

Para sustituir un ADR aceptado, proponer un borrador sucesor, completar sus textos, solicitar revisión y aprobarlo. Después hacer efectiva la sustitución desde el original, seleccionando el sucesor aceptado. La propuesta de sustitución por sí sola mantiene vigente el original.

## Presentación y errores

El diseño sigue la referencia aportada: barra lateral, fondo claro, azul principal, tarjetas, tabla y distintivos de estado. En móvil se reorganiza en una sola columna. No incluye plantillas, actividad ni historial.

Los formularios conservan los valores cuando falla la validación y muestran el error junto al campo cuando corresponde. Los textos se escapan para impedir la ejecución de HTML introducido en decisiones o comentarios.

Los formularios incluyen protección CSRF mediante una cookie de sesión y un valor oculto generado automáticamente. Esto no crea cuentas, autenticación ni permisos. Si el servidor se reinicia y un formulario caduca, recargar la página antes de enviarlo. La API mantiene su contrato JSON y no exige este valor de formulario.

## Verificación

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_web -v
```

Las pruebas cubren formularios, errores, protección CSRF, escape de textos, filtros, paginación y los flujos de estados, relaciones y sustituciones, con datos temporales independientes de la base de ejecución.
