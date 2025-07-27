# Dum Social Agent Implementation Plan

## Implementation Details

### Access Information
- **Supabase URL**: `https://ubxmvvgtbsiimnrvkago.supabase.co`
- **Google Cloud**: Vertex AI credentials (see setup instructions below)
- **Pinecone**: API key available (to be added to environment configuration)

### Design Requirements
- **Primary Brand Color**: #301781
- **UI Framework**: Shadcn UI
- **Assets**: Logo and reference images available

### Deployment Target
- Vercel or Heroku (to be determined based on optimal configuration)

## Project Overview
The goal is to refactor and enhance the forked Valbows/dumsocialagent repository, transforming it from a general-purpose agent into a specialized Social Media Management Agent. This plan outlines the sequential steps to implement a new brand identity, custom authentication, a tiered subscription model, advanced AI-driven content generation workflows, and robust production infrastructure.

## Phase 1: Foundation, Branding & Authentication ✅ COMPLETED
**Objective**: Establish a stable, branded baseline of the application with a custom user authentication flow.

**Status**: ✅ **COMPLETED** - All steps implemented and tested successfully
- ✅ Project setup and environment configuration
- ✅ Google Cloud Vertex AI setup instructions documented
- ✅ Dum Social branding fully integrated (logo, colors, typography)
- ✅ PIN-based authentication system implemented
- ✅ Frontend login/recovery pages with branded UI
- ✅ Backend authentication API with security features
- ✅ Demo environment running and tested

### Step 1: Initial Project Setup
- Clone your forked repository: `git clone https://github.com/Valbows/dumsocialagent.git`
- Run the setup wizard `python setup.py` to configure the baseline Suna environment.

#### Google Cloud & Vertex AI Setup:
1. Set the existing Google Cloud Project as active:
   ```bash
   gcloud config set project dum-social-ai-agent
   ```

2. Enable the Vertex AI API:
   ```bash
   gcloud services enable aiplatform.googleapis.com
   ```

3. Create a Service Account with Vertex AI permissions:
   ```bash
   gcloud iam service-accounts create dum-social-vertex \
     --display-name="Dum Social Vertex AI Service Account"
   
   gcloud projects add-iam-policy-binding dum-social-ai-agent \
     --member="serviceAccount:dum-social-vertex@dum-social-ai-agent.iam.gserviceaccount.com" \
     --role="roles/aiplatform.user"
   ```

4. Download the Service Account Key:
   ```bash
   gcloud iam service-accounts keys create ./dum-social-vertex-key.json \
     --iam-account=dum-social-vertex@dum-social-ai-agent.iam.gserviceaccount.com
   ```

5. Update the backend/.env file with your Google Cloud credentials:
   ```
   GOOGLE_APPLICATION_CREDENTIALS=/path/to/dum-social-vertex-key.json
   GCP_PROJECT_ID=dum-social-ai-agent
   GCP_LOCATION=us-central1  # or your preferred region
   SUPABASE_URL=https://ubxmvvgtbsiimnrvkago.supabase.co
   ```

### Step 2: Apply "Dum Social" Branding
- Logo: Place the DumSocial_logo.svg file into frontend/public/ and update the logo component (e.g., frontend/components/layout/Navbar.tsx) to reference it.
- Colors & Fonts: 
  - Set primary brand color to #301781 in the Shadcn UI theme configuration
  - Modify the global stylesheet (frontend/styles/globals.css or tailwind.config.js) to include the brand's primary color, secondary gradient, and the 'Playfair Display' font from Google Fonts
- UI Framework: Implement Shadcn UI components throughout the application

