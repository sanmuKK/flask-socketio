from flask import Flask, render_template, session, request,copy_current_request_context,redirect,\
    flash,url_for,send_from_directory,abort
from flask_socketio import SocketIO, emit, join_room, leave_room,close_room, rooms, disconnect
from flask_redis import FlaskRedis
import random,json,os,uuid
from flask_sqlalchemy import SQLAlchemy
import pymysql
pymysql.install_as_MySQLdb()


def query_room(roomname):
    room = Room.query.filter(Room.id == roomname).first()
    if room:
        return room

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.config["REDIS_URL"] = "redis://127.0.0.1:6379/0"
app.config["SQLALCHEMY_DATABASE_URI"]='mysql://root:yourmysqlpassword@localhost:3306/first_flask?charset=utf8'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"]='False'
db=SQLAlchemy(app)
socketio = SocketIO(app)
rd = FlaskRedis(app)
rd.flushall()


class Room(db.Model):
    __tablename__='room'
    id=db.Column(db.String(128),primary_key=True)
    name=db.Column(db.String(128))
    image=db.Column(db.String(128))
    introduction=db.Column(db.String(256))
    count=db.Column(db.Integer)
    def __repr__(self):
        return '<Room %r>'%self.id

db.drop_all()
db.create_all()

@app.route('/name',methods=['GET','POST'])
def makename():
    room = request.args.get('room')
    if request.method=='POST':
        room = request.args.get('room')
        name = request.form.get('name')
        session['master'] = session.get('master', '')
        session['room'] = session.get('room', '')
        if(name == ''):
            flash('匿名名称不能为空')
            return  redirect(url_for('makename',room=room))
        else:
            session['name'] = name
            session['room']=room
        return redirect(url_for('join_room_url',room=room))
    return render_template('makename.html',room=room)


@app.route('/creatnewroom')
def creatnewroom():
    icon = '/static/56172956.jpeg'
    room=uuid.uuid4().hex
    if not query_room(room):
        session['master'] = room
        ro = Room(id=room, name='暂无', count=0, introduction='无', image=icon)
        db.session.add(ro)
        db.session.commit()
        return redirect(url_for('join_room_url',room=room))
    else:
        return redirect(url_for('creatnewroom'))

@app.route('/')
def join_room_url():
    room = request.args.get('room')
    if not room:
        return "请输入带房间名的url加入房间,如?room=房间号,或通过访问/creatnewroom来创建一个属于你的新房间"
    if not query_room(room):
        abort(404)
    try:
        session['room']
        session['name']
    except:
        return redirect(url_for('makename',room=room))
    else:
        if session['room'] == room:
            name = session['name']
            session['room'] = room
        else:
            return redirect(url_for('makename', room=room))
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
    return render_template('roomchat.html',room=room,name=name,resp=res,master=session['master'],
                           async_mode=socketio.async_mode,r=r)


@app.route('/changeroom',methods=['GET','POST'])
def changeroom():
    room = request.args.get('room')
    r=query_room(room)
    if request.method == 'POST':
        name=request.form.get('room_name')
        introduction=request.form.get('room_introduction')
        file = request.files['file']
        path=r'.\static'
        if file:
            file.save(os.path.join(path,file.filename))
            icon = '/static/'+file.filename
            r.image = icon
        if introduction:
            r.introduction=introduction
        if name:
            r.name=name
        db.session.commit()
        return redirect(url_for('join_room_url',room=room))
    return render_template('changeroom.html')

@socketio.on('join')
def on_join():
    room = session['room']
    join_room(room)
    key = session['room']
    task = {'data' : '欢迎"'+session['name']+'"进入了房间'}
    resp = json.dumps(task)
    rd.rpush(key,resp)
    r=query_room(room)
    r.count+=1
    db.session.commit()
    emit('people_num',r.count,room=room)
    emit('welcome', {'name': session['name']}, room=room)

@socketio.on('leave')
def leave():
    session['name'] = session.get('name', '')
    session['room'] = session.get('room', '')
    session['master'] = session.get('master', '')
    emit('leaveroom', {'name': session['name']}, room=session['room'])
    if(session['master'] == session['room']):
        emit('close_room', {'room': session['room']}, room=session['room'])
        close_room(session['room'])
        rd.delete(session['room'])
        r = query_room(session['room'])
        db.session.delete(r)
        db.session.commit()
        session['room'] = ''
        session['name'] = ''
        session['master'] = ''
    else:
        key = session['room']
        task = {'data': session['name'] + '"离开了房间'}
        resp = json.dumps(task)
        rd.rpush(key, resp)
        r = query_room(session['room'])
        r.count-=1
        emit('people_num', r.count, room=session['room'])
        db.session.commit()
        leave_room(session['room'])
    session['ifleave'] = 'yes'

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
    emit('roomchat',{'data':data['data'],'name':session['name']},room=session['room'])

@socketio.on('changenamee')
def change_name(data):
    session['room'] = session.get('room', '')
    session['name'] = session.get('name', '')
    if session['name'] != data['data']:
        emit('leaveroom', {'name': session['name']}, room=session['room'])
        session['name'] = data['data']
        emit('welcome', {'name': data['data']},room=session['room'])

@socketio.on('close_room')
def close():
    session['room'] = session.get('room','')
    session['master'] = session.get('master', '')
    if session['master'] == session['room']:
        emit('close_room', {'room':session['room']}, room=session['room'])
        close_room(session['room'])
        r=query_room(session['room'])
        db.session.delete(r)
        db.session.commit()
        rd.delete(session['room'])
        session['room'] = ''
        session['name'] = ''
        session['master'] = ''

@socketio.on('disconnect')
def test_disconnect():
    session['ifleave']=session.get('ifleave','no')
    if session['ifleave'] == 'no':
        r=query_room(session['room'])
        if r:
            r.count-=1
            db.session.commit()
            emit('leaveroom', {'name': session['name']}, room=session['room'])
            emit('people_num', r.count,room=session['room'])

if __name__ == '__main__':
    socketio.run(app)
