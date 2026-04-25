from decimal import Decimal
import enum
from flask_login import UserMixin
from datetime import datetime
from sqlalchemy.dialects.mysql import ENUM  # Make sure this is the MySQL ENUM
import pytz
from sqlalchemy import DECIMAL, UniqueConstraint, event
from werkzeug.security import check_password_hash, generate_password_hash
from app import db, now_eat



# 1. Qeexidda Enum-ka
class UserRole(enum.Enum):
    superadmin = "superadmin"
    user = "user"

class Role(db.Model):
    __tablename__ = 'roles'

    id = db.Column(db.Integer, primary_key=True)
    
    # Haddii aad rabto inaad 'UserRole' Enum-ka u isticmaasho sidii column:
    # Waxaan ku darnay name='user_role_types' si Postgres uusan u bixin error
    role_type = db.Column(db.Enum(UserRole, name='user_role_types'), nullable=True)
    
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(255))

    # Relationships
    # Hubi in 'RolePermission' uu leeyahay back_populates='role'
    role_permissions = db.relationship('RolePermission', back_populates='role', cascade='all, delete-orphan')

 
    users = db.relationship('User', back_populates='role_obj')

    @property
    def permissions(self):
        return [rp.permission for rp in self.role_permissions]

    def __repr__(self):
        return f"<Role {self.name}>"
    



# -------------------------------
# ------ User Model --------------
# -------------------------------

# Define UserRole Enum if not imported

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    
    # 1. ENUM COLUMN (Kani waa xogta nooca user-ka)
    role = db.Column(
        db.Enum(UserRole, name='user_role_enum'), 
        nullable=False, 
        default=UserRole.user 
    )

    # 2. FOREIGN KEY (Kani waa xiriirka table-ka Roles)
    role_id = db.Column(
        db.Integer,
        db.ForeignKey('roles.id', name='fk_user_role'),
        nullable=True
    )

    # 3. RELATIONSHIP (Xiriirka rasmiga ah ee lala leeyahay Model-ka Role)
    # Hubi in Role model-kaaga uu ku qoran yahay: users = db.relationship('User', back_populates='role_obj')
    role_obj = db.relationship('Role', back_populates='users')

    # Basic info
    username = db.Column(db.String(150), unique=True, nullable=False)
    fullname = db.Column(db.String(150), unique=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(250), nullable=False)
    phone = db.Column(db.String(20))
    country = db.Column(db.String(255))
    city = db.Column(db.String(255))
    state = db.Column(db.String(255))
    address = db.Column(db.String(255))
    bio = db.Column(db.Text)
    photo = db.Column(db.String(255))
    gender = db.Column(db.String(10))
    photo_visibility = db.Column(db.String(20), default='everyone')
    status = db.Column(db.Boolean, default=True)

    # Device & Network info
    device = db.Column(db.String(100)) 
    browser = db.Column(db.String(100))
    platform = db.Column(db.String(100))
    device_name = db.Column(db.String(150))
    interface_name = db.Column(db.String(100))

    # Security & authentication
    is_verified = db.Column(db.Boolean, default=False)
    auth_status = db.Column(db.String(10), nullable=False, default='logout')
    session_token = db.Column(db.String(64), nullable=True)
    login_time = db.Column(db.DateTime, nullable=True)
    last_seen = db.Column(db.DateTime, default=now_eat)
    phone_verified = db.Column(db.Boolean, default=False)
    two_factor_enabled = db.Column(db.Boolean, default=False)
    two_factor_code = db.Column(db.String(10), nullable=True)
    two_factor_expires_at = db.Column(db.DateTime, nullable=True)
    last_login_ip = db.Column(db.String(45), nullable=True)
    remember_token = db.Column(db.String(255), nullable=True)
    failed_login_attempts = db.Column(db.Integer, default=0)
    auth_provider = db.Column(db.String(50), default='local')
    last_active = db.Column(db.DateTime, nullable=True)

    # Socials
    facebook = db.Column(db.String(255))
    twitter = db.Column(db.String(255))
    google = db.Column(db.String(255))
    whatsapp = db.Column(db.String(255))
    instagram = db.Column(db.String(255))
    github = db.Column(db.String(255))
    github_id = db.Column(db.String(100), unique=True)

    # Timestamps
    created_at = db.Column(db.DateTime, default=now_eat)
    updated_at = db.Column(db.DateTime, default=now_eat, onupdate=now_eat)

    # Relationships (Tables kale)
    user_logs = db.relationship('UserLog', backref='user_owner', cascade="all, delete-orphan", lazy=True)
    sessions = db.relationship('UserSession', back_populates='user', cascade="all, delete-orphan", lazy=True)
    user_permissions = db.relationship('UserPermission', back_populates='user', cascade='all, delete-orphan')

    @property
    def is_active(self):
        return self.status == True

    @property
    def permissions(self):
        return [up.permission for up in self.user_permissions]
    
    def __repr__(self):
        return f"<User {self.username}>"