### Step 3: Implement Custom PIN Authentication with Email Recovery
- Database Schema: In your Supabase SQL Editor, create the authorized_users table to store pre-loaded user data and hashed PINs. The Admin will manually populate this table.
```sql
CREATE TABLE public.authorized_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    name TEXT,
    pin_hash TEXT NOT NULL,
    user_id UUID REFERENCES auth.users(id) NULL,
    reset_token TEXT NULL,
    reset_token_expires TIMESTAMPTZ NULL,
    created_at TIMESTAMPTZ WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);
```
- Backend API: 
  - Create a new endpoint `/api/v1/auth/pin-login` that validates the user's email and PIN against the authorized_users table and returns Supabase session tokens
  - Create a backup authentication endpoint `/api/v1/auth/email-reset` that sends a PIN reset email with a temporary token
  - Implement rate limiting on authentication endpoints to prevent brute force attacks
  - Use bcrypt for secure PIN hashing
- Frontend UI: 
  - Modify the login page to include Email/PIN login form
  - Add a "Forgot PIN" option that triggers the email-based recovery flow
  - Implement a PIN reset form accessed via email token

## Phase 2: Core Intelligence & Strategy (RAG)
**Objective**: Build the agent's "brain" by enabling it to create, store, and use a foundational strategy document for all content generation.

### Step 1: Strategy Document Generation
- Backend Tool: In a new file backend/agents/tools/strategy_tools.py, define a tool generate_strategy_document(prompt: str) that uses an LLM to generate a comprehensive social media strategy in Markdown.
- Backend API: Create a FastAPI endpoint /api/v1/strategy/generate that runs the generate_strategy_document tool.
- Frontend UI: Create a new page (frontend/app/strategy/page.tsx) where users can input their business goals to trigger the strategy generation.

### Step 2: PDF Conversion and Storage
- Dependencies: Add a PDF library like reportlab to backend/requirements.txt.
- Backend Tool: In strategy_tools.py, add a tool convert_markdown_to_pdf(markdown_text: str, user_id: str) that converts the generated Markdown into a PDF and uploads it to a user-specific folder in Supabase Storage.

### Step 3: Implement RAG with Pinecone
- Prerequisites: Add pinecone-client to backend/requirements.txt and configure Pinecone API keys in .env.
- Vector Store Service: Create backend/services/vector_store.py to manage all Pinecone interactions, including index creation, PDF text extraction, embedding (using a model like text-embedding-3-small), and querying.
- Agent Integration: Modify the core agent logic to call vector_store.query_strategy() before any content generation. The retrieved text chunks must be injected into the LLM prompt to ensure all content aligns with the user's strategy.
- Frontend UI: Add an "Embed Strategy as Reference" button on the strategy page to trigger the embedding process.

## Phase 3: Multimedia Content Workflow
**Objective**: Develop the core content creation capabilities, integrating the specified AI models and enabling various export and upload options.

### Step 1: Implement Multimedia Generation Service
- Dependencies: Add google-cloud-aiplatform to backend/requirements.txt.
- Modify Service (backend/services/media_generation.py):
  - Ensure the generate_image function is explicitly configured to use the gpt-4o model.
  - Create a new generate_video_vertex_ai function that uses the Vertex AI SDK to call the Veo-3 model.
- Agent Tool: In backend/agents/tools/content_creation_tools.py, modify the create_media_asset tool to call the correct generation function based on an asset_type parameter ('image' or 'video').

### Step 2: Enable User Media Uploads
- Frontend UI: Add a media upload component (e.g., react-dropzone) to the content creation page, allowing users to upload files directly to their Supabase Storage folder.
- Agent Tool: Create a list_user_uploads(user_id: str) tool so the agent can see and use files the user has provided.

### Step 3: Implement CSV Export for Schedulers
- Configuration: Define the standard CSV header format in a config file (e.g., backend/core/config.py).
- Agent Tool: Create a generate_content_csv(posts: list[dict]) tool that creates a CSV file in memory from a list of generated post objects.
- Backend API: Create a /api/v1/content/download_csv endpoint that returns the generated CSV file as a downloadable attachment.

## Phase 4: Tiered System, Billing & Admin Controls
**Objective**: Build the complete infrastructure for the tiered subscription model, including usage tracking, limit enforcement, and an admin management dashboard.

