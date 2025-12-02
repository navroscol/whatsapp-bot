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
    """Envía mensaje de bienvenida con botones interactivos"""
    url = f"{EVOLUTION_API_URL}/message/sendButtons/{INSTANCE_NAME}"
    
    headers = {
        'Content-Type': 'application/json',
        'apikey': EVOLUTION_API_KEY
    }
    
    data = {
        "number": phone_number,
        "title": "🖤 ¡Bienvenido a NAVROS!",
        "description": "Streetwear elegante con actitud. Explora nuestras redes:",
        "buttons": [
            {
                "type": "url",
                "displayText": "📸 Instagram",
                "url": "https://www.instagram.com/navros.co/"
            },
            {
                "type": "url", 
                "displayText": "🌐 Página Web",
                "url": "https://navros.co/"
            }
        ]
    }
    
    try:
        response = requests.post(url, json=data, headers=headers)
        print(f"Welcome message sent: {response.status_code}")
        return response.json()
    except Exception as e:
        print(f"Error enviando mensaje de bienvenida: {e}")
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
                
                # Verificar si es un usuario nuevo (primera interacción)
                is_new_user = phone_number not in user_sessions
                
                if is_new_user:
                    print(f"Nuevo usuario detectado: {phone_number}")
                    # Marcar usuario como visto
                    user_sessions[phone_number] = True
                
                # Enviar mensaje de bienvenida si es saludo O usuario nuevo
                if es_saludo or is_new_user:
                    print(f"Enviando mensaje de bienvenida (saludo: {es_saludo}, nuevo: {is_new_user})")
                    send_welcome_message(phone_number)
                    
                    # Esperar un poco para que lleguen los botones primero
                    time.sleep(0.5)
                    
                    # Enviar también un mensaje de texto de bienvenida
                    send_whatsapp_message(phone_number, "¡Hola! ¿En qué te puedo ayudar?")
                    
                    # Si solo fue un saludo simple, terminar aquí
                    if es_saludo and not image_url:
                        return jsonify({
                            "status": "success",
                            "message": "Mensaje de bienvenida enviado",
                            "had_image": False,
                            "greeting": True
                        }), 200
                
                if image_url:
                    print(f"Procesando con imagen: {image_url[:100]}...")  # Solo mostrar primeros 100 caracteres
                
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
