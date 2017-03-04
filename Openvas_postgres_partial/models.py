# -*- coding: utf-8 -*-
import hashlib
import uuid
import time
import datetime

from aenum import Enum
from flask import current_app
from flask_login import UserMixin
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.dialects import postgresql as pq

from apps import stripe
from apps.extensions.clery.tasks import send_email
from apps.extensions.db import CRUDMixin, db, AutoSerialize


# Severities ENUM

class Severity(Enum):
    informational = 0
    low = 1
    medium = 2
    high = 3
    critical = 4


c = db.Column

plans_modules = db.Table('plans_modules_m2m',
                         c('id', db.Integer, db.ForeignKey('plans.id')),
                         c('module_id', db.Integer,
                           db.ForeignKey('modules.id'))
                         )


plans_features = db.Table('plans_features_m2m',
                          c('plan_id', db.Integer,
                            db.ForeignKey('plans.id')),
                          c('feature_id', db.Integer,
                            db.ForeignKey('features.id')))


class User(UserMixin, CRUDMixin, AutoSerialize, db.Model):
    __tablename__ = 'users'
    __public__ = ('first_name', 'last_name', 'middle_name', 'email',
                  'phone', 'company', 'address', 'verified',
                  'profile_pic', 'last_login', 'plan', 'is_admin')
    __mapping__ = {
        'plan': 'tier',
        'last_login': 'lastLogin',
        'is_admin': 'isAdmin',
        'profile_pic': 'avatar',
        'first_name': 'firstName',
        'last_name': 'lastName',
        'middle_name': 'middleName'
    }

    first_name = c(db.String(128), nullable=False)
    last_name = c(db.String(128), nullable=False)
    middle_name = c(db.String(128), nullable=True)
    email = c(db.String(255), unique=True, nullable=False)
    _passwd = c(db.LargeBinary(512))
    phone = c(db.Text, nullable=False)
    last_login = c(db.DateTime)
    company = c(db.String(128))
    address = c(db.Text)
    verified = c(db.Boolean)
    verify_hash = c(db.LargeBinary(128))
    stripe_custid = c(db.String(32))
    profile_pic = c(db.String(512), nullable=True, unique=False, default="/static/images/avatar.png")
    is_admin = c(db.Boolean, nullable=True, default=False)
    promo_code = c(db.String)

    # fk
    plan_id = c(db.Integer, db.ForeignKey('plans.id'))

    # relations
    websites = db.relationship('Website', backref='user', lazy='dynamic')
    Investigations = db.relationship('Investigation', backref='user',
                                     lazy='dynamic')
    scans = db.relationship('ScanResult', backref='user', lazy='dynamic')
    brief = db.relationship('SecurityBrief', uselist=False,
                            backref=db.backref('user')
                            )

    @hybrid_property
    def full_name(self):
        return "%s %s %s" % (self.first_name,
                             self.middle_name or "\b",  # \b to remove white space
                             self.last_name)

    @hybrid_property
    def is_admin(self):
        # FIXME how we decide admin?
        return current_app.config.get('TEST')

    @classmethod
    def from_form(cls, data):
        usr = None
        try:
            plan = data.pop('plan')
            inst = cls.create(first_name=data.get('firstName'),
                              last_name=data.get('lastName'),
                              middle_name=data.get('middleName'),
                              email=data.get('email'),
                              phone=data.get('phone'),
                              stripe_custid=data.get('stripeToken'),
                              password=data.get('password')
                              )
            # data.get('promoCode') TODO
            usr = inst.save()
            p = Plan.query.filter_by(plan_name=plan).first()
            usr.plan = p
            usr.save()
            usr.send_verification()
        except IntegrityError as e:
            current_app.logger.warning(e)
        except Exception as e:
            current_app.logger.error(e)
            return e
        finally:
            if usr:
                return usr.register_with_stripe(data)
            return User.query.filter_by(email=data.get('email'))

    def update_from_json(self, **kwargs):
        for k, v in kwargs.items():
            if k == 'companyName':
                k = 'company_name'
            elif k == 'firstName':
                k = 'first_name'
            elif k == 'lastName':
                k = 'last_name'
            elif k == 'middleName':
                k = 'middle_name'
            setattr(self, k, v)
        self.date_updated = datetime.datetime.utcnow()
        return self.save()

    @hybrid_property
    def tier(self):
        return self.plan.plan_name

    def send_verification(self):
        self.verify_hash = uuid.uuid4().hex
        self.save()
        send_email.delay(self.get_public(extra=('verify_hash','id'),
                                                mapping=None), 'VERIFY')
        return

    @hybrid_property
    def is_mod_allowed(self, modname):
        if self.modules.filter_by(modname).first():
            return True
        return False

    def register_with_stripe(self, data):
        # stripe data goes first
        try:
            self.process_payment()
        except Exception as e:
            current_app.logger.error(e)
            return e.message

        return self

    def is_token_valid(self, v):
        return self.verify_hash == v

    def process_payment(self):
        if (not self.promo_code):
            customer = stripe.Customer.create(
                source=self.stripe_custid,
                plan=self.plan.plan_name,
                email=self.email
            )
        return True

    @hybrid_property
    def password(self):
        return self._passwd

    @password.setter
    def password(self, v):
        # TODO: Set the password after hashing
        self._passwd = self._hash_password(v)

    def is_password_valid(self, v):
        if self._passwd == self._hash_password(v):
            return True
        return False

    def _hash_password(self, v):
        return hashlib.sha512(
            self.date_created.strftime(
                current_app.config.get('TIME_FMT')) + v + self.email
        ).hexdigest()

    @classmethod
    def create(cls, commit=True, **kwargs):
        if 'password' in kwargs.keys():
            p = kwargs.pop('password')
            inst = cls(**kwargs)
            u =inst.save(commit=True)
            u.password = p
            return inst.save(commit=True)
        super(User, cls).create(commit=commit, **kwargs)

    def get_modules(self):
        return [i.get_public()['module_name'] for i in self.plan.modules.all()]

    def get_websites(self):
        return [i.get_public() for i in self.websites.all()]

    def get_last_scans(self):
        res = []
        hosts = self.websites.all()

        for host in hosts:
            scans =  host.get_last_scans()
            scan_graph = {i.name: 0 for i in Severity}
            hpart = {
                "scanDate": time.mktime(scans[0][2].timetuple()),
                "scanGraph": scan_graph,
                "scanHost": host.hostname,
                "scanTitle": "STUB",
                "scanVuln_count": len(scans),
                "scanVulns": []
                }
            for i in scans:
                hpart['scanVulns'].append(i[0].get_public())
                scan_graph[i[1]] += 1
            res.append(hpart)
        return res

    def __repr__(self):
        return "<%d: %s>" % (self.id, self.full_name)


