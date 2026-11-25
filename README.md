# Smart Kisan (سمارٹ کسان) – Streamlit version

Urdu-first advisory web app for cotton farmers in Pakistan. Final year project.
Runs in any phone browser.

## Features
- Urdu right-to-left UI, large text, voice button (browser speech; needs an Urdu voice on the device)
- District and sowing date saved in the page link (bookmark it)
- 7-day weather forecast with rain alert (Open-Meteo, no API key)
- Crop calendar that follows the sowing date
- Mandi rates, edited from a password-protected Admin tab
- Pest/disease photo tab (model is a phase 2 placeholder)

## Important: verify the content
The crop calendar in app.py (STAGES) is generic placeholder text. Replace it with
recommendations from CCRI Multan, PCCC or your provincial agriculture department.
Do not add spray or fertilizer doses without an official source.
Mandi rates are empty on purpose, so no made-up prices reach farmers.

## Run locally
    pip install -r requirements.txt
    streamlit run app.py

## Admin password
Create .streamlit/secrets.toml (it is git-ignored):

    ADMIN_PASSWORD = "choose-a-strong-password"

Or set the ADMIN_PASSWORD environment variable.

## Push to GitHub
    git init
    git add .
    git commit -m "Initial commit: Smart Kisan Streamlit app"
    git branch -M main
    git remote add origin https://github.com/<your-username>/smart-kisan.git
    git push -u origin main

## Deploy free
1. Go to share.streamlit.io and sign in with GitHub.
2. Choose the repo, branch main, main file app.py.
3. Under Advanced settings > Secrets add: ADMIN_PASSWORD = "your-password"

Note: on Streamlit Community Cloud, changes saved from the Admin tab are lost when
the app restarts or redeploys. For permanent data, move the rates to Google Sheets
or Firebase (roadmap).

## Roadmap
- [ ] Verify and complete calendar content with official sources
- [ ] Permanent storage for mandi rates (Google Sheets / Firebase)
- [ ] Pest/disease model (Keras or TFLite) in the Pest tab
- [ ] Test with 15 to 20 farmers (SUS questionnaire)
