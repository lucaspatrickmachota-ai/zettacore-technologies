# ZettaCore Vanguard — Especificación técnica del MVP

**Estado:** propuesta inicial de producto  
**Marca:** ZettaCore Technologies  
**Producto:** ZettaCore Vanguard (independiente de ZettaCore Sentinel)  
**Lema:** “INTELLIGENCE. SECURITY. RESILIENCE.”  
**Primer objetivo de distribución:** aplicación de escritorio para Windows 10/11, manteniendo la arquitectura portable a Linux.

## 1. Visión del producto

Vanguard será una plataforma de ciberseguridad para organizar inteligencia sobre amenazas y vulnerabilidades, evaluar riesgos sobre activos autorizados, conservar el historial de revisiones y producir informes útiles para responsables técnicos y de negocio.

Vanguard no debe presentarse como un antivirus ni afirmar que un equipo está infectado únicamente porque exista información pública sobre malware o una vulnerabilidad en un producto.

## 2. Principios de diseño

- Evidencia antes que afirmaciones: no inventar alertas, cifras, detecciones ni resultados.
- Diferenciar explícitamente **confirmado**, **probable**, **posible** y **no verificado**.
- Privacidad local por defecto para los datos del proyecto; las consultas a fuentes externas se explicarán claramente.
- Análisis autorizados, con alcance definido, inicialmente de solo lectura y no destructivos.
- No ejecutar muestras de malware ni realizar explotación, denegación de servicio o cambios automáticos en sistemas.
- Mantener separados Vanguard y Sentinel; no alterar los módulos existentes de Sentinel.
- Interfaz accesible, adaptable y traducible. Idiomas de producto: español, portugués brasileño e inglés.
- Mantener las credenciales fuera del código y de Git; no registrar secretos ni datos sensibles innecesarios.

## 3. Alcance del MVP

### Incluido en la primera versión funcional

1. **Panel principal:** resumen derivado de los datos reales almacenados; mostrar estados vacíos claros cuando no haya datos.
2. **Inventario de activos:** registrar manualmente activos y sistemas que el usuario tenga autorización para evaluar, con propietario, alcance, entorno y notas.
3. **Inteligencia de vulnerabilidades:** consultar o importar información pública de CVE desde fuentes seleccionadas, comenzando por NVD y CISA Known Exploited Vulnerabilities (KEV), según disponibilidad, límites y condiciones de uso.
4. **Priorización transparente:** mostrar severidad de la fuente, presencia en KEV cuando corresponda, activo afectado, exposición conocida y justificación de la prioridad. No confundir una puntuación CVSS con una probabilidad de explotación.
5. **Historial local:** registrar importaciones, revisiones y cambios relevantes con fechas.
6. **Informes PDF:** informe ejecutivo e informe técnico con alcance, fecha, fuentes, hallazgos, nivel de confianza, limitaciones y recomendaciones.
7. **Internacionalización:** interfaz y explicaciones en español, portugués brasileño e inglés. Mantener sin traducir identificadores técnicos como CVE, hashes y nombres de productos.
8. **Configuración:** idioma, ubicación de datos, preferencias de actualización y exportación.

### Fuera del primer MVP

- Escaneo activo de redes o servicios.
- Auditoría de redes internas, nube, IAM o endpoints.
- Detección de malware en tiempo real o funciones EDR.
- Ejecución o análisis dinámico de muestras sospechosas.
- Remediación automática.
- Gestión multiusuario en servidor, suscripciones comerciales o telemetría centralizada.

Estos módulos se evaluarán posteriormente con requisitos de seguridad, autorización, pruebas y documentación propios.

## 4. Arquitectura propuesta

### Aplicación de escritorio

- **Python** como lenguaje principal.
- **PySide6** para interfaz de escritorio.
- Separación entre interfaz, lógica de negocio, fuentes de inteligencia, persistencia y generación de informes.
- **SQLite** para almacenamiento local estructurado.
- **SQLAlchemy** solo si su valor justifica introducir una capa ORM; puede comenzarse con acceso SQLite sencillo y testeable.
- **pytest** para pruebas unitarias y de integración.
- **ReportLab** para generar PDF.
- Empaquetado inicial con **PyInstaller**; evaluar un instalador de Windows una vez estabilizada la aplicación.

### Estructura orientativa

```text
zettacore-vanguard/
  README.md
  pyproject.toml
  src/vanguard/
    app.py
    ui/
    core/
    models/
    storage/
    intelligence/
    reporting/
    i18n/
  tests/
  docs/
```

Esta estructura es orientativa y se ajustará al código real al iniciar la implementación.

### Separación lógica

- **UI:** ventanas, navegación, formularios y visualización.
- **Core:** validación, reglas de negocio y cálculo explicable de prioridades.
- **Intelligence:** conectores de fuentes públicas y normalización de resultados.
- **Storage:** base de datos local, migraciones y política de retención.
- **Reporting:** PDF ejecutivos y técnicos.
- **i18n:** catálogos de traducción y selección de idioma.

Las consultas externas tendrán tiempos de espera, límites, manejo de errores y mensajes comprensibles. El funcionamiento sin conexión permitirá consultar datos previamente guardados, aunque la inteligencia no estará actualizada hasta volver a sincronizar.

## 5. Modelo de datos inicial

