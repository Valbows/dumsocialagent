#!/usr/bin/env python3
"""
Admin script to add authorized users to Dum Social Agent
Usage: python add_authorized_user.py <email> <name> <pin>
"""

import sys
import os
import asyncio
from pathlib import Path

# Add the parent directory to the path so we can import from auth module
sys.path.append(str(Path(__file__).parent.parent))

from auth.pin_auth import PinAuthService

async def add_user(email: str, name: str, pin: str):
    """Add a new authorized user"""
    try:
        auth_service = PinAuthService()
        result = auth_service.add_authorized_user(email, name, pin)
        
        if result['success']:
            print(f"✅ Successfully added user: {email}")
            print(f"   Name: {name}")
            print(f"   PIN: {'*' * len(pin)}")
        else:
            print(f"❌ Failed to add user: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

def main():
    if len(sys.argv) != 4:
        print("Usage: python add_authorized_user.py <email> <name> <pin>")
        print("Example: python add_authorized_user.py user@example.com 'John Doe' 1234")
        sys.exit(1)
    
    email = sys.argv[1]
    name = sys.argv[2]
    pin = sys.argv[3]
    
    # Validate PIN format
    if not pin.isdigit() or len(pin) < 4 or len(pin) > 6:
        print("❌ PIN must be 4-6 digits")
        sys.exit(1)
    
    # Validate email format (basic check)
    if '@' not in email or '.' not in email:
        print("❌ Invalid email format")
        sys.exit(1)
    
    print(f"Adding authorized user:")
    print(f"  Email: {email}")
    print(f"  Name: {name}")
    print(f"  PIN: {'*' * len(pin)}")
    print()
    
    # Run the async function
    asyncio.run(add_user(email, name, pin))

if __name__ == "__main__":
    main()
