# Chess Atelier · Registro de jugadores (CRUD)

Aplicación web con Flask y base de datos SQLite.

- **Consultar todos:** página principal (con búsqueda por nombre o país)
- **Consultar uno:** clic en el nombre o en "Ver"
- **Agregar:** botón "+ Agregar"
- **Editar:** botón "Editar"
- **Eliminar:** botón "Eliminar" (pide confirmación)

## Probar en tu computadora

```
pip install -r requirements.txt
python app.py
```

Abre http://localhost:5000

## Subir a Render

- Build Command: `pip install -r requirements.txt`
- Start Command: `gunicorn app:app`
