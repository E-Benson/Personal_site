from flask import Flask, render_template, url_for, redirect, request, flash, send_from_directory, session, make_response
from flask_bcrypt import Bcrypt
from flask_session import Session
from flask_login import LoginManager
from markupsafe import escape
import math
import configparser
from db_manage import User_DB, Ammo_DB, Stat_DB
from verify import Verify
import signal
from tracker import tracker

app = Flask(__name__)
app.secret_key = b"83e0f1c532f92e6c741d85d6fe0421c6"

bcrypt = Bcrypt(app)

page_data = dict()
a_types = list()
ammo_db = Ammo_DB()
user_db = User_DB()
stat_db = Stat_DB()
validate = Verify()

conf = configparser.ConfigParser()
conf.read("conf.ini")


for a_type in conf["AMMOTYPES"].keys():
    a_types.append(a_type)


def make_page_data(req, p_name):
    page_data = {
            "useremail": req.cookies.get("useremail"),
            "a_types": a_types,
            "page_name": p_name
            }
    return page_data

@app.route("/")
@app.route("/home")
def home():
    tracker.log_ip(request.remote_addr, request.url)
    page_data = make_page_data(request, "home")
    return render_template("home.html", page_data=page_data)


@app.route("/ammo")
def ammo():
    tracker.log_ip(request.remote_addr, request.url)
    page_data = make_page_data(request, "ammo")
    return render_template("about_ammo.html", page_data=page_data)


@app.route("/ammo/<a_type>", methods=["GET", "POST"])
def ammo_listing(a_type):
    tracker.log_ip(request.remote_addr, request.url)
    page_data = make_page_data(request, "ammo_listing")
    page_data["result_options"] = [10,25,50]
    if escape(a_type) not in a_types:
        return render_template("404_error.html", page_data=page_data)
    page_data["a_type"] = escape(a_type)
    listings= ammo_db.scan_items(escape(a_type))
    sorted_listings = sorted(listings, key = lambda i: float(i['cpr']))
    # Pagination
    num_results = request.form.getlist('results')
    page_data["num_results"] = 10 if len(num_results) < 1 else int(num_results[0])
    
    page_num = request.form.getlist('page')
    page_num = 0 if len(page_num) < 1 else int(page_num[0])
    num_pages = math.ceil(len(sorted_listings) / page_data["num_results"])
    page_data["num_pages"] = list(range(num_pages))
    page_data["page"] = page_num

    page_data["listing_length"] = len(listings)
    page_data["item0"], page_data["item1"] = get_page(listings, page_num, page_data["num_results"])
    page_listings = sorted_listings[page_data["item0"]: page_data["item1"]]
    # Create chart data
    chart_data = make_chart_data(escape(a_type))
    # Format prices to 2 decimals
    for item in page_listings:
        item["cpr"] = "%.2f" % float(item["cpr"])
        item["price"] = "%.2f" % float(item["price"])  
    page_data["listings"] = page_listings
    
    return render_template("ammo_list.html", page_data=page_data, chart_data=chart_data)

def get_page(listings, page_num, num_results):
    tracker.log_ip(request.remote_addr, request.url)
    size = len(listings)
    start = num_results * page_num if num_results * page_num < size else 0
    stop = start + num_results if start + num_results < size else size
    return start, stop
    

@app.route("/signup", methods=["GET", "POST"])
def signup():
    tracker.log_ip(request.remote_addr, request.url)
    page_data = make_page_data(request, "signup")
    if request.method == "GET":
        return render_template("signup.html", page_data=page_data)
    valid_pword = validate.verify_password(request.form["password"])
    if not valid_pword[1]:
        flash(valid_pword[0], 'danger')
    if request.form["password"] != request.form["confirm_password"]:
        flash('Passwords do not match', 'danger')
    valid_email = validate.verify_email(request.form["email"])
    if not valid_email[1]:
        flash(valid_email[0], 'danger')
        return render_template("signup.html", page_data=page_data)
    user_data = dict()
    user_data["email"] = request.form["email"]
    user_data["p_hash"] = bcrypt.generate_password_hash(request.form["password"]).decode('utf-8')
    user_db.add_user(user_data)
    flash('Account successfully created!', 'success')
    return render_template("home.html", page_data=page_data)



@app.route("/user-profile", methods=["GET", "POST"])
def user_profile():
    tracker.log_ip(request.remote_addr, request.url)
    page_data = make_page_data(request, "profile")
    page_data["profile"] = dict()
    verified = True
    #if request.method == "GET":
    user_data = user_db.get_user(request.cookies.get("useremail"))
    for key in user_data.keys():
        if key != "email" and key != "p_hash":
            if key == "sms_count":
                page_data["profile"][key] = "%.2f" % (float(user_data["sms_count"]) * 0.00645)
            elif key == "phone":
                print(format_phone(user_data[key]))
                page_data["profile"][key] = format_phone(user_data[key])
            else:
                page_data["profile"][key] = user_data[key]
    if request.method == "GET":
        return render_template("user_profile.html", page_data=page_data)
    checkbox = request.form.getlist("notifications")
    checkbox = True if len(checkbox) >= 1 else False
    new_settings = {"notifications": checkbox}
    print(f"phone input: {request.form['phone']}")
    phone_number = strip_phone(request.form["phone"])
    print(f"phone_strip: {phone_number}")
    valid_phone = validate.verify_phone(phone_number)
    if valid_phone[1]:
        new_settings["phone"] = phone_number
    else:
        if phone_number != "":
            verified = False
            flash(valid_phone[0], 'danger')
    for a_type in a_types:
        if request.form[a_type] != "":
            valid_cpr = validate.verify_cpr(request.form[a_type])
            if not valid_cpr[1]:
                verified = False
                flash(valid_cpr[0], 'danger')
            else:
                new_settings[a_type] = strip_cpr(request.form[a_type])
    user_db.update_user(request.cookies.get("useremail"), new_settings)
    if verified:
        flash('Profile changes saved', 'success')
    page_data["page_name"] = "profile"
    return render_template("user_profile.html", page_data=page_data)

