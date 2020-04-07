from flask import Flask, render_template, session, request,copy_current_request_context,redirect,url_for
from flask_socketio import SocketIO, emit, join_room, leave_room,close_room, rooms, disconnect
from flask_redis import FlaskRedis
import random,json


def ack():
    print('message was received!')

adj=["浪漫","灵巧","动人","开放","稳健","稳重","外向","热心","坦白","英勇"
    ,"典雅","乐观","勇敢","正直","坚毅","幽默","强干","生动","坦诚","积极"
    ,"调皮","可爱","聪明","果断","务实","精明","仁慈","直率","忠贞","善良"]

num=["大熊猫","白鳍豚","扬子鳄","白唇鹿","藏野驴","黑颈鹤","红腹锦鸡","长江江豚",
     "银杏","水杉","金钱松","珙桐","杨树","柳树","法国梧桐","月季","松树","海棠",
     "黄杨","迎春","连翘","玉兰","酢浆草","三叶草","龙爪槐","国槐","红叶李",
     "银杏","万寿菊","凤蝶","粉蝶","麻雀","蜻蜓","瓢虫","毛毛虫","蚂蚁","蚯蚓","蚊子",
     "蜘蛛","苍蝇","喜鹊","老鼠","壁虎","蚂蚱","蟋蟀","兔子","猫"]


app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.config["REDIS_URL"] = "redis://127.0.0.1:6379/0"
socketio = SocketIO(app)
rd = FlaskRedis(app)
rd.flushall()


@app.route('/')
def join_room_url():
    room = request.args.get('room')
    print(session)
    print('start')
    if not room:
        return "请输入带房间名的url,如?room=房间一号"
    try:
        session['room']
        session['name']
    except:
        a = random.randint(0, len(adj) - 1)
        b = random.randint(0, len(num) - 1)
        name = adj[a] + "的" + num[b]
        session['name'] = name
    else:
        if session['room'] == room:
            name = session['name']
        else:
            a = random.randint(0, len(adj) - 1)
            b = random.randint(0, len(num) - 1)
            name = adj[a] + "的" + num[b]
            session['name'] = name
    session['room'] = room
    session['master'] = session.get('master', '')
    if not rd.exists(room):
        session['master'] = room
    elif room==session['master']:
        pass
    else:
        session['master'] = ''
    key = room
    if rd.llen(key):
        msgs = rd.lrange(key, 0, -1)
        res = {
            "data": [json.loads(v) for v in msgs]
        }
    else:
        res = {
            "data": []
        }
    return render_template('roomchat.html',room=room,name=name,resp=res,master=session['master'],
                           async_mode=socketio.async_mode)


@socketio.on('join')
def on_join():
    room = session['room']
    join_room(room)
    key = session['room']
    task = {'data' : '欢迎"'+session['name']+'"进入了房间:'+session['room']}
    resp = json.dumps(task)
    rd.rpush(key,resp)
    print(room)
    emit('welcome', {'name': session['name'], 'room': room}, room=room)

@socketio.on('leave')
def leave():
    session['name'] = session.get('name', '')
    session['room'] = session.get('room', '')
    session['master'] = session.get('master', '')
    emit('leaveroom', {'name': session['name'], 'room': session['room']}, room=session['room'])
    if(session['master'] == session['room']):
        emit('close_room', {'room': session['room']}, room=session['room'])
        close_room(session['room'])
        rd.delete(session['room'])
    else:
        key = session['room']
        task = {'data': session['name'] + '"离开了房间:' + session['room']}
        resp = json.dumps(task)
        rd.rpush(key, resp)
        leave_room(session['room'])
    session.clear()

@socketio.on('my_room_event')
def room_chat(data):
    session['name'] = session.get('name', '')
    session['room'] = session.get('room','')
    key = session['room']
    task = {
        'name' : session['name'],
        'data' : data['data']
    }
    resp = json.dumps(task)
    rd.rpush(key, resp)
    print(session)
    print('here')
    emit('roomchat',{'data':data['data'],'name':session['name']},room=session['room'])

@socketio.on('changenamee')
def change_name(data):
    session['room'] = session.get('room', '')
    session['name'] = session.get('name', '')
    if session['name'] != data['data']:
        session['name'] = data['data']
        emit('welcome', {'name': data['data'],'room':session['room']},room=session['room'])

@socketio.on('close_room')
def close():
    session['room'] = session.get('room','')
    session['master'] = session.get('master', '')
    if session['master'] == session['room']:
        emit('close_room', {'room':session['room']}, room=session['room'])
        close_room(session['room'])
        rd.delete(session['room'])
        session.clear()

@socketio.on('disconnect')
def test_disconnect():
    print('Client disconnected')

if __name__ == '__main__':
    socketio.run(app,debug=True)