from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///stockMarket.db'


db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    firstName = db.Column(db.String(80), unique=False, nullable=False)
    lastName = db.Column(db.String(80), unique=False, nullable=False)

    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(80), unique=False, nullable=False)
    #credit = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return '%r' % self.id


class Asset(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    assetName = db.Column(db.String(80), unique=True, nullable=False)
    #ticker --> symbol
    ticker = db.Column(db.String(80), unique=True, nullable=False)
    dailyPrice = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return '%r' % self.id


class Portfolio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    #portfolioName = db.Column(db.String(80), nullable=False)
    numAssets = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'),
                        nullable=False)
    user = db.relationship('User',
                           backref=db.backref('portfolios', lazy=True))

    def __repr__(self):
        return '%r' % self.id


class Investment(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    portfolio_id = db.Column(db.Integer, db.ForeignKey('portfolio.id'),
                        nullable=True)
    portfolio = db.relationship('Portfolio',
                           backref=db.backref('investments', lazy=True))

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'),
                        nullable=False)
    user = db.relationship('User',
                           backref=db.backref('investments', lazy=True))

    asset_id = db.Column(db.Integer, db.ForeignKey('asset.id'),
        nullable=False)
    asset = db.relationship('Asset',
        backref=db.backref('investments', lazy=True))

    #assetName = db.Column(db.String(80), nullable=False)

    currentCredit = db.Column(db.Float, nullable=False)
    stocks = db.Column(db.Integer, nullable=False)
    investmentAmount = db.Column(db.Float, nullable=False)
    reminder = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return '%r' % self.id


if __name__ == '__main__':
    db.create_all()
