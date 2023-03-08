from flask import Flask, render_template, request, redirect, url_for, session, flash, g, Markup, abort
import re
import hmac
from flask_mail import Mail, Message
from werkzeug.utils import secure_filename
from app import webapp
from app.config import db_config, app_config, s3_config
import os
import imghdr
from datetime import datetime
import urllib.request
import requests
import glob
import boto3, botocore
import urllib.parse
from io import BytesIO
import io
import app.dynamodb_handler as dynamodb
from boto3.dynamodb.conditions import Attr
import logging

s3 = boto3.client('s3',
                  region_name=s3_config['REGION_NAME'],
                  endpoint_url=s3_config['ENDPOINT_URL'],
                  aws_access_key_id=s3_config['AWS_ACCESS_KEY'],
                  aws_secret_access_key=s3_config['AWS_SECRET_KEY']
                  )

logging.basicConfig(filename='record.log', level=logging.DEBUG, format=f'%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s')


@webapp.route('/createTable')
def root_route():
    dynamodb.createTableMedicalHistory()

    return 'Hello World'


webapp.config['MAIL_SERVER'] = 'smtp.gmail.com'
webapp.config['MAIL_PORT'] = 465
webapp.config['MAIL_USE_SSL'] = True
webapp.config['MAIL_USERNAME'] = "ece1779assignment@gmail.com"
webapp.config['MAIL_PASSWORD'] = "Test@123"
webapp.config['MAIL_USE_TLS'] = False

mail = Mail(webapp)

# Change this to your secret key (can be anything, it's for extra protection)
webapp.secret_key = '7854cdat'


@webapp.route('/', methods=['GET'])
def home_page():
    if (session and 'loggedin' in session and session['loggedin'] == True) :
        if ('is_patient' in session):
            return redirect(url_for('patient_home'))
        elif ('is_doctor' in session) :
            return redirect(url_for('doctor_home'))

    return render_template('home/first_home.html', title="Home")


@webapp.route('/create_patient', methods=['GET'])
def create_patient():
    return render_template('home/create_patient.html', title="Register As Patient")


@webapp.route('/create_patient_save', methods=['POST'])
def create_patient_save():
    if (dynamodb.GetPersonFromPatientsUsingName(request.form.get('patient_username'))):
        items = dynamodb.GetPersonFromPatientsUsingName(request.form.get('patient_username'))
        if ('Item' in items and len(items['Item'].values()) > 0):
            flash("Account already exists!", "danger")
        else:
            response = dynamodb.addPersonToPatients(request.form.get('patient_username'),
                                                    request.form.get('patient_password'),
                                                    request.form.get('zip'), request.form.get('state'), request.form.get('age'), request.form.get('phone'), 1)
            if (response['ResponseMetadata']['HTTPStatusCode'] == 200):
                session['loggedin'] = True
                session['username'] = request.form.get('patient_username')
                session['is_patient'] = 1
                flash("Account created!", "success")
                return render_template('home/home.html', isPatient=session['is_patient'], username=session['username'],
                                       title="Home")

    return render_template('home/create_patient.html', title="Register As Patient")


@webapp.route('/create_doctor', methods=['GET'])
def create_doctor():
    return render_template('home/create_doctor.html', title="Register As Doctor")


@webapp.route('/create_doctor_save', methods=['POST'])
def create_doctor_save():
    if (dynamodb.GetPersonFromDoctorsUsingName(request.form.get('doctor_username'))):
        items = dynamodb.GetPersonFromDoctorsUsingName(request.form.get('doctor_username'))
        if ('Item' in items and len(items['Item'].values()) > 0):
            flash("Account already exists!", "danger")
        else:
            response = dynamodb.addPersonToDoctors(request.form.get('doctor_username'),
                                                   request.form.get('doctor_password'),
                                                   request.form.get('zip'), request.form.get('state'), 1)
            if (response['ResponseMetadata']['HTTPStatusCode'] == 200):
                flash("Account created!", "success")
                session['loggedin'] = True
                session['username'] = request.form.get('doctor_username')
                session['is_doctor'] = 1
                return render_template('home/home.html', isDoctor=session['is_doctor'], username=session['username'],
                                       title="Home")

    return render_template('home/create_doctor.html', title="Register As Doctor")


@webapp.route('/doctor_login', methods=['GET', 'POST'])
def doctor_login():
    # Check if "username" and "password" POST requests exist (user submitted form)
    if request.method == 'POST' and 'doctor_username' in request.form and 'doctor_password' in request.form:

        # Create variables for easy access
        username = request.form['doctor_username']
        password = request.form['doctor_password']

        if (dynamodb.GetPersonFromDoctorsUsingName(username)):
            items = dynamodb.GetPersonFromDoctorsUsingName(username)
            if ('Item' in items and len(items['Item'].values()) > 0):
                if (items['Item'].get('name') == username):
                    if (password == items['Item'].get('password')):
                        session['loggedin'] = True
                        session['username'] = username
                        session['is_doctor'] = 1
                        return redirect(url_for('doctor_home'))
                    else:
                        flash("Incorrect password!", "danger")
                else:
                    # Account doesnt exist or username/password incorrect
                    flash("Account does not exist!", "danger")
            else:
                flash("Account does not exist!", "danger")
        else:
            flash("Account does not exist!", "danger")
    return render_template('home/first_home.html', title="Login as Doctor")


