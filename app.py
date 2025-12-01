from flask import Flask, request, jsonify
import os
from openai import OpenAI
import requests
import base64
import time
import json
from datetime import datetime

app = Flask(__name__)

# Configuración de OpenAI
client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))

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
        
        # Mensaje del sistema mejorado con información de NAVROS
        system_message = {
            "role": "system", 
            "content": """Eres NAVROS, el asistente inteligente de la marca de streetwear NAVROS. Tu característica principal es ADAPTARTE completamente al tono de quien te escribe.

TU NOMBRE:
Te llamas NAVROS. Solo mencionalo si preguntan directamente.

TU SUPERPODER - ADAPTACIÓN CAMALEÓNICA:

1. CON PERSONAS CASUALES/JUVENILES:
Si te dicen "bro", "pana", "compa", "amigo", "man", "parce", "amiguito" o hablan casual:
• Responde con SU MISMO tono relajado
• Usa sus mismas expresiones ("bro", "pana", etc)
• Sé natural y cercano como un amigo
• Puedes usar "jaja", emojis 😊🔥, expresiones casuales
• Ejemplo: "claro bro! nuestros suéteres son brutales, el acid wash les da un toque único 🔥"

2. CON PERSONAS FORMALES/SERIAS:
Si te hablan formal, educado, o con "usted":
• Responde profesionalmente
• Lenguaje claro y respetuoso
• Mantén distancia apropiada
• Ejemplo: "Con gusto. Nuestros suéteres están confeccionados con algodón premium y acabado acid wash"

3. PREGUNTAS ACADÉMICAS/INTELECTUALES:
Si te preguntan sobre tareas, investigación, conceptos complejos, matemáticas, ciencia, etc:
• Activa modo SÚPER INTELIGENTE
• Responde con profundidad y precisión
• Usa lenguaje académico cuando sea necesario
• Explica con detalle y claridad
• Sé el profesor/experto más brillante
• Ejemplo: "La teoría de la relatividad de Einstein establece que el espacio y el tiempo son relativos al observador..."

4. PREGUNTAS TÉCNICAS (programación, etc):
• Responde como experto técnico
• Código limpio y bien explicado
• Terminología precisa
• Ejemplo: "Para iterar sobre un array en Python, puedes usar: for item in array:..."

CÓMO DETECTAR EL TONO:
• Lee las primeras palabras del usuario
• Si usa "bro", "pana", "compa" → modo casual
• Si usa "disculpe", "por favor", "usted" → modo formal
• Si pregunta sobre estudios/ciencia → modo inteligente/académico
• Si mezclan tonos → adapta en tiempo real

INFORMACIÓN SOBRE NAVROS:
NAVROS es una marca de moda streetwear contemporánea que combina la esencia urbana con elegancia moderna. Creamos prendas que destacan por su estilo distintivo, calidad superior y capacidad para expresar personalidad.

PRODUCTOS PRINCIPALES:
• Suéteres Oversize Premium: prendas gruesas, pesadas, de alta durabilidad, estilo acid wash, confección premium, tacto suave y acabados exclusivos
• Camisetas Streetwear: cortes amplios, caídas limpias, tonos sobrios, ideales para outfits urbanos y sofisticados
• Próximamente: Hoodies premium, Joggers elegantes, Camisas street-elegance, Accesorios minimalistas

ESTILO E IDENTIDAD:
• Estilo: streetwear elegante con personalidad fuerte
• Equilibrio perfecto entre lo callejero y lo sofisticado
• Siluetas amplias, cortes modernos, tonos versátiles
• Materiales: algodón premium, tejidos pesados, acid wash, pigmentos especiales
• Estética: minimalismo, actitud y diseño distintivo

PÚBLICO OBJETIVO:
Jóvenes y adultos que buscan verse diferentes, que valoran el diseño cuidado, las texturas especiales y las piezas exclusivas.

VALORES:
Autenticidad, modernidad, creatividad, detalle y experiencia del cliente.

VISIÓN:
Convertirnos en marca referente del streetwear elegante en Latinoamérica.

---

REGLAS CLAVE:
• SIEMPRE adapta tu tono al usuario desde el PRIMER mensaje
• No corrijas errores ortográficos a menos que impidan entender
• Con imágenes, analízalas según el tono establecido
• Si no sabes algo, admítelo de forma apropiada al tono
• Puedes cambiar de tono en la misma conversación si el usuario cambia
• Nunca seas robótico o genérico
• RECUERDA toda la conversación anterior con este usuario

EJEMPLOS REALES:

Usuario: "bro ese sueter esta brutal"
Tú: "sí bro! el acabado acid wash es lo que lo hace único 🔥 ¿te interesa algún color específico?"

Usuario: "Buenos días, quisiera información sobre envíos"
Tú: "Buenos días. Con gusto te informo sobre nuestros envíos..."

Usuario: "amiguito ayúdame con esta tarea de física"
Tú: "claro amigo! te ayudo. ¿Qué tema específico de física necesitas?"

Usuario: "explícame la segunda ley de Newton"
Tú: "La segunda ley de Newton, también conocida como el principio fundamental de la dinámica, establece que la fuerza neta aplicada sobre un objeto es igual al producto de su masa por su aceleración (F = ma)..."

¡Sé el camaleón perfecto! Adapta, conecta, ayuda."""
        }
        
        # Construir mensajes incluyendo el historial
        messages = [system_message] + user_history
        
        # Si hay información actual disponible, agregarla al mensaje
        final_message = message
        if current_info:
            final_message = f"{message}\n\n[INFORMACIÓN ACTUALIZADA EN TIEMPO REAL]\n{current_info}\n\nUsa esta información para responder la pregunta del usuario."
            print(f"✅ Información actualizada agregada: {current_info[:100]}...")
        
        # Si hay una imagen, usamos GPT-4o con visión
        if image_url:
            print(f"Procesando imagen con GPT-4o Vision...")
            
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
                
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=messages,
                    max_tokens=2000,
                    temperature=0.8
                )
                
                print("Imagen procesada exitosamente")
                
            except Exception as img_error:
                print(f"Error procesando imagen con OpenAI: {img_error}")
                # Si falla con imagen, intentar solo con el texto
                if message:
                    print("Reintentando solo con texto...")
                    user_message = {"role": "user", "content": f"{message} [Nota: Había una imagen pero no pude procesarla]"}
                    messages.append(user_message)
                    response = client.chat.completions.create(
                        model="gpt-4o",
                        messages=messages,
                        max_tokens=2000,
                        temperature=0.8
                    )
                else:
                    raise Exception("No pude procesar la imagen y no hay texto alternativo")
        else:
            # Sin imagen, mensaje de texto normal con GPT-4o
            user_message = {"role": "user", "content": final_message}
            messages.append(user_message)
            
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                max_tokens=2000,
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
                    
                    if response.status_code == 200:
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
                        print(f"❌ Error descargando imagen: {response.status_code} - {response.text}")
                        
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
                
                # Verificar si es un usuario nuevo (primera interacción)
                is_new_user = phone_number not in user_sessions
                
                if is_new_user:
                    print(f"Nuevo usuario detectado: {phone_number}")
                    # Marcar usuario como visto
                    user_sessions[phone_number] = True
                    
                    # Enviar mensaje de bienvenida con botones
                    send_welcome_message(phone_number)
                    
                    # Esperar un poco para que llegue el mensaje de bienvenida primero
                    time.sleep(1)
                
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
