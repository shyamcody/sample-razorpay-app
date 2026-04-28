import streamlit as st
import requests
import os
import uuid
import streamlit.components.v1 as components

from dotenv import load_dotenv  # <--- Add this

# Load the .env file from the current directory
load_dotenv()
# --- CONFIGURATION ---
# Pull the Key ID from your environment variables
RAZORPAY_KEY_ID = os.environ.get("RAZORPAY_KEY_ID")

# If you are running locally, this is likely http://127.0.0.1:5000/api
# If deployed on Vercel, use your Vercel URL
API_URL = os.environ.get("BACKEND_API_URL", "http://127.0.0.1:5000/api")

st.set_page_config(page_title="Razorpay Integration Test", layout="centered")

# --- UI ---
st.title("💳 Payment Gateway (Python-only)")

if not RAZORPAY_KEY_ID:
    st.error("Error: RAZORPAY_KEY_ID not found in environment variables.")
    st.stop()

amount = st.number_input("Transaction Amount (INR)", min_value=1.0, value=1.0)
email = st.text_input("Customer Email", "test@example.com")

if st.button("Initialize Payment"):
    try:
        # 1. Call your Flask Backend
        payload = {"amount": int(amount * 100)} 
        response = requests.post(f"{API_URL}/create-order", json=payload)
        
        if response.status_code == 200:
            order_data = response.json()
            order_id = order_data['id']
            
            # Generate a unique ID for this specific script execution
            unique_id = str(uuid.uuid4())[:8]
            
            checkout_js = f"""
            <div id="razorpay-trigger-{unique_id}" style="width:100%;height:100%;">
                <script src="https://checkout.razorpay.com/v1/checkout.js"></script>
                <script>
                    function shrinkIframe() {{
                        try {{
                            var iframe = window.frameElement;
                            if (iframe) {{
                                iframe.style.height = '90px';
                                iframe.style.minHeight = '90px';
                            }}
                        }} catch (e) {{
                            console.warn('Could not resize parent iframe', e);
                        }}
                    }}

                    function finish(status, message) {{
                        document.body.innerHTML = '<div style="padding:12px;font-family:sans-serif;font-size:14px;line-height:1.4;">'
                            + '<strong>' + status + '</strong><div>' + message + '</div></div>';
                        shrinkIframe();
                    }}

                    (function() {{
                        var options = {{
                            "key": "{RAZORPAY_KEY_ID}",
                            "amount": {order_data['amount']},
                            "currency": "INR",
                            "name": "Integration Demo",
                            "description": "Transaction ID: {unique_id}",
                            "order_id": "{order_id}",
                            "handler": function (response) {{
                                fetch('{API_URL}/verify-payment', {{
                                    method: 'POST',
                                    headers: {{ 'Content-Type': 'application/json' }},
                                    body: JSON.stringify(response)
                                }})
                                .then(res => res.json())
                                .then(data => {{
                                    finish('Payment Verified', data.status || 'Verified');
                                }})
                                .catch(err => {{
                                    finish('Verification Error', err.message || err);
                                }});
                            }},
                            "prefill": {{ "email": "{email}" }},
                            "theme": {{ "color": "#3399cc" }}
                        }};
                        var rzp1 = new Razorpay(options);
                        rzp1.on('payment.failed', function (response) {{
                            finish('Payment Failed', response.error.description || 'Payment failed.');
                        }});
                        rzp1.open();
                    }})();
                </script>
            </div>
            """
            # Use a larger height so the iframe has space to load scripts reliably
            components.html(checkout_js, height=400)
            st.success(f"Order {order_id} created. If the modal didn't open, check your browser's popup blocker!")
            
        else:
            st.error(f"Backend Error: {response.text}")
            
    except Exception as e:
        st.error(f"Could not connect to Flask backend: {e}")


st.info("Ensure your Flask backend is running on Port 5000 before clicking.")