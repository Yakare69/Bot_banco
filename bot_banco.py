import discord
import os
import re
import time
import asyncio
from dotenv import load_dotenv

print("Iniciando bot_banco.py...")

# 🔹 Cargar las variables del archivo .env
load_dotenv()
TOKEN = os.getenv("TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

intents = discord.Intents.default()
intents.members = True
intents.messages = True
intents.message_content = True
client = discord.Client(intents=intents)
pedidos = []

@client.event
async def on_ready():  
    print(f"✅ Bot conectado como {client.user}")
    channel = client.get_channel(CHANNEL_ID)

    if channel:
        await channel.send("🎉 BancoBot está listo para recibir comandos.")
    else:
        print("❌ No se encontró el canal en Discord.")

@client.event
async def on_message(message):
    print(f"📩 Mensaje recibido: {message.content}")

    if message.author == client.user:
        return

    contenido = message.content.lower().strip()

    # 🔹 Comando para subir Banco.lua
    if contenido.startswith("!subirbanco"):
        roles_autorizados = {"🎖️ Oficiales 🎖️", "👑 GM 👑"}
        if not any(role.name in roles_autorizados for role in message.author.roles):
            await message.channel.send("⛔ No tienes permisos para subir archivos del banco.")
            return

        if not message.attachments:
            await message.channel.send("❌ Debes adjuntar el archivo `Banco.lua` al mensaje.")
            return

        # 📂 Guardar el archivo Banco.lua
        archivo = message.attachments[0]  
        if not archivo.filename.endswith(".lua"):
            await message.channel.send("❌ El archivo debe ser `Banco.lua`.")
            return

        # Descargar y guardar el archivo en Railway
        ruta_guardado = "Banco.lua"
        await archivo.save(ruta_guardado)

        await message.channel.send(f"✅ Archivo `{archivo.filename}` recibido y actualizado.")

    elif contenido == "!banco":
        print("📩 Comando !banco detectado, enviando lista de objetos...")
        mensajes = leer_banco()

        if mensajes[0].startswith("❌"):  
            await message.channel.send(mensajes[0])
        else:
            for msg in mensajes:
                await message.channel.send(msg)

    elif contenido.startswith("!buscar "):
        query = contenido.replace("!buscar ", "").strip()
        print(f"🔍 Comando !buscar detectado con criterio: {query}")

        if not query:
            await message.channel.send("❌ Debes escribir al menos una palabra clave para buscar.")
            return

        resultados = buscar_objetos(query)
        for resultado in resultados:
            await message.channel.send(resultado)

    elif contenido.startswith("!pedir "):
        datos = message.content.replace("!pedir ", "").strip()
        print(f"📩 Comando !pedir detectado con datos: {datos}")

        partes = [p.strip() for p in datos.split(",")]

        if len(partes) < 2:
            await message.channel.send("❌ Debes escribir el comando con el formato:\n`!pedir [nombre personaje], [nombre objeto], [cantidad (opcional)]`")
            return

        nombre_personaje = partes[0]
        nombre_objeto = partes[1]
        cantidad = partes[2] if len(partes) > 2 and partes[2].isdigit() else "1"

        pedido = f"📌 **{nombre_personaje}** ha pedido: {nombre_objeto} x{cantidad}"
        pedidos.append(pedido)
        await message.channel.send(f"✅ Pedido registrado: {pedido}")

    elif contenido == "!peticiones":
        print("📩 Comando !peticiones detectado, enviando lista de pedidos...")

        if not pedidos:
            await message.channel.send("📭 No hay peticiones registradas en este momento.")
        else:
            mensaje = "**📋 Lista de peticiones registradas:**\n\n"
            mensaje += "\n".join([f"{i+1}️⃣ {pedido}" for i, pedido in enumerate(pedidos)])

            partes = [mensaje[i:i + 2000] for i in range(0, len(mensaje), 2000)]
            for parte in partes:
                await message.channel.send(parte)
    
    elif contenido.startswith("!borrar "):
        parametros = contenido.replace("!borrar ", "").strip()

        if not parametros:
            await message.channel.send("❌ Debes especificar qué deseas borrar. Usa `!borrar peticiones`, `!borrar nombre` o `!borrar número`.")
            return

        roles_autorizados = {"🎖️ Oficiales 🎖️", "👑 GM 👑"}  
        if not any(role.name in roles_autorizados for role in message.author.roles):
            await message.channel.send("⛔ No tienes permisos para borrar peticiones. Solo los **Oficiales** y **GM** pueden hacerlo.")
            return

        # 🔹 Caso 1: Borrar todas las peticiones
        if parametros == "peticiones":
            if not pedidos:
                await message.channel.send("📭 No hay peticiones registradas para borrar.")
            else:
                pedidos.clear()  # 🔥 Borra todas las peticiones
                await message.channel.send("✅ Todas las peticiones han sido eliminadas.")

        # 🔹 Caso 2: Borrar peticiones de un personaje específico
        elif not parametros.isdigit():  
            personaje = parametros
            print(f"📩 Comando !borrar detectado para: {personaje}")

            nuevas_peticiones = [p for p in pedidos if not p.lower().startswith(f"📌 **{personaje.lower()}**")]

            if len(nuevas_peticiones) == len(pedidos):  # Si no se eliminó nada
                await message.channel.send(f"📭 No se encontraron peticiones de **{personaje}**.")
            else:
                pedidos.clear()  # 🔥 Limpiamos la lista original
                pedidos.extend(nuevas_peticiones)  # 🔥 Añadimos las peticiones que quedan
                await message.channel.send(f"✅ Se han eliminado todas las peticiones de **{personaje}**.")

        # 🔹 Caso 3: Borrar una petición específica por número
        else:
            try:
                numero = int(parametros)
                if numero < 1 or numero > len(pedidos):
                    raise ValueError

                pedido_eliminado = pedidos.pop(numero - 1)  # 🔥 Elimina la petición por índice
                await message.channel.send(f"✅ Se ha eliminado la petición: {pedido_eliminado}")

            except ValueError:
                await message.channel.send("❌ Número de petición inválido. Usa `!peticiones` para ver los números disponibles.")

    elif contenido == "!comandos":
        print("📩 Comando !comandos detectado, mostrando lista de comandos...")

        comandos_lista = """
        **📜 Lista de Comandos Disponibles:**
    
        🔹 `!banco` → Muestra el contenido del banco y la cantidad de oro.
        🔹 `!buscar [palabra/s]` → Busca objetos en el banco por palabra clave.
        🔹 `!pedir [nombre personaje], [nombre objeto], [cantidad (opcional)]` → Registra una petición de objeto.
        🔹 `!peticiones` → Muestra la lista de peticiones registradas.
        🔹 `!borrar peticiones` → Elimina todas las peticiones (Solo Oficiales).
        🔹 `!borrar [nombre personaje]` → Elimina todas las peticiones de un personaje (Solo Oficiales).
        🔹 `!borrar [número]` → Borra una petición específica según su número (Solo Oficiales).
        🔹 `!subirbanco` → Permite subir el archivo `Banco.lua` para actualizar el banco (Solo Oficiales).
        🔹 `!comandos` → Muestra esta lista de comandos.
        """

        await message.channel.send(comandos_lista)
# ---------------------- FUNCIONES AUXILIARES ----------------------

def limpiar_nombre_item(item):
    """Extrae solo el nombre del objeto eliminando los códigos de color y enlaces."""
    match = re.search(r'\|h\[(.*?)\]\|h', item)
    return match.group(1) if match else item

def leer_banco():
    """Lee el archivo subido de Banco.lua y devuelve la lista de objetos junto con el oro."""
    banco_path = "Banco.lua"  # 🔹 Ahora siempre lee desde el archivo subido

    if not os.path.exists(banco_path):
        return ["❌ No se encontró el archivo Banco.lua. Usa `!subirbanco` para actualizarlo."]

    with open(banco_path, "r", encoding="utf-8") as file:
        data = file.read()

    # 🔍 Buscar la cantidad de oro
    match_oro = re.search(r'\["oro"\] = (\d+)', data)
    cantidad_oro = int(match_oro.group(1)) if match_oro else 0

    cobre = cantidad_oro % 100
    plata = (cantidad_oro // 100) % 100
    oro = cantidad_oro // 10000
    oro_formateado = f"💰 {oro} 🟡 {plata} ⚪ {cobre} 🟠\n"

    # 🔍 Buscar el contenido del banco o inventario
    match_banco = re.search(r'\["banco"\] = {(.*?)}', data, re.DOTALL)
    match_inventario = re.search(r'\["inventario"\] = {(.*?)}', data, re.DOTALL)

    contenido = match_banco.group(1) if match_banco else match_inventario.group(1) if match_inventario else None
    titulo = "🏦 **Banco de la Hermandad**" if match_banco else "🎒 **Inventario del Banco**" if match_inventario else None

    if not contenido:
        return [oro_formateado + "📂 No hay objetos registrados en el banco."]

    items = re.findall(r'\["(.*?)"\] = (\d+)', contenido)
    lista_objetos = "\n".join([f"- {limpiar_nombre_item(nombre)} x{cantidad}" for nombre, cantidad in items])

    if not lista_objetos.strip():
        return [oro_formateado + "📂 No hay objetos registrados en el banco."]

    mensaje_completo = f"{titulo}\n\n{oro_formateado}\n{lista_objetos}"

    # 📌 Dividir el mensaje en partes de 2000 caracteres si es necesario
    partes = [mensaje_completo[i:i + 2000] for i in range(0, len(mensaje_completo), 2000)]

    return partes

def buscar_objetos(query):
    """Busca objetos en el banco/inventario según palabras clave."""
    palabras = set(query.split())
    banco_path = "Banco.lua"
    
    if not banco_path:
        return ["❌ No se encontró el archivo Banco.lua en SavedVariables."]

    with open(banco_path, "r", encoding="utf-8") as file:
        data = file.read()

    match_banco = re.search(r'\["banco"\] = {(.*?)}', data, re.DOTALL)
    match_inventario = re.search(r'\["inventario"\] = {(.*?)}', data, re.DOTALL)

    contenido = match_banco.group(1) if match_banco else match_inventario.group(1) if match_inventario else None
    if not contenido:
        return ["📂 No hay objetos registrados en el banco ni en el inventario."]

    items = re.findall(r'\["(.*?)"\] = (\d+)', contenido)
    resultados = []

    for nombre, cantidad in items:
        nombre_limpio = limpiar_nombre_item(nombre).lower()
        if all(palabra in nombre_limpio for palabra in palabras):
            resultados.append(f"- {nombre_limpio.capitalize()} x{cantidad}")

    if not resultados:
        return ["📂 No se encontraron objetos con esas palabras clave."]

    mensaje_completo = "🔎 **Resultados de búsqueda:**\n" + "\n".join(resultados)
    partes = [mensaje_completo[i:i + 2000] for i in range(0, len(mensaje_completo), 2000)]
    
    return partes

# ---------------------- EJECUCIÓN DEL BOT ----------------------
print("🚀 Intentando conectar el bot...")
client.run(TOKEN)