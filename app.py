from flask import Flask, render_template, json, request,redirect,session, Response,url_for
from flaskext.mysql import MySQL
import sys
import ctypes
import _ctypes
import os
from werkzeug.utils import secure_filename

mysql = MySQL()
application = app = Flask(__name__)
UPLOAD_FOLDER = 'c:/sitekurs/'
ALLOWED_EXTENSIONS = set(['txt', 'c'])
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = 'why would I tell you my secret key?'
# MySQL configurations
app.config['MYSQL_DATABASE_USER'] = 'userDB'
app.config['MYSQL_DATABASE_PASSWORD'] = '020896lumen'
app.config['MYSQL_DATABASE_DB'] = 'bucketlist'
app.config['MYSQL_DATABASE_HOST'] = 'aa6bkyeme6tejq.c1amhyf5jdyt.us-east-2.rds.amazonaws.com'
mysql.init_app(app)

@app.route('/')
def main():
    return render_template('index.html')

@app.route('/tryTask', methods=['POST'])
def trytask():
    value = request.form.get('taskanswer')
    if value == '':
        return render_template('error.html',error = 'Ошибка! \n Вы не ввели решение!')
    try:
        conn = mysql.connect()
        cursor = conn.cursor()
        #os.chdir('C:\\sitekurs\\tasks')
        contents=session.get('shablon')
        contents=value+contents
        contents=contents.split('\r\n')
        f = open('taskinwork.c', "a")
        for line in contents:
            f.writelines(line + '\n')
        f.close()
        os.system('gcc -c -fPIC taskinwork.c')
        os.system('gcc -shared -o taskinwork.so taskinwork.o')
        libc = ctypes.CDLL("/home/ubuntu/sitekurs1/taskinwork.so")
        #libc = ctypes.CDLL("c:\\sitekurs\\tasks\\taskinwork.dll")
        x=libc.main()
        
        if x==0:
            libHandle = libc._handle
            ctypes.cdll.LoadLibrary("libdl.so").dlclose(libHandle)
            #os.system('del taskinwork.dll taskinwork.o libstdll.a taskinwork.c')
            os.system('rm -f taskinwork.so taskinwork.o  taskinwork.c')
            cursor = conn.cursor()
            cursor.callproc('bucketlist.sp_createDecision',(session.get('user'),request.form['updateId'], value, '1'))
            data = cursor.fetchall()
            if len(data) is 0:
                conn.commit()
            return render_template('success.html', answer = 'Все тесты пройдены! \n Задача решена!')
            
        elif x!=0:
            libHandle = libc._handle
            ctypes.cdll.LoadLibrary("libdl.so").dlclose(libHandle)
            #os.system('del taskinwork.dll taskinwork.o libstdll.a taskinwork.c')
            os.system('rm -f taskinwork.so taskinwork.o  taskinwork.c')
            cursor.execute("SELECT tbl_errors.error_text FROM tbl_errors where tbl_errors.error_number = %s", x )
            errors = cursor.fetchall()
            cursor = conn.cursor()
            cursor.callproc('bucketlist.sp_createDecision',(session.get('user'),request.form['updateId'], value, '0'))
            data = cursor.fetchall()
            if len(data) is 0:
                conn.commit()
            return render_template('success.html', answer = errors[0][0])
    except Exception as e:
        cursor = conn.cursor()
        cursor.callproc('bucketlist.sp_createDecision',(session.get('user'),request.form['updateId'], value, '0'))
        data = cursor.fetchall()
        if len(data) is 0:
            conn.commit()
        os.system('rm -f taskinwork.dll taskinwork.o libstdll.a taskinwork.c')
        #os.system('del taskinwork.dll taskinwork.o libstdll.a taskinwork.c')
        return render_template('error.html',error = 'Ошибка при компиляции программы. Программа не смогла запуститься.')
    	

@app.route('/showAddTask')
def showAddTask():
    return render_template('addtask.html')
	
@app.route('/addError')
def addError():
    return render_template('adderror.html')
	