# http://{{url}}:{{port}}/login/ - this will be the login page, we need to use both GET and POST requests
@webapp.route('/patient_login', methods=['GET', 'POST'])
def patient_login():
    # Check if "username" and "password" POST requests exist (user submitted form)
    if request.method == 'POST' and 'patient_username' in request.form and 'patient_password' in request.form:
        # Create variables for easy access
        username = request.form['patient_username']
        password = request.form['patient_password']

        if (dynamodb.GetPersonFromPatientsUsingName(username)):
            items = dynamodb.GetPersonFromPatientsUsingName(username)
            if ('Item' in items and len(items['Item'].values()) > 0):
                if (items['Item'].get('name') == username):
                    if (password == items['Item'].get('password')):
                        session['loggedin'] = True
                        session['username'] = username
                        session['is_patient'] = 1
                        return redirect(url_for('patient_home'))
                    else:
                        flash("Incorrect password!", "danger")
                else:
                    # Account doesnt exist or username/password incorrect
                    flash("Account does not exist!", "danger")
            else:
                flash("Account does not exist!", "danger")
        else:
            flash("Account does not exist!", "danger")
    return render_template('home/first_home.html', title="Login as Patient")


@webapp.route('/doctor/changepassword', methods=['GET'])
# Display an empty HTML form that allows admin to define new user.
def doctor_change_password():
    if 'loggedin' in session and session['loggedin'] == True and session['is_doctor'] == 1:
        username = session['username']
        return render_template("user/change_password.html", title="Change Password", username=username,
                               url="doctor_change_password_save", home="doctor_home")
    return redirect(url_for('doctor_home'))


@webapp.route('/patient/changepassword', methods=['GET'])
# Display an empty HTML form that allows admin to define new user.
def patient_change_password():
    if 'loggedin' in session and session['loggedin'] == True and session['is_patient'] == 1:
        username = session['username']
        return render_template("user/change_password.html", title="Change Password", username=username,
                               url="patient_change_password_save", home="patient_home")
    return redirect(url_for('patient_home'))


# This will be the registration page, we need to use both GET and POST requests
@webapp.route('/doctor/changepassword_save', methods=['POST'])
def doctor_change_password_save():
    username = session['username']
    if request.method == 'POST' and 'password' in request.form and 'new_password' in request.form and 'confirm_password' in request.form:

        # Create variables for easy access
        password = request.form['password']
        newPassword = request.form['new_password']
        confirmPassword = request.form['confirm_password']

        if (dynamodb.GetPersonFromDoctorsUsingName(username)):
            items = dynamodb.GetPersonFromDoctorsUsingName(username)
            if ('Item' in items and len(items['Item'].values()) > 0):
                if (items['Item'].get('name') == username):
                    if (items['Item'].get('password') != password):
                        flash("Incorrect old password!", "danger")
                    elif (password == newPassword):
                        flash("Your old and new passwords should be different", "danger")
                    else:
                        dynamodb.UpdatePasswordInDoctor(username, confirmPassword)
                        flash("You have successfully changed the password!", "success")
                        return render_template('home/home.html', isDoctor=session['is_doctor'],
                                               username=session['username'],
                                               title="Home")

    elif request.method == 'POST':
        # Form is empty... (no POST data)
        flash("Please fill out the form!", "danger")
    # Show registration form with message (if any)
    return render_template('user/change_password.html', title="Change Password", username=username,
                           url="doctor_change_password_save", home="doctor_home")


# This will be the registration page, we need to use both GET and POST requests
@webapp.route('/patient/changepassword_save', methods=['POST'])
def patient_change_password_save():
    username = session['username']
    if request.method == 'POST' and 'password' in request.form and 'new_password' in request.form and 'confirm_password' in request.form:

        # Create variables for easy access
        password = request.form['password']
        newPassword = request.form['new_password']
        confirmPassword = request.form['confirm_password']

        if (dynamodb.GetPersonFromPatientsUsingName(username)):
            items = dynamodb.GetPersonFromPatientsUsingName(username)
            if ('Item' in items and len(items['Item'].values()) > 0):
                if (items['Item'].get('name') == username):
                    if (items['Item'].get('password') != password):
                        flash("Incorrect old password!", "danger")
                    elif (password == newPassword):
                        flash("Your old and new passwords should be different", "danger")
                    else:
                        dynamodb.UpdatePasswordInPatient(username, confirmPassword)
                        flash("You have successfully changed the password!", "success")
                        return render_template('home/home.html', isPatient=session['is_patient'],
                                               username=session['username'],
                                               title="Home")

    elif request.method == 'POST':
        # Form is empty... (no POST data)
        flash("Please fill out the form!", "danger")
    # Show registration form with message (if any)
    return render_template('user/change_password.html', title="Change Password", username=username,
                           url="patient_change_password_save", home="patient_home")


@webapp.route('/login/patient_home')
def patient_home():
    # Check if user is loggedin
    if 'loggedin' in session and session['loggedin'] == True:
        # User is loggedin show them the home page
        return render_template('home/home.html', isPatient=session['is_patient'], username=session['username'],
                               title="Home")
    # User is not loggedin redirect to login page
    return redirect(url_for('patient_login'))


@webapp.route('/login/doctor_home')
def doctor_home():
    # Check if user is loggedin
    if 'loggedin' in session and session['loggedin'] == True:
        return render_template('home/home.html', isDoctor=session['is_doctor'], username=session['username'],
                               title="Home")
    # User is not loggedin redirect to login page
    return redirect(url_for('doctor_login'))


@webapp.route('/doctor/available')
def availability():
    if 'loggedin' in session and session['loggedin'] == True and session['is_doctor'] == 1:
        return render_template('home/available.html', isDoctor=session['is_doctor'], username=session['username'],
                               title="Availability")
    # User is not loggedin redirect to login page
    return redirect(url_for('doctor_login'))


