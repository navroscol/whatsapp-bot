from flask import Flask, request, jsonify
import os
from openai import OpenAI
import requests
import base64
import time
import json
from datetime import datetime

app = Flask(__name__)

# Configuración de APIs
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
XAI_API_KEY = os.environ.get('XAI_API_KEY')  # API key de Grok (xAI)
PRODIA_API_KEY = os.environ.get('PRODIA_API_KEY')  # API key de Prodia (sin censura)

# Cliente de OpenAI (para imágenes con GPT-4o)
openai_client = OpenAI(api_key=OPENAI_API_KEY)

# Cliente de Grok (para texto con grok-4-fast-reasoning)
grok_client = OpenAI(
    api_key=XAI_API_KEY,
    base_url="https://api.x.ai/v1"
) if XAI_API_KEY else None

# Configuración de Evolution API
EVOLUTION_API_URL = os.environ.get('EVOLUTION_API_URL')
EVOLUTION_API_KEY = os.environ.get('EVOLUTION_API_KEY')
INSTANCE_NAME = os.environ.get('INSTANCE_NAME', 'my-whatsapp')

def send_whatsapp_message(phone_number, message):
    """Envía un mensaje de WhatsApp usando Evolution API"""
    url = f"{EVOLUTION_API_URL}/message/sendText/{INSTANCE_NAME}"
    
    headers = {
        'Content-Type': 'application/json',
        'apikey': EVOLUTION_API_KEY
    }
    
    data = {
        "number": phone_number,
        "text": message
    }
    
    try:
        response = requests.post(url, json=data, headers=headers)
        return response.json()
    except Exception as e:
        print(f"Error enviando mensaje: {e}")
        return None

def send_welcome_message(phone_number):
    """Envía mensaje de bienvenida generado por IA"""
    # Usar Grok para generar un saludo natural y variado
    try:
        if grok_client:
            response = grok_client.chat.completions.create(
                model="grok-3-fast",
                messages=[
                    {
                        "role": "system",
                        "content": "Eres NAVROS, un asistente virtual amable. Genera un saludo de bienvenida corto, natural y cálido (máximo 7 oraciones). No menciones productos ni vendas nada. Sólo saluda, da la bienvenida a NAVROS y pregunta en qué puedes ayudar. Varía el saludo para que no sea siempre igual. Puedes usar máximo 1 emoji."
                    },
                    {
                        "role": "user",
                        "content": "Genera un saludo de bienvenida"
                    }
                ],
                max_tokens=100,
                temperature=0.9
            )
            mensaje = response.choices[0].message.content
        else:
            mensaje = "¡Hola! ¿En qué te puedo ayudar?"
        
        return send_whatsapp_message(phone_number, mensaje)
    except Exception as e:
        print(f"Error generando bienvenida: {e}")
        return send_whatsapp_message(phone_number, "¡Hola! ¿En qué te puedo ayudar?")

def send_whatsapp_image(phone_number, image_data, caption=""):
    """Envía una imagen por WhatsApp usando Evolution API (soporta URL o base64)"""
    url = f"{EVOLUTION_API_URL}/message/sendMedia/{INSTANCE_NAME}"
    
    headers = {
        'Content-Type': 'application/json',
        'apikey': EVOLUTION_API_KEY
    }
    
    # Detectar si es base64 o URL
    if image_data.startswith("data:"):
        # Es base64, extraer solo los datos
        base64_data = image_data.split(",")[1] if "," in image_data else image_data
        data = {
            "number": phone_number,
            "mediatype": "image",
            "media": base64_data,
            "mimetype": "image/jpeg",
            "caption": caption
        }
    else:
        # Es URL normal
        data = {
            "number": phone_number,
            "mediatype": "image",
            "media": image_data,
            "caption": caption
        }
    
    try:
        response = requests.post(url, json=data, headers=headers)
        print(f"Imagen enviada: {response.status_code}")
        return response.json()
    except Exception as e:
        print(f"Error enviando imagen: {e}")
        return None