@app.route('/userHome')
def userHome():
    if session.get('flag_user'):
        return redirect(url_for('userPage', id=session.get('flag_user')))
    if (session.get('user') and session.get('admin') == '1'):
        return redirect('/userHomeAdmin')
    elif session.get('user'):
        getUserById(session.get('user'))
        user = session.get('userallinfo')
        return render_template('userhome.html', user=user[0])
    else:
        return render_template('error.html',error = 'Ошибка, пользователь не найден!')

@app.route('/UserPage/<id>')
def userPage(id):
    if session.get('admin') == '1':
        session.pop('flag_user',None)
        session['flag_user'] = id
        getUserById(id)
        user = session.get('userallinfo')
        return render_template('userstasksadmincheck.html', user=user[0])
    else:
        return render_template('error.html',error = 'Ошибка, пользователь не найден!')

@app.route('/userHomeAdmin')
def userHomeAdmin():
    if (session.get('user') and session.get('admin') == '1'):
        session.pop('flag_user',None)
        return render_template('userhomeadmin.html')
    else:
        return render_template('error.html',error = 'Ошибка, пользователь не найден!')

@app.route('/taskErrors')
def taskErrors():
    if (session.get('user') and session.get('admin') == '1'):
        return render_template('taskerrors.html')
    else:
        return render_template('error.html',error = 'Ошибка, пользователь не найден!')
		
@app.route('/logout')
def logout():
    session.pop('user',None)
    session.pop('admin',None)
    session.pop('flag_user',None)
    return redirect('/signIn')

@app.route('/getTaskById')
def getTaskById():
    try:
        if session.get('user'):
            _id = session.get('idvar')
            if session.get('admin')=='1' and session.get('flag_user') != None:  
                _user_we_need = session.get('flag_user')
            else:
                _user_we_need = session.get('user')
            conn = mysql.connect()
            cursor = conn.cursor()
            cursor.callproc('sp_GetTaskById',(_id,_user_we_need))
            result = cursor.fetchall()
            task1 = []
            task1.append({'Id':result[0][0],'Title':result[0][1],'Description':result[0][2].replace('\n', '\\n').replace('\r', '\\r')})
            session['task_decision']=result[0][6].replace('\n', ' \n ').replace('\r', '').replace('\t', '')
            session['task'] = task1
            session['shablon'] = result[0][5]
            return
        else:
            return render_template('error.html', error = 'Ошибка, пользователь не найден!')
    except Exception as e:
        return render_template('error.html',error = str(e))

@app.route('/getUserById')
def getUserById(id):
    try:
        if session.get('user'):
            conn = mysql.connect()
            cursor = conn.cursor()
            cursor.callproc('sp_GetUserById',(id,))
            result = cursor.fetchall()
            user = []
            user.append({'Id':result[0][0],'Name':result[0][1],'SecName':result[0][2],'Group':result[0][3],'Email':result[0][4],'Password':result[0][5],'Admin':result[0][6]})
            session['userallinfo'] = user
            return json.dumps(user)
        else:
            return render_template('error.html', error = 'Ошибка, пользователь не найден!')
    except Exception as e:
        return render_template('error.html',error = str(e))
   	
		
@app.route('/editTask/<id>')
def editTask(id):
    session['idvar'] = id
    if (session.get('user') and session.get('admin')=='1'):
        getTaskById()
        user = session.get('task')
        return render_template('edittask.html', user=user[0])
    else:
        return render_template('error.html',error = 'Ошибка, пользователь не найден!')


@app.route('/editUser/<id>')
def edituser(id):
    session['idvar'] = id
    if (session.get('user') and session.get('admin') =='1'):
        getUserById(id)
        user = session.get('userallinfo')
        return render_template('edituser.html', user=user[0])
    else:
        return render_template('error.html',error = 'Ошибка, пользователь не найден!')
		
		
@app.route('/editError/<id>')
def editError(id):
    session['idvar'] = id
    if (session.get('user') and session.get('admin') =='1'):
        try:
            _id = session.get('idvar')
            conn = mysql.connect()
            cursor = conn.cursor()
            cursor.callproc('sp_GetErrorById',(_id,))
            result = cursor.fetchall()
            user = []
            user.append({'Id':result[0][0],'Number':result[0][1],'Text':result[0][2].replace('\n', '\\n')})
            return render_template('editerror.html', user=user[0])
        except Exception as e:
            return render_template('error.html',error = str(e))	
    else:
        return render_template('error.html',error = 'Ошибка, пользователь не найден!')

