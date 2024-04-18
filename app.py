import dataclasses

from flask import Flask,request, jsonify,abort
from flask_restful import Resource, Api
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)
api = Api(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///your_database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


@dataclasses.dataclass
class Bills(db.Model):
    billId: int
    firstName: str
    lastName: str
    subscriberNo: int
    month: int
    bill: str
    billDeatils: str
    isPaid: bool
    billId = db.Column(db.Integer, primary_key=True, nullable=False)
    firstName = db.Column(db.String(10),  nullable=False)
    lastName = db.Column(db.String(10), nullable=False)
    subscriberNo = db.Column(db.Integer,unique=True, nullable=False)
    month = db.Column(db.Integer, nullable=False)
    bill = db.Column(db.Integer, nullable=False)
    billDeatils = db.Column(db.String(20), nullable=True)
    isPaid = db.Column(db.Boolean, nullable=False)



class MobileProviderAppQueryBillAPI(Resource):
    def get(self):
        subscriberNo = request.args.get('subscriberNo')
        month = request.args.get('month')
        billreturned = Bills.query.filter_by(subscriberNo=subscriberNo, month=month).first()
        if billreturned:
            bill_total = billreturned.bill
            paid_status = billreturned.isPaid
            return jsonify({'Bill Total': bill_total, 'Paid Status': paid_status})
        else:
            abort(404, description="No bill found for the specified parameters")

api.add_resource(MobileProviderAppQueryBillAPI,'/mobileQueryAPI')

class MobileProviderAppQueryBillDetailedAPI(Resource):
    def get(self):
        subscriberNo = request.args.get('subscriberNo')
        month = request.args.get('month')
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 10))
        offset = (page - 1) * page_size

        bills_query = Bills.query.filter_by(subscriberNo=subscriberNo, month=month)
        total_bills = bills_query.count()

        bills = bills_query.offset(offset).limit(page_size).all()

        if bills:
            bill_details = []
            for bill in bills:
                bill_total = bill.bill
                paid_status = bill.isPaid
                details = bill.billDeatils
                bill_details.append({'Bill Total': bill_total,  'Bill Details': details})

            return jsonify({
                'total_bills': total_bills,
                'bills': bill_details
            })

        abort(404, description='No bills found for the specified parameters')

api.add_resource(MobileProviderAppQueryBillDetailedAPI, '/mobileQueryDetailedAPI')



class BankingAppQueryBillAPI(Resource):
    def get(self):
        subscriberNo = request.args.get('subscriberNo')
        unpaid_bills = Bills.query.filter_by(subscriberNo=subscriberNo, isPaid=False).all()
        if unpaid_bills:
            unpaid_bills_info = []
            for bill in unpaid_bills:
                month = bill.month
                bill_total = bill.bill
                unpaid_bills_info.append({'Bills NOT Paid': bill_total,'Month': month,})
            return jsonify(unpaid_bills_info)
        abort(404, description='No unpaid bills found for the specified subscriber')

api.add_resource(BankingAppQueryBillAPI, '/BankingAppQueryBillAPI')


class WebSitePayBillAPI(Resource):
    def put(self, subscriberNo, month):
        bills = Bills.query.filter_by(subscriberNo=subscriberNo, month=month).all()
        if bills:
            for bill in bills:
                if not bill.isPaid:
                    bill.isPaid = True
                    db.session.commit()
                    return jsonify({'message': f'Bill with ID {bill.billId} marked as paid'})
                else:
                    abort(409, description='Bill is already paid')
        else:
            abort(404, description='No bills found for the specified subscriber or month')

api.add_resource(WebSitePayBillAPI, '/WebSitePayBillAPI/<int:subscriberNo>/<int:month>')

class WebSiteAdminAddBillAPI(Resource):
    def post(self):
        subscriberNo = request.args.get('subscriberNo')
        month = request.args.get('month')
        transaction_status_str = request.args.get('transaction_status')
        firstName = request.args.get('firstName')
        lastName = request.args.get('lastName')
        bill = request.args.get('bill')
        billDeatils = request.args.get('billDeatils')


        if not all([subscriberNo, month, transaction_status_str,firstName,bill, lastName, billDeatils]):
            abort(400, description='Missing parameters. Please provide subscriberNo, month, and transaction_status.')
        isPaid = transaction_status_str.lower() in ['true', '1']

        existing_bill = Bills.query.filter_by(subscriberNo=subscriberNo, month=month, isPaid=isPaid, firstName=firstName, lastName=lastName,bill=bill,billDeatils=billDeatils).first()
        if existing_bill:
            return jsonify({'error': f'A bill already exists for subscriber {subscriberNo} for month {month}'})

        new_bill = Bills(firstName=firstName, lastName=lastName, subscriberNo=subscriberNo, bill=bill, month=month, billDeatils=billDeatils, isPaid=isPaid )
        db.session.add(new_bill)
        db.session.commit()

        return jsonify({                        'message': f'Bill added for subscriber {subscriberNo} for month {month} with transaction status {isPaid}'})


api.add_resource(WebSiteAdminAddBillAPI, '/admin_add_bill')



@app.route('/')
def index():
    return 'This is API Project for Mobile Provider Bill Payment System'




if __name__ == '__main__':
    db.create_all()
    app.run(host="0.0.0.0", port=5000, debug=True)