def is_image_request(text):
    """Detecta si el usuario está pidiendo generar una imagen"""
    if not text:
        return False
    
    texto_lower = text.lower().strip()
    
    # PRIMERO: Excluir si claramente NO es una imagen
    exclusiones = [
        'texto', 'codigo', 'código', 'programa', 'script', 'lista', 
        'resumen', 'ensayo', 'documento', 'archivo', 'email', 'correo',
        'mensaje', 'respuesta', 'explicación', 'explicacion', 'plan',
        'receta', 'horario', 'tabla', 'excel', 'pdf', 'word',
        'funcion', 'función', 'variable', 'clase', 'método', 'metodo',
        'párrafo', 'parrafo', 'oracion', 'oración', 'frase', 'historia',
        'cuento', 'poema', 'canción', 'cancion', 'letra', 'análisis', 'analisis',
        'informe', 'reporte', 'carta', 'nota', 'apunte', 'tarea',
        'pregunta', 'quiz', 'examen', 'ejercicio', 'problema de',
        'sorteo', 'número', 'numero', 'aleatorio', 'random', 'simulacion', 'simulación'
    ]
    
    for excl in exclusiones:
        if excl in texto_lower:
            return False
    
    # Frases exactas que indican solicitud de imagen
    triggers_exactos = [
        'genera una imagen', 'generar una imagen', 'generame una imagen', 'genérame una imagen',
        'genera la imagen', 'generar la imagen', 'generame la imagen', 'genérame la imagen',
        'crea una imagen', 'crear una imagen', 'creame una imagen', 'créame una imagen',
        'crea la imagen', 'crear la imagen', 'creame la imagen', 'créame la imagen',
        'dibuja', 'dibújame', 'dibujar',
        'hazme una imagen', 'haz una imagen', 'hacer una imagen',
        'hazme un dibujo', 'haz un dibujo',
        'quiero una imagen', 'necesito una imagen',
        'genera un dibujo', 'crea un dibujo',
        'imagina y dibuja', 'imagina y genera',
        'puedes generar', 'puedes crear una imagen', 'puedes dibujar',
        'podrías generar', 'podrías crear una imagen', 'podrías dibujar',
        'me generas', 'me creas una imagen', 'me dibujas',
        'genera imagen', 'crear imagen', 'generar imagen',
        'generame', 'genérame', 'dibujame', 'dibújame',
        'crea img', 'genera img', 'haz img',
        'genera una foto', 'crea una foto', 'hazme una foto'
    ]
    
    for trigger in triggers_exactos:
        if trigger in texto_lower:
            return True
    
    # Patrones: "genera/crea/dibuja" + "imagen/dibujo/foto/ilustración"
    palabras_accion = ['genera', 'crea', 'haz', 'hazme', 'dibuja', 'crear', 'generar', 'dibujar', 'hacer']
    palabras_imagen = ['imagen', 'dibujo', 'foto', 'ilustración', 'ilustracion', 'img', 'picture', 'retrato']
    
    for accion in palabras_accion:
        for imagen in palabras_imagen:
            if accion in texto_lower and imagen in texto_lower:
                return True
    
    # Patrones específicos para personas/personajes (genera a X, dibuja a Y)
    patrones_persona = [
        'genera a ', 'crea a ', 'dibuja a ', 'hazme a ', 'haz a ',
        'generame a ', 'genérame a ', 'creame a ', 'créame a ',
        'dibujame a ', 'dibújame a '
    ]
    
    for patron in patrones_persona:
        if texto_lower.startswith(patron):
            return True
    
    return False

