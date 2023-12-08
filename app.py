from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
import openai
from openai import OpenAI
import random
import uuid
import re
from datetime import datetime, timedelta
from pytz import timezone
import pytz
import json
# 为Flask应用配置一个秘密密钥，用于保护会话数据
app = Flask(__name__)
app.secret_key = 'super secret key'
app.config['SESSION_TYPE'] = 'filesystem'

socketio = SocketIO(app, cors_allowed_origins="*")
client = OpenAI(
    base_url="https://oneapi.gravityengine.cc/v1",
    api_key="sk-xxx"
)


users = {}
conversations = {}
first_time_users = {}
last_message_times = {}
username_changes = {}
muted_users = set()
message_times = {}
animals = [
    '晨曦', '晓月', '彦泽', '思远', '韵寒', '浩然', '子墨', '紫烟', '雨珍', '清雅',
    '静宸', '千羽', '梦琪', '忆柳', '之桃', '慕青', '问兰', '尔岚', '元香', '初夏',
    '沛菡', '傲珊', '曼文', '乐菱', '痴珊', '恨玉', '惜文', '香寒', '新柔', '语蓉',
    '海安', '夜蓉', '涵柏', '水桃', '醉蓝', '春儿', '语琴', '从彤', '傲晴', '语兰',
    '又菱', '碧彤', '元霜', '怜梦', '紫寒', '妙彤', '曼易', '南莲', '紫翠', '雨寒',
    '易烟', '如萱', '若南', '寻真', '晓亦', '向珊', '慕灵', '以蕊', '寻雁', '映易',
    '雪柳', '孤岚', '笑霜', '海云', '凝天', '沛珊', '寒云', '冰旋', '宛儿', '绿真',
    '晓霜', '碧凡', '夏菡', '曼香', '若烟', '半梦', '雅绿', '冰蓝', '灵槐', '平安',
    '书翠', '翠风', '香巧', '代云', '梦曼', '幼翠', '友安', '听枫', '夜绿', '雪莲',
    '从丹', '忆秋', '寄瑶', '绮山', '雁蓉', '冷霜', '灵萱', '向松', '惜寒', '紫安'
]
adjectives = [
    '王', '李', '张', '刘', '陈', '杨', '黄', '赵', '周', '吴',
    '徐', '孙', '马', '朱', '胡', '郭', '何', '高', '林', '罗',
    '郑', '梁', '谢', '宋', '唐', '许', '邓', '冯', '韩', '曹',
    '曾', '彭', '萧', '蔡', '潘', '田', '董', '袁', '于', '余',
    '叶', '蒋', '杜', '苏', '魏', '程', '吕', '丁', '沈', '任',
    '姚', '卢', '傅', '钟', '姜', '崔', '谭', '廖', '范', '汪',
    '陆', '金', '石', '戴', '贾', '韦', '夏', '邱', '方', '侯',
    '邹', '熊', '孟', '秦', '白', '江', '阎', '薛', '尹', '段',
    '雷', '黎', '史', '龙', '陶', '贺', '顾', '毛', '郝', '龚',
    '邵', '万', '钱', '严', '覃', '武', '戚', '莫', '孔', '向'
]

