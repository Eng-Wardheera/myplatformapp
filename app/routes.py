import base64
from collections import defaultdict
import csv
from decimal import Decimal
from email import parser
import io
import platform
import socket
import string
import sys
import traceback
from xml.dom.minidom import Document
from flask_wtf import FlaskForm
from googletrans import Translator
import imgkit
from pandas import read_csv 
import pandas as pd
from flask_mail import Message
from math import ceil
import os
import random
import re
from sqlite3 import IntegrityError
import uuid
import psutil
import pycountry
import pyotp
import qrcode
from datetime import date, datetime, timedelta
import pytz
from flask import Blueprint, Response, after_this_request, current_app, flash, g, json, jsonify, make_response, render_template, request, redirect, send_file, send_from_directory, session, url_for
from flask_login import login_user, logout_user, login_required, current_user, user_logged_in
import requests
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash
from sqlalchemy.orm import aliased, joinedload
from sqlalchemy import Integer, and_, case, cast, exists, extract, func, or_
from wtforms import DecimalField, SubmitField, TextAreaField
from app import EAT, now_eat, UPLOAD_FOLDER, db, ALLOWED_EXTENSIONS
from app import mail
from app import google 
from app import github 
import phonenumbers
from phonenumbers import NumberParseException, PhoneMetadata, parse, is_valid_number, format_number, PhoneNumberFormat
from user_agents import parse as parse_ua  # install: pip install pyyaml user-agents
from docx import Document
from docx.shared import Cm, Pt, RGBColor
from docx.enum.section import WD_ORIENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from io import BytesIO
from app import csrf
from app.modal import SettingsData, User, UserLog, UserSession
from app.view import LoginForm, RegisterForm, SettingsDataForm   




bp = Blueprint('main', __name__)

#------------------------------------------
#---- Function: 1 | Func Allowed Files  ---
#------------------------------------------
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
 

@bp.context_processor
def inject_settings():
    settings = SettingsData.query.first()
    return dict(settings=settings)


# Get real IP
# Get real client IP

def get_ip():
    """Return the real client IP, handling proxies."""
    headers_to_check = ['X-Forwarded-For', 'X-Real-IP', 'CF-Connecting-IP', 'Forwarded']
    for header in headers_to_check:
        ip = request.headers.get(header)
        if ip:
            ip = ip.split(',')[0].strip()
            if ip:
                return ip
    return request.remote_addr or "Unknown"

def get_active_network_interface():
    if_addrs = psutil.net_if_addrs()
    if_stats = psutil.net_if_stats()

    for iface, stats in if_stats.items():
        if stats.isup:
            name_lower = iface.lower()
            if "wi-fi" in name_lower or "wlan" in name_lower or "wireless" in name_lower:
                return "Wi-Fi"
            elif "eth" in name_lower or "en" in name_lower:
                return "Ethernet"
            elif "loopback" in name_lower:
                continue  # skip loopback
            else:
                return iface
    return "Unknown"


def get_device_name_from_ua(ua_string, user_id=""):
    """Return detailed device info from User-Agent."""
    ua = parse_ua(ua_string)
    device_type = "Desktop"
    os_name = ua.os.family
    os_version = ua.os.version_string or "Unknown"
    browser_name = ua.browser.family or "Unknown"
    manufacturer = ""
    model = ""

    if ua.is_mobile or ua.is_tablet:
        device_type = "Mobile" if ua.is_mobile else "Tablet"

        if "Android" in ua_string:
            match = re.search(r'Android [\d\.]+; ([^;)\]]+)', ua_string)
            if match:
                raw_model = match.group(1).strip()
                parts = raw_model.split(" ")
                if len(parts) > 1:
                    manufacturer = parts[0]
                    model = " ".join(parts[1:])
                else:
                    model = raw_model
            os_name = "Android"
            ver_match = re.search(r'Android ([\d\.]+)', ua_string)
            if ver_match:
                os_version = ver_match.group(1)

        elif "iPhone" in ua_string or "iPad" in ua_string:
            manufacturer = "Apple"
            model = "iPhone" if "iPhone" in ua_string else "iPad"
            os_name = "iOS"
            ver_match = re.search(r'OS ([\d_]+)', ua_string)
            if ver_match:
                os_version = ver_match.group(1).replace('_', '.')

    device_name = f"{user_id} | {os_name} {os_version} | {device_type} | {manufacturer} {model}".strip()
    return device_name, os_name, os_version, device_type, browser_name, manufacturer, model

