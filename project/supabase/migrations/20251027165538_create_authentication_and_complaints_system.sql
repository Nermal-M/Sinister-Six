/*
  # Create Authentication and Complaints Management System

  1. New Tables
    - `profiles`
      - `id` (uuid, primary key, references auth.users)
      - `email` (text, unique, not null)
      - `full_name` (text)
      - `phone` (text)
      - `created_at` (timestamptz, default now())
      - `updated_at` (timestamptz, default now())
    
    - `officials`
      - `id` (uuid, primary key, references auth.users)
      - `email` (text, unique, not null)
      - `full_name` (text, not null)
      - `department` (text)
      - `created_at` (timestamptz, default now())
      - `updated_at` (timestamptz, default now())
    
    - `complaints`
      - `id` (uuid, primary key)
      - `user_id` (uuid, references profiles, not null)
      - `title` (text, not null)
      - `description` (text, not null)
      - `category` (text, not null)
      - `status` (text, default 'pending')
      - `priority` (text, default 'normal')
      - `created_at` (timestamptz, default now())
      - `updated_at` (timestamptz, default now())

  2. Security
    - Enable RLS on all tables
    - Add policies for users to manage their own profiles
    - Add policies for users to create and view their own complaints
    - Add policies for officials to view and manage all complaints
*/

-- Create profiles table for regular users
CREATE TABLE IF NOT EXISTS profiles (
  id uuid PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  email text UNIQUE NOT NULL,
  full_name text,
  phone text,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;

-- Create officials table
CREATE TABLE IF NOT EXISTS officials (
  id uuid PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  email text UNIQUE NOT NULL,
  full_name text NOT NULL,
  department text,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

ALTER TABLE officials ENABLE ROW LEVEL SECURITY;

-- Create complaints table
CREATE TABLE IF NOT EXISTS complaints (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid REFERENCES profiles(id) ON DELETE CASCADE NOT NULL,
  title text NOT NULL,
  description text NOT NULL,
  category text NOT NULL,
  status text DEFAULT 'pending',
  priority text DEFAULT 'normal',
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

ALTER TABLE complaints ENABLE ROW LEVEL SECURITY;

-- Profiles policies
CREATE POLICY "Users can view own profile"
  ON profiles FOR SELECT
  TO authenticated
  USING (auth.uid() = id);

CREATE POLICY "Users can insert own profile"
  ON profiles FOR INSERT
  TO authenticated
  WITH CHECK (auth.uid() = id);

CREATE POLICY "Users can update own profile"
  ON profiles FOR UPDATE
  TO authenticated
  USING (auth.uid() = id)
  WITH CHECK (auth.uid() = id);

-- Officials policies
CREATE POLICY "Officials can view own profile"
  ON officials FOR SELECT
  TO authenticated
  USING (auth.uid() = id);

CREATE POLICY "Officials can insert own profile"
  ON officials FOR INSERT
  TO authenticated
  WITH CHECK (auth.uid() = id);

CREATE POLICY "Officials can update own profile"
  ON officials FOR UPDATE
  TO authenticated
  USING (auth.uid() = id)
  WITH CHECK (auth.uid() = id);

-- Complaints policies for users
CREATE POLICY "Users can view own complaints"
  ON complaints FOR SELECT
  TO authenticated
  USING (user_id IN (SELECT id FROM profiles WHERE id = auth.uid()));

CREATE POLICY "Users can create complaints"
  ON complaints FOR INSERT
  TO authenticated
  WITH CHECK (user_id IN (SELECT id FROM profiles WHERE id = auth.uid()));

CREATE POLICY "Users can update own complaints"
  ON complaints FOR UPDATE
  TO authenticated
  USING (user_id IN (SELECT id FROM profiles WHERE id = auth.uid()))
  WITH CHECK (user_id IN (SELECT id FROM profiles WHERE id = auth.uid()));

-- Complaints policies for officials
CREATE POLICY "Officials can view all complaints"
  ON complaints FOR SELECT
  TO authenticated
  USING (EXISTS (SELECT 1 FROM officials WHERE id = auth.uid()));

CREATE POLICY "Officials can update all complaints"
  ON complaints FOR UPDATE
  TO authenticated
  USING (EXISTS (SELECT 1 FROM officials WHERE id = auth.uid()))
  WITH CHECK (EXISTS (SELECT 1 FROM officials WHERE id = auth.uid()));

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_complaints_user_id ON complaints(user_id);
CREATE INDEX IF NOT EXISTS idx_complaints_status ON complaints(status);
CREATE INDEX IF NOT EXISTS idx_complaints_category ON complaints(category);
CREATE INDEX IF NOT EXISTS idx_complaints_created_at ON complaints(created_at DESC);