@app.route('/usersadmin')
def usersadmin():
    if (session.get('user') and session.get('admin') == '1'):
        session.pop('flag_user',None)
        return render_template('usersadmin.html')
    else:
        return render_template('error.html',error = 'Ошибка, пользователь не найден!')


@app.route('/tasks/<id>')
def tasksId(id):
    session['idvar'] = id
    if session.get('user'):
        session.pop('task_decision',None)
        getTaskById()
        user = session.get('task')
        user_decision =[]
        user_decision.append(session.get('task_decision'))
        return render_template("tasks.html",user=user[0], user_decision=user_decision[0])
    else:
        return render_template('error.html',error = 'Ошибка, пользователь не найден!')
		
@app.route('/getTask')
def getTask():
    try:
        if session.get('user'):
            _user = session.get('user')
            con = mysql.connect()
            cursor = con.cursor()
            tasks_dict = []
            if session.get('flag_user') != None:
                cursor.callproc('sp_GetTaskByUser', (session.get('flag_user'),))
                tasks = cursor.fetchall()
                for task in tasks:
                    task_dict = {
                            'Id': task[0],
                            'Title': task[1],
                            'Description': task[2],
                            'Decision': task[10]}
                    tasks_dict.append(task_dict)
            elif session.get('admin')=='1':
                cursor.callproc('sp_GetAllTasks')
                tasks = cursor.fetchall()
                for task in tasks:
                    task_dict = {
                            'Id': task[0],
                            'Title': task[1],
                            'Description': task[2],
                            'Decision': task[5]}
                    tasks_dict.append(task_dict)
            else:
                cursor.callproc('sp_GetTaskByUser', (_user,))
                tasks = cursor.fetchall()
                for task in tasks:
                    task_dict = {
                            'Id': task[0],
                            'Title': task[1],
                            'Description': task[2],
                            'Decision': task[10]}
                    tasks_dict.append(task_dict)
            return json.dumps(tasks_dict)
        else:
            return render_template('error.html', error = 'Ошибка, пользователь не найден!')
    except Exception as e:
        return render_template('error.html', error = str(e))
		
@app.route('/getUsers')
def getUsers():
    try:
        if session.get('user'):
            _user = session.get('user')
            con = mysql.connect()
            cursor = con.cursor()
            cursor.callproc('sp_GetUsersByUser')
            users = cursor.fetchall()
            users_dict = []
            for user in users:
                user_dict = {
                        'Id': user[0],
                        'Name': user[1],
                        'SecName':user[2],
                        'Group':user[3],
                        'Email': user[4],
                        'Password': user[5],
                        'Admin': user[6]}
                users_dict.append(user_dict)
            return json.dumps(users_dict)
        else:
            return render_template('error.html', error = 'Ошибка, пользователь не найден!')
    except Exception as e:
        return render_template('error.html', error = str(e))

@app.route('/getErrors')
def getErrors():
    try:
        if session.get('admin') == '1':
            _user = session.get('user')
            con = mysql.connect()
            cursor = con.cursor()
            cursor.callproc('sp_GetErrors')
            errors = cursor.fetchall()
            errors_dict = []
            for error in errors:
                error_dict = {
                        'Id': error[1],
                        'Text': error[2]}
                errors_dict.append(error_dict)
            return json.dumps(errors_dict)
        else:
            return render_template('error.html', error = 'Ошибка, пользователь не найден!')
    except Exception as e:
        return render_template('error.html', error = str(e))

@app.route('/signUp',methods=['GET','POST'])
def signUp():
    if request.method == 'GET':
        conn = mysql.connect()
        cursor = conn.cursor()
        cursor.callproc('sp_GetGroupNumbers')
        data = cursor.fetchall()
        datanormalview=[]
        for i in data:
            datanormalview.append(i)
        return render_template('signup.html', user=datanormalview)
    else:
        try:
            _name = request.form['inputName']
            _secname=request.form['input2Name']
            _group=request.form['inputGroup']
            _email = request.form['inputEmail']
            _password = request.form['inputPassword']
            conn = mysql.connect()
            cursor = conn.cursor()
            cursor.callproc('sp_createUser',(_name,_secname, _group,_email,_password))
            data = cursor.fetchall()
            if len(data) is 0:
                conn.commit()
                return redirect('/signIn')
            else:
                return render_template('taskerrors.html')
        except Exception as e:
            return json.dumps({'error':str(e)})
            