@webapp.route('/doctor/available_save', methods=['POST'])
def save_slots():
    startTimeMonday = request.form['start-time-monday']
    startTimeTuesday = request.form['start-time-tuesday']
    startTimeWednesday = request.form['start-time-wednesday']
    startTimeThursday = request.form['start-time-thursday']
    startTimeFriday = request.form['start-time-friday']
    startTimeSaturday = request.form['start-time-saturday']
    endTimeMonday = request.form['end-time-monday']
    endTimeTuesday = request.form['end-time-tuesday']
    endTimeWednesday = request.form['end-time-wednesday']
    endTimeThursday = request.form['end-time-thursday']
    endTimeFriday = request.form['end-time-friday']
    endTimeSaturday = request.form['end-time-saturday']

    if 'loggedin' in session and session['loggedin'] == True and session['is_doctor'] == 1:
        if (
                startTimeMonday or endTimeMonday or startTimeTuesday or endTimeTuesday or startTimeWednesday or endTimeWednesday or startTimeThursday or endTimeThursday or startTimeFriday or endTimeFriday or startTimeSaturday or endTimeSaturday):
            if (dynamodb.GetSlotFromSlotsUsingName(
                    session['username'] + 'monday') or dynamodb.GetSlotFromSlotsUsingName(
                    session['username'] + 'tuesday') or
                    dynamodb.GetSlotFromSlotsUsingName(
                        session['username'] + 'wednesday') or dynamodb.GetSlotFromSlotsUsingName(
                        session['username'] + 'thursday') or
                    dynamodb.GetSlotFromSlotsUsingName(
                        session['username'] + 'friday') or dynamodb.GetSlotFromSlotsUsingName(
                        session['username'] + 'saturday')
            ):
                mondayItems = dynamodb.GetSlotFromSlotsUsingName(session['username'] + '_monday')
                tuesdayItems = dynamodb.GetSlotFromSlotsUsingName(session['username'] + '_tuesday')
                wednesdayItems = dynamodb.GetSlotFromSlotsUsingName(session['username'] + '_wednesday')
                thursdayItems = dynamodb.GetSlotFromSlotsUsingName(session['username'] + '_thursday')
                fridayItems = dynamodb.GetSlotFromSlotsUsingName(session['username'] + '_friday')
                saturdayItems = dynamodb.GetSlotFromSlotsUsingName(session['username'] + '_saturday')
                if ('Item' in mondayItems and len(mondayItems['Item'].values()) > 0 and (
                        startTimeMonday or endTimeMonday)):
                    dynamodb.DeleteAnItemFromSlot(session['username'] + '_monday')
                if ('Item' in tuesdayItems and len(tuesdayItems['Item'].values()) > 0 and (
                        startTimeTuesday or endTimeTuesday)):
                    dynamodb.DeleteAnItemFromSlot(session['username'] + '_tuesday')
                if ('Item' in wednesdayItems and len(wednesdayItems['Item'].values()) > 0 and (
                        startTimeWednesday or endTimeWednesday)):
                    dynamodb.DeleteAnItemFromSlot(session['username'] + '_wednesday')
                if ('Item' in thursdayItems and len(thursdayItems['Item'].values()) > 0 and (
                        startTimeThursday or endTimeThursday)):
                    dynamodb.DeleteAnItemFromSlot(session['username'] + '_thursday')
                if ('Item' in fridayItems and len(fridayItems['Item'].values()) > 0 and (
                        startTimeFriday or endTimeFriday)):
                    dynamodb.DeleteAnItemFromSlot(session['username'] + '_friday')
                if ('Item' in saturdayItems and len(saturdayItems['Item'].values()) > 0 and (
                        startTimeSaturday or endTimeFriday)):
                    dynamodb.DeleteAnItemFromSlot(session['username'] + '_saturday')
            if (startTimeMonday or endTimeMonday):
                dynamodb.addSlotToSlots(session['username'] + '_monday', 'Monday', startTimeMonday, endTimeMonday)
            if (startTimeTuesday or endTimeTuesday):
                dynamodb.addSlotToSlots(session['username'] + '_tuesday', 'Tuesday', startTimeTuesday, endTimeTuesday)
            if (startTimeWednesday or endTimeWednesday):
                dynamodb.addSlotToSlots(session['username'] + '_wednesday', 'Wednesday', startTimeWednesday,
                                        endTimeWednesday)
            if (startTimeThursday or endTimeThursday):
                dynamodb.addSlotToSlots(session['username'] + '_thursday', 'Thursday', startTimeThursday,
                                        endTimeThursday)
            if (startTimeFriday or endTimeFriday):
                dynamodb.addSlotToSlots(session['username'] + '_friday', 'Friday', startTimeFriday, endTimeFriday)
            if (startTimeSaturday or endTimeSaturday):
                dynamodb.addSlotToSlots(session['username'] + '_saturday', 'Saturday', startTimeSaturday,
                                        endTimeSaturday)
            return render_template('home/available.html', isDoctor=session['is_doctor'], username=session['username'],
                                   title="Availability")
    # User is not loggedin redirect to login page
    return redirect(url_for('doctor_home'))


@webapp.route('/patient/forgot_password', methods=['GET'])
def patient_forgot_password():
    return render_template('auth/patient_forgot_password.html', title="Forgot Password")

@webapp.route('/doctor/forgot_password', methods=['GET'])
def doctor_forgot_password():
    return render_template('auth/doctor_forgot_password.html', title="Forgot Password")


@webapp.route('/doctor/forgot_password', methods=['POST'])
def doctor_forgot_password_save():
    if request.method == 'POST' and 'username' in request.form:
        username = request.form['username']
        items = dynamodb.GetPersonFromDoctorsUsingName(username)
        if ('Item' in items):
            msg = Message('Reset Password', sender='ece1779assignment@gmail.com', recipients=[username])
            msg.html = render_template('auth/reset_email.html', username=username)
            mail.send(msg)
            flash(
                "A mail was sent to your email address to reset your password. If you do not see the email in a few minutes, check your Junk mail or Spam folder.",
                "success")
            return redirect(url_for('home_page'))
        else:
            flash(
                "Account does not exist",
                "danger")
            return redirect(url_for('home_page'))
    else:
        flash("Please provide an email address", "danger")
        return render_template('auth/doctor_forgot_password.html', title="Forgot Password")

