from flask import Flask, request, jsonify
import os
from openai import OpenAI
import requests

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

def get_chatgpt_response(message, phone_number):
    """Obtiene respuesta de ChatGPT"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o",  # Puedes cambiarlo a "gpt-4" si quieres mejor calidad
            messages=[
                {"role": "system", "content": "Eres NAVROS, un asistente de inteligencia artificial desarrollado por OpenAI. Respondes de forma inteligente, detallada y natural. Puedes ayudar con cualquier tema: explicar conceptos, resolver problemas, dar consejos, programar, escribir, analizar información y mucho más. Siempre eres útil, creativo y conversacional. Adaptas tu tono al contexto de la conversación."},
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
        "mensaje": "Envía mensajes al webhook /webhook"
    })

@app.route('/webhook', methods=['POST'])
def webhook():
    """Recibe mensajes de WhatsApp y responde con ChatGPT"""
    try:
        data = request.json
        print(f"Mensaje recibido: {data}")
        
        # Verifica que sea un mensaje de texto
        if data.get('event') == 'messages.upsert':
            message_data = data.get('data', {})
            
            # Extrae información del mensaje
            message_info = message_data.get('message', {})
            
            # Solo procesa mensajes de texto del usuario (no respuestas del bot)
            if message_info.get('conversation') or message_info.get('extendedTextMessage'):
                text = message_info.get('conversation') or message_info.get('extendedTextMessage', {}).get('text')
                phone_number = message_data.get('key', {}).get('remoteJid')
                from_me = message_data.get('key', {}).get('fromMe', False)
                
                # No responde a mensajes propios
                if from_me:
                    return jsonify({"status": "ignored", "reason": "mensaje propio"}), 200
                
                if text and phone_number:
                    print(f"Procesando mensaje de {phone_number}: {text}")
                    
                    # Obtiene respuesta de ChatGPT
                    chatgpt_response = get_chatgpt_response(text, phone_number)
                    
                    # Envía respuesta por WhatsApp
                    send_whatsapp_message(phone_number, chatgpt_response)
                    
                    return jsonify({
                        "status": "success",
                        "message": "Respuesta enviada"
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
