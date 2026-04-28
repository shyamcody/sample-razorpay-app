from flask import Flask, request, jsonify
from flask_cors import CORS
import razorpay
import os
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

app = Flask(__name__)
CORS(app)

# Fetch keys from environment variables
RAZORPAY_KEY_ID = os.environ.get("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.environ.get("RAZORPAY_KEY_SECRET")
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL environment variable is required. "
        "Example: postgresql://postgres:yourpassword@localhost:5432/razorpay_db"
    )

client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
engine = create_engine(DATABASE_URL, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(String(255), unique=True, nullable=False)
    payment_id = Column(String(255), nullable=True)
    signature = Column(String(255), nullable=True)
    amount = Column(Integer, nullable=False)
    currency = Column(String(10), nullable=False)
    status = Column(String(50), nullable=False)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

Base.metadata.create_all(bind=engine)

@app.route('/api/create-order', methods=['POST'])
def create_order():
    try:
        data = request.json
        # Amount is in paise (100 paise = 1 INR)
        amount = int(data.get("amount", 100)) 
        
        options = {
            "amount": amount,
            "currency": "INR",
            "receipt": "order_rcptid_11",
        }
        order = client.order.create(data=options)

        session = SessionLocal()
        try:
            transaction = Transaction(
                order_id=order["id"],
                amount=order["amount"],
                currency=order["currency"],
                status="order_created",
                error=None,
            )
            session.add(transaction)
            session.commit()
        finally:
            session.close()

        return jsonify(order), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/api/verify-payment', methods=['POST'])
def verify_payment():
    data = request.json
    params_dict = {
        'razorpay_order_id': data.get('razorpay_order_id'),
        'razorpay_payment_id': data.get('razorpay_payment_id'),
        'razorpay_signature': data.get('razorpay_signature')
    }

    updated_status = "payment_verified"
    error_message = None

    try:
        client.utility.verify_payment_signature(params_dict)
    except Exception as e:
        updated_status = "verification_failed"
        error_message = str(e)

    session = SessionLocal()
    try:
        transaction = session.query(Transaction).filter_by(order_id=params_dict['razorpay_order_id']).first()
        if transaction:
            transaction.payment_id = params_dict['razorpay_payment_id']
            transaction.signature = params_dict['razorpay_signature']
            transaction.status = updated_status
            transaction.error = error_message
        else:
            transaction = Transaction(
                order_id=params_dict['razorpay_order_id'] or "",
                payment_id=params_dict['razorpay_payment_id'],
                signature=params_dict['razorpay_signature'],
                amount=0,
                currency="INR",
                status=updated_status,
                error=error_message,
            )
            session.add(transaction)
        session.commit()
    finally:
        session.close()

    if updated_status == "payment_verified":
        return jsonify({"status": "Payment Verified"}), 200
    return jsonify({"status": "Verification Failed", "error": error_message}), 400

if __name__ == "__main__":
    app.run(debug=True)