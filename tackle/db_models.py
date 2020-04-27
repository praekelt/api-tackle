from typing import Optional
from tackle.flask_utils import db


class APIKeyData(db.Model):
    __tablename__ = "api_key_data"

    auth_key = db.Column(db.String(1024), primary_key=True)
    desc = db.Column(db.String(1024), primary_key=False)

    call_count = db.Column(db.Integer, primary_key=False)
    call_count_limit = db.Column(db.Integer, primary_key=False)

    def __init__(self,
                 _auth_key: str,
                 _desc: str,
                 _call_count: int,
                 _call_count_limit: Optional[int]) -> None:
        self.auth_key = _auth_key
        self.desc = _desc
        self.call_count = _call_count
        self.call_count_limit = _call_count_limit


class AdminAPIKeyData(db.Model):
    __tablename__ = "admin_api_key_data"

    auth_key = db.Column(db.String(1024), primary_key=True)
    desc = db.Column(db.String(1024), primary_key=False)

    def __init__(self,
                 _auth_key: str,
                 _desc: str) -> None:
        self.auth_key = _auth_key
        self.desc = _desc


class APICallCountBreakdownData(db.Model):
    __tablename__ = "api_callcount_breakdown_data"

    auth_key = db.Column(db.String(1024), primary_key=True)
    endpoint = db.Column(db.String, primary_key=True)
    call_count = db.Column(db.Integer, primary_key=False)

    def __init__(self,
                 _auth_key: str,
                 _endpoint: str,
                 _call_count: int) -> None:
        self.auth_key = _auth_key
        self.endpoint = _endpoint
        self.call_count = _call_count
