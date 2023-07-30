from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
import openai
import random
import uuid
from html import escape

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")
openai.api_key = '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'

users = {}
conversations = {}
animals = ['Cat', 'Dog', 'Elephant', 'Lion', 'Tiger', 'Bear',
           'Owl', 'Fish', 'Shark', 'Eagle', 'Panda', 'Leopard']
adjectives = ['Crazy', 'Happy', 'Sad', 'Amusing',
              'Furious', 'Fast', 'Slow', 'Serious']
@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def connect():
    username = random.choice(adjectives) + random.choice(animals) + str(random.randint(1000,9999))
    users[request.sid] = username
    conversations[request.sid] = []
    emit(
        'message',
        {
          'user': 'admin',
          'text': f'{username} has joined the chat, please @ChatGPT to get responses. My personal website: chatgpt.org.uk'
        },
        broadcast=True
    )
    emit('onlineUsers', users, broadcast=True)

@socketio.on('disconnect')
def disconnect():
    user = users[request.sid]
    del users[request.sid]
    if request.sid in conversations:
        del conversations[request.sid]
    emit('message', {'user': 'admin', 'text': f'{user} has left the chat.'}, broadcast=True)
    emit('onlineUsers', users, broadcast=True)

@socketio.on('sendMessage')
def handle_message(data):
    user = users[request.sid]
    message = data['message']
    model_str = data.get('model', 'gpt-3.5-turbo')
    message = escape(message)

    emit('message', {'user': user, 'text': message}, broadcast=True)

    if '@ChatGPT' in message:
        prompt = message.replace('@ChatGPT', '').strip()

        if model_str == 'DALL-E':
            handle_dalle_image_generation(prompt, user)
        else:
            try:
                conversation_history = conversations.get(request.sid)
                conversation_history.append({"role": "user", "content": prompt})

                if len(conversation_history) > 10:
                    del conversation_history[0]

                response = openai.ChatCompletion.create(
                    model=model_str,
                    messages=conversation_history,
                    max_tokens=2000,
                    stream=True
                )

                chatGPTReplyWithUsername = "<strong>ChatGPT: @" + user + "</strong> <br>"

                collected_messages = []
                update_id = None

                for chunk in response:
                    if 'content' in chunk['choices'][0]['delta']:
                        chunk_message_content = chunk['choices'][0]['delta']['content']

                        # 对消息内容进行HTML转义
                        chunk_message_content = escape(chunk_message_content)
                        
                        chunk_message_content = chunk_message_content.replace('\n', '<br>')

                        chatGPTReplyWithUsername += chunk_message_content

                        if update_id is None:
                            msg = {"id": str(uuid.uuid4()), "user": "ChatGPT", "text": chatGPTReplyWithUsername}
                            update_id = msg["id"]
                            emit('message', msg, broadcast=True)
                        else:
                            emit('updateMessage', {"id": update_id, "newText": chatGPTReplyWithUsername}, broadcast=True)

                    collected_messages.append(chunk['choices'][0]['delta'])

                assistant_reply_content = ''.join([m.get('content', '') for m in collected_messages])
                conversation_history.append({"role": "assistant", "content": assistant_reply_content})

            except Exception as e:
                print(f'Error calling OpenAI API: {e}')
                errorMsg = f'Sorry, but we encountered an error while processing your request. Details: {str(e)}'
                emit('message', {'user': 'System Message', 'text': errorMsg, 'type': 'system-msg'}, broadcast=True)

def handle_dalle_image_generation(prompt, user):
    # Send status update message with unique id
    msg_id = str(uuid.uuid4())
    emit('message', {'id': msg_id, 'user': 'System Message', 'text': f'Image generation for {user} has started. This might take a moment...', 'type': 'system-msg'}, broadcast=True)
    
    try:
        response = openai.Image.create(
            prompt=prompt,
            n=1,
            size="1024x1024"
        )
        image_url = response['data'][0]['url']
        
        # When the result arrives emit an update event type with the same id
        emit('updateMessage', {'id': msg_id, 'newText': f"<strong>ChatGPT:</strong> Image generated for {user}:<br> <a href='{image_url}' target='_blank'><img src='{image_url}' alt='Generated Image' width='300px' height='300px'/></a>"}, broadcast=True)
        
    except Exception as e:
        print(f'Error calling OpenAI API: {e}')
        errorMsg = f'<strong>System Message:</strong> Sorry, but we encountered an error while processing your request. Details: {str(e)}'
        
        # On exception also send an update to original message
        emit('updateMessage', {'id': msg_id, 'user': 'System Message', 'newText': errorMsg,'type': 'system-msg'}, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', debug=False)
