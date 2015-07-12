from jinja2 import StrictUndefined
from flask import Flask, render_template, redirect, request, flash, session
from flask_debugtoolbar import DebugToolbarExtension
from model import connect_to_db, db, User, Route
from haversine import haversine
from call import send_sms

app = Flask(__name__)
app.secret_key = 'public key'


@app.route('/')
def index():

    """Homepage."""

    if 'email' not in session:
        flash('You must Log In or Register before viewing projects')
        return redirect('/login')

    return render_template('index.html')


@app.route('/call', methods=["POST"])
def caller():
    """Make twilio call"""
    send_sms()
    return "Success"



###########
#how do I make another route that will activate call.py on the index page?
###########

##################################
    #SIGN UP/ LOGIN/ SIGN OUT
##################################


@app.route("/register")
def user_signup():

    """Sign up a new user."""

    print "SESSION: ", session
    return render_template("/register.html")


@app.route("/register-process", methods=["POST"])
def process_signup():

    """Route to process login for users."""

    email = request.form['email']
    phone = request.form['phone']
    entered_pw = request.form['password']
    entered_pw2 = request.form['password2']
    invite_code = request.form['invite']

    if User.query.filter_by(email=email).first():
        flash("A user already exists with this email")
        return render_template("register.html")
    else:
        new_user = User(password=entered_pw, email=email, phone=phone, invite_code=invite_code)
        db.session.add(new_user)
        db.session.commit()
        if not session.get('new_user.email'):
            session['email'] = new_user.email
        flash("You have been registered successfully.")
        return redirect("/")


@app.route("/login")
def user_login():

    """Login page with form for users."""

    return render_template("login.html")


@app.route("/process_login", methods=["POST"])
def process_login():
    """GET - displays a form that asks for email and password
        POST - collects that data and authenticates --> redirect to user profile"""

    email = request.form["email"]
    print "Email: ", email
    password = request.form["password"]
    user_object = User.query.filter(User.email == email).first()
    print "USER OBECT", user_object

    if user_object:
        if user_object.password == password:
            session["email"] = email
            return redirect("/")
        else:
            flash("Incorrect password. Try again.")
            return redirect("/login")
    else:
        flash("We do not have this email on file. Click Register if you would like to create an account.")
        return redirect("/login")

    return render_template("login.html")
        ###


@app.route("/logout")
def process_logout():

    """Route to process logout for users."""

    session.pop('user_id', None)
    session.pop('email', None)
    flash('You successfully logged out!')
    return redirect("/")


@app.route("/register_location", methods = ["POST"])
def register_route():

    """Add user's origin and destination to Route table"""
    print request.form
    originlat = request.form["marker1[latitude]"]
    originlng = request.form["marker1[longitude]"]
    destinationlat = request.form["marker2[latitude]"]
    destinationlng = request.form["marker2[longitude]"]

    print "here"
    user_obj = User.query.filter(User.email == session['email']).first()
    user_id = user_obj.user_id

    user_route = Route(route_user_id = user_id,
                        start_lat = originlat,
                        start_long = originlng,
                        end_lat = destinationlat,
                        end_long = destinationlng)

    db.session.add(user_route)
    db.session.commit()
   
    return ""


# not on call --- delete route data


@app.route("/match_walkers")
def match_walkers():

    """Filter on call users to match together based on proximity of origin and destination"""

    user_origin_lat = 5
    user_origin_lng = 4

    user_destination_lat = 5
    user_destination_lng = 4

    lat_range = .00724
    lng_range = .00943

    matches = []

    for other_user in route_table:
        if (other_user.origin_lat < user_origin_lat + lat_range and
            other_user.origin_lat > user_origin_lat - lat_range and
            other_user.origin_lng < user_origin_lng + lng_range and
            other_user.origin_lng > user_origin_lng - lng_range and
            other_user.destination_lat < user_destination_lat + lat_range and
            other_user.destination_lat > user_destination_lat - lat_range and
            other_user.destination_lng < user_destination_lng + lng_range and
            other_user.destination_lng > user_destination_lng - lng_range):
            # calculate distance using haversine and store dist and match id

            other_user_origin = (other_user.origin_lat, other_user.origin_lng)
            other_user_destination = (other_user.destination_lat, other_user.destination_lng)
            user_origin = (user_origin_lat, user_origin_lng)
            user_destination = (user_destination_lat, user_destination_lng)


            origin_difference = haversine(other_user_origin, user_origin)
            destination_difference = haversine(other_user_destination, user_destination)

            total = origin_difference + destination_difference
            matches.append((total, other_user_id))

    matches.sort()

    close_matches = []
    for i in range(4):
        user_id = matches[i][1]
        match_phone = query_for_match_phone
        match_name = query_for_match_name
        match_photo = query_for_match_photo
        close_matches.append((user_id, match_phone, match_name, match_photo))


    # query by match id (in order - lowest 5) - get contacts --> initialize twilio contact



##################################
    # Finish Walk #
##################################
@app.route("/finish", methods=['GET'])
def finish_walk():
    """After the user finishes her walk, take her to the rating form"""


    return redirect("/rating")

##################################
    # Rate walking companion #
##################################

@app.route("/rating", methods=["GET"])
def rate_user():

    
    return render_template("rating.html")

@app.route("/rating_process", methods=["POST"])
def process_rating():
    if request.method == "POST":

        companion_id = request.form['companion']
        companion_user = User.query.get(int(companion_id))
        safety_score = request.form['safe-rating']
        respect_score = request.form['respect-rating']

        overall_rating = (0.7 * int(safety_score)) + (0.3 * int(respect_score))

        print overall_rating

        companion_user.set_rating(overall_rating)
        db.session.commit()

        return redirect("/")


##################################
    # Invite a Friend #
##################################
@app.route("/invite", methods=['GET'])
def invite_friend():
    """Invite a friend to the app"""
    
    return render_template("invite.html")

@app.route("/invite_process", methods=['POST'])
def invite_sent():
    """Confirm Friend is invited"""
    
    return render_template("invite_sent.html")

if __name__ == "__main__":
    app.debug = True
    app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

    # Use the DebugToolbar
    DebugToolbarExtension(app)
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True
    connect_to_db(app)

    app.run()
