from flask import Flask, render_template, session, request,copy_current_request_context,redirect,\
    flash,url_for,send_from_directory,abort,jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room,close_room, rooms, disconnect
from flask_redis import FlaskRedis
from flask_cors import CORS
import random,json,os,uuid
from flask_sqlalchemy import SQLAlchemy
import pymysql
pymysql.install_as_MySQLdb()

ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])

def query_room(roomname):
    room = Room.query.filter(Room.id == roomname).first()
    if room:
        return room

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.config["REDIS_URL"] = "redis://127.0.0.1:6379/0"
app.config["SQLALCHEMY_DATABASE_URI"]='mysql://root:yourmysqlpassword@localhost:3306/first_flask?charset=utf8'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"]='False'
db=SQLAlchemy(app)
cors=CORS(app,supports_credentials=True)
socketio = SocketIO(app,async_mode='eventlet',cors_allowed_origins="*")
rd = FlaskRedis(app)
rd.flushall()

class Room(db.Model):
    __tablename__='room'
    id=db.Column(db.String(128),primary_key=True)
    name=db.Column(db.String(128))
    image=db.Column(db.String(128))
    introduction=db.Column(db.String(256))
    count=db.Column(db.Integer)
    ip = db.Column(db.String(64))
    browser = db.Column(db.String(256))
    def __repr__(self):
        return '<Room %r>'%self.id

db.drop_all()
db.create_all()

@app.route('/api/name',methods=['POST'])
def makename():
    name = request.form.get('name','')
    session['name'] = name
    file = request.files.get('file')
    session['icon'] = session.get('icon','')
    path = r'./static'
    if not file:
        if session['icon'] == '':
            session['icon'] == '/static/HK3A`%S97J~6Y[X01QAT{YM.jpg'
    elif not allowed_file(file.filename):
        session['icon'] = ''
    else:
        file.save(os.path.join(path, file.filename))
        icon = '/static/' + file.filename
        session['icon'] = icon
    return jsonify({'name': name,'icon':session['icon']})


@app.route('/api/creatnewroom',methods=['POST'])
def creatnewroom():
    room=uuid.uuid4().hex
    if not query_room(room):
        session['room'] = session.get('room',room)
        session[session['room']] = session.get(session['room'],0)
        session[session['room']] = 0
        session['room'] = room
        name = request.form.get('roomname','')
        introduction = request.form.get('roomintroduction','')
        file = request.files.get('file')
        path = r'./static'
        if not file:
            icon = ''
        elif not allowed_file(file.filename):
            icon = ''
        elif file:
            file.save(os.path.join(path, file.filename))
            icon = '/static/' + file.filename
        ip = request.headers.getlist("X-Forwarded-For")[0]
        browser = request.user_agent.browser
        ro = Room(id=room, name=name, count=0, introduction=introduction, image=icon,ip=ip,browser=browser)
        db.session.add(ro)
        db.session.commit()
        return jsonify({'room': room,'roomname': name, 'roomintroduction': introduction, 'icon': icon})
    else:
        return jsonify({'room': '','roomname': '', 'roomintroduction': '', 'icon': ''})

@app.route('/api/home')
def join_room_url():
    room = request.args.get('room')
    if not room:
        return jsonify({'error': 'noroom'})
    if not query_room(room):
        abort(404)
    session['room'] = session.get('room','')
    if room != session['room']:
        session[session['room']] = 0
    session['name']=session.get('name','')
    session['icon']=session.get('icon','')
    session['room'] = room
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
    r=query_room(room)
    ip = request.headers.getlist("X-Forwarded-For")[0]
    browser = request.user_agent.browser
    if ip == r.ip and browser == r.browser:
        session['master'] = room
    else:
        session['master'] = ''
    session[session['room']]=session.get(session['room'],0)
    session[session['room']] += 1
    return jsonify({'count':session[session['room']],'room': room,'roomname':r.name,'roomicon':r.image,'roomintroduction':r.introduction,
                    'name':session['name'],'resp':res,'master':session['master'],'icon':session['icon'],
                    'ip':ip,'browser':browser})


@app.route('/api/changeroom',methods=['POST'])
def changeroom():
    room = request.args.get('room')
    r=query_room(room)
    name=request.form.get('roomname')
    introduction=request.form.get('roomintroduction')
    file = request.files.get('file')
    session['icon'] = session.get("icon",'')
    icon = session['icon']
    path=r'./static'
    if r:
        if not file:
            icon = session['icon']
        elif not allowed_file(file.filename):
            icon = session['icon']
        else:
            file.save(os.path.join(path,file.filename))
            icon = '/static/'+file.filename
            r.image = icon
        if introduction:
            r.introduction=introduction
        if name:
            r.name=name
        db.session.commit()
    return jsonify({'roomname': name,'roomintroduction':introduction,'icon':icon})

@socketio.on('join')
def on_join(data):
    session[data['room']] = session.get(data['room'],0)
    session['name'] = session.get('name','')
    session['room'] = session.get('room', '')
    session['current_room'] = data['room']
    if session['name'] != '' and session[data['room']] != 1:
        room = data['room']
        join_room(room)
        r=query_room(room)
        r.count+=1
        db.session.commit()
        emit('people_num',r.count,room=room)
        emit('welcome', {'name': session['name']}, room=room)
    elif session['name'] != '':
        room = data['room']
        join_room(room)
        r = query_room(room)
        emit('people_num', r.count, room=room)


@socketio.on('my_room_event')
def room_chat(data):
    session['name'] = session.get('name', '')
    key = data['room']
    task = {
        'name' : session['name'],
        'icon' : session['icon'],
        'data' : data['data'],
        'ip' :  request.headers.getlist("X-Forwarded-For")[0],
        'browser' : request.user_agent.browser
    }
    resp = json.dumps(task)
    rd.rpush(key, resp)
    emit('roomchat',{'data':data['data'],'name':session['name'],'icon':session['icon']},room=key)


@socketio.on('close_room')
def close(data):
    room = data['room']
    r=query_room(room)
    ip = request.headers.getlist("X-Forwarded-For")[0]
    browser = request.user_agent.browser
    if ip == r.ip and browser == r.browser:
        emit('close_room', {'room':room}, room=room)
        close_room(room)
        r=query_room(room)
        db.session.delete(r)
        db.session.commit()
        rd.delete(room)

@socketio.on('disconnect')
def test_disconnect():
    if session['name'] != '' and session['room'] == session['current_room']:
        room = session['room']
        r=query_room(room)
        if r:
            r.count-=1
            db.session.commit()
            emit('leaveroom', {'name': session['name']}, room=room)
            emit('people_num', r.count,room=room)

if __name__ == '__main__':
    socketio.run(app,log_output=True,debug=True)