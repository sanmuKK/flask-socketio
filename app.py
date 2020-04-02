from flask import Flask, render_template, session, request,copy_current_request_context,redirect,url_for
from flask_socketio import SocketIO, emit, join_room, leave_room,close_room, rooms, disconnect
import random

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
socketio = SocketIO(app)


@app.route('/',methods=['GET','POST'])
def index():
    if request.method == 'POST':
        room=request.form.get('join_room_url')
        return redirect(url_for('join_room_url',room=room))
    return render_template('home.html',async_mode=socketio.async_mode)


@app.route('/room/<room>')
def join_room_url(room):
    session['room'] = room
    a = random.randint(0, len(adj)-1)
    b = random.randint(0, len(num)-1)
    name = adj[a] + "的" + num[b]
    session['name'] = name
    return render_template('roomchat.html',room=room,name=name)


@socketio.on('join')
def on_join():
    room = session['room']
    join_room(room)
    emit('welcome', {'name': session['name'], 'room': session['room']}, room=session['room'])

@socketio.on('leave')
def on_leave(data):
    pass

@socketio.on('my_room_event')
def room_chat(data):
    emit('roomchat',{'data':data['data'],'name':session['name']},room=session['room'])

@socketio.on('changenamee')
def change_name(data):
    session['name'] = data['data']
    print(session)
    emit('welcome', {'name': data['data'],'room':session['room']},room=session['room'])

@socketio.on('disconnect')
def test_disconnect():
    print('Client disconnected')

if __name__ == '__main__':
    socketio.run(app,debug=True)