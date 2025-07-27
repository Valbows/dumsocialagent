"""
PIN-based authentication service for Dum Social Agent
Implements secure PIN authentication with email recovery
"""

import bcrypt
import secrets
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict, Any
import os
from supabase import create_client, Client
import logging

logger = logging.getLogger(__name__)

class PinAuthService:
    def __init__(self):
        """Initialize the PIN authentication service"""
        self.supabase: Client = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        )
        
    def hash_pin(self, pin: str) -> str:
        """Hash a PIN using bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(pin.encode('utf-8'), salt).decode('utf-8')
    
    def verify_pin(self, pin: str, pin_hash: str) -> bool:
        """Verify a PIN against its hash"""
        return bcrypt.checkpw(pin.encode('utf-8'), pin_hash.encode('utf-8'))
    
    def authenticate_user(self, email: str, pin: str) -> Dict[str, Any]:
        """
        Authenticate a user with email and PIN
        Returns user data and session tokens if successful
        """
        try:
            # Get user from authorized_users table
            response = self.supabase.table('authorized_users').select('*').eq('email', email).execute()
            
            if not response.data:
                return {
                    'success': False,
                    'error': 'User not found or not authorized'
                }
            
            user_data = response.data[0]
            
            # Verify PIN
            if not self.verify_pin(pin, user_data['pin_hash']):
                return {
                    'success': False,
                    'error': 'Invalid PIN'
                }
            
            # Check if user already has a Supabase auth account
            if user_data['user_id']:
                # Get existing user session
                auth_response = self.supabase.auth.admin.get_user_by_id(user_data['user_id'])
                if auth_response.user:
                    # Generate new session
                    session_response = self.supabase.auth.admin.generate_link({
                        'type': 'magiclink',
                        'email': email
                    })
                    
                    return {
                        'success': True,
                        'user': auth_response.user,
                        'session': session_response
                    }
            
            # Create new Supabase auth user if doesn't exist
            auth_response = self.supabase.auth.admin.create_user({
                'email': email,
                'email_confirm': True,
                'user_metadata': {
                    'name': user_data['name'],
                    'auth_method': 'pin'
                }
            })
            
            if auth_response.user:
                # Update authorized_users with the new user_id
                self.supabase.table('authorized_users').update({
                    'user_id': auth_response.user.id
                }).eq('email', email).execute()
                
                return {
                    'success': True,
                    'user': auth_response.user,
                    'session': None  # Will need to generate session separately
                }
            
            return {
                'success': False,
                'error': 'Failed to create user session'
            }
            
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return {
                'success': False,
                'error': 'Authentication failed'
            }
    
    def generate_reset_token(self, email: str) -> Dict[str, Any]:
        """
        Generate a reset token for PIN recovery
        """
        try:
            # Check if user exists
            response = self.supabase.table('authorized_users').select('*').eq('email', email).execute()
            
            if not response.data:
                return {
                    'success': False,
                    'error': 'User not found'
                }
            
            # Generate secure reset token
            reset_token = secrets.token_urlsafe(32)
            expires_at = datetime.utcnow() + timedelta(hours=1)  # Token expires in 1 hour
            
            # Update user with reset token
            self.supabase.table('authorized_users').update({
                'reset_token': reset_token,
                'reset_token_expires': expires_at.isoformat()
            }).eq('email', email).execute()
            
            # Send reset email
            if self._send_reset_email(email, reset_token):
                return {
                    'success': True,
                    'message': 'Reset email sent successfully'
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to send reset email'
                }
                
        except Exception as e:
            logger.error(f"Reset token generation error: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to generate reset token'
            }
    
    def reset_pin_with_token(self, token: str, new_pin: str) -> Dict[str, Any]:
        """
        Reset PIN using a valid reset token
        """
        try:
            # Find user by reset token
            response = self.supabase.table('authorized_users').select('*').eq('reset_token', token).execute()
            
            if not response.data:
                return {
                    'success': False,
                    'error': 'Invalid reset token'
                }
            
            user_data = response.data[0]
            
            # Check if token is expired
            if user_data['reset_token_expires']:
                expires_at = datetime.fromisoformat(user_data['reset_token_expires'].replace('Z', '+00:00'))
                if datetime.utcnow().replace(tzinfo=expires_at.tzinfo) > expires_at:
                    return {
                        'success': False,
                        'error': 'Reset token has expired'
                    }
            
            # Hash new PIN
            new_pin_hash = self.hash_pin(new_pin)
            
            # Update user with new PIN and clear reset token
            self.supabase.table('authorized_users').update({
                'pin_hash': new_pin_hash,
                'reset_token': None,
                'reset_token_expires': None
            }).eq('reset_token', token).execute()
            
            return {
                'success': True,
                'message': 'PIN reset successfully'
            }
            
        except Exception as e:
            logger.error(f"PIN reset error: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to reset PIN'
            }
    
    def _send_reset_email(self, email: str, reset_token: str) -> bool:
        """
        Send PIN reset email to user
        """
        try:
            # Email configuration (you'll need to set these environment variables)
            smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
            smtp_port = int(os.getenv('SMTP_PORT', '587'))
            smtp_username = os.getenv('SMTP_USERNAME')
            smtp_password = os.getenv('SMTP_PASSWORD')
            
            if not smtp_username or not smtp_password:
                logger.error("SMTP credentials not configured")
                return False
            
            # Create reset URL
            reset_url = f"{os.getenv('FRONTEND_URL', 'http://localhost:3001')}/auth/reset-pin?token={reset_token}"
            
            # Create email content
            msg = MIMEMultipart()
            msg['From'] = smtp_username
            msg['To'] = email
            msg['Subject'] = "Dum Social - PIN Reset Request"
            
            body = f"""
            Hello,
            
            You requested to reset your PIN for Dum Social Agent.
            
            Click the link below to reset your PIN:
            {reset_url}
            
            This link will expire in 1 hour.
            
            If you didn't request this reset, please ignore this email.
            
            Best regards,
            Dum Social Team
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(smtp_username, smtp_password)
            text = msg.as_string()
            server.sendmail(smtp_username, email, text)
            server.quit()
            
            return True
            
        except Exception as e:
            logger.error(f"Email sending error: {str(e)}")
            return False
    
    def add_authorized_user(self, email: str, name: str, pin: str) -> Dict[str, Any]:
        """
        Add a new authorized user (admin function)
        """
        try:
            pin_hash = self.hash_pin(pin)
            
            response = self.supabase.table('authorized_users').insert({
                'email': email,
                'name': name,
                'pin_hash': pin_hash
            }).execute()
            
            if response.data:
                return {
                    'success': True,
                    'message': 'User added successfully'
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to add user'
                }
                
        except Exception as e:
            logger.error(f"Add user error: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to add user'
            }
