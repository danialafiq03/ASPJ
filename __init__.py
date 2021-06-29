#test
import math
import os
import random
import shelve
from urllib import parse
import stripe
from flask import Flask, render_template, request, redirect, url_for, session, g, flash, jsonify, make_response, render_template_string
from flask_mail import Message, Mail
# from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from base64 import b64encode, b64decode
import pickle
import Message as Msg
import Product
import Review
from Forms import RegisterForm, ContactUsForm, ReviewForm, reportForm, FAQSearchForm, ForgetPasswordForm

from flask_mysqldb import MySQL
import MySQLdb.cursors

mail = Mail()

app = Flask(__name__)
app.secret_key = 'secret_key'
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '@$PJ_Pr0j3ct'
app.config['MYSQL_DB'] = 'securityproject'
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 465
app.config["MAIL_USE_SSL"] = True
app.config["MAIL_USERNAME"] = 'abcrestaurant4@gmail.com'
app.config["MAIL_PASSWORD"] = 'nypAppDev123'
app.config['STRIPE PUBLIC KEY'] = 'pk_test_lfuZUTGObUfh7pa11TSt8CeA'
app.config[
    'STRIPE_SECRET_KEY'] = 'sk_test_51Bn3MVDe4uhAIaEt75dOEI0bOr2ZI2RVfKSdSAxvvVnWYyjEsPsXm0BeU8WpKWTlNP82M7lKmd0GMAJL6umBRhh900DVMUFavT'
stripe.api_key = 'sk_test_51Bn3MVDe4uhAIaEt75dOEI0bOr2ZI2RVfKSdSAxvvVnWYyjEsPsXm0BeU8WpKWTlNP82M7lKmd0GMAJL6umBRhh900DVMUFavT'
UPLOAD_FOLDER = '/static/img/avatars'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

mail.init_app(app)
mysql = MySQL(app)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/register', methods=["GET", "POST"])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        email = form.email.data
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM accounts WHERE email = '%s'" % email)
        email_exists = cursor.fetchone()
        if email_exists:
            error = 'Email has already been registered!'
        else:
            cursor.execute("SELECT MAX(id) FROM accounts")
            max_id_result = cursor.fetchone()  # returns a dict e.g. {'MAX(id)': 2}
            last_id = max_id_result['MAX(id)'] + 1
            cursor.execute("INSERT INTO accounts VALUES ('%s','%s','%s','%s','%s','%s','%s')"
                           % (last_id, form.email.data, form.password.data,
                              form.first_name.data, form.last_name.data, form.gender.data, 'avatar.jpg'))
            mysql.connection.commit()
            return redirect(url_for('login'))
        return render_template('register.html', form=form, error=error)
    else:
        return render_template('register.html', form=form)




@app.route('/login', methods=["GET", "POST"])
def login():
    error = ''
    if request.method == 'POST':
        session.clear()
        email = request.form['email']
        password = request.form['psw']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM accounts WHERE email = '%s' AND password = '%s';" % (email, password,))
        user = cursor.fetchone()
        if user:
            session['user_id'] = user['id']
            session['fullname'] = user['fname'] + " " + user['lname']
            session['user'] = user
            if session['user_id'] == 1:
                return redirect(url_for('user_dashboard'))
            return redirect(url_for('home'))
        else:
            error = 'Invalid Credentials. Please try again.'
    return render_template('login.html', error=error)


