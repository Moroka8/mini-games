# -*- coding: utf-8 -*-
import os
from flask import Flask, render_template,flash, redirect, request, json, session, send_from_directory,url_for
from config import Config
from forms import LoginForm,SignForm,StakeForm, Stake1Form,CaseForm, LoginChangeForm, PasswordChangeForm
from werkzeug.utils import secure_filename
import sqlite3
import random
import time
import math


app=Flask(__name__)
app.config.from_object(Config)
UPLOAD_FOLDER = './static/ico'
ALLOWED_EXTENSIONS = set(['png'])
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    conn = sqlite3.connect("Casino_base.db")
    cursor = conn.cursor()
    if request.method == 'POST':
        file = request.files['file']#берем файлик
        if file and allowed_file(file.filename):
            try:
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))#сохраняем его
                os.rename(os.path.join(app.config['UPLOAD_FOLDER'], filename),os.path.join(app.config['UPLOAD_FOLDER'],'{0}.png'.format(session['user_id'])))#переименовываем его
                filename='{0}.png'.format(session['user_id'])
                upd="UPDATE users SET ico=? WHERE ID=?"#сохранили в бд
                cursor.executemany(upd,[(filename,session['user_id'])])
                conn.commit()
            except FileExistsError:#Если уже меняли иконку
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], '{0}.png'.format(session['user_id'])))#удаляем старую
                os.rename(os.path.join(app.config['UPLOAD_FOLDER'], filename),os.path.join(app.config['UPLOAD_FOLDER'],'{0}.png'.format(session['user_id'])))#переименовываем новоиспеченную
            return redirect(url_for('options'))
    #если загрузили не png
    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form action="" method=post enctype=multipart/form-data>
      <p><input type=file name=file>
         <input type=submit value=Send (only PNG)>
    </form>
    '''    


@app.route('/return_on_index',methods=['GET','POST'])
def return_on_index():#по сути не нужна, ведь я добавил window.reload, но пусть будет
    return redirect('/index')

@app.route('/options',methods=['GET','POST'])
def options():
    conn = sqlite3.connect("Casino_base.db")
    cursor = conn.cursor()
    ask="SELECT ico FROM users WHERE ID=?"
    cursor.execute(ask,[(session['user_id'])])
    ico=cursor.fetchall()[0][0]#адрес иконочки
    home='Home'
    escape='Exit'
    log_form=LoginChangeForm()
    pass_form=PasswordChangeForm()
    wrong_log=0
    success_log=0
    wrong_pass_old=0
    wrong_pass_new=0
    wrong_pass_repeat=0
    success_pass=0
    if log_form.validate_on_submit():
        new_log=str(log_form.login.data)#записываем новый логин
        ask="SELECT login FROM users WHERE login=?"#проверяем наличие такого же логина
        cursor.execute(ask,[(new_log)])
        print(new_log)
        try:
            real_log=cursor.fetchall()[0][0]
            print(real_log)
            if str(real_log)==str(new_log):#если такой есть, то error
                wrong_log+=1
                print("Login is already exist")
        except IndexError:
            print("All Good!")#иначе все классно
            upd="UPDATE users SET login=? WHERE ID=?"
            cursor.executemany(upd,[(new_log,session['user_id'])])
            conn.commit()
            success_log+=1
    elif pass_form.validate_on_submit():
        old_pass=str(pass_form.old_pass.data)
        new_pass=str(pass_form.new_pass.data)
        repeat_pass=str(pass_form.repeat_pass.data)
        ask="SELECT password FROM users WHERE ID=?"#спрашиваем старый пароль
        cursor.execute(ask,[(session['user_id'])])
        real_pass=str(cursor.fetchall()[0][0])
        if old_pass!=real_pass:#если старый пароль не совпадает с веденным
            wrong_pass_old+=1
        elif real_pass==new_pass:#если новый совпадает со старым
            wrong_pass_new+=1
        elif new_pass!=repeat_pass:#если новый не совпадает с повторенным
            wrong_pass_repeat+=1
        else:
            upd="UPDATE users SET password=? WHERE ID=?"
            cursor.executemany(upd,[(new_pass,session['user_id'])])
            conn.commit()
            success_pass+=1
    if wrong_log!=0:
        return render_template('options.html',title="Options",home=home,escape=escape,ico=ico,log_form=log_form,pass_form=pass_form,wrong="Login already exist")
    elif success_log!=0:
        return render_template('options.html',title="Options",home=home,escape=escape,ico=ico,log_form=log_form,pass_form=pass_form,success="Login successfully changed")
    elif wrong_pass_old!=0:
        return render_template('options.html',title="Options",home=home,escape=escape,ico=ico,log_form=log_form,pass_form=pass_form,wrong_pass="Wrong old password")
    elif wrong_pass_new!=0:
        return render_template('options.html',title="Options",home=home,escape=escape,ico=ico,log_form=log_form,pass_form=pass_form,wrong_pass="New password must not match with old password")
    elif wrong_pass_repeat!=0:
        return render_template('options.html',title="Options",home=home,escape=escape,ico=ico,log_form=log_form,pass_form=pass_form,wrong_pass="Wrong in repeat password")
    elif success_pass!=0:
        return render_template('options.html',title="Options",home=home,escape=escape,ico=ico,log_form=log_form,pass_form=pass_form,success_pass="Password successfully changed")
    else:
        return render_template('options.html',title="Options",home=home,escape=escape,ico=ico,log_form=log_form,pass_form=pass_form)

@app.route('/exit', methods=['GET','POST'])
def exit():
    session['user_id']=None
    return redirect('/')

@app.route('/case/<rare>',methods=['GET','POST'])
def case(rare):
    global win_prize,kruger,a,case_rare
    case_rare=rare
    conn = sqlite3.connect("Casino_base.db")
    cursor = conn.cursor()
    ask="SELECT ico FROM users WHERE ID=?"
    cursor.execute(ask,[(session['user_id'])])
    ico=cursor.fetchall()[0][0]
    ask="SELECT coins FROM users WHERE ID=?"#спросил баланс, отобразил
    cursor.execute(ask,[(session['user_id'])])
    balance=cursor.fetchall()[0][0]
    case_name="Open for {0} coins".format(rare)#для тех, кто забыл, на какой кейс зашел
    a=0
    escape='Exit'
    #тут выигрыши, заходите
    if int(rare)==10:
        win_prize=[2,5,6,7,8,9,10,11,12,13,14,15,20,25,30,35,50,60,100,200,500]
    elif int(rare)==25:
        win_prize=[5,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,30,40,45,50,75,80,100,200,500,1000]
    elif int(rare)==50:
        win_prize=[10,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,35,40,50,75,100,200,500,1000,1500]
    elif int(rare)==100:
        win_prize=[25,40,50,60,70,80,90,100,150,200,250,350,500,1000,2000,5000]
    elif int(rare)==250:
        win_prize=[50,75,80,90,100,150,200,250,350,500,1000,2000,5000]
    elif int(rare)==500:
        win_prize=[100,150,160,170,180,190,200,250,350,500,1000,2000,5000,10000]
    return render_template('case.html',case_name=case_name,title='Case',home=home,rare=rare,balance=balance,mb_win=win_prize,escape=escape,ico=ico)


@app.route('/open_case',methods=['GET','POST'])
def open_case():
    global win_prize,a,case_rare
    conn = sqlite3.connect("Casino_base.db")
    cursor = conn.cursor()
    ask="SELECT coins FROM users WHERE ID=?"#спрашиваем баланс
    cursor.execute(ask,[(session['user_id'])])
    balance=cursor.fetchall()[0][0]
    if balance-int(case_rare)<0:#денег нет
        return {'status':'Balance Error'}
    balance=balance-int(case_rare)
    take="UPDATE users SET coins=? WHERE ID=?"
    cursor.executemany(take,[(balance,session['user_id'])])
    conn.commit()
    a=random.choice(win_prize)#рандомим выигрыш
    if a>int(case_rare):
        a=random.choice(win_prize)
        print('respin')
    balance=balance+a#и прибавляем его
    give="UPDATE users SET coins=? WHERE ID=?"
    cursor.executemany(give,[(balance,session['user_id'])])
    conn.commit()
    return {'win_prize':a,'balance':balance}
    

@app.route('/check_time',methods=['GET', 'POST'])
def check_time():#это таймер для халявы
    conn = sqlite3.connect("Casino_base.db")
    cursor = conn.cursor()
    current_time=time.time()
    ask="SELECT time_for_prize FROM users WHERE ID=?"#берем время сбора с бд
    cursor.execute(ask,[(session['user_id'])])
    time_to_take=cursor.fetchall()[0][0]
    time_to_wait=round(time_to_take-current_time)#отнимаем от текущего
    print(time_to_wait)#много-много секунд
    hours=time_to_wait//3600#превращаем в часы и минуты
    minutes=math.floor(time_to_wait%3600/60)
    seconds=time_to_wait%60#еще и остаток покажем
    if hours>-1:
        return {'seconds':seconds, 'minutes':minutes, 'hours':hours}
    
@app.route('/')
def start():#нуждается в объяснении?
    return redirect('/login')

@app.route('/index',methods=['GET', 'POST'])
def index():
    global home
    stake=StakeForm()#это во flip
    stake1=Stake1Form()#это в playroom
    home = 'Home'
    flip_url = 'Flip'
    case_url = 'Case'
    playroom_url = 'Playroom'
    conn = sqlite3.connect("Casino_base.db")
    cursor = conn.cursor()
    ask="SELECT coins FROM users WHERE ID=?"
    cursor.execute(ask,[(session['user_id'])])
    balance=cursor.fetchall()[0][0]
    ask="SELECT COUNT(*) FROM playrooms"
    cursor.execute(ask)
    count=cursor.fetchall()[0][0]
    ask="SELECT * FROM playrooms"
    cursor.execute(ask)
    info=cursor.fetchall()
    ask="SELECT ico FROM users WHERE ID=?"
    cursor.execute(ask,[(session['user_id'])])
    ico=cursor.fetchall()[0][0]
    status=''
    sum_wrong=0
    balance_wrong=0
    escape='Exit'
    session['check_count']=count#эти 2 переменные session нужны для update_playroom
    session['playrooms_info']=info
    user = {'username':session['log']}#что-то я тут немного усложнил с передачей, ну да ладно
    return render_template('index.html', title='Home', user=user, current_id=session['user_id'],home=home,balance=balance,flip=flip_url,case=case_url,playroom=playroom_url,count=count,info=info,stake=stake,escape=escape,ico=ico,stake1=stake1)

@app.route('/action',methods=['GET', 'POST'])
def action():#неудачненькое название, но менять уже поздновато (если что, мы тут берем бонус с халявы)
    conn = sqlite3.connect("Casino_base.db")
    cursor = conn.cursor()
    if request.form['sub']=='Take':
        ask_balance="SELECT coins FROM users WHERE ID=?"#спрашиваем баланс
        cursor.execute(ask_balance,[(session['user_id'])])
        balance=cursor.fetchall()[0][0]
        balance+=100#тот самый бонус
        current_time=time.time()
        time_to_take=current_time+86400#возвращайся через сутки
        upd_balance="UPDATE users SET coins=? WHERE ID=?"#обновляем баланс
        cursor.executemany(upd_balance,[(balance,session['user_id'])])
        conn.commit()
        upd_time_for_prize="UPDATE users SET time_for_prize=? WHERE ID=?"#обновляем время сбора
        cursor.executemany(upd_time_for_prize,[(time_to_take,session['user_id'])])
        conn.commit()
        return redirect('/index')
        
        


@app.route('/login', methods=['GET', 'POST'])
def login():
    global form,log
    conn = sqlite3.connect("Casino_base.db")
    cursor = conn.cursor()#подключение таблиц
    form = LoginForm()
    login='Log In'
    sign_up='Sign Up'
    wrong=0
    if form.validate_on_submit():
        session['log']=form.username.data#Собираем вводимые данные после submit`а
        pas=form.password.data
        try:
            ask_login="SELECT login FROM users WHERE login=? and password=?"#проверка существования вводимых данных
            cursor.execute(ask_login,[(session['log']),(pas)])
            print(cursor.fetchall()[0][0])
        except IndexError:
            wrong+=1 #если не нашел, то error
        if wrong==0:
            ask_id="SELECT ID FROM users WHERE login=? and password=?"#если нашел, то для дальнейшей работы мы в сессии сохраняем id пользователя
            cursor.execute(ask_id,[(session['log']),(pas)])
            session['user_id']=cursor.fetchall()[0][0]
            return redirect('/index')
    if wrong!=0:
        return render_template('login.html', title='Log In', wrong='Username or Password is wrong', form=form,login=login,sign_up=sign_up)
    else:
        return render_template('login.html', title='Log In', form=form,login=login,sign_up=sign_up)

@app.route('/sign_up',methods=['GET','POST'])
def sign_up():
    conn = sqlite3.connect("Casino_base.db")
    cursor = conn.cursor()
    sign = SignForm()
    wrong=0
    login='Log In'
    sign_up='Sign Up'
    if sign.validate_on_submit():
        log=sign.username.data#собираем вводимые данные
        pas=sign.password.data
        ask_login="SELECT login FROM users WHERE login=?"#проверяем наличие логина
        cursor.execute(ask_login,[(log)])
        try:
            real_log=cursor.fetchall()[0][0]#если есть, то error
            if real_log==log:
                wrong+=1
                print("Login is already exist")
        except IndexError:
            print("All Good!")#если нет, то все ок, регаем
            new_account=[(log,pas)]
            cursor.executemany("INSERT INTO users(login,password) VALUES(?,?)",new_account)
            conn.commit()
            return redirect('/login')
    if wrong!=0:
        return render_template('sign_up.html',title="Sign Up", sign=sign,wrong='Login is already exist',login=login,sign_up=sign_up)
    else:
        return render_template('sign_up.html',title="Sign Up", sign=sign,login=login,sign_up=sign_up)

@app.route('/free_prize',methods=['GET','POST'])
def free_prize():
    conn = sqlite3.connect("Casino_base.db")
    cursor = conn.cursor()
    current_time=time.time()
    print(current_time)
    ask="SELECT ico FROM users WHERE ID=?"
    cursor.execute(ask,[(session['user_id'])])
    ico=cursor.fetchall()[0][0]
    ask="SELECT time_for_prize FROM users WHERE ID=?"#проверяем время, когда нужно забрать бонус
    cursor.execute(ask,[(session['user_id'])])
    time_to_take=cursor.fetchall()[0][0]
    but=None #чтобы кнопка не появлялась
    escape='Exit'
    if time_to_take<current_time: #если время, когда забирать, меньше, чем актуальное время
        mes="You can take your prize"# то чел забирает
        but='but'
    else:
        mes="Wait, please"#иначе таймер
        colon=':'
        time.sleep(1)
    if but!=None:
        return render_template('free_prize.html',title="Free Prize",home=home, message=mes,button=but,escape=escape,ico=ico)
    else:
        return render_template('free_prize.html',title="Free Prize",home=home, message=mes,colon=colon,escape=escape,ico=ico)

@app.route('/coin_flip/<bet>',methods=['GET','POST'])
def coin_flip(bet):
    conn = sqlite3.connect("Casino_base.db")
    cursor = conn.cursor()
    ask="SELECT coins FROM users WHERE ID=?"
    cursor.execute(ask,[(session['user_id'])])
    balance=cursor.fetchall()[0][0]#берем баланс
    swap=random.randint(0,1)#рандомим монетку
    sum_wrong=0
    balance_wrong=0
    bet=int(bet)
    if bet<=0:
        sum_wrong+=1#опа обманщик пойман за руку
        status='Stake error'
    if balance<=0:
        balance_wrong+=1#не хватает денег
        status='Balance error'
    if swap==0 and sum_wrong==0 and balance_wrong==0:
        status='Sorry, you lose('#проиграли
        ask="SELECT loses_flip FROM users WHERE ID=?"
        cursor.execute(ask,[(session['user_id'])])
        loses=cursor.fetchall()[0][0]
        loses+=1
        balance=balance-bet
        upd="UPDATE users SET loses_flip=? WHERE ID=?"
        cursor.executemany(upd,[(loses,session['user_id'])])
        conn.commit()
        upd="UPDATE users SET coins=? WHERE ID=?"
        cursor.executemany(upd,[(balance,session['user_id'])])
        conn.commit()
    elif swap==1 and sum_wrong==0 and balance_wrong==0:
        status='Congrutilation! You win!'#выиграли
        ask="SELECT wins_flip FROM users WHERE ID=?"
        cursor.execute(ask,[(session['user_id'])])
        wins=cursor.fetchall()[0][0]
        wins+=1
        balance=balance+bet
        upd="UPDATE users SET wins_flip=? WHERE ID=?"
        cursor.executemany(upd,[(wins,session['user_id'])])
        conn.commit()
        upd="UPDATE users SET coins=? WHERE ID=?"
        cursor.executemany(upd,[(balance,session['user_id'])])
        conn.commit()
    print(status)
    return {'status':status,'balance':balance} 

@app.route('/stake_playroom/<id_playroom>/<sum_of_stake>',methods=['GET','POST'])
def stake_playroom(id_playroom,sum_of_stake):
    session['id_playroom']=id_playroom
    print('Playroom:',session['id_playroom'])
    status=''
    sum_wrong=0
    id_wrong=0
    balance_wrong=0
    conn = sqlite3.connect("Casino_base.db")
    cursor = conn.cursor()
    ask="SELECT coins FROM users WHERE ID=?"#спрашиваем баланс
    cursor.execute(ask,[(session['user_id'])])
    balance=cursor.fetchall()[0][0]
    print(sum_of_stake)
    if session['id_playroom']!="new":
        ask="SELECT * FROM playrooms WHERE id_playroom=?"#если мы не в новой комнате, то спрашиваем инфу по комнате и о том, кто еще тут есть
        cursor.execute(ask,[(session['id_playroom'])])
        info_playroom=cursor.fetchall()
        ask="SELECT id_second FROM playrooms WHERE id_playroom=?"
        cursor.execute(ask,[(session['id_playroom'])])
        id_second=cursor.fetchall()[0][0]
        print(id_second)
        if info_playroom[0][2]==session['user_id'] or info_playroom[0][4]==session['user_id'] or info_playroom[0][6]==session['user_id']:
            id_wrong+=1#от предовращения повторных ставок от юзера
            print(session['user_id'])
    if int(sum_of_stake)<=0:
        sum_wrong+=1#от 0 и отрицательных ставок
    if balance<=0:
        balance_wrong+=1#деняк нет
    if sum_wrong!=0:
        return {'status':'Stake Error'}
    elif balance_wrong!=0:
        return {'status':'Balance Error'}
    elif id_wrong!=0:
        return {'status':'You have already placed a bet'}
    if id_playroom=="new":#если комната новая, то добавим ее в бд
        take="INSERT INTO playrooms(first_stake,id_first) VALUES(?,?)"
        cursor.executemany(take,[(sum_of_stake,session['user_id'])])
        conn.commit()
    elif id_second==None:#если мы все-таки не в новой, проверяем второго пользователя, может там свободно
        print("Stap 1")
        take="UPDATE playrooms SET id_second=? WHERE id_playroom=?"
        cursor.executemany(take,[(session['user_id'],session['id_playroom'])])
        conn.commit()
        take="UPDATE playrooms SET second_stake=? WHERE id_playroom=?"
        cursor.executemany(take,[(sum_of_stake,session['id_playroom'])])
        conn.commit()
    elif id_second!=None:#а если не свободно, то в прыгаем в третьего пользователя
        print("Stap 2")
        take="UPDATE playrooms SET id_third=? WHERE id_playroom=?"
        cursor.executemany(take,[(session['user_id'],session['id_playroom'])])
        conn.commit()
        take="UPDATE playrooms SET third_stake=? WHERE id_playroom=?"
        cursor.executemany(take,[(sum_of_stake,session['id_playroom'])])
        conn.commit()
    balance=balance-int(sum_of_stake)
    take_balance="UPDATE users SET coins=? WHERE ID=?"
    cursor.executemany(take_balance,[(balance,session['user_id'])])
    conn.commit()
    print('stake complete')
    return redirect('/return_on_index')
    
@app.route('/update_playroom',methods=['GET','POST'])
def update_playroom():
    conn = sqlite3.connect("Casino_base.db")
    cursor = conn.cursor()
    ask="SELECT * FROM playrooms"#инфа про комнаты
    cursor.execute(ask)
    info=cursor.fetchall()
    ask="SELECT COUNT(*) FROM playrooms"#кол-во комнат
    cursor.execute(ask)
    count=cursor.fetchall()[0][0]
    print(session['user_id'],session['check_count'],count)
    if session['check_count']!=count:#если отличается от того кол-ва, которое мы получаем при заходе на страницу, то обновляем
        old_count=session['check_count']
        session['check_count']=count
        ask="SELECT * FROM playrooms"
        cursor.execute(ask)
        info=cursor.fetchall()
        print(info)
        return {'new_table':info,'new_count':count}
    if session['playrooms_info']!=info:#если инфа отличается
        old_info=session['playrooms_info']
        session['playrooms_info']=info
        return {'new_table':info,'new_count':count}
    winner_stage=0
    try:
        ask="SELECT id_third FROM playrooms WHERE id_playroom=?"
        cursor.execute(ask,[(session['id_playroom'])])
        id_third=cursor.fetchall()[0][0]#спрашиваем, есть ли 3 игрок в комнате
        print('id',id_third)
        if id_third!=None: #если есть, то собираем id игроков и ставки
            ask="SELECT id_first FROM playrooms WHERE id_playroom=?"
            cursor.execute(ask,[(session['id_playroom'])])
            id_first=cursor.fetchall()[0][0]
            ask="SELECT id_second FROM playrooms WHERE id_playroom=?"
            cursor.execute(ask,[(session['id_playroom'])])
            id_second=cursor.fetchall()[0][0]
            ask="SELECT winner FROM playrooms WHERE id_playroom=?"
            cursor.execute(ask,[(session['id_playroom'])])
            winner_playroom=cursor.fetchall()[0][0]
            ask="SELECT first_stake FROM playrooms WHERE id_playroom=?"
            cursor.execute(ask,[(session['id_playroom'])])
            first_stake=cursor.fetchall()[0][0]
            ask="SELECT second_stake FROM playrooms WHERE id_playroom=?"
            cursor.execute(ask,[(session['id_playroom'])])
            second_stake=cursor.fetchall()[0][0]
            ask="SELECT third_stake FROM playrooms WHERE id_playroom=?"
            cursor.execute(ask,[(session['id_playroom'])])
            third_stake=cursor.fetchall()[0][0]
            if winner_playroom==None:#если еще нет победителя
                players=[]#то его надо выбрать. добавляем всех в списочек, исходя из их ставки
                for i in range(0,first_stake):
                    players.append(id_first)
                for i in range(0,second_stake):
                    players.append(id_second)
                for i in range(0,third_stake):
                    players.append(id_third)
                print(players)
                winner_playroom=random.choice(players)#выбираем
                give="UPDATE playrooms SET winner=? WHERE id_playroom=?"
                cursor.executemany(give,[(winner_playroom,session['id_playroom'])])
                conn.commit()
                ask="SELECT coins FROM users WHERE ID=?"
                cursor.execute(ask,[(winner_playroom)])
                balance=cursor.fetchall()[0][0]
                balance=balance+first_stake+second_stake+third_stake#победителю денег
                give="UPDATE users SET coins=? WHERE ID=?"
                cursor.executemany(give,[(balance,winner_playroom)])
                conn.commit()
                print('balance update for',winner_playroom)
                winner_stage=1
            ask="SELECT first_update FROM playrooms WHERE id_playroom=?"#3 апдейта должны гарантировано отобразить всем игрокам победителя (вроде)
            cursor.execute(ask,[(session['id_playroom'])])
            first_update=cursor.fetchall()[0][0]
            ask="SELECT second_update FROM playrooms WHERE id_playroom=?"
            cursor.execute(ask,[(session['id_playroom'])])
            second_update=cursor.fetchall()[0][0]
            ask="SELECT third_update FROM playrooms WHERE id_playroom=?"
            cursor.execute(ask,[(session['id_playroom'])])
            third_update=cursor.fetchall()[0][0]
            if first_update==0 and winner_stage==1:
                upd="UPDATE playrooms SET first_update=? WHERE id_playroom=?"
                cursor.executemany(upd,[(1,session['id_playroom'])])
                conn.commit()
            elif first_update!=0 and second_update==0:
                upd="UPDATE playrooms SET second_update=? WHERE id_playroom=?"
                cursor.executemany(upd,[(1,session['id_playroom'])])
                conn.commit()
            elif first_update!=0 and second_update!=0 and third_update==0:
                upd="UPDATE playrooms SET third_update=? WHERE id_playroom=?"
                cursor.executemany(upd,[(1,session['id_playroom'])])
                conn.commit()
            else:#после апдейтов комната удаляется
                delete="DELETE FROM playrooms WHERE id_playroom=?"
                cursor.execute(delete,[(session['id_playroom'])])
                conn.commit()
                print('playroom deleted')
            print('first_update:',first_update)
            print('second_update:',second_update)
            print('third_update:',third_update)
            return {'info':info}
    except IndexError:#3 игрока нет, дальше обновляем комнату
        return {'info':info}
    

if __name__ == '__main__':
    app.run()
