# 🤖 Bot de WhatsApp con ChatGPT

Bot completamente funcional que conecta WhatsApp con ChatGPT para responder mensajes automáticamente.

## 📋 GUÍA COMPLETA PASO A PASO

---

## PASO 1: Crear cuenta en OpenAI (5 minutos)

1. **Ve a** https://platform.openai.com/signup
2. **Regístrate** con tu email
3. **Verifica tu email**
4. **Ve a "API Keys"** en el menú izquierdo
5. **Haz clic en "Create new secret key"**
6. **Copia y guarda** esta clave en un lugar seguro (la necesitarás después)
7. **Ve a "Billing"** → "Add payment method"
8. **Agrega $5-10** de crédito (esto durará mucho tiempo)

✅ **¡Listo!** Ahora tienes tu API Key de OpenAI

---

## PASO 2: Crear cuenta en Render (3 minutos)

1. **Ve a** https://render.com
2. **Haz clic en "Get Started"**
3. **Regístrate con GitHub** (o crea cuenta nueva)
4. **Confirma tu email**

✅ **¡Listo!** Ahora puedes subir aplicaciones gratis

---

## PASO 3: Subir el código a GitHub (10 minutos)

Tienes dos opciones:

### Opción A - Usar GitHub Desktop (Más fácil)

1. **Descarga GitHub Desktop** desde https://desktop.github.com
2. **Instálalo y crea una cuenta en GitHub** si no tienes
3. **En GitHub Desktop:**
   - File → New Repository
   - Name: `whatsapp-chatgpt-bot`
   - Local Path: Selecciona donde guardaste los archivos
   - Create Repository
4. **Sube los archivos:**
   - Copia los 3 archivos (app.py, requirements.txt, .env.example) a esa carpeta
   - En GitHub Desktop verás los archivos
   - Escribe "Initial commit" abajo
   - Click en "Commit to main"
   - Click en "Publish repository"
   - Desmarca "Keep this code private"
   - Click "Publish Repository"

### Opción B - Manual en GitHub.com

1. **Ve a** https://github.com/new
2. **Nombre del repositorio:** whatsapp-chatgpt-bot
3. **Marca:** Public
4. **Click en "Create repository"**
5. **Click en "uploading an existing file"**
6. **Arrastra los 3 archivos** (app.py, requirements.txt, .env.example)
7. **Click en "Commit changes"**

✅ **¡Listo!** Tu código está en GitHub

---

## PASO 4: Configurar Evolution API para WhatsApp (15 minutos)

Evolution API es lo que conecta WhatsApp. Puedes usar un servicio gratuito:

### Opción Recomendada: Usar un servicio de Evolution API

Hay varios servicios que ofrecen Evolution API gratis o muy barato:

1. **Ve a** https://evolution-api.com (o busca "evolution api hosting")
2. **Crea una cuenta**
3. **Crea una nueva instancia** con un nombre (ejemplo: "mi-bot")
4. **Guarda estos datos:**
   - URL de la API (ejemplo: https://api.evolution.com)
   - API Key
   - Nombre de tu instancia

5. **Conecta tu WhatsApp:**
   - En el panel, busca "QR Code"
   - Abre WhatsApp en tu teléfono
   - Ve a Configuración → Dispositivos vinculados
   - Escanea el QR code
   - ¡WhatsApp conectado! ✅

**ALTERNATIVA GRATUITA:** Puedes instalar Evolution API gratis en:
- Railway: https://railway.app
- Render: https://render.com
- (Te puedo dar instrucciones si lo prefieres)

---

## PASO 5: Subir tu bot a Render (10 minutos)

1. **Ve a tu Dashboard de Render:** https://dashboard.render.com

2. **Haz clic en "New +"** → **"Web Service"**

3. **Conecta tu repositorio de GitHub:**
   - Click en "Connect account" si es primera vez
   - Busca tu repositorio "whatsapp-chatgpt-bot"
   - Click en "Connect"

4. **Configura el servicio:**
   - **Name:** whatsapp-bot (o el que quieras)
   - **Environment:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
   - **Instance Type:** Free

5. **Agrega las variables de entorno** (click en "Advanced" → "Add Environment Variable"):
   
   ```
   OPENAI_API_KEY = tu-clave-de-openai-aqui
   EVOLUTION_API_URL = https://tu-evolution-api-url
   EVOLUTION_API_KEY = tu-api-key-de-evolution
   INSTANCE_NAME = nombre-de-tu-instancia
   ```

6. **Click en "Create Web Service"**

7. **Espera 5-10 minutos** mientras se instala todo

8. **Cuando termine**, verás una URL tipo: `https://whatsapp-bot-xxxx.onrender.com`

✅ **¡Tu bot está en línea!**

---

## PASO 6: Conectar Evolution API con tu bot (5 minutos)

1. **Ve al panel de Evolution API**

2. **Busca la sección "Webhook" o "Configuración"**

3. **Agrega la URL de tu bot + /webhook:**
   ```
   https://tu-bot.onrender.com/webhook
   ```

4. **Selecciona el evento:** "messages.upsert" o "all messages"

5. **Guarda la configuración**

✅ **¡Todo conectado!**

---

## PASO 7: ¡PRUEBA TU BOT! 🎉

1. **Abre WhatsApp en tu teléfono**
2. **Envía un mensaje al número conectado**
3. **¡El bot debería responder automáticamente!**

---

## 🛠️ SOLUCIÓN DE PROBLEMAS

### El bot no responde:

1. **Verifica que tu bot está activo:**
   - Ve a `https://tu-bot.onrender.com/`
   - Deberías ver: "Bot de WhatsApp funcionando ✅"

2. **Revisa los logs en Render:**
   - Dashboard → Tu servicio → "Logs"
   - Busca errores en rojo

3. **Verifica las variables de entorno:**
   - Asegúrate de que todas estén correctamente configuradas
   - Sin espacios extra al inicio o final

4. **Verifica el webhook en Evolution API:**
   - La URL debe terminar en `/webhook`
   - Debe estar activo

### Errores comunes:

- **"Invalid API Key"**: Tu OPENAI_API_KEY está mal
- **"Connection refused"**: La URL de Evolution API está mal
- **Bot responde dos veces**: Desactiva otras instancias/webhooks

---

## 💰 COSTOS ESTIMADOS

- **Render:** $0/mes (plan gratuito)
- **Evolution API:** $0-5/mes (depende del servicio)
- **OpenAI:** ~$0.002 por mensaje
  - 100 mensajes/día = ~$6/mes
  - 500 mensajes/día = ~$30/mes

---

## 🎨 PERSONALIZACIÓN

### Cambiar la personalidad del bot:

Edita en `app.py` la línea:

```python
{"role": "system", "content": "Eres un asistente útil y amigable en WhatsApp..."}
```

Ejemplos:
- `"Eres un experto en atención al cliente de una tienda de ropa"`
- `"Eres un profesor de inglés que ayuda con vocabulario"`
- `"Eres un asistente personal que ayuda con recordatorios"`

### Usar GPT-4 (mejor calidad):

Cambia en `app.py`:
```python
model="gpt-3.5-turbo"  # Cambia a "gpt-4"
```

⚠️ GPT-4 es ~10x más caro pero mucho mejor

---

## 📞 SOPORTE

Si tienes problemas:
1. Revisa los logs en Render
2. Verifica que todas las variables estén correctas
3. Prueba enviando un mensaje simple como "hola"

---

## 🎉 ¡DISFRUTA TU BOT!

Ahora tienes un bot de WhatsApp profesional conectado con ChatGPT. 
Puedes personalizarlo como quieras y usarlo para tu negocio o proyectos personales.
