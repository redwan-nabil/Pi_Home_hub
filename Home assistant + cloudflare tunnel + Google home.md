# 🏰 Nexus Hub: The Home Assistant Architecture

A comprehensive, military-grade guide to securely exposing a local Home Assistant instance to the internet **bypassing CGNAT** (shared ISP IPs) and linking it to **Google Home** without opening any router ports.

## 🏗️ Architecture Overview

Traditional smart home setups require port-forwarding (dangerous) or static public IPs (expensive/impossible with CGNAT). This setup uses a **Split-Bridge Architecture**:

1. **The Network Bridge (Cloudflare Tunnel):** A Docker container inside your local network digs a secure, outbound-only tunnel to Cloudflare. This completely bypasses ISP firewalls and CGNAT.
2. **The Voice Bridge (Google Cloud):** We manually link the Google Developer Console directly to your secure Cloudflare endpoint, allowing voice control without monthly subscription fees.

---

## 🌍 PHASE 1: The Secure Tunnel (Bypassing the ISP)

### Prerequisites

- A registered domain name (e.g., `yourdomain.com`)
- Your domain's nameservers pointed to Cloudflare
- Home Assistant running on a local IP (e.g., `192.168.0.40:8123`)

---

### 1) Create the Cloudflare Connector

1. Go to the Cloudflare Zero Trust Dashboard: https://one.dash.cloudflare.com/
2. On the left sidebar, go to **Networks → Connectors**
3. Click **Create a tunnel** (Choose **Cloudflared**)
4. Name your tunnel (e.g., `Home-Assistant-Tunnel`) and save
5. In the installation screen, select the **Docker** environment
6. Copy the provided `docker run` command

---

### 2) Deploy on the Raspberry Pi

Run the command on your Pi, but **add `-d`** so it runs in the background:

```bash
docker run -d cloudflare/cloudflared:latest tunnel --no-autoupdate run --token YOUR_VERY_LONG_TOKEN_HERE
```

Verify the tunnel shows as **HEALTHY** in the Cloudflare dashboard.

---

### 3) Route the Traffic

In the Cloudflare Tunnel setup, click **Next** to configure the **Public Hostname**:

- **Subdomain:** `ha`
- **Domain:** `yourdomain.com` (Result: `ha.yourdomain.com`)
- **Service Type:** `HTTP`
- **URL:** `192.168.0.40:8123` (replace with your Pi’s local IP)

Click **Save**.

---

### 4) Tell Home Assistant to Trust the Tunnel

By default, Home Assistant blocks proxy traffic (often shows **Error 400: Bad Request**). You must whitelist the tunnel.

Open your Home Assistant `configuration.yaml` and add:

```yaml
http:
  use_x_forwarded_for: true
  trusted_proxies:
    - 127.0.0.1
    - 172.16.0.0/12   # Docker Network
    - 192.168.0.0/16  # Home Wi-Fi Network
```

Restart Home Assistant.

You can now access your server anywhere via:

- `https://ha.yourdomain.com`

---

## 🧠 PHASE 2: The Google Home Bridge

### 1) Create the Integration Project

1. Go to the Google Home Developer Console
2. Click **Create project** and name it (e.g., `My Home Hub`)
3. Navigate to **Cloud-to-cloud → Develop**
4. Click **Add integration**

---

### 2) Configure Fulfillment & OAuth

Fill out the form with your new public link:

- **Fulfillment URL:** `https://ha.yourdomain.com/api/google_assistant`
- **Client ID:** `https://oauth-redirect.googleusercontent.com/r/YOUR_PROJECT_ID` (Find `PROJECT_ID` in the URL bar)
- **Client Secret:** `AnyRandomPassword123`
- **Authorization URL:** `https://ha.yourdomain.com/auth/authorize`
- **Token URL:** `https://ha.yourdomain.com/auth/token`

Save the configuration.

---

### 3) Generate the VIP Pass (Service Account)

1. Go to the Google Cloud Console
2. Ensure your smart home project is selected at the top
3. Search: **Service Accounts → Create Service Account**
4. Name it: `home-assistant`
5. Assign the Role: **Service Account Token Creator**
6. Click the three dots next to the account → **Manage Keys**
7. **Add Key → Create New Key (JSON)**
8. Download the file, rename it to `SERVICE_ACCOUNT.json`
9. Place it in your Home Assistant config folder

---

### 4) Finalize Home Assistant Config

Add this block to your `configuration.yaml`:

```yaml
google_assistant:
  project_id: YOUR_PROJECT_ID
  service_account: !include SERVICE_ACCOUNT.json
  report_state: true
  exposed_domains:
    - switch
    - light
    - camera
    - sensor
```

Restart Home Assistant.

---

### 5) Link the App

1. Open the **Google Home App** on your phone
2. Go to **Devices → + Add → Works with Google**
3. Search for: **[test] My Home Hub**
4. Log in with your Home Assistant credentials

All your ESP32 devices and cameras should sync.

---

## 🔄 MAINTENANCE: Changing Your Domain Name

If you ever buy a new domain (e.g., switching from `.studio` to `.com`), you do **NOT** need to rebuild the Docker tunnel.

### 1) Update Cloudflare Routing

Go to:

- Zero Trust → Networks → Connectors → your Tunnel → **Edit** → **Public Hostname**

Edit the route and change the domain dropdown to your new domain.

### 2) Update Google Developer Console

Google Home Developer Console → Cloud-to-cloud → update these URLs:

- Fulfillment: `https://ha.NEWDOMAIN.com/api/google_assistant`
- Auth: `https://ha.NEWDOMAIN.com/auth/authorize`
- Token: `https://ha.NEWDOMAIN.com/auth/token`

### 3) Re-link the App

Google Home app:

- Settings → Works with Google → select your test project → **Unlink**
- Add it again so it logs in via the new domain URL