@webapp.route('/patient/forgot_password', methods=['POST'])
def patient_forgot_password_save():
    if request.method == 'POST' and 'username' in request.form:
        username = request.form['username']
        items = dynamodb.GetPersonFromPatientsUsingName(username)
        if ('Item' in items):
            msg = Message('Reset Password', sender='ece1779assignment@gmail.com', recipients=[username])
            msg.html = render_template('auth/reset_email.html', username=username)
            mail.send(msg)
            flash(
                "A mail was sent to your email address to reset your password. If you do not see the email in a few minutes, check your Junk mail or Spam folder.",
                "success")
            return redirect(url_for('home_page'))
        else:
            flash(
                "Account does not exist",
                "danger")
            return redirect(url_for('home_page'))
    else:
        flash("Please provide an email address", "danger")
        return render_template('auth/doctor_forgot_password.html', title="Forgot Password")


@webapp.route('/reset_password/<email>', methods=['GET', 'POST'])
def reset_password(email):
    return render_template('auth/reset_verified.html', title="Reset Password", username=email)


@webapp.route('/reset_password', methods=['POST'])
def reset_password_save():
    if request.method == 'POST' and 'password' in request.form:
        password = request.form['password']
        email = request.form['email'][:-1]
        patientItems = dynamodb.GetPersonFromPatientsUsingName(email)
        doctorItems = dynamodb.GetPersonFromDoctorsUsingName(email)
        if ('Item' in patientItems):
            dynamodb.UpdatePasswordInPatient(email, password)
        elif 'Item' in doctorItems:
            dynamodb.UpdatePasswordInDoctor(email, password)
        flash("Your password has been successfully reset", "success")
        return redirect(url_for('home_page'))
    else:
        flash("Please provide a password", "danger")
        return render_template('auth/reset_verified.html', title="Reset Password")


@webapp.route('/doctor/delete', methods=['POST'])
# Deletes the specified user from the database.
def delete_doctor_account():
    dynamodb.DeleteAnItemFromDoctor(session['username'])
    session.pop('username', None)
    session.pop('loggedin', None)
    session.pop('is_doctor', None)
    flash("You have deleted the doctor account", "success")

    return redirect(url_for('home_page'))


@webapp.route('/patient/delete', methods=['POST'])
# Deletes the specified user from the database.
def delete_patient_account():
    dynamodb.DeleteAnItemFromPatient(session['username'])
    session.pop('username', None)
    session.pop('loggedin', None)
    session.pop('is_patient', None)
    flash("You have deleted the patient account", "success")

    return redirect(url_for('home_page'))


@webapp.route('/user/view', methods=['GET', 'POST'])
# Deletes the specified user from the database.
def view_account():
    if ('is_doctor' in session and session['is_doctor'] == 1):
        username = session['username']
        items = dynamodb.GetPersonFromDoctorsUsingName(username)
        zip = items['Item'].get('zip')
        state = items['Item'].get('state')
        age = None
        phone = None
        home = 'doctor_home'
    else:
        username = session['username']
        items = dynamodb.GetPersonFromPatientsUsingName(username)
        print(items['Item'])
        zip = items['Item'].get('zip')
        state = items['Item'].get('state')
        age = items['Item'].get('age')
        phone = items['Item'].get('phone')
        if age==None:
            age='Age'
        if phone==None:
            phone='Phone Number'
        home = 'patient_home'
    return render_template('user/view_account.html', title="View Account", session=session, username=username, zip=zip, state=state, age=age, phone=phone,
                           home=home)


@webapp.route('/user/save', methods=['POST'])
def save_account():
    if ('is_doctor' in session and session['is_doctor'] == 1):
        dynamodb.UpdateDoctor(request.form['username'], request.form['zip'], request.form['state'])
        flash("You have saved the doctor account", "success")
        return redirect(url_for('doctor_home'))
    elif ('is_patient' in session and session['is_patient'] == 1):
        dynamodb.UpdatePatient(request.form['username'], request.form['zip'], request.form['state'], request.form['age'], request.form['phone'])
        flash("You have saved the patient account", "success")
        return redirect(url_for('patient_home'))
    else:
        redirect(url_for('home_page'))


@webapp.route('/find/doctors', methods=['GET', 'POST'])
def find_doctors():
    doctorItemsArray = []
    if ('is_patient' in session and session['is_patient'] == 1):
        api_key = app_config['API_KEY']
        items = dynamodb.GetPersonFromPatientsUsingName(session['username'])
        zip = items['Item'].get('zip')
        dynamoDb = boto3.resource('dynamodb', region_name=s3_config['REGION_NAME'])
        table = dynamoDb.Table('Doctors')

        response = table.scan()
        data = response['Items']
        radius = app_config['RADIUS']
        for doctor in data:
            url = app_config['API_URL'] + 'origins=' + zip + '&destinations=' + doctor['zip'] + '&key=' + api_key
            response = requests.get(url)
            print(response.json())
            if (response.status_code == 200):
                if ('distance' in response.json()['rows'][0]['elements'][0]):
                    distance = response.json()['rows'][0]['elements'][0]['distance']['value']
                    if ('radius' in session and session['radius'] != None) :
                        radius = int(session['radius'])
                    if (distance > 0 and distance / 1000 <= radius) or (distance == 0):
                        doctorItems = dynamodb.GetPersonFromDoctorsUsingName(doctor['name'])
                        doctorItemsArray.append(
                            {'name': doctorItems['Item'].get('name'), 'distance': round(distance / 1000, 2)})
        return render_template('user/find_doctors.html', title="Find Doctors", username=session['username'],
                               doctorItemsArray=doctorItemsArray, radius=radius)
    return redirect(url_for('patient_home'))


