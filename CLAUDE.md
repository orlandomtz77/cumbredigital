# Cumbre Digital MX 2026 — Proyecto de Práctica

## Sobre este proyecto
App web de registro de asistentes para "Cumbre Digital MX 2026".

## Stack tecnológico
- Fase 1: HTML + CSS + JavaScript (sin servidor)
- Fase 2: Python 3 + Flask + SQLite
- Despliegue: Render.com (opcional)

## Reglas de trabajo
- Todo el contenido y comentarios en español
- Sin frameworks CSS externos (solo CSS puro)
- Diseño responsivo, tema oscuro, moderno
- La base de datos se llama evento.db y está en la raíz del proyecto
- Sin autenticación ni login de momento
- Mensajes de error claros en español

## Estructura del proyecto (Fase 2)
- app.py → servidor Flask principal
- evento.db → base de datos SQLite
- templates/ → páginas HTML (index, confirmacion, admin)
- requirements.txt → dependencias Python
- Procfile → configuración para Render

## Contexto del evento
- Nombre: Cumbre Digital MX 2026
- Tema: Transformación digital para PyMEs
- Campos del formulario: nombre completo, email, empresa, área de interés
- Áreas: Tecnología / Marketing / Negocios / Emprendimiento

## Servidores MCP disponibles (alcance proyecto)
- github: para subir el código al repositorio
- sqlite: para interactuar con evento.db (se agrega en Fase 2)
- playwright: para pruebas automáticas (Fase 3)