### Step 1: Define Data Architecture for Tiers
- Database Schema: In Supabase, create the necessary tables:
  - packages: Defines the tiers ("Bronze", "Silver", etc.) and their respective limits (storage, searches, images, videos).
  - user_packages: Links each user to their assigned package.
  - usage_logs: Records every single billable action (llm_text, image_gen, etc.) with its associated cost in units.

### Step 2: Build the Admin Dashboard
- Backend API: Create backend/api/v1/admin.py with role-protected endpoints to list all users and assign a package_id to a user_id.
- Frontend UI: Create a secure admin route (frontend/app/admin/page.tsx) where an admin can view all users and use a dropdown menu to assign them to a subscription package.

### Step 3: Implement Usage Tracking and Enforcement
- Usage Service: Create backend/services/usage_tracker.py with two key functions:
  - check_limits(user_id, action_type): Checks if a user has exceeded their monthly limit for an action before it runs.
  - log_action(...): Records the action in usage_logs after it successfully completes.
- Decorator Implementation: Create a Python decorator (@track_usage) that wraps the agent tools. This decorator will automatically call check_limits before the tool runs and log_action after, making enforcement clean and scalable.
- Apply Decorator: Apply the @track_usage decorator to all cost-incurring tools, such as create_media_asset, LLM calls, and web searches.

## Phase 5: Advanced Agent Intelligence & Workflow
**Objective**: Make the agent smarter and more autonomous by implementing a multi-agent workflow and defining its core "personality" through prompt engineering.

### Step 1: Implement the "Agent Crew" Workflow
- Orchestration: Use QStash to chain agent tasks asynchronously. A user request to /api/v1/content/generate-post will trigger the workflow.
- Research Agent: The first task scrapes for trending topics and keywords relevant to the user's strategy.
- Content Agent: The second task takes the user's prompt, the research findings, and the RAG context to write the post copy and generate the media asset.
- Database: Create the central social_posts table to store all generated content, its status (researching, writing, draft), media URLs, and other metadata.

### Step 2: Engineer Agent Prompts
- Research Agent Prompt: Create a system prompt in backend/agents/prompts/researcher.txt that instructs the agent to act as a Research Analyst and return a structured JSON object of its findings.
- Content Writing Agent Prompt: Create a system prompt in backend/agents/prompts/writer.txt that defines the 'Dum Social' persona. It will take the RAG context and research findings as input and must produce a final JSON object containing the complete post.

### Step 3: Implement System Resilience & Real-Time Updates
- Error Handling: Use QStash failure callbacks to catch errors in the agent workflow, update the post status to failed, and log the error message in the social_posts table.
- Real-Time UI: Use the Supabase real-time subscription feature on the frontend to listen for changes to the social_posts table. This will allow the UI to update automatically as a post moves from generating to draft without a page refresh.
- In-App Notifications: Implement toast notifications for important events (post completion, failures) within the application UI, reducing the need for external webhook notifications until needed for third-party integrations

## Phase 6: User Experience & External Integrations
**Objective**: Refine the user journey from a functional tool to an intuitive platform and expand its capabilities by connecting to external services like Google Drive.

### Step 1: Develop a Centralized User Dashboard & Onboarding
- Dashboard UI: Create a primary dashboard page (frontend/app/dashboard/page.tsx) with widgets for recent posts, quick actions, and usage overview.
- Onboarding Tour: Use a library like react-joyride to create an interactive tour for new users that guides them through the key first steps: creating a strategy and generating their first post.
- In-App Notifications: Use a library like react-hot-toast to provide immediate feedback for events like "Post ready for review" or "Generation failed."

### Step 2: Implement a User Feedback Mechanism
- Database: Add a user_rating column (e.g., 1 for good, -1 for bad) to the social_posts table.
- UI/API: Add "thumbs up/down" icons to each post card that call a new /api/v1/posts/{post_id}/rate endpoint. This feedback is crucial for future AI model fine-tuning.