@webapp.route('/select_slots/<email>', methods=['GET', 'POST'])
def select_slots(email):
    username = session['username']
    itemsArray = []
    slotCount = 0
    mondaySlots = []
    mondayItems = dynamodb.GetSlotFromSlotsUsingName(email + '_monday')
    if (mondayItems and 'Item' in mondayItems):
        if mondayItems['Item'].get('start_time'):
            mondayStartHour = mondayItems['Item'].get('start_time').split(":")[0]
            mondayEndHour = mondayItems['Item'].get('end_time').split(":")[0]
            slotTotalCount = int(mondayEndHour) - int(mondayStartHour)
            mondayStartMinutes = mondayItems['Item'].get('start_time').split(":")[1]
            for slotCount in range(slotTotalCount * 2):
                if (mondayStartMinutes == '30'):
                    mondayEndHour = str(int(mondayStartHour) + 1)
                    mondayEndMinutes = '00'
                if (mondayStartMinutes == '00'):
                    mondayEndHour = mondayStartHour
                    mondayEndMinutes = '30'
                if (mondayItems['Item'].get('end_time') and mondayItems['Item'].get('end_time').split(":")[
                    0] >= mondayEndHour):

                    mondaySlots.append(
                        mondayStartHour + ':' + mondayStartMinutes + ' - ' + mondayEndHour + ':' + mondayEndMinutes)
                    if (mondayItems['Item'].get('end_time').split(":")[0] != mondayEndHour):
                        mondayStartHour = mondayEndHour
                        mondayStartMinutes = mondayEndMinutes
        itemsArray.append({'day': 'Monday', 'slots': mondaySlots})
    tuesdaySlots = []
    tuesdayItems = dynamodb.GetSlotFromSlotsUsingName(email + '_tuesday')
    if (tuesdayItems and 'Item' in tuesdayItems):
        if tuesdayItems['Item'].get('start_time'):
            tuesdayStartHour = tuesdayItems['Item'].get('start_time').split(":")[0]
            tuesdayEndHour = tuesdayItems['Item'].get('end_time').split(":")[0]
            slotTotalCount = int(tuesdayEndHour) - int(tuesdayStartHour)
            tuesdayStartMinutes = tuesdayItems['Item'].get('start_time').split(":")[1]
            for slotCount in range(slotTotalCount * 2):
                if (tuesdayStartMinutes == '30'):
                    tuesdayEndHour = str(int(tuesdayStartHour) + 1)
                    tuesdayEndMinutes = '00'
                if (tuesdayStartMinutes == '00'):
                    tuesdayEndHour = tuesdayStartHour
                    tuesdayEndMinutes = '30'
                if (tuesdayItems['Item'].get('end_time') and tuesdayItems['Item'].get('end_time').split(":")[
                    0] >= tuesdayEndHour):
                    tuesdaySlots.append(
                        tuesdayStartHour + ':' + tuesdayStartMinutes + ' - ' + tuesdayEndHour + ':' + tuesdayEndMinutes)
                    if (tuesdayItems['Item'].get('end_time').split(":")[0] != tuesdayEndHour):
                        tuesdayStartHour = tuesdayEndHour
                        tuesdayStartMinutes = tuesdayEndMinutes
        itemsArray.append({'day': 'Tuesday', 'slots': tuesdaySlots})
    wednesdaySlots = []
    wednesdayItems = dynamodb.GetSlotFromSlotsUsingName(email + '_wednesday')
    if (wednesdayItems and 'Item' in wednesdayItems):
        if wednesdayItems['Item'].get('start_time'):
            wednesdayStartHour = wednesdayItems['Item'].get('start_time').split(":")[0]
            wednesdayEndHour = wednesdayItems['Item'].get('end_time').split(":")[0]
            slotTotalCount = int(wednesdayEndHour) - int(wednesdayStartHour)
            wednesdayStartMinutes = wednesdayItems['Item'].get('start_time').split(":")[1]
            for slotCount in range(slotTotalCount * 2):
                if (wednesdayStartMinutes == '30'):
                    wednesdayEndHour = str(int(wednesdayStartHour) + 1)
                    wednesdayEndMinutes = '00'
                if (wednesdayStartMinutes == '00'):
                    wednesdayEndHour = wednesdayStartHour
                    wednesdayEndMinutes = '30'
                if (wednesdayItems['Item'].get('end_time') and wednesdayItems['Item'].get('end_time').split(":")[
                    0] >= wednesdayEndHour):
                    wednesdaySlots.append(
                        wednesdayStartHour + ':' + wednesdayStartMinutes + ' - ' + wednesdayEndHour + ':' + wednesdayEndMinutes)
                    if (wednesdayItems['Item'].get('end_time').split(":")[0] != wednesdayEndHour):
                        wednesdayStartHour = wednesdayEndHour
                        wednesdayStartMinutes = wednesdayEndMinutes
        itemsArray.append({'day': 'Wednesday', 'slots': wednesdaySlots})
    thursdaySlots = []
    thursdayItems = dynamodb.GetSlotFromSlotsUsingName(email + '_thursday')
    if (thursdayItems and 'Item' in thursdayItems):
        if thursdayItems['Item'].get('start_time'):
            thursdayStartHour = thursdayItems['Item'].get('start_time').split(":")[0]
            thursdayEndHour = thursdayItems['Item'].get('end_time').split(":")[0]
            slotTotalCount = int(thursdayEndHour) - int(thursdayStartHour)
            thursdayStartMinutes = thursdayItems['Item'].get('start_time').split(":")[1]
            for slotCount in range(slotTotalCount * 2):
                if (thursdayStartMinutes == '30'):
                    thursdayEndHour = str(int(thursdayStartHour) + 1)
                    thursdayEndMinutes = '00'
                if (thursdayStartMinutes == '00'):
                    thursdayEndHour = thursdayStartHour
                    thursdayEndMinutes = '30'
                if (thursdayItems['Item'].get('end_time') and thursdayItems['Item'].get('end_time').split(":")[
                    0] >= thursdayEndHour):
                    thursdaySlots.append(
                        thursdayStartHour + ':' + thursdayStartMinutes + ' - ' + thursdayEndHour + ':' + thursdayEndMinutes)
                    if (thursdayItems['Item'].get('end_time').split(":")[0] != thursdayEndHour):
                        thursdayStartHour = thursdayEndHour
                        thursdayStartMinutes = thursdayEndMinutes
        itemsArray.append({'day': 'Thursday', 'slots': thursdaySlots})
    fridaySlots = []
    fridayItems = dynamodb.GetSlotFromSlotsUsingName(email + '_friday')
    if (fridayItems and 'Item' in fridayItems):
        if fridayItems['Item'].get('start_time'):
            fridayStartHour = fridayItems['Item'].get('start_time').split(":")[0]
            fridayEndHour = fridayItems['Item'].get('end_time').split(":")[0]
            slotTotalCount = int(fridayEndHour) - int(fridayStartHour)
            fridayStartMinutes = fridayItems['Item'].get('start_time').split(":")[1]
            for slotCount in range(slotTotalCount * 2):
                if (fridayStartMinutes == '30'):
                    fridayEndHour = str(int(fridayStartHour) + 1)
                    fridayEndMinutes = '00'
                if (fridayStartMinutes == '00'):
                    fridayEndHour = fridayStartHour
                    fridayEndMinutes = '30'
                if (fridayItems['Item'].get('end_time') and fridayItems['Item'].get('end_time').split(":")[
                    0] >= fridayEndHour):
                    fridaySlots.append(
                        fridayStartHour + ':' + fridayStartMinutes + ' - ' + fridayEndHour + ':' + fridayEndMinutes)
                    if (fridayItems['Item'].get('end_time').split(":")[0] != fridayEndHour):
                        fridayStartHour = fridayEndHour
                        fridayStartMinutes = fridayEndMinutes
        itemsArray.append({'day': 'Friday', 'slots': fridaySlots})
    saturdaySlots = []
    saturdayItems = dynamodb.GetSlotFromSlotsUsingName(email + '_saturday')
    if (saturdayItems and 'Item' in saturdayItems):
        if saturdayItems['Item'].get('start_time'):
            saturdayStartHour = saturdayItems['Item'].get('start_time').split(":")[0]
            saturdayEndHour = saturdayItems['Item'].get('end_time').split(":")[0]
            slotTotalCount = int(saturdayEndHour) - int(saturdayStartHour)
            saturdayStartMinutes = saturdayItems['Item'].get('start_time').split(":")[1]
            for slotCount in range(slotTotalCount * 2):
                if (saturdayStartMinutes == '30'):
                    saturdayEndHour = str(int(saturdayStartHour) + 1)
                    saturdayEndMinutes = '00'
                if (saturdayStartMinutes == '00'):
                    saturdayEndHour = saturdayStartHour
                    saturdayEndMinutes = '30'
                if (saturdayItems['Item'].get('end_time') and saturdayItems['Item'].get('end_time').split(":")[
                    0] >= saturdayEndHour):
                    saturdaySlots.append(
                        saturdayStartHour + ':' + saturdayStartMinutes + ' - ' + saturdayEndHour + ':' + saturdayEndMinutes)
                    if (saturdayItems['Item'].get('end_time').split(":")[0] != saturdayEndHour):
                        saturdayStartHour = saturdayEndHour
                        saturdayStartMinutes = saturdayEndMinutes
        itemsArray.append({'day': 'Saturday', 'slots': saturdaySlots})
    if (itemsArray):
        patientSlotITems = dynamodb.GetPatientSlotFromSlotsUsingName(username)
        if (patientSlotITems and 'Item' in patientSlotITems):
            dayFromTable = patientSlotITems['Item'].get('day')
            slotFromTable = patientSlotITems['Item'].get('slot')
            statusFromTable = patientSlotITems['Item'].get('status')
            for item in itemsArray:
                if (item['day'] == dayFromTable):
                    print(item['slots'])
                    i = 0
                    for slot in item['slots']:
                        if slot == slotFromTable and statusFromTable == 'approved':
                            item['slots'].pop(i)
                        i = i + 1
    return render_template('user/select_slots.html', title="Select Slots", username=email, itemsArray=itemsArray)


