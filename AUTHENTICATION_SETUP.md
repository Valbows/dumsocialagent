# Dum Social Agent - Authentication Setup Guide

This guide walks you through setting up the PIN-based authentication system for Dum Social Agent.

## Prerequisites

1. **Supabase Project**: You should have your Supabase project URL: `https://ubxmvvgtbsiimnrvkago.supabase.co`
2. **Backend Dependencies**: Ensure all Python dependencies are installed
3. **Frontend Dependencies**: Ensure all Node.js dependencies are installed

## Step 1: Database Setup

### 1.1 Run the Database Migration

Navigate to your Supabase dashboard and run the SQL migration:

```sql
-- Copy the contents of backend/supabase/migrations/001_create_authorized_users.sql
-- and run it in your Supabase SQL editor
```

Or use the Supabase CLI if you have it set up:

```bash
cd backend
supabase db push
```

### 1.2 Verify Tables

Check that the `authorized_users` table was created with these columns:
- `id` (UUID, primary key)
- `email` (TEXT, unique)
- `name` (TEXT)
- `pin_hash` (TEXT)
- `user_id` (UUID, references auth.users)
- `reset_token` (TEXT, nullable)
- `reset_token_expires` (TIMESTAMPTZ, nullable)
- `created_at` (TIMESTAMPTZ)
- `updated_at` (TIMESTAMPTZ)

## Step 2: Backend Configuration

### 2.1 Environment Variables

Copy the backend environment file and configure it:

```bash
cd backend
cp .env.example .env
```

Edit `.env` and set these required variables:

```bash
# Supabase Configuration
SUPABASE_URL=https://ubxmvvgtbsiimnrvkago.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_here

# Frontend URL (for email links)
FRONTEND_URL=http://localhost:3001

# Email Configuration (for PIN recovery)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password_here
```

### 2.2 Email Setup (Gmail Example)

1. Enable 2-factor authentication on your Gmail account
2. Generate an App Password:
   - Go to Google Account settings
   - Security → 2-Step Verification → App passwords
   - Generate a password for "Mail"
   - Use this as your `SMTP_PASSWORD`

## Step 3: Add Your First Authorized User

### 3.1 Using the Admin Script

```bash
cd backend
python scripts/add_authorized_user.py your_email@example.com "Your Name" 1234
```

### 3.2 Using the API Endpoint

```bash
curl -X POST http://localhost:8000/api/auth/add-user \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your_email@example.com",
    "name": "Your Name",
    "pin": "1234"
  }'
```

## Step 4: Start the Services

### 4.1 Start Backend

```bash
cd backend
python api.py
```

The backend will be available at: `http://localhost:8000`

### 4.2 Start Frontend

```bash
cd frontend
npm run dev
```

The frontend will be available at: `http://localhost:3001`

## Step 5: Test Authentication

1. **Access the Application**: Navigate to `http://localhost:3001`
2. **Automatic Redirect**: You should be redirected to `/auth/login`
3. **Login**: Use the email and PIN you created in Step 3
4. **Success**: You should be redirected to the main dashboard

## Authentication Flow

### Login Process
1. User enters email and PIN on `/auth/login`
2. Frontend sends POST request to `/api/auth/login`
3. Backend validates PIN against hashed version in database
4. If valid, creates/updates Supabase auth user
5. Frontend stores user session and redirects to dashboard

### PIN Recovery Process
1. User clicks "Forgot PIN" on login page
2. User enters email on `/auth/forgot-pin`
3. Frontend sends POST request to `/api/auth/request-reset`
4. Backend generates secure token and sends email
5. User clicks link in email to go to `/auth/reset-pin?token=...`
6. User enters new PIN, backend validates token and updates PIN

## Security Features

- **Rate Limiting**: 5 attempts per 5 minutes per IP/email combination
- **Secure Hashing**: PINs are hashed using bcrypt with salt
- **Token Expiry**: Reset tokens expire after 1 hour
- **Input Validation**: PIN format validation (4-6 digits)
- **CORS Protection**: Configured for specific origins only

## Troubleshooting

### Common Issues

1. **Database Connection Error**
   - Verify `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY`
   - Check that the migration was run successfully

2. **Email Not Sending**
   - Verify SMTP credentials
   - Check that Gmail App Password is correct
   - Ensure 2FA is enabled on Gmail account

3. **CORS Errors**
   - Verify frontend is running on `localhost:3001`
   - Check backend CORS configuration includes the frontend URL

4. **Authentication Redirect Loop**
   - Clear browser localStorage
   - Check that user was added to `authorized_users` table

### API Endpoints

- `POST /api/auth/login` - Authenticate with email/PIN
- `POST /api/auth/request-reset` - Request PIN reset email
- `POST /api/auth/reset-pin` - Reset PIN with token
- `POST /api/auth/add-user` - Add authorized user (admin)
- `GET /api/auth/health` - Health check

## Next Steps

Once authentication is working:

1. **Configure Google Cloud Vertex AI** (see plan.md)
2. **Set up Pinecone vector database**
3. **Implement AI strategy and social media features**
4. **Configure production deployment**

For detailed implementation roadmap, see `plan.md`.
