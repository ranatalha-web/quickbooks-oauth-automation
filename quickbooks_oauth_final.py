import os
import time
import json
import logging
import requests
import trafilatura

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class QuickBooksOAuth:
    """
    QuickBooks OAuth 2.0 Authorization Class
    
    This class handles the complete QuickBooks OAuth 2.0 authorization flow:
    1. Getting authorization URL 
    2. Capturing authorization code from redirect
    3. Exchanging code for access and refresh tokens
    4. Making API calls with token
    5. Refreshing expired access tokens
    
    No tokens are hardcoded - all are generated during the OAuth flow.
    """
    
    def __init__(self, client_id, client_secret, redirect_uri):
        """
        Initialize QuickBooks OAuth with required credentials
        
        Args:
            client_id (str): QuickBooks application client ID
            client_secret (str): QuickBooks application client secret
            redirect_uri (str): Authorized redirect URI
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.auth_code = None
        self.access_token = None
        self.refresh_token = None
        self.token_expiry = None
        self.realm_id = None
    
    def get_authorization_url(self):
        """
        Generate the authorization URL for QuickBooks OAuth
        
        Returns:
            str: Authorization URL to redirect the user to
        """
        auth_url = (
            f"https://appcenter.intuit.com/connect/oauth2"
            f"?client_id={self.client_id}"
            f"&redirect_uri={self.redirect_uri}"
            f"&response_type=code"
            f"&scope=com.intuit.quickbooks.accounting"
            f"&state=randomstate"
        )
        
        return auth_url
    
    def set_auth_code_from_redirect(self, redirect_url):
        """
        Extract authorization code and realm ID from redirect URL
        
        Args:
            redirect_url (str): The full redirect URL with query parameters
            
        Returns:
            bool: True if successful, False otherwise
        """
        logger.info(f"Processing redirect URL: {redirect_url}")
        
        if "code=" not in redirect_url:
            logger.error("Authorization code not found in redirect URL")
            return False
            
        # Extract the authorization code
        code_segment = redirect_url.split("code=")[1]
        self.auth_code = code_segment.split("&")[0] if "&" in code_segment else code_segment
        
        # Extract the realm ID if present
        if "realmId=" in redirect_url:
            realm_id_segment = redirect_url.split("realmId=")[1]
            self.realm_id = realm_id_segment.split("&")[0] if "&" in realm_id_segment else realm_id_segment
            
        logger.info(f"Successfully extracted authorization code: {self.auth_code}")
        if self.realm_id:
            logger.info(f"Successfully extracted realm ID: {self.realm_id}")
            
        return True
    
    def exchange_code_for_tokens(self):
        """
        Exchange authorization code for access and refresh tokens
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.auth_code:
            logger.error("No authorization code available to exchange for tokens")
            return False
            
        logger.info("Exchanging authorization code for tokens...")
        token_url = "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer"
        
        payload = {
            "grant_type": "authorization_code",
            "code": self.auth_code,
            "redirect_uri": self.redirect_uri
        }
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json"
        }
        
        try:
            response = requests.post(
                token_url,
                data=payload,
                headers=headers,
                auth=(self.client_id, self.client_secret)
            )
            
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data.get("access_token")
                self.refresh_token = token_data.get("refresh_token")
                self.token_expiry = int(time.time()) + token_data.get("expires_in", 3600)
                
                logger.info("Successfully obtained access and refresh tokens")
                return True
            else:
                logger.error(f"Failed to exchange code for tokens. Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error during token exchange: {str(e)}")
            return False
    
    def refresh_access_token(self):
        """
        Refresh the access token using the refresh token
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.refresh_token:
            logger.error("No refresh token available")
            return False
            
        logger.info("Refreshing access token...")
        token_url = "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer"
        
        payload = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token
        }
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json"
        }
        
        try:
            response = requests.post(
                token_url,
                data=payload,
                headers=headers,
                auth=(self.client_id, self.client_secret)
            )
            
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data.get("access_token")
                self.refresh_token = token_data.get("refresh_token")
                self.token_expiry = int(time.time()) + token_data.get("expires_in", 3600)
                
                logger.info("Successfully refreshed access token")
                return True
            else:
                logger.error(f"Failed to refresh access token. Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error during token refresh: {str(e)}")
            return False
    
    def make_api_call(self, endpoint):
        """
        Make an API call to QuickBooks API
        
        Args:
            endpoint (str): API endpoint to call
            
        Returns:
            dict: API response data
        """
        if not self.access_token or not self.realm_id:
            logger.error("Access token or Realm ID not available")
            return None
            
        # Check if token is expired and refresh if needed
        if self.token_expiry and int(time.time()) >= self.token_expiry:
            logger.info("Access token expired, refreshing...")
            if not self.refresh_access_token():
                logger.error("Failed to refresh expired token")
                return None
                
        logger.info(f"Making API call to {endpoint}")
        
        api_url = f"https://quickbooks.api.intuit.com/v3/company/{self.realm_id}/{endpoint}"
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get(api_url, headers=headers)
            
            if response.status_code == 200:
                logger.info("API call successful")
                return response.json()
            else:
                logger.error(f"API call failed. Status: {response.status_code}, Response: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error during API call: {str(e)}")
            return None
    
    def display_token_info(self):
        """Display token information in a formatted way"""
        print("\n" + "="*50)
        print("QUICKBOOKS OAUTH TOKEN INFORMATION")
        print("="*50)
        
        if self.auth_code:
            print(f"Authorization Code: {self.auth_code}")
        else:
            print("Authorization Code: Not obtained")
            
        if self.access_token:
            print(f"Access Token: {self.access_token}")
            
            # Calculate remaining time
            if self.token_expiry:
                remaining = max(0, self.token_expiry - int(time.time()))
                minutes = remaining // 60
                print(f"Access Token Expires In: {minutes} minutes")
        else:
            print("Access Token: Not obtained")
            
        if self.refresh_token:
            print(f"Refresh Token: {self.refresh_token}")
        else:
            print("Refresh Token: Not obtained")
            
        if self.realm_id:
            print(f"Realm ID: {self.realm_id}")
        else:
            print("Realm ID: Not obtained")
            
        print("="*50 + "\n")


def scrape_oauth_playground_docs():
    """
    Scrape the QuickBooks OAuth 2.0 Playground documentation
    
    Returns:
        str: Scraped content or None if failed
    """
    url = "https://developer.intuit.com/app/developer/qbo/docs/develop/authentication-and-authorization/oauth-2.0-playground"
    try:
        print(f"Scraping OAuth documentation from: {url}")
        downloaded = trafilatura.fetch_url(url)
        content = trafilatura.extract(downloaded)
        if content:
            return content
        return None
    except Exception as e:
        print(f"Error scraping website: {str(e)}")
        return None


def display_oauth_playground_info():
    """Display information about the OAuth 2.0 Playground"""
    print("\n" + "="*50)
    print("OAUTH 2.0 PLAYGROUND OVERVIEW")
    print("="*50)
    
    # Try to get the documentation via web scraping
    content = scrape_oauth_playground_docs()
    
    if content:
        print("\nSuccessfully scraped OAuth Playground documentation:")
        print("-" * 40)
        # Display a preview (first 500 characters)
        print(content[:500] + "...\n")
    else:
        # Fallback to static information
        print("""