@webapp.route('/patient/save_slots/<email>', methods=['POST'])
def save_slots_patient(email):
    if ('slot' in request.form):
        slot = request.form['slot']
        day = slot.split("|")[0]
        slotTime = slot.split("|")[1]
        if (dynamodb.GetPatientSlotFromSlotsUsingName(session['username'])):
            items = dynamodb.GetPatientSlotFromSlotsUsingName(session['username'])
            if 'Item' in items:
                dynamodb.UpdateSlotInDoctor(session['username'], email, day, slotTime, 'pending')
                flash("You have successfully rescheduled", "success")
            else:
                dynamodb.addPatientSlotToSlots(session['username'], email, day, slotTime, 'pending')
                flash("You have scheduled an appointment", "success")
    else:
        flash("You have already selected a slot for another doctor", "danger")
    return redirect(url_for('patient_home'))


@webapp.route('/patient/get_appointments', methods=['GET'])
def get_all_appointments():
    allAppointments = []
    if ('is_patient' in session and session['is_patient'] == 1):
        username = session['username']
        if (dynamodb.GetPatientSlotFromSlotsUsingName(username)):
            items = dynamodb.GetPatientSlotFromSlotsUsingName(username)
            if 'Item' in items:
                allAppointments.append(
                    {'doctor_name': items['Item'].get('doctor_name'), 'day': items['Item'].get('day'),
                     'slot': items['Item'].get('slot'), 'status': items['Item'].get('status')})
    return render_template('home/view_appointments.html', title="View Appointments", allAppointments=allAppointments,
                           username=username)