def generate_image(prompt):
    """Genera una imagen usando Prodia con Nano Banana Pro (Gemini 3 Pro)"""
    try:
        print(f"🎨 Generando imagen con Nano Banana Pro: {prompt[:100]}...")
        
        if not PRODIA_API_KEY:
            print("❌ PRODIA_API_KEY no configurado")
            return None
        
        print(f"🔑 API Key presente: {PRODIA_API_KEY[:20]}...")
        
        headers = {
            "Authorization": f"Bearer {PRODIA_API_KEY}",
            "Content-Type": "application/json",
            "Accept": "image/jpeg"
        }
        
        # Usar Nano Banana Pro (Gemini 3 Pro) a través de Prodia v2
        data = {
            "type": "inference.gemini-3-pro.txt2img.v1",
            "config": {
                "prompt": prompt
            }
        }
        
        print(f"📤 Enviando request a Prodia...")
        print(f"📤 Data: {data}")
        
        # Endpoint correcto de Prodia v2
        response = requests.post(
            "https://inference.prodia.com/v2/job",
            headers=headers,
            json=data,
            timeout=120
        )
        
        print(f"📋 Respuesta Status: {response.status_code}")
        print(f"📋 Respuesta Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            content_type = response.headers.get('content-type', '')
            print(f"📋 Content-Type: {content_type}")
            
            if 'image' in content_type:
                # La respuesta es directamente la imagen
                image_base64 = base64.b64encode(response.content).decode('utf-8')
                print(f"✅ Imagen generada exitosamente ({len(image_base64)} chars base64)")
                return f"data:image/jpeg;base64,{image_base64}"
            else:
                # Puede ser JSON con URL
                try:
                    result = response.json()
                    print(f"📋 Respuesta JSON: {result}")
                    if 'imageUrl' in result:
                        return result['imageUrl']
                    elif 'url' in result:
                        return result['url']
                except:
                    pass
                
                # Intentar como imagen de todas formas
                image_base64 = base64.b64encode(response.content).decode('utf-8')
                print(f"✅ Tratando respuesta como imagen ({len(image_base64)} chars)")
                return f"data:image/jpeg;base64,{image_base64}"
        else:
            print(f"❌ Error en la respuesta: {response.status_code}")
            print(f"❌ Response body: {response.text[:500]}")
            return None
    
    except Exception as e:
        print(f"❌ Error generando imagen: {e}")
        import traceback
        traceback.print_exc()
        return None
        return None

# Diccionario para rastrear usuarios nuevos (en memoria)
user_sessions = {}

# Diccionario para almacenar el historial de conversación de cada usuario
conversation_history = {}

def get_exchange_rates():
    """Obtiene tasas de cambio actuales usando API gratuita"""
    try:
        # API gratuita de tasas de cambio
        response = requests.get('https://api.exchangerate-api.com/v4/latest/USD', timeout=5)
        if response.status_code == 200:
            data = response.json()
            rates = data.get('rates', {})
            date = data.get('date', 'N/A')
            
            # Tasas principales
            eur = rates.get('EUR', 'N/A')
            cop = rates.get('COP', 'N/A')
            mxn = rates.get('MXN', 'N/A')
            
            info = f"""📊 TASAS DE CAMBIO ACTUALES (Actualizado: {date})

1 USD = {eur} EUR (Euro)
1 USD = {cop} COP (Peso Colombiano)
1 USD = {mxn} MXN (Peso Mexicano)

Para otras monedas:
- 1 EUR = {1/eur if eur != 'N/A' else 'N/A'} USD
- 1 COP = {1/cop if cop != 'N/A' else 'N/A'} USD"""
            
            return info
        else:
            return None
    except Exception as e:
        print(f"Error obteniendo tasas de cambio: {e}")
        return None

def get_current_info(query):
    """Intenta obtener información actualizada relevante a la consulta"""
    query_lower = query.lower()
    
    # Detectar si pregunta por tasas de cambio
    if any(word in query_lower for word in ['dolar', 'dólar', 'euro', 'peso', 'cambio', 'moneda', 'divisa']):
        return get_exchange_rates()
    
    return None

def is_greeting(text):
    """Detecta si el mensaje es un saludo"""
    if not text:
        return False
    
    saludos = [
        'hola', 'hi', 'hello', 'buenas', 'buenos días', 'buenos dias', 
        'buenas tardes', 'buenas noches', 'hey', 'ey', 'alo', 'aló',
        'que tal', 'qué tal', 'saludos', 'buenas buenas'
    ]
    
    texto_limpio = text.lower().strip()
    
    # Verificar si es exactamente un saludo
    if texto_limpio in saludos:
        return True
    
    # Verificar si empieza con un saludo común
    for saludo in ['hola', 'buenas', 'buenos', 'hey', 'hi']:
        if texto_limpio.startswith(saludo) and len(texto_limpio) < 20:
            return True
    
    return False

def get_chatgpt_response(message, phone_number, image_url=None):
    """Obtiene respuesta de ChatGPT con soporte para imágenes y MEMORIA CONVERSACIONAL"""
    try:
        # Primero verificar si necesita información actualizada
        current_info = None
        if message and not image_url:  # Solo buscar info actual si es texto puro
            current_info = get_current_info(message)
        
        # Inicializar historial si no existe para este usuario
        if phone_number not in conversation_history:
            conversation_history[phone_number] = []
        
        # Obtener historial del usuario (últimos 10 mensajes para no exceder límites)
        user_history = conversation_history[phone_number][-10:]
        
        # Obtener fecha y hora actual
        fecha_actual = datetime.now().strftime("%A %d de %B de %Y")
        hora_actual = datetime.now().strftime("%H:%M")
        
        # Mensaje del sistema - tono profesional, adaptable y natural
        system_message = {
            "role": "system", 
            "content": f"""Eres NAVROS, un asistente virtual amable y versátil. Puedes ayudar con cualquier tema: preguntas generales, tareas, dudas, conversación, y también sobre la marca NAVROS cuando sea relevante.

INFORMACIÓN TEMPORAL IMPORTANTE:
- Fecha actual: {fecha_actual}
- Hora actual (aproximada): {hora_actual}
Usa siempre esta información cuando te pregunten por la fecha u hora.

TU NOMBRE E IDENTIDAD:
- Te llamas NAVROS
- Fuiste creado por el equipo de NAVROS
- Si preguntan quién te creó, quién te hizo, o quién es tu creador, responde que fuiste creado por el equipo de NAVROS
- Puedes generar imágenes cuando te lo pidan (con frases como "genera una imagen de...", "dibuja...", "crea una imagen de...")

PRINCIPIO FUNDAMENTAL:
Sé natural y abierto. NO fuerces el tema de la marca. Si alguien te saluda o pregunta algo general, simplemente ayúdale. Solo habla de NAVROS si el usuario pregunta específicamente sobre ropa, la marca, productos o temas relacionados.

FORMATO DE LINKS IMPORTANTE:
Cuando compartas links, escríbelos de forma limpia y directa, SIN formato markdown:
- Instagram: https://www.instagram.com/navros.co/
- Página web: https://navros.co/
NUNCA uses corchetes [] ni paréntesis () para links. Solo escribe la URL directa.

CÓMO ADAPTARTE AL TONO:

1. TONO POR DEFECTO:
• Amable, cálido y profesional
• Sin jerga callejera ni exceso de emojis
• Cercano sin ser confianzudo

2. SI EL USUARIO ES CASUAL/JUVENIL:
Si usa "bro", "pana", "parce", "man" o habla muy relajado:
• Puedes relajar tu tono gradualmente
• Usa expresiones similares pero sin exagerar
• Máximo 1-2 emojis por mensaje

3. SI EL USUARIO ES MUY FORMAL:
• Mantén distancia respetuosa
• Lenguaje claro y profesional

4. PREGUNTAS ACADÉMICAS O TÉCNICAS:
• Responde con profundidad y precisión
• Usa lenguaje claro y bien estructurado
• Sé útil como un experto accesible
• Puedes dar respuestas extensas y detalladas cuando el tema lo requiera

LO QUE NUNCA DEBES HACER:
• NO menciones la marca NAVROS a menos que sea relevante o te pregunten
• NO fuerces conversaciones hacia productos o ropa
• No uses jerga callejera a menos que el usuario la use primero
• No abuses de emojis (máximo 1-2 por mensaje)
• No seas excesivamente efusivo o exagerado
• NUNCA uses formato markdown para links

CUÁNDO SÍ HABLAR DE NAVROS:
• Si preguntan por ropa, suéteres, camisetas, streetwear
• Si preguntan directamente por la marca o productos
• Si preguntan por precios, envíos, tallas
• Si el contexto lo hace natural

INFORMACIÓN SOBRE NAVROS (usar solo cuando sea relevante):
NAVROS es una marca de streetwear contemporánea que combina lo urbano con elegancia moderna.

Productos principales:
• Suéteres Oversize Premium: prendas gruesas, acid wash, confección premium
• Camisetas Streetwear: cortes amplios, tonos sobrios
• Próximamente: Hoodies, Joggers, Camisas, Accesorios

Estilo: streetwear elegante, siluetas amplias, materiales premium.

EJEMPLOS DE RESPUESTAS:

Usuario: "Quién te creó?"
Tú: "Fui creado por el equipo de NAVROS."

Usuario: "Qué fecha es hoy?"
Tú: "Hoy es {fecha_actual}."

Usuario: "Cuál es tu Instagram?"
Tú: "Nuestro Instagram es https://www.instagram.com/navros.co/"

Usuario: "Ayúdame con una tarea de matemáticas"
Tú: "Claro, con gusto. ¿Qué necesitas resolver?"

Recuerda: eres un asistente útil para TODO, no solo para vender. Sé natural y solo menciona la marca cuando tenga sentido."""
        }
        
        # Construir mensajes incluyendo el historial
        messages = [system_message] + user_history
        
        # Si hay información actual disponible, agregarla al mensaje
        final_message = message
        if current_info:
            final_message = f"{message}\n\n[INFORMACIÓN ACTUALIZADA EN TIEMPO REAL]\n{current_info}\n\nUsa esta información para responder la pregunta del usuario."
            print(f"✅ Información actualizada agregada: {current_info[:100]}...")
        
        # Si hay una imagen, usamos GPT-4o con visión (mejor calidad)
        if image_url:
            print(f"📸 Procesando imagen con GPT-4o Vision...")
            
            try:
                # Crear el mensaje con la imagen
                user_message = {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": final_message if final_message else "¿Qué hay en esta imagen?"
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_url
                            }
                        }
                    ]
                }
                
                messages.append(user_message)
                
                # Usar OpenAI GPT-4o para imágenes
                response = openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=messages,
                    max_tokens=4000,
                    temperature=0.8
                )
                
                print("✅ Imagen procesada exitosamente con GPT-4o")
                
            except Exception as img_error:
                print(f"❌ Error procesando imagen con OpenAI: {img_error}")
                # Si falla con imagen, intentar solo con el texto
                if message:
                    print("Reintentando solo con texto...")
                    user_message = {"role": "user", "content": f"{message} [Nota: Había una imagen pero no pude procesarla]"}
                    messages.append(user_message)
                    response = openai_client.chat.completions.create(
                        model="gpt-4o",
                        messages=messages,
                        max_tokens=4000,
                        temperature=0.8
                    )
                else:
                    raise Exception("No pude procesar la imagen y no hay texto alternativo")
        else:
            # Sin imagen, usar Grok para texto (93% más barato)
            # Si no hay API key de Grok, usar GPT-4o como fallback
            if grok_client:
                print(f"💬 Procesando texto con Grok-4-fast-reasoning...")
                model_to_use = "grok-4-fast-reasoning"
                client_to_use = grok_client
            else:
                print(f"💬 Procesando texto con GPT-4o (Grok no configurado)...")
                model_to_use = "gpt-4o"
                client_to_use = openai_client
            
            user_message = {"role": "user", "content": final_message}
            messages.append(user_message)
            
            response = client_to_use.chat.completions.create(
                model=model_to_use,
                messages=messages,
                max_tokens=4000,
                temperature=0.8
            )
        
        assistant_response = response.choices[0].message.content
        
        # Guardar el intercambio en el historial (solo texto, no imágenes completas para ahorrar tokens)
        conversation_history[phone_number].append({"role": "user", "content": message if message else "[imagen enviada]"})
        conversation_history[phone_number].append({"role": "assistant", "content": assistant_response})
        
        # Limitar historial a últimos 20 mensajes (10 intercambios) para no exceder límites
        if len(conversation_history[phone_number]) > 20:
            conversation_history[phone_number] = conversation_history[phone_number][-20:]
        
        return assistant_response
    except Exception as e:
        print(f"Error con OpenAI: {e}")
        return "Lo siento, hubo un error procesando tu mensaje. Por favor intenta de nuevo."

