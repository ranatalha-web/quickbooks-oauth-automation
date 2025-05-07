# QuickBooks OAuth 2.0 Automation

A comprehensive QuickBooks OAuth 2.0 automation tool that simplifies the authentication process through web scraping and dynamic token generation.

## Features

- Complete QuickBooks OAuth 2.0 flow implementation
- No hardcoded authorization codes, access tokens, or refresh tokens
- Web interface for easy OAuth flow demonstration
- Detailed step-by-step guidance through the OAuth process
- Automatic extraction of authorization codes from redirect URLs
- Token exchange and refresh functionality
- API call capabilities with valid credentials

## Getting Started

### Prerequisites

- Python 3.6 or higher
- Required packages: flask, requests, trafilatura

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/quickbooks-oauth.git
cd quickbooks-oauth
```

2. Install the dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python main.py
```

4. Open your browser and navigate to:
```
http://localhost:5000
```

## Usage

1. Enter your QuickBooks developer application credentials:
   - Client ID
   - Client Secret
   - Redirect URI

2. Click "Generate Authorization URL" to get an authorization URL

3. Open the authorization URL in your browser and complete the authorization process

4. Copy the redirect URL after authorization and paste it into the application

5. The application will extract the authorization code and show you how to use it for token exchange

## Deployment

This project is ready for deployment on platforms like Vercel. See the deployment section for details on how to deploy.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- QuickBooks Developer API documentation
- Flask documentation
- Trafilatura library