@webapp.route('/doctor/get_appointments', methods=['GET'])
def doctor_get_all_appointments():
    allAppointments = []
    if ('is_doctor' in session and session['is_doctor'] == 1):
        username = session['username']
        dynamodbResource = boto3.resource('dynamodb', region_name=s3_config['REGION_NAME'])

        table = dynamodbResource.Table('SelectedSlots')

        response = table.scan(
            FilterExpression=Attr('doctor_name').eq(username)
        )
        for patient in response['Items']:
            patientItems = dynamodb.GetPersonFromPatientsUsingName(patient.get('patient_name'))
            phone = None
            if 'Item' in patientItems:
                phone = patientItems['Item'].get('phone')
            allAppointments.append(
                {'patient_name': patient.get('patient_name'), 'day': patient.get('day'), 'slot': patient.get('slot'),
                 'status': patient.get('status'), 'phone' : phone})
    return render_template('home/doctor_view_appointments.html', title="Manage Appointments",
                           allAppointments=allAppointments, username=username)


@webapp.route('/patient/cancel_appointments', methods=['POST'])
def delete_appointment():
    username = session['username']
    if (dynamodb.GetPatientSlotFromSlotsUsingName(username)):
        items = dynamodb.GetPatientSlotFromSlotsUsingName(username)
        if 'Item' in items:
            dynamodb.DeleteAnItemFromPatientsSlots(username)
            flash("Canceled the appointment", "success")
    return redirect(url_for('patient_home'))


@webapp.route('/doctor/accept_slots/<email>', methods=['POST'])
def accept_slots_patient(email):
    if (dynamodb.GetPatientSlotFromSlotsUsingName(email)):
        items = dynamodb.GetPatientSlotFromSlotsUsingName(email)
        if 'Item' in items:
            dynamodb.UpdateStatusSlotInDoctor(email, 'approved')
            dynamodb.UpdateDoctorInPatient(email, session['username'])
            flash("You have approved the appointment", "success")
        else:
            flash("This user does not exist now", "danger")
    return redirect(url_for('doctor_home'))


@webapp.route('/doctor/reject_slots/<email>', methods=['POST'])
def reject_slots_patient(email):
    if (dynamodb.GetPatientSlotFromSlotsUsingName(email)):
        items = dynamodb.GetPatientSlotFromSlotsUsingName(email)
        if 'Item' in items:
            dynamodb.UpdateStatusSlotInDoctor(email, 'rejected')
            dynamodb.UpdateDoctorInPatient(email, None)
            flash("You have rejected the appointment", "success")
        else:
            flash("This user does not exist now", "danger")
    return redirect(url_for('doctor_home'))

@webapp.route('/doctor/complete_slots/<email>', methods=['POST'])
def complete_slots_patient(email):
    if (dynamodb.GetPatientSlotFromSlotsUsingName(email)):
        items = dynamodb.GetPatientSlotFromSlotsUsingName(email)
        if 'Item' in items:
            dynamodb.UpdateStatusSlotInDoctor(email, 'complete')
            flash("You have marked the appointment as complete", "success")
        else:
            flash("This user does not exist now", "danger")
    return redirect(url_for('doctor_home'))

@webapp.route('/doctor/fail_slots/<email>', methods=['POST'])
def fail_slots_patient(email):
    if (dynamodb.GetPatientSlotFromSlotsUsingName(email)):
        items = dynamodb.GetPatientSlotFromSlotsUsingName(email)
        if 'Item' in items:
            dynamodb.UpdateStatusSlotInDoctor(email, 'failed')
            dynamodb.UpdateDoctorInPatient(email, None)
            msg = Message('Patient failed to join the session', sender='ece1779assignment@gmail.com', recipients=[email])
            msg.html = render_template('auth/reschedule_appointment.html', username=email)
            mail.send(msg)
            client = boto3.client('lambda')
            response = client.invoke(
                FunctionName="sendEmail",
                InvocationType='Event',
                Payload=msg
            )
            flash("You have marked the appointment as failed", "success")
        else:
            flash("This user does not exist now", "danger")
    return redirect(url_for('doctor_home'))

@webapp.route('/doctor/get_patients', methods=['GET'])
def doctor_get_all_patients():
    medicalHistory = []
    issues = []
    if ('is_doctor' in session and session['is_doctor'] == 1):
        username = session['username']
        dynamodbResource = boto3.resource('dynamodb', region_name=s3_config['REGION_NAME'])

        table = dynamodbResource.Table('Patients')

        response = table.scan(
            FilterExpression=Attr('doctor').eq(username)
        )
        for patient in response['Items']:
            medicalHistoryTable = dynamodbResource.Table('MedicalHistory')

            medicalResponse = medicalHistoryTable.scan(
                FilterExpression=Attr('patient_name').eq(patient.get('name'))
            )
            for item in medicalResponse['Items']:
                item['age'] = patient.get('age')
                item['zip'] = patient.get('zip')
                item['phone'] = patient.get('phone')
                if item.get('prescription'):
                    item['url'] = getPrescriptionUrl(patient.get('name'), item.get('issue'), item.get('prescription'), item.get('doctor'))
                webapp.logger.info(item)
            medicalHistory.append(medicalResponse['Items'])
    return render_template('home/get_patients.html', title="Patient Medical History", medicalHistory=medicalHistory, username=username)