class Module(CRUDMixin, AutoSerialize, db.Model):
    __tablename__ = "modules"
    __public__ = ('module_name',)

    module_name = c(db.String(128), nullable=False, unique=True)

    plans = db.relationship('Plan', secondary=plans_modules,
                            backref=db.backref('module'), lazy='dynamic')

    def __repr__(self):
        return "<%s>" % self.module_name


class Plan(CRUDMixin, AutoSerialize, db.Model):
    __tablename__ = "plans"
    __public__ = ('plan_name', 'plan_hours')
    __mapping__ = {
        'plan_name': 'planName',
        'plan_hours': 'planHours'
    }

    plan_name = c(db.String(255), unique=True, nullable=False)
    plan_hours = c(db.Integer, nullable=False)
    plan_website_limit = c(db.Integer, nullable=True)

    # This is for custom plans so we won't have to fetch the price from stripe
    plan_price = c(db.Numeric, nullable=True)

    # relations
    plan_features = db.relationship('Feature', secondary=plans_features,
                                    backref=db.backref('plan'),
                                    lazy='dynamic')
    user = db.relationship('User', backref='plan', lazy='dynamic')
    modules = db.relationship('Module', secondary=plans_modules,
                              backref=db.backref('plan'),
                              lazy='dynamic')
    # TODO add module M2M relation

    def __repr__(self):
        return "%s" % self.plan_name


class Feature(CRUDMixin, db.Model):
    __tablename__ = 'features'
    feature_name = c(db.String(128), nullable=False, unique=True)
    feature_desc = c(db.Text)

    def __repr__(self):
        return "<%s>" % self.feature_name


class Investigation(CRUDMixin, db.Model):
    __tablename__ = "investigations"

    description = c(db.Text, nullable=False)
    email = c(db.Text, nullable=False)
    phone = c(db.String(16), nullable=False)

    # relations
    user_id = c(db.Integer, db.ForeignKey('users.id'))
    website = db.relationship('Website', uselist=False,
                              backref='investigation', lazy='select')

    def __repr__(self):
        return "<%s>" % self.website.ws_alias