The OAuth 2.0 Playground is a tool that helps you understand and test the
QuickBooks OAuth 2.0 authorization flow. It consists of the following steps:

Step 1: Get authorization code
Generate an authorization URL with your client ID, redirect URI, and scopes.
The user authorizes your app, and you receive an authorization code.

Step 2: Get OAuth 2.0 token from auth code
Exchange the authorization code for access and refresh tokens.

Step 3: Make API calls
Use the access token to make API calls to QuickBooks.

Step 4: Refresh access token
When the access token expires, use the refresh token to get a new one.
""")
    
    print("Full documentation available at: https://developer.intuit.com/app/developer/qbo/docs/develop/authentication-and-authorization/oauth-2.0-playground")
    print("="*50)


def demonstrate_oauth_flow():
    """Run a demonstration of the QuickBooks OAuth flow"""
    # Use example credentials (these would normally come from secure storage or user input)
    client_id = "EXAMPLE_CLIENT_ID"
    client_secret = "EXAMPLE_CLIENT_SECRET" 
    redirect_uri = "https://developer.intuit.com/v2/OAuth2Playground/RedirectUrl"
    
    # Initialize the OAuth handler
    qb_oauth = QuickBooksOAuth(client_id, client_secret, redirect_uri)
    
    # Step 1: Get Authorization URL
    auth_url = qb_oauth.get_authorization_url()
    print("\nSTEP 1: Get Authorization URL")
    print(f"Authorization URL: {auth_url}")
    print("\nIn a real implementation, you would redirect the user to this URL.")
    print("After authorization, they would be redirected back to your redirect URI.")
    
    # Step 2: Simulate receiving a redirect with authorization code
    print("\nSTEP 2: Receive Authorization Code")
    print("After the user authorizes your application, they're redirected back to your")
    print("redirect URI with an authorization code and realm ID (if they selected a company).")
    print("\nExample redirect URL:")
    sample_redirect = f"{redirect_uri}?code=AB123456789&realmId=1234567890&state=randomstate"
    print(sample_redirect)
    
    # Process the redirect URL to extract the authorization code and realm ID
    qb_oauth.set_auth_code_from_redirect(sample_redirect)
    
    # Display the current token information
    qb_oauth.display_token_info()
    
    # Step 3: Exchange authorization code for tokens
    print("\nSTEP 3: Exchange Authorization Code for Tokens")
    print("In a real implementation with valid credentials, you would exchange the")
    print("authorization code for access and refresh tokens by making a POST request")
    print("to the token endpoint with your client credentials and authorization code.")
    
    # Step 4: Make API calls
    print("\nSTEP 4: Make API Calls with Access Token")
    print("With a valid access token, you can make API calls to QuickBooks, such as:")
    print("- Get company information")
    print("- Query customers, invoices, bills, etc.")
    print("- Create or update records")
    
    # Step 5: Refresh access token
    print("\nSTEP 5: Refresh Access Token")
    print("When the access token expires (typically after 1 hour), you can use the")
    print("refresh token to get a new access token without requiring the user to")
    print("go through the authorization process again.")


def main():
    """Main function to run the QuickBooks OAuth demonstration"""
    print("\n" + "="*50)
    print("QUICKBOOKS OAUTH 2.0 AUTOMATION")
    print("="*50)
    
    print("\nThis is a complete implementation of the QuickBooks OAuth 2.0 flow.")
    print("It demonstrates the entire process from authorization to API calls")
    print("without hardcoding any authorization codes, tokens, or secrets.")
    
    # Display information about the OAuth 2.0 Playground
    display_oauth_playground_info()
    
    # Run the OAuth flow demonstration
    demonstrate_oauth_flow()
    
    print("\nIMPORTANT NOTES:")
    print("1. This demonstration shows the complete OAuth flow without making actual API calls.")
    print("2. No authorization codes, access tokens, or refresh tokens are hardcoded.")
    print("3. In a real implementation, these values are obtained dynamically through the OAuth flow.")
    print("4. To use this code with real QuickBooks accounts, replace the example credentials")
    print("   with your actual QuickBooks application credentials.")
    print("\nFor more information about QuickBooks OAuth 2.0, visit:")
    print("https://developer.intuit.com/app/developer/qbo/docs/develop/authentication-and-authorization")


if __name__ == "__main__":
    main()