@app.route('/addTask',methods=['POST'])
def addTask():
    try:
        if session.get('user'):

            _title = request.form['inputTitle']
            _description = request.form['inputDescription']
            _user = session.get('user')
            try:
                file = request.files['file']
                file.save(secure_filename(file.filename))
                f = open(file.filename, 'r')
                _data = f.read()
                f.close()
            except:
                file = None
                return render_template('error.html',error = 'Тест-кейсы не были загружены!')
            conn = mysql.connect()
            cursor = conn.cursor()
            cursor.callproc('sp_addTask',(_title,_description,_user, _data))
            data = cursor.fetchall()
            cmd = "rm -f " + file.filename
            os.system(cmd)
            if len(data) is 0:
                conn.commit()
                return redirect('/userHomeAdmin')
            else:
                return render_template('error.html',error = 'An error occurred!')

        else:
            return render_template('error.html',error = 'Ошибка, пользователь не найден!')
    except Exception as e:
        return render_template('error.html',error = str(e))
    finally:
        cursor.close()
        conn.close()

@app.route('/addNewError',methods=['POST'])
def addNewError():
    _number = request.form['inputTitle']
    try:
        int(_number)
    except ValueError:
        return render_template('error.html',error = 'Код ошибки должен быть числом!')
    try:
        if session.get('user'):
            
            _text = request.form['inputDescription']
            conn = mysql.connect()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tbl_errors where tbl_errors.error_number = %s", _number)
            data = cursor.fetchone()
            if data is not None:
                return render_template('error.html',error = 'Ошибка с таким кодом уже существует!')
            cursor.callproc('sp_addError',(_number,_text, session.get('user')))
            data = cursor.fetchall()
            if len(data) is 0:
                conn.commit()
                return redirect('/taskErrors')
            else:
                return render_template('error.html',error = 'An error occurred!')

        else:
            return render_template('error.html',error = 'Ошибка, пользователь не найден!')
    except Exception as e:
        return render_template('error.html',error = str(e))
    finally:
        cursor.close()
        conn.close()
	
@app.route('/updateTask', methods=['POST'])
def updateTask():
    try:
        if session.get('user'):
            _title = request.form['updateTitle']
            _description = request.form['updateDescription']
            _task_id = request.form['updateId']
            try:
                file = request.files['file']
                file.save(secure_filename(file.filename))
                f = open(file.filename, 'r')
                _data = f.read()
                f.close()
            except:
                file = None
            conn = mysql.connect()
            cursor = conn.cursor()
            _description=_description.replace('\r', "")
            if file == None:
                cursor.callproc('sp_updateTask',(_title,_description,_task_id))
            else:
                cursor.execute('update tbl_tasks set task_title = %s,task_description = %s, task_var = %s where task_id = %s', (_title, _description, _data, _task_id))
                cmd = "rm -f " + file.filename
                os.system(cmd)
            data = cursor.fetchall()
            if len(data) is 0:
                conn.commit()
                return redirect('/userHomeAdmin')
            else:
                return json.dumps({'status':'ERROR'})
    except Exception as e:
        return json.dumps({'status':'Ошибка, пользователь не найден!'})
    finally:
        cursor.close()
        conn.close()

@app.route('/updateUser', methods=['POST'])
def updateUser():
    try:
        if session.get('user'):
            _name = request.form['updateName']
            _email = request.form['updateEmail']
            _password = request.form['updatePassword']
            _id = request.form['JustId']
            if request.form.get('updateAdmin') is None:
                _admin = 0
            else:
                _admin = 1
            conn = mysql.connect()
            cursor = conn.cursor()
            cursor.callproc('sp_updateUser',(_name,_email,_password,_id,_admin))
            data = cursor.fetchall()
            if len(data) is 0:
                conn.commit()
                return redirect('/usersadmin')
            else:
                return json.dumps({'status':'ERROR'})
    except Exception as e:
        print(e, file=sys.stderr)
        return json.dumps({'status':'Ошибка, пользователь не найден!'})
    finally:
        cursor.close()
        conn.close()

