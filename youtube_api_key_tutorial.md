# How to Get and Use a YouTube API Key

This guide walks you through creating a YouTube Data API key using the Google Cloud Console and configuring it securely for your project.

---

## 1. Create a Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/).
2. Sign in with your Google account.
3. At the top-left, open the **project selector** → click **New Project**.
4. Give your project a name and click **Create**.

---

## 2. Enable the YouTube Data API
1. In the left menu, go to **APIs & Services → Library**.
2. Search for **YouTube Data API v3**.
3. Click it and select **Enable**.

---

## 3. Create an API Key
1. Go to **APIs & Services → Credentials**.
2. Click **Create Credentials → API Key**.
3. A pop-up will display your new API key. Copy it.

---

## 4. Restrict Your API Key (Recommended)
To prevent unauthorized use:
1. In the **Credentials** page, click your key name.
2. Under **Application restrictions**, choose one:
   - **HTTP referrers (websites)** → for web apps.
   - **IP addresses** → for backend servers.
   - **Android/iOS apps** → for mobile.
3. Under **API restrictions**, select **YouTube Data API v3**.
4. Save your changes.

---

## 5. Test Your API Key with Python
You can test the API key using the `googleapiclient` package in Python:

```python
from googleapiclient.discovery import build

# Replace with your API key
api_key = "YOUR_API_KEY"

# Build the YouTube client
youtube = build("youtube", "v3", developerKey=api_key)

# Make a simple search request
request = youtube.search().list(
    part="snippet",
    q="cats",
    maxResults=5
)
response = request.execute()

print(response)
```

This will print out JSON search results from YouTube.

---

## 6. Quotas & Limits
- Each project has **10,000 units per day** by default.
- Different API requests cost different units (e.g., a `search.list` request costs 100 units).
- You can monitor usage in **APIs & Services → Quotas**.

---

## 7. Pricing
- The YouTube Data API is **completely free to use** within the quota limits.
- There are no charges for API requests.
- You only need to manage quota usage (and optionally request more if your project requires higher limits).

---

## Best Practices
- Never expose unrestricted keys in public repos.
- Rotate keys periodically.
- Use `.env` files for local development.
- Always restrict keys by application and API.

---

✅ Now you’re ready to start using the YouTube Data API in your project!