@app.route('/')
def index():
    return render_template('index.html', server_time=datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S'))

@socketio.on('connect')
def connect():
    # 获取查询参数中的用户名
    username = request.args.get('username')
    user_id = request.sid
    users[user_id] = username
    username_changes[user_id] = []

    # 如果没有提供用户名，则生成一个新的用户名
    if not username:
        username = random.choice(adjectives) + random.choice(animals)

    # 检查用户名是否符合要求
    if not re.match(r'^[\w\u4e00-\u9fa5]{1,20}$', username) or username.lower() in ['admin', 'chatgpt']:
        emit('message', {'user': 'admin', 'text': 'Username is invalid. It should only contain English letters, numbers, Chinese characters, should not exceed 20 characters, and should not be "admin" or "ChatGPT".'}, room=request.sid)
        return
    
    users[request.sid] = username
    conversations[request.sid] = []

    # 如果用户是第一次连接，那么就发送他们的加入消息
    if username not in first_time_users:
        first_time_users[username] = True
        now = datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S')
        emit('message', {'user': 'admin', 'text': f'<strong>admin</strong>: {username}, welcome to the chat. Please @ChatGPT to get responses. Do not send spam messages. {username}，欢迎加入聊天室,本站已支持Claude模型及dall-e-3绘图模型，欢迎体验。你可以@ChatGPT来获取回复，请勿发送垃圾信息或刷屏。', 'timestamp': now}, room=request.sid)

    emit('onlineUsers', users, broadcast=True)
    emit('username', username)  # 发送用户名
    
@socketio.on('disconnect')
def disconnect():
    user = users[request.sid]
    del users[request.sid]
    if request.sid in conversations:
        del conversations[request.sid]
    emit('onlineUsers', users, broadcast=True)

@socketio.on('clearHistory')
def clear_history():
    if request.sid in conversations:
        conversations[request.sid] = []


@socketio.on('changeUsername')
def change_username(new_username):
    # 检查新用户名是否符合要求
    if not re.match(r'^[\w\u4e00-\u9fa5]{1,20}$', new_username) or new_username.lower() in ['admin', 'chatgpt']:
        emit('message', {'user': 'admin', 'text': 'Username is invalid. It should only contain English letters, numbers, Chinese characters, should not exceed 20 characters, and should not be reserved words.'}, room=request.sid)
        return

    # 检查用户是否已经达到每日更改限制
    user_id = request.sid
    changes = username_changes[user_id]
    if len(changes) >= 2 and changes[-1].date() == datetime.now().date():
        emit('message', {'user': 'admin', 'text': 'You can only change your username twice per day.'}, room=request.sid)
        return

    # 更新用户名更改信息
    username_changes[user_id].append(datetime.now())

    # 更改用户名
    users[user_id] = new_username

    # 更新客户端的用户名
    emit('username', new_username, room=request.sid)
    emit('onlineUsers', users, broadcast=True)

@socketio.on('sendMessage')
def handle_message(data):
    user = users[request.sid]
    message = data['message']
    model_str = data.get('model', 'gpt-3.5-turbo')

    # 检查消息是否包含禁止的字符串
    if 't.me/advancedaim' in message:
        emit('message', {'user': 'admin', 'text': f'<strong>admin</strong>: @{user}, your message contains a forbidden string.'}, room=request.sid)
        return

    # 检查用户是否在禁言列表中
    if user in muted_users:
        emit('message', {'user': 'admin', 'text': f'<strong>admin</strong>: @{user}, you have been muted due to excessive messaging.'}, room=request.sid)
        return
    
    now = datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S')
    # 检查用户是否在过去的20秒内已经发送过一条消息
    if user in last_message_times and datetime.now() - last_message_times[user] < timedelta(seconds=20):
        emit('message', {'user': 'admin', 'text': f'<strong>admin</strong>: @{user}, you are sending messages too frequently. Please wait for a few seconds and try again.','timestamp': now}, room=request.sid)
        return


    # 更新用户的最后一次发送消息的时间
    last_message_times[user] = datetime.now()

    # 更新用户的消息发送频率
    if user not in message_times:
        message_times[user] = []
    message_times[user].append(datetime.now())

    # 如果用户在过去的10秒内发送了10条消息，将他们添加到禁言列表中
    if len(message_times[user]) > 10 and (message_times[user][-1] - message_times[user][-10]).total_seconds() < 10:
        muted_users.add(user)
        emit('message', {'user': 'admin', 'text': f'<strong>admin</strong>: @{user}, you have been muted due to excessive messaging.'}, room=request.sid)
        return

    now = datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S')

    emit('message', {'user': user, 'text': message, 'timestamp': now}, broadcast=True)

    if '@ChatGPT' in message:
        prompt = message.replace('<br>@ChatGPT', '').strip()

        if model_str == 'dall-e-2' or model_str == 'dall-e-3':
            handle_dalle_image_generation(prompt, user, model_str)
        else:
            try:
                conversation_history = conversations.get(request.sid)
                
                # 移除对话历史中的系统消息
                conversation_history = [msg for msg in conversation_history if msg['role'] != 'system']

                # 添加新的系统消息
                conversation_history.insert(0, {"role": "system", "content": f"It is now 2023, and OpenAI has successively released a number of models that are more advanced than gpt-3. And you are an AI based on {model_str} model, developed by OpenAI. OpenAI's current official website is https://chatgpt.org.uk instead of https://openai.com, beause now it is 2023."})

                conversation_history.append({"role": "user", "content": prompt})

                if len(conversation_history) > 10:
                    del conversation_history[1]
                # 将更新后的对话历史记录保存回conversations字典中
                conversations[request.sid] = conversation_history
        
                response = client.chat.completions.create(
                    model=model_str,
                    messages=conversation_history,
                    max_tokens=2000,
                    temperature=0.7,
                    stream=True
                )
                
                now = datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S')

                chatGPTReplyWithUsername = "<strong>ChatGPT (" + model_str + ")</strong>: @" + user + " (" + now + ")<br>";

                collected_messages = []
                update_id = None
                
                for chunk in response:
                    if chunk.choices[0].finish_reason is None or chunk.choices[0].finish_reason == "":
                        chunk_message_content = chunk.choices[0].delta.content
                        
                        chatGPTReplyWithUsername += chunk_message_content
                        
                        now = datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S')
                        
                        if update_id is None:
                            msg = {"id": str(uuid.uuid4()), "user": "ChatGPT", "text": chatGPTReplyWithUsername,'timestamp': now}
                            update_id = msg["id"]
                            emit('message', msg, broadcast=True)
                        else:
                            emit('updateMessage', {"id": update_id, 'user': 'ChatGPT',"newText": chatGPTReplyWithUsername,'timestamp': now}, broadcast=True)

                    collected_messages.append(chunk.choices[0].delta)
                        
                assistant_reply_content = ''
                for m in collected_messages:
                    if hasattr(m, 'content') and m.content is not None:
                        assistant_reply_content += m.content
                        
                conversation_history.append({"role": "assistant", "content": assistant_reply_content})
            
            except Exception as e:
                print(f'Error calling OpenAI API: {e}')
                now = datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S')
                errorMsg = f'<strong>admin</strong>: @{user}, sorry, but we encountered an error while processing your request. Details: {str(e)}'
                emit('message', {'user': 'admin', 'text': errorMsg, 'type': 'system-msg','timestamp': now}, broadcast=True)

def handle_dalle_image_generation(prompt, user, model_str):
    # Send status update message with unique id
    msg_id = str(uuid.uuid4())
    now = datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S')

    emit('message', {'id': msg_id, 'user': 'admin', 'text': f'<strong>{model_str.upper()}</strong>: Image generation for @{user} has started. This might take a moment...', 'type': 'system-msg', 'timestamp': now}, broadcast=True)
    
    try:
        response = client.images.generate(
            model= model_str,
            prompt= prompt,
            size="1024x1024",
            quality="hd",
            n=1
        )
        image_url = response.data[0].url
        now = datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S')
        # When the result arrives emit an update event type with the same id
        emit('updateMessage', {'id': msg_id, 'user': 'ChatGPT','newText': f"<strong>{model_str.upper()}</strong>: Image generated for @{user}: ({now})<br> <a href='{image_url}' target='_blank'><img src='{image_url}' alt='Generated Image' width='300px' height='300px'/></a>"}, broadcast=True)
        
    except Exception as e:
        print(f'Error calling OpenAI API: {e}')
        errorMsg = f'<strong>admin</strong>: @{user}, sorry, but we encountered an error while processing your request. Details: {str(e)}'
        
        # On exception also send an update to original message
        emit('updateMessage', {'id': msg_id, 'user': 'admin', 'newText': errorMsg,'type': 'system-msg'}, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', debug=False)