- **Asset:** identificador, nombre, tipo, propietario, entorno, alcance autorizado, notas y fecha de creación.
- **CVERecord:** identificador CVE, descripción de la fuente, CVSS y versión, referencias, fechas y fuente.
- **AssetFinding:** activo relacionado, evidencia, estado, nivel de confianza, severidad, recomendación y fecha de revisión.
- **SyncRun:** fuente, hora de inicio y fin, resultado, número de registros importados y errores.
- **ReportRecord:** fecha, tipo de informe, activos incluidos y ruta de exportación.
- **AppSetting:** idioma y preferencias no sensibles.

No almacenar contraseñas en texto plano. Si en el futuro fueran necesarias credenciales, usar el almacén seguro del sistema operativo y aplicar el principio de mínimo privilegio.

## 6. Reglas para la inteligencia de amenazas

- Mostrar la fuente y la fecha de actualización junto a cada dato importante.
- Diferenciar una amenaza descrita públicamente de una detección observada en el entorno.
- Una CVE asociada a un producto no demuestra por sí sola que un activo esté afectado: se necesita evidencia de producto, versión y contexto.
- La inclusión en CISA KEV indica explotación conocida en el catálogo; no demuestra que el activo del cliente haya sido comprometido.
- Si faltan datos o una fuente no está disponible, indicarlo sin fabricar valores.
- Respetar licencias, condiciones de uso, límites de API y atribución de cada fuente.

## 7. Seguridad y límites operativos

- El MVP se limita a inventario manual e inteligencia pública; no ejecutará pruebas activas sobre objetivos.
- Las funciones futuras de escaneo exigirán autorización explícita, alcance permitido y registro de la operación.
- No realizar explotación, fuerza bruta, DoS ni cambios automáticos por defecto.
- Validar entradas, usar consultas parametrizadas, restringir rutas de exportación y evitar que informes incluyan secretos.
- Tratar descripciones, referencias y contenido importado como datos no confiables, nunca como instrucciones ejecutables.
- Añadir pruebas de actualización, restauración y migración de base de datos antes de distribuir versiones estables.

## 8. Interfaz y marca

- Fondo grafito/negro, azul eléctrico para acciones defensivas, plata para jerarquía visual y rojo reservado a amenazas reales.
- Respetar el emblema de Vanguard ya aprobado. No rediseñarlo ni sustituirlo por una imagen alternativa; adaptar únicamente el fondo o la integración técnica si hiciera falta.
- Navegación propuesta: Inicio, Activos, Vulnerabilidades, Inteligencia, Informes y Configuración.
- Mostrar estados vacíos y datos de demostración claramente etiquetados; nunca presentarlos como telemetría real.

## 9. Hitos de desarrollo

### Hito 0 — Base reproducible
- Crear estructura del proyecto, dependencias y guía de instalación.
- Arranque de aplicación y ventana principal.
- Pruebas básicas y control de calidad automatizado.

### Hito 1 — Inventario local
- Esquema SQLite.
- Alta, edición, consulta y eliminación controlada de activos.
- Validación de campos y pruebas.

### Hito 2 — Inteligencia CVE
- Conector de fuente pública, comenzando por NVD.
- Importación, normalización, deduplicación y registro de sincronizaciones.
- Manejo de límites, errores y datos antiguos.
- Integración de CISA KEV para enriquecer la priorización.

### Hito 3 — Hallazgos e informes
- Relación explícita entre activos y evidencia.
- Priorización explicable.
- Exportación PDF ejecutiva y técnica.

### Hito 4 — Idiomas y calidad
- Español, portugués brasileño e inglés.
- Pruebas de interfaz, accesibilidad básica y mensajes de error.
- Revisión de privacidad y seguridad local.

### Hito 5 — Empaquetado
- Crear ejecutable de Windows.
- Probar en un entorno limpio sin Python instalado.
- Verificar instalación, actualización, persistencia de datos y desinstalación.
- Documentar limitaciones y procedimiento de publicación.

## 10. Criterios de aceptación del MVP

- La aplicación arranca localmente con instrucciones reproducibles.
- El usuario puede gestionar activos sin conexión.
- Los datos importados identifican su fuente y fecha; errores y falta de conexión no generan hallazgos ficticios.
- La priorización expone los factores usados y sus limitaciones.
- Los informes PDF identifican el alcance, fecha, fuentes y limitaciones.
- La interfaz admite los tres idiomas acordados.
- Las pruebas automatizadas cubren la lógica principal y los casos de error.
- El instalador funciona en un Windows de prueba sin requerir una instalación previa de Python.
- No se ejecutan escaneos activos ni remediaciones automáticas en el MVP.

## 11. Decisiones pendientes antes de implementar módulos concretos

- Versión mínima exacta de Windows y versión de Python a fijar tras comprobar compatibilidad.
- Licencias y límites actuales de las fuentes de datos.
- Política final de actualización y retención de datos.
- Diseño final de navegación basado en una interfaz funcional, respetando el emblema aprobado.
- Método de firma del instalador y canal de distribución cuando exista una versión estable.

## 12. Principio de entrega

Cada hito debe terminar con código ejecutable, pruebas y documentación. No anunciar funciones como disponibles hasta que estén implementadas y verificadas. La primera meta es una aplicación local pequeña, fiable y útil; después se ampliará gradualmente hacia auditorías autorizadas, seguridad cloud e integraciones empresariales.
