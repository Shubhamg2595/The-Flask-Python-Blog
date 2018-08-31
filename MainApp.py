from flask import Flask,render_template,request,session,redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_mail import Mail
from werkzeug import secure_filename
import json,os,math


local_server=True
with open('config.json' , 'r') as c:
    params=json.load(c)["params"]

app=Flask(__name__)
app.secret_key="my-secret-key"
app.config['UPLOAD_FOLDER']=params['upload_location']
#configuring mail settings
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT='465',
    MAIL_USE_SSL=True,
    MAIL_USERNAME=params['gmail-user'],
    MAIL_PASSWORD=params['gmail-pwd']

)

mail=Mail(app)



# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:@localhost/pythonblog'
# replacing above line using my config file
if(local_server):
    app.config['SQLALCHEMY_DATABASE_URI']=params['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_uri']
db = SQLAlchemy(app)

class Contacts(db.Model):
    '''sno,name,email,phone_num,msg,date'''
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone_num = db.Column(db.String(12), nullable=False)
    msg = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12), nullable=True)

#creating Class for post template
class Posts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    sub_heading = db.Column(db.String(80), nullable=False)
    slug = db.Column(db.String(120), nullable=False)
    content = db.Column(db.String(12), nullable=False)
    img_file = db.Column(db.String(80), nullable=False)
    date = db.Column(db.String(12), nullable=True)


#this route if for my homepage
@app.route('/')
def index():
    #making sure only 2posts are shown at a time,using slicing operaton
    posts=Posts.query.filter_by().all()
    last=math.floor(len(posts)/int(params['no_of_posts']))
    page=request.args.get('page')
    if(not str(page).isnumeric()):
        page=1
    page=int(page)
    posts=posts[(page-1)*int(params['no_of_posts']):(page-1)*int(params['no_of_posts'])+int(params['no_of_posts'])]
    if page==1:
        prev="#"
        next="/?page="+str(page+1)
    elif page==last:
        prev="/?page="+str(page-1)
        next ="#"
    else:
        prev="/?page="+str(page - 1)
        next="/?page="+str(page + 1)
    #[0:params['no_of_posts']]

    return render_template('index.html',params=params,posts=posts,prev=prev,next=next)

#creating route for login page
@app.route('/loginDashboard',methods=['GET','POST'])
def loginDashboard():
    if 'user' in session and session['user']==params['admin_user']:
        posts = Posts.query.filter_by().all()
        return render_template('dashboard.html',params=params,posts=posts)
    if request.method=='POST':
        username=request.form.get('username')
        password=request.form.get('password')
        if (username==params['admin_user'] and password==params['admin_password']):
            session['user']=username
            posts=Posts.query.filter_by().all()
            return render_template('dashboard.html',params=params,posts=posts)

    return render_template('login.html',params=params)


@app.route("/add/<string:sno>",methods=['GET','POST'])
def addpost(sno):
    if('user' in session and session['user']==params['admin_user']):
        if (request.method =='POST'):
            requesting_newtitle = request.form.get('title')
            requesting_newsubheading = request.form.get('sub_heading')
            requesting_newslug = request.form.get('slug')
            requesting_newcontent = request.form.get('content')
            requesting_newimgfile = request.form.get('img_file')
            setting_date = datetime.now()
            post=Posts(title=requesting_newtitle,sub_heading=requesting_newsubheading,slug=requesting_newslug,content=requesting_newcontent,img_file=requesting_newimgfile,date=setting_date)
            db.session.add(post)
            db.session.commit()

    return render_template('addpost.html',sno=sno)

#creating a route for edit and delete buttons in dashboard.html
@app.route("/edit/<string:sno>",methods=['GET','POST'])
def edit(sno):
    if('user' in session and session['user']==params['admin_user']):
        if (request.method =='POST'):
            requesting_newtitle = request.form.get('title')
            requesting_newsubheading = request.form.get('sub_heading')
            requesting_newslug = request.form.get('slug')
            requesting_newcontent = request.form.get('content')
            requesting_newimgfile = request.form.get('img_file')
            setting_date = datetime.now()
            if sno!=0:
                post=Posts.query.filter_by(sno=sno).first()
                post.title=requesting_newtitle
                post.sub_heading=requesting_newsubheading
                post.slug=requesting_newslug
                post.content=requesting_newslug
                post.img_file=requesting_newimgfile
                post.date=setting_date
                db.session.commit()
                return redirect('/edit/'+sno)

        post = Posts.query.filter_by(sno=sno).first()
        return render_template('edit.html',params=params,post=post)


#creating a route to delete a post:
@app.route("/delete/<string:sno>", methods=['GET', 'POST'])
def delete(sno):
    if ('user' in session and session['user'] == params['admin_user']):
        post=Posts.query.filter_by(sno=sno).first()
        db.session.delete(post)
        db.session.commit()
    return redirect('/loginDashboard')

#creating a route for file upload
@app.route('/uploader',methods=['GET','POST'])
def uploader():
    if request.method=='POST':
        f=request.files['fileupload']
        f.save(os.path.join(app.config['UPLOAD_FOLDER'],secure_filename(f.filename)))
        return "uploaded successfully"
        #use of secure.filename
    '''to make sure that no user can upload files with
    paths as:
    --,/dir_name
    etc
    and get access to your linux server'''



#creating a route for logout
@app.route('/logout')
def logout():
    session.pop('user')
    return redirect('/loginDashboard')



@app.route('/contact',methods=['GET','POST'])
def contact():
    if(request.method=='POST'):
        '''add entry to the database'''
        name=request.form.get('name')
        email = request.form.get('email')
        phone_num = request.form.get('phone_num')
        msg = request.form.get('msg')

        entry=Contacts(name=name,email=email,phone_num=phone_num,msg=msg,date=datetime.now())
        db.session.add(entry)#to add our new contact entry to the db
        db.session.commit()
        mail.send_message("New message from "+name,
                          sender=email,
                          recipients=[params['gmail-user']],
                          body=msg+'\n'+phone_num
                          )
    return render_template('contact.html',params=params)

@app.route('/post/<string:quiz_generator>',methods=['GET'])
def post(quiz_generator):
    post=Posts.query.filter_by(slug=quiz_generator).first()
    return render_template('post.html',params=params,post=post)



@app.route('/about')
def about():
    return render_template('about.html')


if __name__ == '__main__':
    app.run(port=5000,debug=True)