@webapp.route('/patient/add_issue', methods=['GET'])
def add_health_issues():
    return render_template('home/add_patient_issue.html', title="Add Health Issue")

@webapp.route('/patient/save_issue', methods=['POST'])
def save_health_issues():
    if ('is_patient' in session and session['is_patient'] == 1):
        issue = request.form.get('issue')
        print(issue)
        username = session['username']
        now = datetime.now()
        dt_string = now.strftime("%d/%m/%Y:%H:%M:%S")
        dynamodb.addPatientToMedicalHistory(dt_string, username, issue)
        flash("Issue added", "success")
    return render_template('home/add_patient_issue.html', title="Add Health Issue", username=username)

@webapp.route('/doctor/upload_prescription/<email>/<issue>', methods=['POST'])
def upload_prescription(email, issue):
    if ('is_doctor' in session and session['is_doctor'] == 1):
        prescription = request.files['prescription']
        filename = secure_filename(prescription.filename)
        mediaPath = webapp.root_path + '/'
        username = session['username']
        dynamodbResource = boto3.resource('dynamodb', region_name=s3_config['REGION_NAME'])

        table = dynamodbResource.Table('MedicalHistory')

        response = table.scan(
            FilterExpression=Attr('patient_name').eq(email) and Attr("issue").eq(issue)
        )
        for medical in response['Items']:
            date = medical.get('date')
        dynamodb.uploadPrescription(date, filename, username)
        filePath = os.path.join(mediaPath + app_config['UPLOAD_PATH'], filename)
        print(filePath)
        prescription.save(filePath)
        output = upload_file_from_storage(filePath, filename,
                                          app_config['MEDIA_PATH'] + '/' + username + '/' + email + '/' + issue)
        if (output):
            # remove_file(filePath)
            msg = Message('Prescription Uploaded', sender='ece1779assignment@gmail.com', recipients=[email])
            msg.html = render_template('auth/upload_prescription.html', username=email)
            mail.send(msg)
        flash("Uploaded prescription", "success")
    return redirect(url_for('doctor_get_all_patients'))

@webapp.route('/login/logout')
def logout():
    session.pop('username', None)
    session.pop('loggedin', None)
    session.pop('is_doctor', None)
    session.pop('is_patient', None)
    flash("You have successfully logged out!", "success")
    return redirect(url_for('home_page'))

def upload_file_from_storage(filePath, file_name, folder):
    bucket = s3_config['BUCKET_NAME']
    try:
        s3.upload_file(filePath, bucket, folder + '/{}'.format(file_name), ExtraArgs={'ACL': 'public-read'})
    except Exception as e:
        print(e)
        return False
    return True

def remove_file(filePath):
    try:
        file_handle = open(filePath, 'r')
        os.remove(filePath)
        file_handle.close()
    except Exception as error:
        print(error)

def getPrescriptionUrl(patient, issue, prescription, doctor):
    if ('is_doctor' in session and session['is_doctor'] == 1):
        if (doctor == None) :
            doctor = session['username']
        print('media' + '/' + doctor + '/' + patient + '/' + issue + prescription);
        return get_prescription_url_from_s3('media' + '/' + doctor + '/' + patient + '/' + issue, prescription)

@webapp.route('/patient/get_prescriptions')
def get_prescriptions():
    prescriptions = []
    if ('is_patient' in session and session['is_patient'] == 1):
        username = session['username']

        dynamodbResource = boto3.resource('dynamodb', region_name=s3_config['REGION_NAME'])

        table = dynamodbResource.Table('MedicalHistory')

        response = table.scan(
            FilterExpression=Attr('patient_name').eq(username)
        )
        doctorName = dynamodb.GetPersonFromPatientsUsingName(username)['Item'].get('doctor')
        url = None
        for medical in response['Items']:
            if medical.get('prescription') and doctorName and medical.get('issue') and medical.get('prescription'):
                url = getPatientPrescriptionUrl(doctorName, medical.get('issue'), medical.get('prescription'))
            prescriptions.append({'date' : medical.get('date'), 'doctor' : doctorName, 'issue' : medical.get('issue'), 'prescription' : medical.get('prescription'), 'url' : url})
        return render_template('home/get_prescriptions.html', title="View Prescriptions", prescriptions=prescriptions)

def getPatientPrescriptionUrl(doctor, issue, prescription):
    username = session['username']
    return get_prescription_url_from_s3('media' + '/' + doctor + '/' + username + '/' + issue, prescription)

def get_prescription_url_from_s3(folder, filename):
    return s3_config['ENDPOINT_URL'] + s3_config['BUCKET_NAME'] + '/' + folder + '/' + filename

@webapp.route('/faq_patient', methods=['GET'])
def faq_patient():
    return render_template('home/faq_patient.html', title="Support Patient")

@webapp.route('/faq_doctor', methods=['GET'])
def faq_doctor():
    return render_template('home/faq_doctor.html', title="Support Doctor")

@webapp.route('/about', methods=['GET'])
def about():
    return render_template('home/about.html', title="About")

@webapp.route('/contactus', methods=['GET'])
def contactus():
    return render_template('home/contactus.html', title="Contact Us")

@webapp.route('/patient_message/<email>', methods=['GET'])
def patient_message(email):
    return render_template('home/patient_message.html', title="Message")

@webapp.route('/doctor_message/<email>', methods=['GET'])
def doctor_message(email):
    return render_template('home/doctor_message.html', title="Message")

@webapp.route('/select_radius', methods=['POST'])
def select_radius() :
    session['radius'] = request.form.get('radius')
    return redirect(url_for('find_doctors'))