def strip_phone(phone_number):
    phone_stripped = ""
    for part in phone_number.split("-"):
        phone_stripped += part
    return phone_stripped
    
def format_phone(phone_number):
    area_code = phone_number[:3]
    mid = phone_number[3:6]
    end = phone_number[6:]
    return area_code + "-" + mid + "-" + end
    
def strip_cpr(cpr):
    if cpr.startswith('$'):
        return cpr[1:]

@app.route("/login", methods=["GET", "POST"])
def login():
    tracker.log_ip(request.remote_addr, request.url)
    page_data = make_page_data(request, "login")
    if request.method == "GET":
        return render_template("login.html", page_data=page_data)
    email = request.form["useremail"]
    p_hash = user_db.get_password(email)
    if p_hash is None:
        flash('User with that email not found', 'danger')
        return render_template("login.html", page_data=page_data)
    if bcrypt.check_password_hash(p_hash, request.form["password"]):
        flash('Login success!', 'success')
        page_data["useremail"] = email
        page_data["page_name"] = "home"
        response = make_response(render_template("home.html", page_data=page_data))
        response.set_cookie("useremail", email)
        return response
    else:
        flash('Incorrect password', 'danger')
        return render_template("login.html", page_data=page_data)


@app.route("/logout")
def logout():
    tracker.log_ip(request.remote_addr, request.url)
    #request.set_coiokies("useremail", None)
    page_data = make_page_data(request, "home")
    page_data["useremail"] = None
    flash('You have been logged out', "success")
    response = make_response( render_template("home.html", page_data=page_data) )
    response.set_cookie("useremail", "None")
    #page_data = make_page_data(response)
    return response
    #page_data["useremail"] = None
    #return render_template("home.html", page_data=page_data)


@app.route("/test/<a_type>")
def test(a_type):
    tracker.log_ip(request.remote_addr, request.url)
    page_data = make_page_data(request, "test")
    
    page_data["a_type"] = escape(a_type)

    listings = stat_db.query_items(page_data["a_type"])
    chart_data = "[\"Day\", \"Minimum ppr\", \"Maximum ppr\"],\n"
    plot_data = "[\"Minimum ppr\", \"Time listed\"],\n"
    for item in listings:
        chart_data += f"[\"{item['date_str']}\", {item['min_cpr']}, {item['max_cpr']}],\n"
        plot_data += f"[{item['min_cpr']}, {item['min_time']}],\n"

    return render_template("test.html", page_data=page_data, chart_data=chart_data, plot_data=plot_data)


@app.errorhandler(404)
def page_not_found(e):
    tracker.log_ip(request.remote_addr, request.url)
    page_data = make_page_data(request, "404")
    return render_template("404_error.html", page_data=page_data)


@app.route("/robots.txt")
def robots():
    return send_from_directory(app.static_folder, "robots.txt")


@app.route("/favicon.ico")
def favicon():
    return send_from_directory(app.static_folder, "favicon.ico")

def make_chart_data(a_type):
    listings = stat_db.query_items(a_type)
    listings = sort_dates(listings)[-30:]
    chart_data = "[\"Day\", \"Minimum $/rd\", \"Maximum $/rd\"],\n"
    for item in listings:
        date_str = fmt_date(item["date_str"])
        if float(item["max_cpr"]) < 5.0:
            chart_data += f"[\"{date_str}\", {item['min_cpr']}, {item['max_cpr']}],\n"
        else:
            chart_data += f"[\"{date_str}\", {item['min_cpr']}, 5],\n"
        
    return chart_data
    
def fmt_date(date_str):
    months = {"January": "01", "February": "02", "March": "03", "April": "04", "May": "05", "June": "06", "July": "07", "August": "08", "September": "09", "October": "10", "November": "11", "December": "12"}
    date_sp = date_str.split("-")
    return months[date_sp[0]] + "/" + date_sp[1]# + "/" + date_sp[2][2:]

        

def sort_dates(data):
    return sorted(data, key = lambda i: num_date(i['date_str']))

        

def num_date(date_str):
    months = {"January": 1, "February": 2, "March": 3, "April": 4, "May": 5, "June": 6, "July": 7, "August": 8, "September": 9,
            "October": 10, "November": 11, "December": 12}   
    m, d, y = date_str.split("-")
    return (months[m] * 31) + int(d) + (int(y) * 365)




def exit_handler(signum, frame):
    sys.exit(0)

#signal.signal(signal.SIGTERM, exit_handler)


if __name__ == '__main__':
    app.run(debug=False,
            host="0.0.0.0",
            port=443,
            ssl_context=("/etc/letsencrypt/live/www.bensonea.com/cert.pem",
                         "/etc/letsencrypt/live/www.bensonea.com/privkey.pem"
                         )
            )




