-- Create authorized_users table for PIN-based authentication
CREATE TABLE IF NOT EXISTS public.authorized_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    name TEXT,
    pin_hash TEXT NOT NULL,
    user_id UUID REFERENCES auth.users(id) NULL,
    reset_token TEXT NULL,
    reset_token_expires TIMESTAMPTZ NULL,
    created_at TIMESTAMPTZ WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMPTZ WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Create RLS policies for authorized_users table
ALTER TABLE public.authorized_users ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see their own record
CREATE POLICY "Users can view own authorized_user record" ON public.authorized_users
    FOR SELECT USING (auth.uid() = user_id);

-- Policy: Users can update their own record (for PIN resets)
CREATE POLICY "Users can update own authorized_user record" ON public.authorized_users
    FOR UPDATE USING (auth.uid() = user_id);

-- Create indexes for performance
CREATE INDEX idx_authorized_users_email ON public.authorized_users(email);
CREATE INDEX idx_authorized_users_user_id ON public.authorized_users(user_id);
CREATE INDEX idx_authorized_users_reset_token ON public.authorized_users(reset_token);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = timezone('utc'::text, now());
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger to automatically update updated_at
CREATE TRIGGER update_authorized_users_updated_at 
    BEFORE UPDATE ON public.authorized_users 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
