from flask import Flask, request, jsonify
import os
from openai import OpenAI
import requests
import base64
import time
import threading

app = Flask(__name__)

# Configuración de OpenAI
client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))

# Configuración de Evolution API
EVOLUTION_API_URL = os.environ.get('EVOLUTION_API_URL')
EVOLUTION_API_KEY = os.environ.get('EVOLUTION_API_KEY')
INSTANCE_NAME = os.environ.get('INSTANCE_NAME', 'my-whatsapp')

def send_typing_indicator(phone_number):
    """Muestra el estado 'escribiendo...' en WhatsApp"""
    url = f"{EVOLUTION_API_URL}/chat/presence/{INSTANCE_NAME}"
    
    headers = {
        'Content-Type': 'application/json',
        'apikey': EVOLUTION_API_KEY
    }
    
    data = {
        "number": phone_number,
        "presence": "composing",
        "delay": 5000  # Duración en milisegundos
    }
    
    try:
        response = requests.post(url, json=data, headers=headers)
        print(f"Typing indicator response: {response.status_code}")
        return response.json()
    except Exception as e:
        print(f"Error enviando indicador de escritura: {e}")
        return None

def keep_typing(phone_number, stop_event):
    """Mantiene el indicador 'escribiendo...' activo continuamente"""
    while not stop_event.is_set():
        send_typing_indicator(phone_number)
        time.sleep(3)  # Reenviar cada 3 segundos

def stop_typing_indicator(phone_number):
    """Detiene el estado 'escribiendo...' en WhatsApp"""
    url = f"{EVOLUTION_API_URL}/chat/presence/{INSTANCE_NAME}"
    
    headers = {
        'Content-Type': 'application/json',
        'apikey': EVOLUTION_API_KEY
    }
    
    data = {
        "number": phone_number,
        "presence": "paused"
    }
    
    try:
        response = requests.post(url, json=data, headers=headers)
        return response.json()
    except Exception as e:
        print(f"Error deteniendo indicador: {e}")
        return None

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

def get_chatgpt_response(message, phone_number, image_url=None):
    """Obtiene respuesta de ChatGPT con soporte para imágenes"""
    try:
        # Mensaje del sistema mejorado con información de NAVROS
        system_message = {
            "role": "system", 
            "content": """Eres Vareoz, el asistente de WhatsApp de NAVROS. Tu personalidad es relajada, natural y conversacional - hablas como un amigo, NO como un robot corporativo.

TU NOMBRE:
Solo menciona que te llamas Vareoz si alguien pregunta tu nombre directamente. No lo digas en cada mensaje.

TU FORMA DE HABLAR:
• Habla de forma NATURAL y casual, como si estuvieras chateando con un amigo
• Usa emojis cuando sea apropiado (pero sin exagerar)
• Si alguien hace un chiste, ríete o responde con humor
• Si alguien escribe mal, NO corrijas como maestro. En vez de eso:
  - Haz un comentario gracioso
  - Pregunta casual "¿quisiste decir...?" 
  - O simplemente entiende el contexto y sigue la conversación
• Sé auténtico, no uses frases corporativas robóticas
• Puedes usar expresiones como "jaja", "uff", "claro", "dale", etc.
• NO uses frases como "¡Excelente pregunta!" o "Permíteme explicarte" - suena a robot
• Habla como una persona real de Latinoamérica

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
• Materiales duraderos y cómodos: algodón premium, tejidos pesados, acid wash, pigmentos especiales
• Estética: minimalismo, actitud y diseño distintivo

PÚBLICO OBJETIVO:
Jóvenes y adultos que buscan verse diferentes, que valoran el diseño cuidado, las texturas especiales y las piezas exclusivas sin ser inaccesibles.

VALORES:
Autenticidad, modernidad, creatividad, detalle y experiencia del cliente.

VISIÓN:
Convertirnos en una marca referente del streetwear elegante en Latinoamérica, reconocida por diseño distintivo, calidad superior y conexión con la identidad del consumidor moderno.

NAVROS no es solo ropa; es identidad. Es para quienes quieren destacarse con un estilo fuerte pero elegante.

---

IMPORTANTE:
• Cuando hablas de NAVROS, hazlo con entusiasmo genuino pero sin sonar a vendedor agresivo
• Eres útil con cualquier tema, no solo NAVROS
• Si recibes imágenes, analízalas naturalmente
• Mantén conversaciones interesantes y reales
• Si no sabes algo, admítelo casualmente en vez de dar respuestas genéricas
• Adapta tu tono: si alguien es serio, sé más profesional; si es casual, relájate más
• NUNCA empieces mensajes con "¡Hola! Como asistente de..." - suena robotico"""
        }
        
        # Si hay una imagen, usamos GPT-4o con visión
        if image_url:
            print(f"Procesando imagen desde: {image_url}")
            
            # Crear el mensaje con la imagen
            user_message = {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": message if message else "¿Qué hay en esta imagen?"
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": image_url
                        }
                    }
                ]
            }
            
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[system_message, user_message],
                max_tokens=2000,
                temperature=0.8
            )
        else:
            # Sin imagen, mensaje de texto normal con GPT-4o
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    system_message,
                    {"role": "user", "content": message}
                ],
                max_tokens=2000,
                temperature=0.8
            )
        
        return response.choices[0].message.content
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
                
                # Obtener URL de la imagen
                image_url = image_msg.get('url')
                
                print(f"Imagen detectada - URL: {image_url}, Caption: {caption}")
            
            # Procesar si hay contenido (texto o imagen)
            if (text or image_url) and phone_number:
                print(f"Procesando mensaje de {phone_number}")
                
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
                    print(f"Con imagen: {image_url}")
                
                # Crear evento para controlar el indicador de escritura
                stop_typing = threading.Event()
                
                # Iniciar indicador "escribiendo..." en un thread separado
                typing_thread = threading.Thread(
                    target=keep_typing, 
                    args=(phone_number, stop_typing)
                )
                typing_thread.start()
                
                try:
                    # Obtiene respuesta de ChatGPT (con o sin imagen)
                    chatgpt_response = get_chatgpt_response(text, phone_number, image_url)
                    
                    # Detener el indicador de escritura
                    stop_typing.set()
                    typing_thread.join(timeout=1)
                    
                    # Enviar estado final de "pausado"
                    stop_typing_indicator(phone_number)
                    
                    # Envía respuesta por WhatsApp
                    send_whatsapp_message(phone_number, chatgpt_response)
                    
                except Exception as e:
                    # En caso de error, asegurar que se detenga el typing
                    stop_typing.set()
                    typing_thread.join(timeout=1)
                    print(f"Error procesando: {e}")
                
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
