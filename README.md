# Investment Advisor System

A personalized investment recommendation system for beginners. This application helps users determine their risk profile through a questionnaire, generates tailored investment recommendations, and provides detailed PDF reports.

## Features

- Interactive questionnaire to determine investor risk profile
- Personalized investment recommendations across different regions and asset classes
- ESG (Environmental, Social, Governance) score integration
- AI-powered personalized explanations
- Detailed PDF report generation
- Email delivery of investment reports

## System Requirements

- Python 3.8+
- Required Python packages (see Installation section)
- Internet connection (for financial data API and AI explanations)
- Email account for sending reports (GMX email recommended based on current config)

## Installation

### Step 1: Download the code files

Create a new folder on your computer for the project. You'll need to save the following files:
- `MertCodev1.py` - The backend code for investment recommendations
- `paste-2.txt` - The Streamlit frontend application (rename this to `app.py`)

### Step 2: Create a virtual environment (recommended)

Open your command prompt or terminal, navigate to your project folder, and run:

```bash
python -m venv venv
```

Activate the virtual environment:

**Windows:**
```bash
venv\Scripts\activate
```

**macOS/Linux:**
```bash
source venv/bin/activate
```

### Step 3: Install required packages

Create a file named `requirements.txt` in your project folder with the following content:

```
yfinance>=0.2.3
streamlit>=1.22.0
pandas>=1.5.0
python-dotenv>=1.0.0
fpdf>=1.7.2
openai>=1.0.0
```

Then install all required packages by running:

```bash
pip install -r requirements.txt
```

### Step 4: Download font files

Create a folder named 'Fonts' in your project directory:

```bash
mkdir Fonts
```

Download the DejaVuSans.ttf font from [the DejaVu Fonts project](https://dejavu-fonts.github.io/) and place it in the Fonts directory.

> **Note:** On the DejaVu Fonts website, click "Download" and extract the zip file. Find the DejaVuSans.ttf file in the TTF folder and copy it to your project's Fonts directory.

## Configuration

### Step 1: Create a .env file

Create a file named `.env` in your project folder with the following variables:

```
OPENAI_API_KEY=your_openai_api_key
EMAIL_PASSWORD=your_email_password
```

You will need to:
- Replace `your_email_password` with the password for your email account
- Get an OpenRouter API key from [https://openrouter.ai/](https://openrouter.ai/) (free tier available)

### Step 2: Configure email settings

By default, the application is configured to use a GMX email account. If you want to use a different provider, open `app.py` and update the following variables:

```python
EMAIL_SENDER = "your_email@example.com"
SMTP_SERVER = "your_smtp_server"
SMTP_PORT = your_smtp_port  # Typically 587 for TLS
```

Common SMTP settings:

| Email Provider | SMTP Server | SMTP Port |
|----------------|-------------|-----------|
| Gmail | smtp.gmail.com | 587 |
| Outlook/Hotmail | smtp-mail.outlook.com | 587 |
| Yahoo | smtp.mail.yahoo.com | 587 |
| GMX | mail.gmx.net | 587 |

> **Warning:** Gmail Users: You'll need to enable "Less secure app access" or create an "App Password" if you have 2-factor authentication enabled. Visit your Google Account Security settings to set this up.

### Step 3: Configure API settings

The application uses OpenRouter for AI-generated explanations. If you want to use a different provider or model, update the API configuration in `app.py`:

```python
client = OpenAI(base_url="https://openrouter.ai/api/v1")
```

## Usage

### Running the application

1. Start the Streamlit app:
   ```bash
   streamlit run app.py
   ```

2. Access the application in your web browser (typically at http://localhost:8501)

3. Complete the questionnaire to get your investment recommendations

4. Request a detailed PDF report via email

## File Structure

```
investment-advisor/
├── app.py                  # Streamlit frontend application (renamed from paste-2.txt)
├── MertCodev1.py           # Backend code for investment recommendations
├── requirements.txt        # List of required Python packages
├── .env                    # Environment variables file
└── Fonts/
    └── DejaVuSans.ttf      # Font file for PDF generation
```

## Troubleshooting

### Email issues

If you're not receiving emails:

1. Check your spam/junk folder
2. Verify your email password in the `.env` file
3. Make sure your email provider allows sending from external applications (you may need to enable "less secure apps" or generate an app password)
4. Add debug print statements around the email sending function in `app.py`:
   ```python
   try:
       print("Attempting to send email...")
       send_email_with_pdf(st.session_state.email, filename)
       print("Email sent successfully!")
   except Exception as e:
       print(f"Email error: {str(e)}")
       st.error(f"Error sending email: {str(e)}")
   ```

### API issues

If AI explanations aren't working:

1. Check your API keys in the `.env` file
2. Make sure the keys have sufficient credits/quota
3. Try alternate models in the models list
4. Add debug print statements around the API calls:
   ```python
   try:
       print(f"Calling API with model: {model}")
       response = client.chat.completions.create(...)
       print("API response received")
   except Exception as e:
       print(f"API error: {str(e)}")
   ```

### Financial data issues

If you're getting errors with financial data:

1. Check your internet connection
2. The yfinance API might be rate-limited; add delays between requests
3. Some tickers might not be available; ensure they exist in your region