# -------------------------------
#---------  3. Permission -------
# -------------------------------
# -------------------------------
# ------- 3. Permission ---------
# -------------------------------
class Permission(db.Model):
    __tablename__ = 'permissions'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    code = db.Column(db.String(100), nullable=False, unique=True)  # e.g. 'manage_users'
    group_name = db.Column(db.String(100), nullable=True)         # e.g. 'User Management'

    # Relationships
    role_permissions = db.relationship('RolePermission', back_populates='permission', cascade='all, delete-orphan')
    user_permissions = db.relationship('UserPermission', back_populates='permission', cascade='all, delete-orphan')

    def __repr__(self):
        return f"<Permission {self.code}>"

# -------------------------------
# ------- 4. Role Permission -----
# -------------------------------
class RolePermission(db.Model):
    __tablename__ = 'role_permissions'

    id = db.Column(db.Integer, primary_key=True)
    
    # ForeignKey leh magac gaar ah si looga fogaado isku dhaca PostgreSQL
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id', name='fk_role_permission_role'), nullable=False)
    permission_id = db.Column(db.Integer, db.ForeignKey('permissions.id', name='fk_role_permission_perm'), nullable=False)

    # Relationships
    role = db.relationship('Role', back_populates='role_permissions')
    permission = db.relationship('Permission', back_populates='role_permissions')

# -------------------------------
# - 5. User Permission -----------
# -------------------------------
class UserPermission(db.Model):
    __tablename__ = 'user_permissions'

    id = db.Column(db.Integer, primary_key=True)
    
    # ForeignKey leh magac gaar ah (Naming Convention)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', name='fk_user_permission_user'), nullable=False)
    permission_id = db.Column(db.Integer, db.ForeignKey('permissions.id', name='fk_user_permission_perm'), nullable=False)

    # Relationships
    permission = db.relationship('Permission', back_populates='user_permissions')
    user = db.relationship('User', back_populates='user_permissions')


# -------------------------------
# ------- 6. User Log -----------
# -------------------------------
class UserLog(db.Model):
    __tablename__ = 'user_logs'

    id = db.Column(db.Integer, primary_key=True)
    
    # PostgreSQL wuxu jecelyahay in Foreign Key-ga loo bixiyo magac (name)
    user_id = db.Column(
        db.Integer, 
        db.ForeignKey('users.id', name='fk_user_log_user_id', ondelete='CASCADE')
    )

    action = db.Column(db.Text)
    status = db.Column(db.String(10), default='login')

    # Time
    login_time = db.Column(db.DateTime, default=now_eat)
    timestamp = db.Column(db.DateTime, default=now_eat)

    # Network info
    ip_address = db.Column(db.String(45))
    subnet_mask = db.Column(db.String(45))
    gateway = db.Column(db.String(45))
    mac_address = db.Column(db.String(50))

    # Device info
    device = db.Column(db.String(100))
    browser = db.Column(db.String(100))
    platform = db.Column(db.String(100))
    device_name = db.Column(db.String(150))
    interface_name = db.Column(db.String(100))

    # Extra
    extra_info = db.Column(db.String(255))
    is_read = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, default=now_eat)
    updated_at = db.Column(db.DateTime, default=now_eat, onupdate=now_eat)

