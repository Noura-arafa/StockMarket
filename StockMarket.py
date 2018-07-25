from flask import Flask, request, render_template, url_for
from flask_restful import Resource, Api
from sqlalchemy import create_engine
from json import dumps
from flask import jsonify
from flask_sqlalchemy import SQLAlchemy
from marshmallow import Schema, fields, pre_load, validate
from flask_marshmallow import Marshmallow
from Model import User, Asset, Portfolio, Investment
import requests
from datetime import datetime, timedelta

db_connect = create_engine('sqlite:///stockMarket.db')
app = Flask(__name__)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///stockMarket.db'
api = Api(app)
db = SQLAlchemy(app)

@app.route('/user', methods=["POST"])
def new_User():
    user = User.query.filter_by(username=request.form.get('username')).first()
    if user:
        return render_template('warningPage.html', title='userexist')

    user = User.query.filter_by(username=request.form.get('email')).first()
    if user:
        return render_template('warningPage.html', title='email')

    user = User(firstName=request.form.get('firstName'), lastName=request.form.get('lastName'), username=request.form.get('username'),
                email=request.form.get('email'), password= request.form.get('password'))
    db.session.add(user)
    db.session.commit()
    return render_template('warningPage.html', title='welcome', name=request.form.get('firstName'))


@app.route('/addAsset', methods=["POST"])
def Add_Asset():
    asset = Asset.query.filter_by(assetName=request.form.get('assetName')).first()
    if asset:
        return render_template('warningPage.html', title='asset')
    asset = Asset(assetName=request.form.get('assetName'), ticker=request.form.get('ticker'), dailyPrice=request.form.get('dailyPrice'))
    db.session.add(asset)
    db.session.commit()
    return render_template('List Assets.html', asset=asset, title='add')

# def create_invest(user_id, porfolio_id, assetslist):


@app.route('/createPortfolio', methods=["POST"])
def Create_Portfolio():
    amount_Moneylist = request.form.getlist("amount")
    assetsname = request.form.getlist("assetname")
    userName = request.form.get("userName")

    conn = db_connect.connect()
    user = User.query.filter_by(username=userName).first()
    if user is None:
        return render_template('warningPage.html', title="user")
    user_id = int(str(user))

  #create obj of portfolio to insert it in db
    portfolio = Portfolio(numAssets=len(assetsname), user_id=user_id)

    for i in range(len(assetsname)):
        #get assetsID and dailyPrice
        query2 = conn.execute("select id, dailyPrice from asset where assetName = '%s'" %assetsname[i])
        row = query2.cursor.fetchone()
        if row is None:
            return render_template('warningPage.html', title="NotAsset")
        asset_id = int(row[0])
        dailyPrice = float(row[1])

        # cal number of shares and keep reminder in user credit if exist
        num_shares = int(float(amount_Moneylist[i]) / dailyPrice)
        reminder = round(float(amount_Moneylist[i]) % dailyPrice)
        current_credit = round(num_shares * dailyPrice)

        investment = Investment(user_id=user_id, asset_id=asset_id, currentCredit=current_credit,
                                stocks=num_shares, investmentAmount=amount_Moneylist[i], reminder=reminder)

        #add investment to portfolio's list to add them to db togther
        portfolio.investments.append(investment)

    #add them to database
    db.session.add(portfolio)
    db.session.commit()
    return render_template('CreatePortfolio.html')


@app.route('/listAssets')
def List_Assets():
    assets = Asset.query.all()
    return render_template('List Assets.html', assets=assets, title='list')


@app.route('/getAsset', methods=['GET'])
def Get_Asset():
    asset_name = request.args.get("asset_name")
    asset = Asset.query.filter_by(assetName=asset_name).first()
    if asset is None:
        return render_template('warningPage.html', title="NotAsset")
    return render_template('List Assets.html', asset=asset)


def updateUser_investment(dailyprice, asset_id):
    investment = Investment.query.filter_by(asset_id=asset_id).all()
    for id in investment:
        conn = db_connect.connect()
        invest = conn.execute("select stocks from investment where id = %d " % int(str(id)))
        stocks = int(invest.cursor.fetchone()[0])
        new_amount = round(stocks* float(dailyprice), 2)
        print(type(new_amount))
        conn.execute(
            "UPDATE investment SET currentCredit = ?  WHERE id= ? ",(new_amount, int(str(id))))


