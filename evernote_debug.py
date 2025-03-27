# test_evernote_environments.py
import sys
import logging
from evernote.api.client import EvernoteClient
import inspect

# Add compatibility for newer Python versions
if not hasattr(inspect, 'getargspec'):
    inspect.getargspec = inspect.getfullargspec

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("evernote_test")

def test_environment(auth_token, sandbox):
    """Test connection to a specific Evernote environment."""
    try:
        logger.info(f"Testing Evernote connection (sandbox={sandbox})")
        
        # Create client
        client = EvernoteClient(token=auth_token, sandbox=False)
        
        # Try to get user store
        user_store = client.get_user_store()
        user = user_store.getUser()
        logger.info(f"Connected as user: {user.username}")
        
        # Try to get note store
        note_store = client.get_note_store()
        notebooks = note_store.listNotebooks()
        logger.info(f"Found {len(notebooks)} notebooks")
        
        logger.info(f"✅ SUCCESS: Connected to {'sandbox' if sandbox else 'production'} environment!")
        return True
    
    except Exception as e:
        logger.error(f"❌ ERROR: Could not connect to {'sandbox' if sandbox else 'production'}: {str(e)}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_evernote_environments.py YOUR_AUTH_TOKEN")
        sys.exit(1)
    
    token = sys.argv[1]
    
    logger.info("Testing Evernote API environments...")
    
    # Test both environments
    prod_success = test_environment(token, sandbox=False)
    sandbox_success = test_environment(token, sandbox=True)
    
    # Summary
    logger.info("\n===== RESULTS =====")
    logger.info(f"Production environment: {'✅ SUCCESS' if prod_success else '❌ FAILURE'}")
    logger.info(f"Sandbox environment: {'✅ SUCCESS' if sandbox_success else '❌ FAILURE'}")
    
    if prod_success:
        logger.info("\nYou should use sandbox=false in your config")
    elif sandbox_success:
        logger.info("\nYou should use sandbox=true in your config")
    else:
        logger.info("\nNeither environment worked. Try generating a new token at https://dev.evernote.com/")