### Step 3: Integrate with Google Drive
- OAuth Flow: In a new service (backend/services/google_drive.py), handle the complete OAuth 2.0 flow for the Google Drive API. Store user tokens securely encrypted in the database.
- Agent Tools: Create tools like list_drive_files and download_drive_file that use the stored user tokens to interact with their Google Drive.
- Frontend UI: Add a "Connect Google Drive" button in the user settings to initiate the connection.

## Phase 7: Production Readiness, Security & Scalability
**Objective**: Prepare the application for a public launch by hardening security, optimizing for performance, and establishing robust operational procedures.

### Step 1: Harden Application Security
- Row Level Security (RLS): Implement and enable RLS policies on ALL tables containing user-specific data (e.g., social_posts, strategies, usage_logs). A user must only be able to access their own data.
- Secrets Management: Use the hosting provider's secrets manager (Vercel/Heroku) for production API keys and credentials instead of .env files.
- Role-Based Access Control: Ensure all admin-level API endpoints are protected by a role check that verifies the user is an administrator.
- Authentication Security: 
  - Implement proper JWT token validation for all API endpoints
  - Configure secure storage of all third-party API keys (Google Cloud, Pinecone, etc.)
  - Add rate limiting on authentication endpoints

### Step 2: Optimize for Scalability
- Database Indexing: Add indexes to frequently queried columns in the database, especially foreign keys (user_id, package_id) and columns used in WHERE clauses (status, created_at).
- Data Archiving: Design a scheduled task to periodically archive old usage_logs to a separate table or file storage to keep the primary operational table lean and fast.

### Step 3: Establish CI/CD and Monitoring
- CI/CD Pipeline: Set up GitHub Actions to automatically run linters and tests on every push, and to build and deploy Docker containers to your hosting platform on merges to the main branch.
- Logging & Monitoring: Integrate a service like Sentry or Datadog to capture all backend and frontend errors, and set up uptime monitoring to get alerts if the application goes down.

## Phase 8: Go-Live Preparations & Launch
**Objective**: Complete all final checks and procedures for a smooth and successful launch.

### Step 1: Final Configuration and Setup
- Admin Onboarding: Manually assign the 'admin' role to your primary user account in Supabase. Use the admin dashboard to create the initial subscription packages in the packages table.
- Production Environment: Double-check that all production environment variables are correctly set in your secrets manager and that all webhook URLs (QStash, Stripe) point to your production domain.
- Database State: Run all database migrations on the production database. Pre-load the initial set of customers into the authorized_users table.

### Step 2: Final Testing and Verification
- End-to-End Testing: Perform a full, manual run-through of the user journey with a non-admin test account: from PIN login, to strategy creation, to content generation, to checking usage meters.
- Backup Verification: Confirm that automated database backups are active in your Supabase project.

### Step 3: Launch
- Deploy the final version of the main branch to production on Vercel or Heroku (based on final determination).
- Closely monitor the logging and analytics dashboards for any errors or unusual activity.
- Be prepared to gather user feedback and iterate quickly on any issues that arise.

## Implementation Roadmap

Based on the established plan and your requirements, here's a proposed timeline for implementation:

1. **Week 1: Foundation & Authentication**
   - Project setup and configuration
   - Brand implementation and UI foundation
   - PIN authentication with email recovery

2. **Week 2: Core Intelligence & RAG**
   - Strategy document generation and storage
   - Pinecone integration for vector database
   - RAG implementation and testing

3. **Week 3: Content Generation & Management**
   - Multimedia generation with Vertex AI
   - Content workflow and export capabilities
   - User upload functionality

4. **Week 4: Tiered System & Admin Controls**
   - Subscription model implementation
   - Usage tracking and enforcement
   - Admin dashboard

5. **Week 5: Advanced Intelligence & Testing**
   - Multi-agent workflow implementation
   - Error handling and system resilience
   - Comprehensive testing and bug fixes

6. **Week 6: Production Readiness & Launch**
   - Security hardening and performance optimization
   - Final testing and validation
   - Deployment to production