def create_user_log(user_id, action, extra_info="", status="info"):
    """Logs user action and updates user's device info fields."""
    ua_string = request.headers.get('User-Agent', '')
    device_name, os_name, os_version, device_type, browser_name, manufacturer, model = get_device_name_from_ua(
        ua_string, user_id=str(user_id)
    )

    # Server-side system info
    system_info = {
        "architecture": platform.architecture()[0],
        "processor": platform.processor() or "Unknown",
        "ram_gb": round(psutil.virtual_memory().total / (1024**3), 2)
    }

    full_device_name = f"{device_name} | {system_info['architecture']} | {system_info['processor']} | RAM {system_info['ram_gb']} GB"

    # Get network interface (optional, demo placeholder)
    interface_name = get_active_network_interface()
    # Update password
    africa_time = datetime.now(pytz.timezone("Africa/Nairobi"))
    
    # Create log
    log = UserLog(
        user_id=user_id,
        login_time=africa_time,
        ip_address=get_ip(),
        device=device_type,         # Desktop / Mobile / Tablet
        browser=browser_name,
        platform=os_name,
        device_name=full_device_name,
        interface_name=interface_name,
        action=action,
        status=status,
        extra_info=extra_info
    )

    # Update the user record
    user = User.query.get(user_id)
    if user:
        user.device = device_type
        user.browser = browser_name
        user.ip_address=get_ip()
        user.platform = os_name
        user.device_name = full_device_name
        user.interface_name = interface_name
        user.extra_info = extra_info
        user.last_login_ip = get_ip()
        user.login_time = africa_time
        db.session.add(user)

    db.session.add(log)
    db.session.commit()

    
@bp.route("/api/device_info", methods=["POST"])
def device_info():
    data = request.json

    log = UserLog(
        user_id=data.get("user_id"),
        ip_address=data.get("ip"),
        subnet_mask=data.get("subnet"),
        gateway=data.get("gateway"),
        mac_address=data.get("mac"),
        device_name=data.get("device_name"),
        interface_name=data.get("interface_name"),
        platform=data.get("platform"),
        device="Desktop Agent",
        browser="N/A",
        action="device_info",
        status="info",
        extra_info="Device info from agent"
    )

    db.session.add(log)
    db.session.commit()
    return {"status": "success"}




@bp.route('/', methods=['GET', 'POST'])
def index():
    settings = SettingsData.query.first()

    # **Pass the form to the template**
    return render_template("frontend/index.html",  settings=settings,)


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        flash("You are already logged in!", "info")
        return redirect(url_for("main.dashboard"))

    form = LoginForm()

    if form.validate_on_submit():
        login_id = form.login_id.data.strip()
        password = form.password.data

        # 🔍 Fetch user
        user = User.query.filter(
            (User.email == login_id) |
            (User.username == login_id) |
            (User.phone == login_id)
        ).first()

        if not user or not check_password_hash(user.password, password):
            flash("Invalid login credentials", "danger")
            return redirect(url_for("main.login"))

        if not bool(user.status):
            flash("Your account is inactive", "danger")
            return redirect(url_for("main.login"))

        # 🔹 Clear old local session
        session.clear()

        now = now_eat()
        ua_string = request.headers.get('User-Agent', '')
        ip_address = get_ip()
        interface_name = get_active_network_interface()

        # 🔹 Detect device details
        device_name, os_name, os_version, device_type, browser_name, manufacturer, model = get_device_name_from_ua(
            ua_string,
            user_id=user.username
        )

        # ---------------------------------------------------------
        # 🔥 UNIQUE SESSION LOGIC (Hal Qalab = Hal Token)
        # ---------------------------------------------------------
        # Waxaan fiirinaynaa haddii uu jiro session hore oo isku mid ka ah:
        # User ID + User Agent (Browser-ka) + IP Address
        existing_session = UserSession.query.filter_by(
            user_id=user.id,
            user_agent=ua_string,
            ip_address=ip_address
        ).first()

        import uuid

        if existing_session:
            # Qofkaas waa la yaqaan, isla Token-kiisii hore u daay
            session_entry = existing_session
            session_entry.last_activity = now
            session_token = session_entry.session_token
            extra_msg = "Existing device & browser session reused."
        else:
            # Haddii uu yahay qalab cusub ama browser kale: Samey Token cusub
            session_token = str(uuid.uuid4())
            session_entry = UserSession(
                id=uuid.uuid4().hex,
                user_id=user.id,
                session_token=session_token,  # Token-kan wuxuu noqonayaa aqoonsiga qalabkan
                ip_address=ip_address,
                user_agent=ua_string,
                device=device_type,
                browser=browser_name,
                platform=os_name,
                payload=None,
                last_activity=now
            )
            db.session.add(session_entry)
            extra_msg = "New session created (New device/browser)."

        # -----------------------------
        # ✅ Create UserLog
        # -----------------------------
        log = UserLog(
            user_id=user.id,
            login_time=now,
            ip_address=ip_address,
            device=device_type,
            browser=browser_name,
            platform=os_name,
            device_name=device_name,
            interface_name=interface_name,
            extra_info=f"{extra_msg} | Manufacturer: {manufacturer}, Model: {model}",
            status="login",
            action="login"
        )
        db.session.add(log)

        # -----------------------------
        # ✅ Update USER Table
        # -----------------------------
        user.device = device_type
        user.browser = browser_name
        user.platform = os_name
        user.device_name = device_name
        user.interface_name = interface_name
        user.last_login_ip = ip_address
        user.login_time = now
        user.last_active = now
        user.auth_status = "login"

        db.session.add(user)
        db.session.commit()

        # 🔥 SAVE TO FLASK SESSION
        session["session_id"] = session_entry.id
        session["session_token"] = session_token # Token-kan waa kan loo isticmaali doono hubinta qalabka
        session["log_id"] = log.id

        # 🔥 LOGIN USER
        login_user(user)

        flash(f"Welcome back, {user.fullname}!", "success")
        return redirect(url_for("main.dashboard"))

    return render_template("backend/auth/auth-login.html", form=form)




@bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        flash("Logout first to create a new account!", "info")
        return redirect(url_for("main.dashboard"))

    form = RegisterForm()
    
    if form.validate_on_submit():
        fullname = form.fullname.data
        username = form.username.data
        email = form.email.data
        phone = form.phone.data
        password = form.password.data
        confirm_password = form.confirm_password.data

        if password != confirm_password:
            flash("Passwords do not match", "danger")
            return redirect(url_for("main.register"))

        existing_user = User.query.filter(
            (User.username == username) |
            (User.email == email) |
            (User.phone == phone)
        ).first()

        if existing_user:
            flash("Username, email or phone already exists", "danger")
            return redirect(url_for("main.register"))

        user = User(
            fullname=fullname,
            username=username,
            email=email,
            phone=phone,
            password=generate_password_hash(password),
            role="user",
            status=0
        )

        db.session.add(user)
        db.session.commit()

        flash("Account created successfully. Please login!", "success")
        return redirect(url_for("main.login"))

    # ✅ Halkan waa muhiim: ku soo dir 'form' template-ka
    return render_template("backend/auth/auth-register.html", form=form)








@bp.route('/settings/site', methods=['GET', 'POST'])
@login_required
def site_settings():
    # Get or create settings
    settings = SettingsData.query.first()
    if not settings:
        settings = SettingsData(group_name="default", address="", phone1="")
        db.session.add(settings)
        db.session.commit()

    form = SettingsDataForm(obj=settings)

    if form.validate_on_submit():
        try:
            # 🔹 Update text fields
            fields = [
                "group_name", "system_name", "address",
                "short_desc", "long_desc", "success_desc",
                "video_url", "phone1", "phone2", "email",
                "facebook", "twitter", "instagram", "dribbble"
            ]

            for field in fields:
                setattr(settings, field, getattr(form, field).data)

            # 🔹 Handle file uploads safely
            upload_fields = ["head_image", "image_success", "about_image", "logo", "logo2"]
            upload_folder = os.path.join("static", "backend", "uploads", "settings")
            os.makedirs(upload_folder, exist_ok=True)

            for field in upload_fields:
                file = getattr(form, field).data

                # ✅ Only process real uploaded files
                if file and isinstance(file, FileStorage) and file.filename:
                    filename = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
                    file_path = os.path.join(upload_folder, filename)

                    file.save(file_path)

                    # Save relative path to DB
                    setattr(settings, field, f"backend/uploads/settings/{filename}")

            db.session.commit()
            flash("Site settings updated successfully!", "success")
            return redirect(url_for("settings.site_settings"))

        except IntegrityError as e:
            db.session.rollback()
            flash(f"Database error: {str(e)}", "danger")

        except Exception as e:
            db.session.rollback()
            flash(f"Error: {str(e)}", "danger")

    return render_template(
        "backend/pages/components/settings/site-settings.html",
        form=form,
        settings=settings,
        user=current_user
    )



#---------------------------------------------------
#---- Route: 70 | Dashboard - Backend Template -----
#---------------------------------------------------
@bp.route("/logout")
def logout():
    if current_user.is_authenticated:

        # Log the logout action
       

        # Only log out from Flask-Login
        logout_user()

        # ✅ Do NOT clear session or delete DB session yet
        # session.clear()  <-- remove this
        # db.session.delete(user_session)  <-- remove this

        # Flash message
        flash("You have been logged out! Your session record remains for inspection.", "success")

    # Clear remember_token cookie to prevent auto-login
    resp = make_response(redirect(url_for("main.login")))
    resp.set_cookie("remember_token", "", expires=0)
    return resp