class Website(CRUDMixin, AutoSerialize, db.Model):
    __tablename__ = 'websites'

    __public__ = ('hostname', 'total_scans', 'issues', 'priorities', 'solutions',
                  'auto_issues', 'manual_issues', 'last_scan_date', 'total_issues',
                  'total_scans')
    __mapping__ = {'total_scans': 'totalScans','auto_issues': 'autoIssues',
                   'manual_issues': 'manualIssues', 'total_issues': 'totalIssues',
                   'last_scan_date': 'lastScanDate'}

    # TODO: Should it be limited length?
    hostname = c(db.Text, nullable=False)
    total_scans = c(db.Integer, default=0)
    issues = c(db.Integer, default=0)
    priorities = c(db.Integer, default=0)
    solutions = c(db.Integer, default=0)
    last_scan_date = c(db.DateTime)


    ws_alias = c(db.String(128))  # might be a good idea for future references

    # relations
    scans = db.relationship('ScanResult', backref='website',
                            lazy='dynamic')

    investigation_id = c(db.Integer, db.ForeignKey('investigations.id'),
                         nullable=True)
    user_id = c(db.Integer, db.ForeignKey('users.id'))


    @hybrid_property
    def auto_issues(self):
        return self.scans.filter(ScanResult.manual==False).count()

    @hybrid_property
    def manual_issues(self):
        return self.scans.filter(ScanResult.manual==True).count()

    @hybrid_property
    def total_issues(self):
        return self.scans.count()

    @hybrid_property
    def total_scans(self):
        return self.scans.with_entities(ScanResult.scan_id
                                        ).group_by(ScanResult.scan_id).count()

    def get_last_scans(self):
        return self.scans.filter(
            ScanResult.scan_id==db.func.max(
                ScanResult.scan_id).select(),
            ).with_entities(
                ScanResult,
                ScanResult.severity.name,
                ScanResult.date_created,
            ).all()

    def get_security_rank(self):
        usr = {i[0].name: i[1] for i in db.session.query(
                    ScanResult.severity,
                    db.func.count(ScanResult.severity)
                ).group_by(
                    ScanResult.severity
                ).all()}
        avgs = Averages.get_counts()
        brief = self.user.brief.get_public()
        return {
            'averageRanking': avgs,
            'userRanking': usr,
            'securityBrief': brief
        }

    def __repr__(self):
        return "<%s>" % self.ws_alias


class ScanResult(CRUDMixin, AutoSerialize, db.Model):
    __tablename__ = 'scan_history'
    __public__ = ('scan_id', 'vuln_id', 'port', 'port_type',
                  'description', 'severity', 'family')
    __mapping__ = {'scan_id': 'scanID', 'vuln_id': 'vulnID',
                   'port_type': 'portType'}
    scan_id = c(db.Integer, nullable=False)
    vuln_id = c(db.String(256))
    port = c(db.Integer)
    port_type = c(db.String(32))
    description = c(db.Text)
    family = c(db.String(256))
    severity = c(db.Enum(Severity), nullable=False,
                 default=Severity.informational)
    manual = c(db.Boolean, default=False)
    # relations
    website_id = c(db.Integer, db.ForeignKey('websites.id'))
    user_id = c(db.Integer, db.ForeignKey('users.id'))


class SecurityBrief(CRUDMixin, AutoSerialize, db.Model):
    __tablename__ = 'security_brief'
    __public__ = ('summary', 'bullets', 'date_created')
    __mapping = {'date_created': 'dateCreated'}

    # Dummy tablespace, FIXME brainstorming
    summary = c(db.Text, nullable=False)

    bullets = c(pq.ARRAY(db.String))

    p1 = c(db.Text, nullable=True)
    p2 = c(db.Text, nullable=True)
    p3 = c(db.Text, nullable=True)

    # relations
    user_id = c(db.Integer, db.ForeignKey('users.id'))

    def __repr__(self):
        return "<%d: %s>" % (self.id, self.text)


class Averages(CRUDMixin, AutoSerialize, db.Model):
    __tablename__ = 'averages'
    __public__ = ('critical', 'high', 'medium', 'low', 'info')
    critical = c(db.Float)
    high = c(db.Float)
    medium = c(db.Float)
    low = c(db.Float)
    info = c(db.Float)

    @classmethod
    def get_counts(cls, offset=None):
        return cls.query.order_by(cls.id.desc()).first().get_public()


class PreRegister(CRUDMixin, db.Model):
    __tablename__ = 'pre_register'

    email = c(db.String)

    def __repr__(self):
        return self.email
#  vim: set ts=4 sw=4 tw=0 fdm=expr et :
