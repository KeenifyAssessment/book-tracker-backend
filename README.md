
# 📚 Book Tracker API (FastAPI + Supabase)

This is the **backend** service for the Book Tracker SaaS application, built with **FastAPI** and integrated with **Supabase** for database and authentication.

---

## 🌐 Overview

- 🔐 JWT-based authentication with Supabase
- 📖 CRUD operations for personal book management
- 📊 Book status tracking (Reading, Completed, Wishlist)
- 🧼 Supabase Row Level Security (RLS) to protect user data

---

## 🛠 Tech Stack

- **FastAPI**
- **Python 3.9+**
- **Supabase (PostgreSQL + Auth)**
- **Uvicorn** for development server
- **python-dotenv** for environment variable management

---

## 📁 Project Structure

book-tracker-backend/
├── main.py # FastAPI app entry point
├── .env # Environment variables (not committed)
├── requirements.txt # Python dependencies
└── README.md # You are here


---

## ⚙️ Environment Setup

### 🔐 .env File

Create a `.env` file in the root directory:

SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_anon_public_key
SUPABASE_JWT_SECRET=your_jwt_secret

---

## 📦 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/book-tracker-backend.git
cd book-tracker-backend

2. Create a Virtual Environment

python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

3. Install Dependencies

pip install -r requirements.txt

🚀 Run the Server (Dev)

uvicorn main:app 

The API will be available at:
👉 http://localhost:8000
🧪 API Endpoints
Method	Endpoint	Description
GET	/	Health check
POST	/books	Add new book
GET	/books	Get all books (filter optional)
PATCH	/books/{id}	Update book status
DELETE	/books/{id}	Delete a book

    All endpoints (except /) require a valid JWT token in the Authorization header.

🧾 Supabase SQL Setup

In your Supabase SQL Editor, run:

create table books (
  id uuid primary key default uuid_generate_v4(),
  user_id uuid references auth.users(id) on delete cascade,
  title text not null,
  author text not null,
  status text check (status in ('reading', 'completed', 'wishlist')) default 'reading',
  created_at timestamptz default now()
);


create policy "Users can view own books" on books for select using (auth.uid() = user_id);
create policy "Users can insert own books" on books for insert with check (auth.uid() = user_id);
create policy "Users can update own books" on books for update using (auth.uid() = user_id);
create policy "Users can delete own books" on books for delete using (auth.uid() = user_id);

🧑‍💻 Development Tips

    Make sure to pass the Authorization: Bearer <token> header in requests.

    Use Supabase’s JWT playground to debug token issues.

🚀 Deployment 

    Push your code to GitHub

    Create a new project in railways

    Set:

        Build Command: pip install -r requirements.txt

        Start Command: uvicorn main:app --host 0.0.0.0 --port $PORT

    Add your environment variables from .env into Render’s dashboard

    Deploy and test your endpoint URL

🔒 Security Highlights

    JWT token verification

    Supabase RLS: users can only access their own data

    No hardcoded secrets (use .env)

    Input validation via Pydantic

📝 License

This project was developed as part of the Keenify technical assessment. Not intended for commercial use.