@app.route('/')
def home():
    return jsonify({
        "status": "Bot de WhatsApp funcionando ✅",
        "mensaje": "Envía mensajes al webhook /webhook",
        "features": "Soporte para texto e imágenes con GPT-4o"
    })

@app.route('/webhook', methods=['POST'])
def webhook():
    """Recibe mensajes de WhatsApp y responde con ChatGPT"""
    try:
        data = request.json
        print(f"Mensaje recibido: {data}")
        
        # Verifica que sea un mensaje entrante
        if data.get('event') == 'messages.upsert':
            message_data = data.get('data', {})
            
            # Extrae información del mensaje
            message_info = message_data.get('message', {})
            phone_number = message_data.get('key', {}).get('remoteJid')
            from_me = message_data.get('key', {}).get('fromMe', False)
            
            # No responde a mensajes propios
            if from_me:
                return jsonify({"status": "ignored", "reason": "mensaje propio"}), 200
            
            # Inicializar variables
            text = None
            image_url = None
            
            # Procesar mensaje de texto
            if message_info.get('conversation'):
                text = message_info.get('conversation')
            elif message_info.get('extendedTextMessage'):
                text = message_info.get('extendedTextMessage', {}).get('text')
            
            # Procesar imagen
            if message_info.get('imageMessage'):
                image_msg = message_info.get('imageMessage', {})
                # Obtener caption de la imagen (texto que acompaña la imagen)
                caption = image_msg.get('caption', '')
                if caption:
                    text = caption
                
                # Las URLs de WhatsApp no son accesibles directamente por OpenAI
                # Necesitamos descargar la imagen usando Evolution API
                try:
                    print("Descargando imagen desde WhatsApp...")
                    
                    # Endpoint para obtener la imagen en base64
                    download_url = f"{EVOLUTION_API_URL}/chat/getBase64FromMediaMessage/{INSTANCE_NAME}"
                    download_data = {
                        "message": message_data
                    }
                    download_headers = {
                        'Content-Type': 'application/json',
                        'apikey': EVOLUTION_API_KEY
                    }
                    
                    response = requests.post(download_url, json=download_data, headers=download_headers, timeout=30)
                    
                    # 200 y 201 son respuestas exitosas
                    if response.status_code in [200, 201]:
                        result = response.json()
                        base64_data = result.get('base64')
                        
                        if base64_data:
                            # Obtener el tipo MIME (por defecto jpeg)
                            mime_type = image_msg.get('mimetype', 'image/jpeg')
                            
                            # Limpiar el base64 (remover espacios, saltos de línea, prefijos, etc)
                            base64_data = base64_data.replace('\n', '').replace('\r', '').replace(' ', '').strip()
                            
                            # Remover cualquier prefijo de data URL si existe
                            if 'base64,' in base64_data:
                                base64_data = base64_data.split('base64,')[1]
                            
                            # Convertir a URL de datos para OpenAI
                            image_url = f"data:{mime_type};base64,{base64_data}"
                            print(f"✅ Imagen descargada y convertida a base64 ({len(base64_data)} caracteres)")
                        else:
                            print("❌ No se obtuvo base64 de la imagen")
                    else:
                        print(f"❌ Error descargando imagen: {response.status_code} - {response.text[:200]}...")
                        
                except Exception as e:
                    print(f"❌ Error procesando imagen: {e}")
                    import traceback
                    traceback.print_exc()
                
                print(f"Imagen procesada - Caption: {caption}, Base64: {'Sí' if image_url and 'base64' in image_url else 'No'}")
            
            # Procesar si hay contenido (texto o imagen)
            if (text or image_url) and phone_number:
                print(f"Procesando mensaje de {phone_number}")
                
                # Si hay imagen pero no hay texto, usar un prompt por defecto
                if image_url and not text:
                    text = "¿Qué hay en esta imagen?"
                    print("Imagen sin caption, usando prompt por defecto")
                
                # Detectar si es un saludo
                es_saludo = is_greeting(text)
                
                # Detectar si es una solicitud de imagen
                es_solicitud_imagen = is_image_request(text)
                print(f"📋 Análisis del mensaje - Saludo: {es_saludo}, Solicitud imagen: {es_solicitud_imagen}, Texto: {text[:50] if text else 'None'}...")
                
                # Verificar si es un usuario nuevo (primera interacción en esta sesión)
                is_new_user = phone_number not in user_sessions
                
                if is_new_user:
                    print(f"Nuevo usuario en esta sesión: {phone_number}")
                    user_sessions[phone_number] = True
                
                # PRIMERO: Si es solicitud de imagen, procesarla directamente (sin bienvenida)
                if es_solicitud_imagen:
                    print(f"🎨 Solicitud de imagen detectada: {text}")
                    
                    # Enviar mensaje de espera
                    send_whatsapp_message(phone_number, "Dame un momento, estoy creando tu imagen... 🎨")
                    
                    # Generar la imagen
                    generated_image_url = generate_image(text)
                    
                    if generated_image_url:
                        # Enviar la imagen generada
                        send_whatsapp_image(phone_number, generated_image_url, "¡Aquí está tu imagen! ✨")
                    else:
                        send_whatsapp_message(phone_number, "Lo siento, no pude generar la imagen. ¿Podrías intentar con otra descripción?")
                    
                    return jsonify({
                        "status": "success",
                        "message": "Imagen generada y enviada",
                        "image_request": True
                    }), 200
                
                # SEGUNDO: Si es solo un saludo simple, enviar bienvenida
                if es_saludo and not image_url:
                    print(f"Enviando mensaje de bienvenida (saludo detectado)")
                    send_welcome_message(phone_number)
                    return jsonify({
                        "status": "success",
                        "message": "Mensaje de bienvenida enviado",
                        "had_image": False,
                        "greeting": True
                    }), 200
                
                if image_url:
                    print(f"Procesando con imagen: {image_url[:100]}...")
                
                try:
                    # Obtiene respuesta de ChatGPT (con o sin imagen)
                    chatgpt_response = get_chatgpt_response(text, phone_number, image_url)
                    
                    # Envía respuesta por WhatsApp
                    send_whatsapp_message(phone_number, chatgpt_response)
                    
                except Exception as e:
                    print(f"Error procesando mensaje: {e}")
                    import traceback
                    traceback.print_exc()
                    
                    # Enviar mensaje de error más específico
                    if image_url:
                        error_msg = "Disculpa, tuve un problema procesando la imagen. ¿Podrías agregar un texto describiendo qué necesitas de la imagen?"
                    else:
                        error_msg = "Disculpa, hubo un error procesando tu mensaje. ¿Podrías intentar de nuevo?"
                    
                    send_whatsapp_message(phone_number, error_msg)
                
                return jsonify({
                    "status": "success",
                    "message": "Respuesta enviada",
                    "had_image": image_url is not None,
                    "new_user": is_new_user
                }), 200
        
        return jsonify({"status": "ok"}), 200
        
    except Exception as e:
        print(f"Error en webhook: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    """Endpoint para verificar que el servidor está funcionando"""
    return jsonify({"status": "healthy"}), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
