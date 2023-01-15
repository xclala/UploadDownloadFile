from flask import Flask, render_template, request, session, abort, send_file
from flask.views import MethodView
from flask_wtf.csrf import CSRFProtect
from waitress import serve
from os import path, urandom, scandir, rename
from werkzeug.utils import secure_filename
from uuid import uuid4

app = Flask(__name__)
app.config['SECRET_KEY'] = urandom(666)
CSRFProtect(app)


class Upload(MethodView):

    def __init__(self, password):
        self.password = password

    def get(self):
        return render_template('index.html')

    def post(self):
        pw = self.password
        if session.get("password") is None:
            p = request.form['passwd']
            if p != pw:
                return render_template('index.html', alert_message="密码错误！！！")
            session['password'] = pw
        if session.get("password") == pw:
            for f in request.files.getlist('file'):
                if f.filename == "":
                    return render_template("index.html",
                                           alert_message="请先选择文件！")
                if path.exists("共享的文件/" + secure_filename(f.filename)):
                    f.save("共享的文件/" + uuid4().hex +
                           path.splitext(f.filename)[1])
                else:
                    f.save("共享的文件/" + secure_filename(f.filename))
            return render_template('upload.html', alert_message="文件成功上传！")
        return render_template('index.html', alert_message="密码错误！！！")


class DeleteSession(MethodView):
    def __init__(self, template):
        self.template = template

    def get(self):
        session.clear()
        session.pop("password", None)
        return render_template(self.template, alert_message="成功退出登录！")


class FileList(MethodView):
    def __init__(self, password):
        self.password = password

    def get(self):
        if session.get("password") == self.password:
            filelist = []
            for fl in scandir("共享的文件"):
                if fl.is_file():
                    filelist.append(fl.name)
            return render_template("download.html", filelist=filelist)
        elif session.get("password") is None:
            return render_template("filelist.html", filelist='', alert_message='')
        else:
            return render_template("filelist.html", filelist='', alert_message="密码错误！")

    def post(self):
        if request.form['passwd'] == self.password:
            session['password'] = request.form['passwd']
            filelist = []
            for fl in scandir("共享的文件"):
                if fl.is_file():
                    filelist.append(fl.name)
            return render_template("download.html", filelist=filelist)
        else:
            return render_template("filelist.html", filelist='', alert_message="密码错误！")


class DownloadFile(MethodView):

    def __init__(self, password):
        self.password = password

    def get(self, filename):
        if self.password == session.get('password'):
            filepath = path.join("共享的文件/", filename)
            if path.exists("共享的文件/del_session"):
                filepath = uuid4().hex
                rename("共享的文件/del_session", filepath)
            if path.exists(filepath) and path.isfile(filepath):
                return send_file(filepath)
            abort(404)
        else:
            return render_template("filelist.html", filelist='', alert_message="密码错误！")


def upload(port, thread, pw):
    app.add_url_rule('/', view_func=Upload.as_view("index", pw))
    app.add_url_rule('/del_session',
                     view_func=DeleteSession.as_view("delsession", "index.html"))
    serve(app, port=port, threads=thread)


def download(port, thread, pw):
    app.add_url_rule("/", view_func=FileList.as_view("filelist", pw))
    app.add_url_rule("/filelist/<filename>",
                     view_func=DownloadFile.as_view("downloadfile", pw))
    app.add_url_rule('/del_session',
                    view_func=DeleteSession.as_view("delsession", "filelist.html"))
    serve(app, port=port, threads=thread)


def upload_download(port, thread, pw):
    app.add_url_rule("/filelist", view_func=FileList.as_view("filelist", pw))
    app.add_url_rule("/filelist/<filename>",
                     view_func=DownloadFile.as_view("downloadfile", pw))
    upload(port, thread, pw)