@app.route('/Update_Asset_Price', methods=['GET'])
def get_DailyPrice():
    try:
        symbol = request.args.get("symbol")
        url = 'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY'
        result = requests.get(url, params={
            "symbol": symbol,
            "apikey": "NN925NXZSUJVXV5L"
        }).json()

        today = datetime.today().strftime("%A")
        # get the day befor bec it will update the price at the end of the day
        daybefor = (datetime.today() - timedelta(days=1)).strftime('%Y-%m-%d')
        # if Today is sunday make the date mnus 2 days bec no update in stocker in saturday and Sunday So check the date first
        if today == "Sunday":
            daybefor = (datetime.today() - timedelta(days=2)).strftime('%Y-%m-%d')
        elif today == "Monday":
            daybefor = (datetime.today() - timedelta(days=3)).strftime('%Y-%m-%d')
        # test = result['Time Series (Daily)'][today]
        price = result['Time Series (Daily)'][daybefor]['4. close']
        updateprice(symbol, price)
        assetup = Asset.query.filter_by(ticker=symbol).first()
    except:
        return render_template('warningPage.html', title="symbol")
    return render_template('List Assets.html', asset=assetup, title='update')


#updated according to market price
def updateprice(asset_symbol, price):
    db.session.query(Asset).filter_by(ticker=asset_symbol).update({"dailyPrice":price})
    asset =  Asset.query.filter_by(ticker=asset_symbol).first()
    # if asset is None:
    #     return render_template('warningPage.html', title="symbol")
    print("id  ", int(str(asset)))
    db.session.commit()
    updateUser_investment(price, int(str(asset)))
    return asset

@app.route("/MyPortfolios", methods=['GET'])
def userportfolios():
    userName = request.args.get("userName")
    user = User.query.filter_by(username=userName).first()
    if user is None:
        return render_template('warningPage.html', title="user")
    user_id = int(str(user))
    portfolios = Portfolio.query.filter_by(user_id=user_id)
    if portfolios is None:
        return render_template('warningPage.html', title="nouserportf")
    return render_template('userPortfolios.html', portfolios=portfolios)


@app.route("/getPortfolio", methods=['GET'])
def get_portfolio():
    conn = db_connect.connect()
    portfolio_id = request.args.get("portfolio_id")
    portfolio = Portfolio.query.filter_by(id=portfolio_id).first()
    if portfolio is None:
        return render_template('portfolio.html')

    query = conn.execute("select * from investment where portfolio_id = '%d'" % int(portfolio.id))
    invests = query.fetchall()
    #invests = Investment.query.filter_by(portfolio_id=portfolio.id).all()
    assets_listID = []
    assets = []
    totalamount = 0
    for invest in invests:
        print("whyyy")
        assets_listID.append(invest.asset_id)
        totalamount += invest.currentCredit
        assets.append((conn.execute("select * from asset where id ='%d'" % int(invest.asset_id))).cursor.fetchone())
    #assets = db.session.query(Asset).filter(Asset.id.in_(assets_listID)).all()
    print(assets)
    return render_template('portfolio.html', invests=invests, assets=assets, totalamount=totalamount)


@app.route("/addAsset")
def add_assetPage():
    return render_template('addasset.html')


@app.route("/CreatePortfolio")
def createPortfolio():
    assets = Asset.query.all()
    return render_template('CreatePortfolio.html')


# @app.route("/createPortfolio")
# def createPortfolio():
#     return render_template('CreatePortfolio.html')


@app.route("/UpdateAsset_Price")
def update_Price():
    return render_template('updatePrice.html')

@app.route("/New_user")
def newAccount():
    return render_template('newUser.html')

@app.route("/")
def home():
    return render_template('navbar.html')

# api.add_resource(New_User, '/user')
#api.add_resource(Add_Asset, '/addAsset')
#api.add_resource(List_Assets, '/listAssets')
#api.add_resource(Get_Asset, '/getAsset/<asset_name>')
#api.add_resource(Create_Portfolio, '/createPortfolio/<user_id>')
#api.add_resource(Create_Portfolio, '/Update_Asset_Price/<asset_id>/<price>')

if __name__ == '__main__':
    app.run(port='5002')