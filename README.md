# sample-razorpay-app
shows sample razorpay integration

## Postgres transaction storage

This app now stores each created Razorpay order and payment verification result in a Postgres database.

### Setup

1. Create a Postgres database locally.

   If `createdb` is available:

   ```powershell
   createdb razorpay_db
   ```

   If you do not have `createdb` or `psql`, install Postgres for Windows:

   - Download from https://www.postgresql.org/download/windows/
   - During install, enable the command line tools
   - Then rerun the `createdb` or `psql` command above

   Alternatively, use Docker if you have Docker Desktop:

   ```powershell
   docker run --name razorpay-postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=razorpay_db -p 5432:5432 -d postgres
   ```

   If you prefer a GUI, create the database using pgAdmin or the Postgres installer management tools.

2. Set environment variables in a `.env` file or your shell.
   Use your actual Postgres credentials and do not wrap values in quotes:

   ```text
   RAZORPAY_KEY_ID=your_key_id
   RAZORPAY_KEY_SECRET=your_key_secret
   DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/razorpay_db
   BACKEND_API_URL=http://127.0.0.1:5000/api
   ```

   If your Postgres password is not `postgres`, replace it with the correct password.


3. Install dependencies:

   ```powershell
   pip install -r requirements.txt
   ```

4. Run the backend:

   ```powershell
   python api/index.py
   ```

5. Run the frontend:

   ```powershell
   streamlit run frontend.py
   ```

### Notes

- The backend will automatically create a `transactions` table in the configured Postgres database.
- Each order creation and verification call is saved in the database.