@app.route('/updateErrors', methods=['POST'])
def updateErrors():
    try:
        if session.get('user'):
            _number = request.form['updateTitle']
            _text = request.form['updateDescription']
            _id = request.form['updateId']
            conn = mysql.connect()
            cursor = conn.cursor()
            _text=_text.replace('\r', "")
            cursor.callproc('sp_updateError',(_number,_text,_id))
            data = cursor.fetchall()
            if len(data) is 0:
                conn.commit()
                return redirect('/taskErrors')
            else:
                return json.dumps({'status':'ERROR'})
    except Exception as e:
        return json.dumps({'status':'Ошибка, пользователь не найден!'})
    finally:
        cursor.close()
        conn.close()

@app.route('/signIn',methods=['GET', 'POST'])
def signIn():
    if request.method == 'GET':
        if (session.get('user') and session.get('admin')=='1'):
            return redirect('/userHomeAdmin')
        elif session.get('user'):
            return redirect('/userHome')
        else:
            return render_template('signin.html')
    else:
        try:
            _username = request.form['inputEmail']
            _passwordIn = request.form['inputPassword']

            con = mysql.connect()
            cursor = con.cursor()
            cursor.callproc('bucketlist.sp_validateLogin',(_username, ))
            data = cursor.fetchall()
            session['userdata']=data
            if len(data) > 0:
                if (data[0][5] == _passwordIn):
                    session['user'] = data[0][0]
                    if data[0][6]=='1':
                        session['admin'] = data[0][6]
                    return redirect('/userHome')
                else:
                    return render_template('error.html',error = 'Неверный email или пароль!')
            else:
                return render_template('error.html',error = 'Неверный email или пароль!')
        except Exception as e:
            return json.dumps({'error':str(e)})
        finally:
            cursor.close()
            con.close()
		
@app.route('/deleteTask',methods=['POST'])
def deleteTask():
    try:
        if session.get('user'):
            _id = request.form['id']
            conn = mysql.connect()
            cursor = conn.cursor()
            cursor.callproc('sp_deleteTask',(_id,))
            result = cursor.fetchall()
            if len(result) is 0:
                conn.commit()
                return json.dumps({'status':'OK'})
            else:
                return json.dumps({'status':'An Error occured'})
        else:
            return render_template('error.html',error = 'Ошибка, пользователь не найден!')
    except Exception as e:
        return json.dumps({'status':str(e)})
    finally:
        cursor.close()
        conn.close()
		
@app.route('/deleteUser',methods=['POST'])
def deleteUser():
    try:
        if session.get('user'):
            _id = request.form['id']
            conn = mysql.connect()
            cursor = conn.cursor()
            cursor.callproc('sp_deleteUser',(_id,))
            result = cursor.fetchall()
            if len(result) is 0:
                conn.commit()
                return json.dumps({'status':'OK'})
            else:
                return json.dumps({'status':'An Error occured'})
        else:
            return render_template('error.html',error = 'Ошибка, пользователь не найден!')
    except Exception as e:
        return json.dumps({'status':str(e)})
    finally:
        cursor.close()
        conn.close()
		
@app.route('/deleteError',methods=['POST'])
def deleteError():
    try:
        if session.get('user'):
            _id = request.form['id']
            conn = mysql.connect()
            cursor = conn.cursor()
            cursor.callproc('sp_deleteError',(_id,))
            result = cursor.fetchall()
            if len(result) is 0:
                conn.commit()
                return json.dumps({'status':'OK'})
            else:
                return json.dumps({'status':'An Error occured'})
        else:
            return render_template('error.html',error = 'Ошибка, пользователь не найден!')
    except Exception as e:
        return json.dumps({'status':str(e)})
    finally:
        cursor.close()
        conn.close()
if __name__ == "__main__":
    app.run(debug = True)
