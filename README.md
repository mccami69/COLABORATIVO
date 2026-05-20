# Cafetería virtual

Proyecto Flask + MySQL + HTML + CSS + JavaScript con 3 roles:

- Usuario
- Administrador
- Cocinero

## 1. Qué hace

- Registro e inicio de sesión de usuario.
- Login fijo de administrador: `admin@x.com` / `123`.
- Login fijo de cocinero: `cocina@x.com` / `123`.
- Catálogo con productos por categoría.
- Carrito funcional con cambio de cantidades.
- Checkout con opción de pago efectivo o tarjeta.
- Mensaje especial si paga en efectivo.
- Historial de pedidos del usuario.
- Rastreo del pedido con actualización en tiempo real.
- Simulación visual de entrega cuando el pedido pasa a `en camino`.
- Panel de administrador para inventario, productos y estados.
- Panel de cocina para ver pedidos e ingredientes.

## 2. Instalación

1. Importa [database.sql](database.sql) en MySQL. Ese archivo crea la base `cafeteria_virtual` y las tablas.
2. Copia [.env.example](.env.example) a `.env` y ajusta tus credenciales.
3. Instala dependencias:

```bash
pip install -r requirements.txt
```

4. Ejecuta la app:

```bash
python app.py
```

O en Windows puedes usar el script asistido:

```powershell
./start_server.ps1
```

Ese script se reinicia como administrador, crea la regla de firewall para el puerto `5000` si hace falta y luego arranca la app.

5. Abre en tu PC:

```text
http://127.0.0.1:5000
```

6. Para abrirlo desde otro dispositivo conectado a la misma red Wi-Fi, usa la IP que imprime la consola al iniciar, por ejemplo:

```text
http://192.168.1.20:5000
```

7. Si quieres abrirlo desde cualquier lugar con una URL pública, necesitas desplegarlo en un servidor o usar un túnel HTTPS como ngrok o Cloudflare Tunnel.

8. Si desde otro dispositivo de la misma red no abre, revisa el Firewall de Windows y permite el puerto `5000` para `python.exe` o abre una regla TCP entrante en ese puerto. En PowerShell como administrador:

```powershell
netsh advfirewall firewall add rule name="Flask Cafeteria 5000" dir=in action=allow protocol=TCP localport=5000
```

## 3. Credenciales de prueba

- Administrador: `admin@x.com` / `123`
- Cocinero: `cocina@x.com` / `123`

## 4. Nota importante

Localmente el proyecto usa la base de datos que definas en `DATABASE_URL`. Para guardar en MySQL, deja `DATABASE_URL` apuntando a `mysql+pymysql://root@localhost/cafeteria_virtual` y asegúrate de que MySQL esté encendido.

Ejemplo de conexión sin contraseña:

```text
mysql+pymysql://root@localhost/cafeteria_virtual
```