@app.route('/profile')
def profile():
    return render_template('profile.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))


@app.route('/forget_password', methods=["GET", "POST"])
def forget_password():
    global random_str, user_id, email, attempts_left
    error = None
    db = shelve.open('register.db', 'r')
    user_dict = db['Users']
    form = ForgetPasswordForm(request.form)

    if request.method == 'POST' and form.validate:
        if 'pin' in request.form:
            pin_input = request.form['pin']
            if attempts_left > 1:
                if pin_input == random_str:
                    session['user_id'] = user_id
                else:
                    attempts_left -= 1
                    error = f'Pin is incorrect. You have {attempts_left} attempts left.'
            else:
                error = 'You entered the wrong pin too many times.'
                return render_template('forget_password.html', form=form, error=error)

            if pin_input == random_str:
                return redirect(url_for('update_profile', id=user_id))
            else:
                return render_template('forget_password.html', error=error, form=form, email=email, pin=random_str,
                                       attempts_left=attempts_left)

        else:
            session.pop('user_id', None)
            email = request.form['email']

            for key in user_dict:
                user = user_dict.get(key)
                if user.get_email() == email:
                    user_id = user.get_user_id()
                    error = None
                    digits = [i for i in range(0, 10)]
                    random_str = ""
                    for i in range(6):
                        index = math.floor(random.random() * 10)
                        random_str += str(digits[index])
                    print(random_str)

                    confirmation = "We have sent you the reset password link in your email."
                    message = "We have sent you the reset password link in your email.\n\nThe pin is {}".format(
                        random_str)
                    mail.send_message(
                        sender='abcrestaurant4@gmail.com',
                        recipients=[email],
                        subject="Reset Password For F&B Restaurant",
                        body=message
                    )
                    attempts_left = 4
                    return render_template('forget_password.html', error=error, form=form, message=confirmation,
                                           email=email, pin=random_str, user_id=user_id)
                else:
                    error = "Please enter a registered email account!"
    elif request.method == "GET":
        return render_template('forget_password.html', form=form)
    db.close()
    return render_template('forget_password.html', form=form, error=error)


@app.route('/dashboard')
def user_dashboard():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM accounts")
    users_tuple = cursor.fetchall()
    if 'user_id' in session and session['user_id'] == 1:
        return render_template('UserDashboard.html', count=len(users_tuple), users_tuple=users_tuple)
    else:
        return 'You do not have authorized access to this webpage.'


# @app.route('/updateUser/<int:id>/', methods=['GET', 'POST'])
# def update_user(id):
#     update_user_form = RegisterForm(request.form)
#     if request.method == 'POST' and update_user_form.validate():
#         users_dict = {}
#         db = shelve.open('register.db', 'w')
#         users_dict = db['Users']
#
#         user = users_dict.get(id)
#
#         user.set_first_name(update_user_form.first_name.data)
#         user.set_last_name(update_user_form.last_name.data)
#         user.set_gender(update_user_form.gender.data)
#         user.set_password(generate_password_hash(update_user_form.password.data, method='sha256'))
#         user.set_email(update_user_form.email.data)
#         db['Users'] = users_dict
#
#         db.close()
#
#         session['user_updated'] = user.get_first_name() + ' ' + user.get_last_name()
#
#         return redirect(url_for('user_dashboard'))
#     else:
#         # users_dict = {}
#         # db = shelve.open('register.db', 'r')
#         # users_dict = db['Users']
#         # db.close()
#
#         # user = users_dict.get(id)
#         user = session['user']
#         update_user_form.first_name.data = user['fname']
#         update_user_form.last_name.data = user['lname']
#         update_user_form.gender.data = user['gender']
#         update_user_form.email.data = user['email']
#         update_user_form.password.data = user['password']
#     if 'user_id' in session and session['user_id'] == 1:
#         return render_template('updateUser.html', form=update_user_form)
#     else:
#         return 'You do not have authorized access to this webpage.'


@app.route('/updateProfile/<int:id>/', methods=['GET', 'POST'])
def update_profile(id):
    update_user_form = RegisterForm(request.form)
    filename = ''
    if request.method == 'POST' and update_user_form.validate():
        user = session['user']
        avatar = request.files['avatar']
        if avatar.filename == '':
            filename = user['avatar']
        elif avatar and allowed_file(avatar.filename):
            filename = secure_filename(avatar.filename)

            ver = 0
            while os.path.isfile('static/img/avatars/' + filename):  # if theres existing file
                ver += 1
                for filetype in ALLOWED_EXTENSIONS:
                    if filetype in filename.split('.'):
                        filename = avatar.filename.split('.')[0] + str(ver) + '.' + avatar.filename.split('.')[-1]
            avatar.save(os.path.join('static/img/avatars/', filename))
        elif not allowed_file(avatar.filename):
            fileTypeError = 'Invalid file type. (Only accepts .png, .jpg, .jpeg, and .gif files)'
            return render_template('updateProfile.html', id=id, form=update_user_form, fileTypeError=fileTypeError)
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT email FROM accounts")
        emails = cursor.fetchall()  # looks like this: ({'email': 'admin@gmail.com'}, {'email': 'danial.afiq.official@gmail.com'}, {'email': 'ali@gmail.com'})
        emails_list = []
        for dict in emails:
            emails_list.append(dict['email'])
        if update_user_form.email.data == user['email']:
            pass
        elif update_user_form.email.data in emails_list:
            emailError = "Email has already been registered!"
            return render_template('updateProfile.html', id=id, form=update_user_form, emailError=emailError)
        cursor.execute("UPDATE accounts SET email = '%s', password = '%s', fname = '%s', lname = '%s',"
                       " gender = '%s', avatar = '%s' WHERE id = '%s'"
                       %(update_user_form.email.data, update_user_form.password.data, update_user_form.first_name.data,
                         update_user_form.last_name.data, update_user_form.gender.data, filename, id))
        mysql.connection.commit()
        cursor.execute("SELECT * FROM accounts where id = %s" % user['id'])
        user = cursor.fetchone()
        session['user'] = user
        session['user_updated'] = user['fname'] + ' ' + user['lname']
        session['profile_updated'] = 'Profile successfully updated!'
        return redirect(url_for('profile'))
    else:
        user = session['user']
        update_user_form.first_name.data = user['fname']
        update_user_form.last_name.data = user['lname']
        update_user_form.gender.data = user['gender']
        update_user_form.email.data = user['email']

        if 'user_id' in session and session['user_id'] == id:
            return render_template('updateProfile.html', form=update_user_form)
        else:
            return 'You do not have authorized access to this webpage.'


@app.route('/deleteUser/<int:id>', methods=['POST'])
def delete_user(id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT fname, lname FROM accounts WHERE id = %s" % id)
    fullname = cursor.fetchone()
    cursor.execute("DELETE FROM accounts WHERE id = %s" % id)
    mysql.connection.commit()
    session['user_deleted'] = fullname['fname'] + ' ' + fullname['lname']

    return redirect(url_for('user_dashboard'))


@app.route('/FAQ', methods=["GET", "POST"])
def faq():
    form = FAQSearchForm(request.form)
    if request.method == "POST" and form.validate():
        if "sell" in form.search.data.lower():
            keyword = "sell"
        elif "not delivered" in form.search.data.lower() or "wrong order" in form.search.data.lower():
            keyword = ["not delivered", "wrong order"]
        elif "refund" in form.search.data.lower():
            keyword = "refund"
        elif "order" in form.search.data.lower():
            keyword = "order"
        elif "pay" in form.search.data.lower():
            keyword = "pay"
        elif "contact" in form.search.data.lower():
            keyword = "contact"
        elif "login" in form.search.data.lower() or "register" in form.search.data.lower():
            keyword = ["login", "register"]
        else:
            keyword = form.search.data.lower()
        return render_template('FAQ.html', form=form, kw=keyword)
    else:
        keyword = ""
        return render_template('FAQ.html', form=form, kw=keyword)


@app.route('/ContactUs', methods=['GET', 'POST'])
def contactus():
    form = ContactUsForm(request.form)
    if request.method == 'POST' and form.validate():
        messages_dict = {}
        db = shelve.open('messages.db', 'c')

        try:
            messages_dict = db['Messages']
        except:
            print("Error in retrieving Messages in messages.db")

        Msg.count_id = db['Messages_Count'] + 1

        message = Msg.Message(form.first_name.data, form.last_name.data, form.email.data, form.subject.data,
                              form.enquiry.data)

        messages_dict[message.get_message_id()] = message
        db['Messages'] = messages_dict

        # Test codes
        messages_dict = db['Messages']
        message = messages_dict[message.get_message_id()]
        print(message.get_subject(), "was stored in messages.db successfully.")

        db.close()

        first_name = form.first_name.data
        last_name = form.last_name.data
        email = form.email.data
        subject = form.subject.data
        enquiry = form.enquiry.data

        msg = Message(subject, sender='abcrestaurant4@gmail.com', recipients=[email])
        msg.body = f'Hello, {first_name} {last_name}. \n\nHere was your message sent to us: {enquiry}\n\nThank you for your enquiry. We will get back to you soon.\n\nRegards, \nABC Restaurant'
        mail.send(msg)

        return render_template('ContactUs.html', success=True)
    else:
        flash('All fields are required.')
        return render_template('ContactUs.html', form=form)


@app.route('/retrieveMessages', methods=['GET', 'POST'])
def retrieve_messages():
    messages_dict = {}
    db = shelve.open('messages.db', 'c')
    messages_dict = db['Messages']

    messages_list = []
    for key in messages_dict:
        message = messages_dict.get(key)
        messages_list.append(message)

    db['Messages_Count'] = len(messages_list)
    new_messages_dict = {}

    for index, message in enumerate(messages_list):
        message.set_message_id(index + 1)
        new_messages_dict[index + 1] = message

    db['Messages'] = new_messages_dict
    db.close()

    if request.method == 'POST':
        recipient = request.form['recipient']
        email = request.form['email']
        subject = request.form['subject']
        reply = request.form['reply']
        msg = Message(subject, sender='abcrestaurant4@gmail.com', recipients=[email])
        msg.body = f'Hello, {recipient}.\n\n{reply}\n\nRegards,\nABC Restaurant'
        mail.send(msg)
        replysent = True
        return render_template('retrieveMessages.html', count=len(messages_list), messages_list=messages_list,
                               replysent=replysent)
    else:
        if 'user_id' in session and session['user_id'] == 1:
            return render_template('retrieveMessages.html', count=len(messages_list), messages_list=messages_list)
        else:
            return 'You do not have authorized access to this webpage.'


@app.route('/deleteMessage/<int:id>', methods=["POST"])
def delete_message(id):
    messages_dict = {}
    db = shelve.open('messages.db', 'w')
    messages_dict = db['Messages']

    message = messages_dict.pop(id)

    db['Messages'] = messages_dict
    db.close()

    session['message_deleted'] = message.get_message_id()

    return redirect(url_for('retrieve_messages'))


@app.route('/<product_id>/review', methods=['GET', 'POST'])
def review(product_id):
    products = ['CknKb', 'CknRc', 'NsLmk', 'RtPrata', 'Water', 'TehTarik', 'IcedCola', 'anw']
    if product_id not in products:
        return '404 Page Not Found'
    else:
        form = ReviewForm(request.form)
        already_submitted = False
        if request.method == 'POST' and form.validate():
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute("SELECT MAX(review_id) FROM reviews")
            review_id = cursor.fetchone()['MAX(review_id)'] + 1
            user_dict = session['user']
            user_id = session['user_id']
            user_name = user_dict['fname'] + " " + user_dict['lname']
            avatar = user_dict['avatar']
            rating = form.rating.data
            title = form.title.data
            review = form.review.data
            votes = 0
            upvoters = ''  # '1, 3, 5'
            downvoters = ''
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute("INSERT INTO reviews VALUES ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s')"
                   %(review_id, product_id, user_id, user_name, avatar, rating, title, review, votes, upvoters, downvoters))
            mysql.connection.commit()
            return redirect(url_for('review_submitted'))
        elif request.method == 'GET':
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute("SELECT * FROM reviews WHERE product_id = '%s'" % product_id)
            reviews_list = list(cursor.fetchall())

            # for review in reviews_list:
            #     for key in users_dict:
            #         user = users_dict.get(key)
            #         users_email_list.append(user.get_email())
            #         if review.get_user_object().get_email() == user.get_email():
            #             setattr(review.get_user_object(), 'avatar', user.avatar)
            #             review.get_user_object().set_first_name(user.get_first_name())
            #             review.get_user_object().set_last_name(user.get_last_name())
            #     if review.get_user_object().get_email() not in users_email_list:
            #         review.get_user_object().set_first_name('[deleted]')
            #         review.get_user_object().set_last_name('')

            if 'user_id' in session:
                for review in reviews_list:
                    upvoters = review['upvoters']  # '1, 3, 5'
                    if upvoters == '':
                        upvoters_list = []
                    else:
                        upvoters_list = upvoters.split(", ")  # ['1', '3', '5']
                        for i in range(0, len(upvoters_list)):
                            upvoters_list[i] = int(upvoters_list[i])  # [1, 3, 5]
                    review['upvoters'] = upvoters_list

                    downvoters = review['downvoters']  # '1, 3, 5'
                    if downvoters == '':
                        downvoters_list = []
                    else:
                        downvoters_list = downvoters.split(", ")  # ['1', '3', '5']
                        for i in range(0, len(downvoters_list)):
                            downvoters_list[i] = int(downvoters_list[i])  # [1, 3, 5]
                    review['downvoters'] = downvoters_list

                    if session['user_id'] == review['user_id']:
                        already_submitted = True
            reviews_list = sorted(reviews_list, key=lambda review: review['votes'], reverse=True)

            template = 'products/' + product_id + '.html'
            return render_template(template, form=form, count=len(reviews_list), reviews_list=reviews_list,
                                   already_submitted=already_submitted)


@app.route('/review_submitted')
def review_submitted():
    return render_template('reviewSubmitted.html')


@app.route('/<product_id>/review/upvote/<int:review_id>/')
def upvote(product_id, review_id):
    if 'user_id' in session:
        reviews_dict = {}
        db_name = 'Review-' + product_id
        db = shelve.open('reviews.db', 'w')
        reviews_dict = db[db_name]

        review = reviews_dict.get(review_id)

        downvoters = review.downvoters
        upvoters = review.upvoters
        if g.user.get_email() in upvoters:
            votes = review.votes - 1
            setattr(review, 'votes', votes)
            upvoters.remove(g.user.get_email())
        else:
            votes = review.votes
            if g.user.get_email() in downvoters:
                votes = review.votes + 1
                downvoters.remove(g.user.get_email())
            votes = votes + 1
            setattr(review, 'votes', votes)
            upvoters.append(g.user.get_email())
            setattr(review, 'upvoters', upvoters)
        print(review.upvoters)
        db[db_name] = reviews_dict
        db.close()
        return redirect(url_for('review', product_id=product_id))
    else:
        return redirect(url_for('login'))


@app.route('/<product_id>/review/downvote/<int:review_id>/')
def downvote(product_id, review_id):
    if 'user_id' in session:
        reviews_dict = {}
        db_name = 'Review-' + product_id
        db = shelve.open('reviews.db', 'w')
        reviews_dict = db[db_name]

        review = reviews_dict.get(review_id)

        upvoters = review.upvoters
        downvoters = review.downvoters
        if g.user.get_email() in downvoters:
            votes = review.votes + 1
            setattr(review, 'votes', votes)
            downvoters.remove(g.user.get_email())
        else:
            votes = review.votes
            if g.user.get_email() in upvoters:
                votes = review.votes - 1
                upvoters.remove(g.user.get_email())
            votes = votes - 1
            setattr(review, 'votes', votes)
            downvoters.append(g.user.get_email())
            setattr(review, 'downvoters', downvoters)
        print(review.downvoters)
        db[db_name] = reviews_dict
        db.close()
        return redirect(url_for('review', product_id=product_id))
    else:
        return redirect(url_for('login'))


@app.route('/<product_id>/deleteReview/<int:id>', methods=["POST"])
def delete_review(product_id, id):
    reviews_dict = {}
    db_name = 'Review-' + product_id
    db = shelve.open('reviews.db', 'w')
    reviews_dict = db[db_name]
    print(db_name)
    print(reviews_dict[id].get_title())
    review = reviews_dict.pop(id)

    db[db_name] = reviews_dict
    db.close()

    return redirect(url_for('review', product_id=product_id))


@app.route('/<product_id>/updateReview/<int:id>/', methods=['GET', 'POST'])
def update_review(product_id, id):
    reviews_dict = {}
    db_name = 'Review-' + product_id
    db = shelve.open('reviews.db', 'w')
    reviews_dict = db[db_name]

    review = reviews_dict.get(id)

    review.set_rating(request.form['rating'])
    review.set_title(request.form['title'])
    review.set_review(request.form['review'])

    db[db_name] = reviews_dict
    db.close()

    return redirect(url_for('review', product_id=product_id))


@app.route('/ReportGeneration', methods=["GET", "POST"])
def report_generation():
    if 'user_id' in session and session['user_id'] == 1:
        option = ""
        users_list = []
        one_star_count = 0
        two_star_count = 0
        three_star_count = 0
        four_star_count = 0
        five_star_count = 0
        form = reportForm(request.form)

        users_dict = {}
        db = shelve.open('reviews.db', 'r')
        users_dict = db['Review-CknKb']
        db.close()

        for key in users_dict:
            user = users_dict.get(key)
            users_list.append(user)

        for i in range(len(users_list)):
            rating = users_list[i].get_rating()
            if int(rating) == 1:
                one_star_count += 1
            elif int(rating) == 2:
                two_star_count += 1
            elif int(rating) == 3:
                three_star_count += 1
            elif int(rating) == 4:
                four_star_count += 1
            elif int(rating) == 5:
                five_star_count += 1

        countlist = [one_star_count, two_star_count, three_star_count, four_star_count, five_star_count]

        if request.method == 'POST':
            if form.value.data == 'Review Ratings':
                option = 'Review Ratings'
            elif form.value.data == 'Customer Transaction History':
                option = 'Customer Transaction History'
            elif form.value.data == 'Total Amount':
                option = 'Total Amount'
            elif form.value.data == 'Payment Method':
                option = 'Payment Method'
        print(countlist)
        return render_template('ReportGeneration.html', form=form, option=option, count=len(users_list),
                               countlist=countlist, users_list=users_list)
    else:
        return 'You do not have authorized access to this webpage.'


@app.route('/Products', methods=["GET", "POST"])
def add_to_cart():
    already_in_cart = False
    if 'cart' in request.cookies:
        serialized_encoded_cart_list = request.cookies.get("cart")
        serialized_cart_list = b64decode(serialized_encoded_cart_list)
        cart_list = pickle.loads(serialized_cart_list)
    else:
        cart_list = []
    if request.method == 'POST':
        product_id = request.form.get('product_id')
        product_name = request.form.get('product_name')
        quantity = int(request.form.get('quantity'))
        price = round(float(request.form.get('price')), 2)
        for product in cart_list:
            if product.get_product_id() == product_id:
                already_in_cart = True
                current_quantity = product.get_quantity()
                new_quantity = current_quantity + quantity
                product.set_quantity(new_quantity)
                new_price = price * product.get_quantity()
                product.set_price(new_price)
                break
        if not already_in_cart:
            product_obj = Product.Product(product_id, product_name, quantity, price)
            cart_list.append(product_obj)
        response = make_response(redirect(url_for("add_to_cart")))
        response.set_cookie("cart", b64encode(pickle.dumps(cart_list)))
        return response
    else:
        return render_template('trialproductpage.html', cart_list=cart_list)





@app.route('/cart', methods=["GET", "POST"])
def cart():
    subtotal = 0
    if 'user_id' in session:
        if 'cart' in request.cookies:
            serialized_encoded_cart_list = request.cookies.get("cart")
            serialized_cart_list = b64decode(serialized_encoded_cart_list)
            cart_list = pickle.loads(serialized_cart_list)
            for i in range(len(cart_list)):
                product_price = cart_list[i].get_price()
                subtotal += product_price
        else:
            cart_list = []
        return render_template('cart.html', cart_list=cart_list, subtotal=round(subtotal, 2))
    else:
        return render_template('cart.html')


@app.route('/deleteProduct/<int:product_id>', methods=["POST"])
def delete_product(product_id):
    serialized_encoded_cart_list = request.cookies.get("cart")
    serialized_cart_list = b64decode(serialized_encoded_cart_list)
    cart_list = pickle.loads(serialized_cart_list)
    cart_list.pop(product_id)
    response = make_response(redirect(url_for("cart")))
    response.set_cookie("cart", b64encode(pickle.dumps(cart_list)))
    return response


@app.route('/create-checkout-session', methods=['POST'])
def create_checkout_session():
    cart_dict = {}
    cart_list = []
    user_id = g.user.get_user_id()
    db = shelve.open('cart.db', 'c')
    try:
        cart_dict = db['Cart']
    except:
        print('error')

    try:
        cart_list = cart_dict[user_id]
    except:
        pass
    subtotal = 0
    for i in range(len(cart_list)):
        price = cart_list[i].get_price()
        subtotal += price
    subtotal = subtotal * 100

    session = stripe.checkout.Session.create(
        billing_address_collection='required',
        payment_method_types=['card'],
        line_items=[{
            'price_data': {
                'currency': 'sgd',
                'product_data': {
                    'name': 'Subtotal',
                },
                'unit_amount': int(subtotal),
            },
            'quantity': 1,
        }],
        mode='payment',
        success_url=url_for("success", _external=True),
        cancel_url=url_for("cart", _external=True),
    )

    db.close()

    return jsonify(id=session.id)


@app.route("/success")
def success():
    cart_dict = {}
    cart_list = []
    user_id = g.user.get_user_id()
    db = shelve.open('cart.db', 'c')
    try:
        cart_dict = db['Cart']
    except:
        print('error')

    try:
        cart_list = cart_dict[user_id]
    except:
        pass
    cart_list.clear()
    cart_dict[user_id] = cart_list
    db['Cart'] = cart_dict
    db.close()
    return render_template("Thanks.html")


@app.errorhandler(404)
def page_not_found(error):
    # note that we set the 404 status explicitly
    template = '''
        <h1>{}</h1>
        <h3>{}</h3>
    '''.format(error, parse.unquote(request.url))
    return render_template_string(template)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