# -------------------------------
# ------- 7. User Session -------
# -------------------------------
class UserSession(db.Model):
    __tablename__ = 'user_sessions'

    id = db.Column(db.String(64), primary_key=True)
    
    # ForeignKey leh magac gaar ah
    user_id = db.Column(
        db.Integer, 
        db.ForeignKey('users.id', name='fk_user_session_user_id', ondelete='CASCADE'), 
        nullable=False
    )
    
    session_token = db.Column(db.String(255), nullable=False)

    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.Text, nullable=True)
    device = db.Column(db.String(100))
    browser = db.Column(db.String(100))
    platform = db.Column(db.String(100))
    payload = db.Column(db.Text, nullable=True)
    last_activity = db.Column(db.DateTime, default=now_eat)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationship
    user = db.relationship('User', back_populates='sessions')

    created_at = db.Column(db.DateTime, default=now_eat)
    updated_at = db.Column(db.DateTime, default=now_eat, onupdate=now_eat)

    def __repr__(self):
        return f"<UserSession {self.id} - User {self.user_id}>"


# ------------------------------------
#   Somalia Location Table ---------
# ------------------------------------
class SomaliaLocation(db.Model):
    __tablename__ = 'somalia_locations'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Gobolka (e.g., Banaadir, Bari, Woqooyi Galbeed)
    region = db.Column(db.String(100), nullable=False)
    
    # Degmada (e.g., Hodan, Boosaaso, Hargeysa)
    district = db.Column(db.String(100), nullable=False)
    
    # Timestamps
    # PostgreSQL wuxuu si sax ah u keydiyaa DateTime isagoo raacaya 'now_eat'
    created_at = db.Column(db.DateTime, default=now_eat)
    updated_at = db.Column(db.DateTime, default=now_eat, onupdate=now_eat)

    def __repr__(self):
        return f"<Location: {self.region}, District: {self.district}>"


# -------------------------------------
# 4. Settings Data Model Table --------
# ------------------------------------- 

class SettingsData(db.Model):
    __tablename__ = 'settings_data'

    id = db.Column(db.Integer, primary_key=True)
    
    # Magaca kooxda iyo nidaamka (System information)
    group_name = db.Column(db.String(255), nullable=False)
    system_name = db.Column(db.String(255), nullable=True)  # New column
    address = db.Column(db.String(255), nullable=False)
    
    # Qoraallada (PostgreSQL Text waxay u maamushaa si aad u wanaagsan)
    short_desc = db.Column(db.Text, nullable=True)
    long_desc = db.Column(db.Text, nullable=True)
    success_desc = db.Column(db.Text, nullable=True)
    
    # Sawirrada iyo Video-ga (Path-yada sawirrada)
    head_image = db.Column(db.String(255), nullable=True)
    image_success = db.Column(db.String(255), nullable=True)
    about_image = db.Column(db.String(255), nullable=True)
    logo = db.Column(db.String(255), nullable=True)
    logo2 = db.Column(db.String(255), nullable=True)
    video_url = db.Column(db.String(255), nullable=True)
    
    # Xiriirka (Contact info)
    phone1 = db.Column(db.String(15), nullable=False)
    phone2 = db.Column(db.String(15), nullable=True)
    email = db.Column(db.String(100), nullable=True)
    
    # Social Media
    facebook = db.Column(db.String(255), nullable=True)
    twitter = db.Column(db.String(255), nullable=True)
    instagram = db.Column(db.String(255), nullable=True)
    dribbble = db.Column(db.String(255), nullable=True)
    
    # Waqtiga (Timestamps)
    created_at = db.Column(db.DateTime, default=now_eat)
    updated_at = db.Column(db.DateTime, default=now_eat, onupdate=now_eat)

    def __repr__(self):
        return f"<SettingsData {self.id} - {self.group_name}>"





