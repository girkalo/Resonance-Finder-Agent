# Email Agent Setup Guide

## Overview
The Email Agent allows your professor to control the STT-MRAM resonance finder remotely by sending emails.

## What the Professor Can Do

| Email Command | What Happens |
|---------------|--------------|
| `find resonance` | Run full resonance search with current parameters |
| `find resonance with h-dc 20` | Set DC field to 20 mT, then search |
| `find resonance with k-u 8.0e+05` | Set anisotropy to 8e5 J/m³, then search |
| `test frequency 5.5e8` | Run single experiment at 550 MHz |
| `status` | Get current results and plot |
| `help` | Get command list |

## Response Includes
- Peak resonance frequency (MHz)
- Maximum Mz amplitude
- Q-factor estimate
- `resonance_curve.png` (attached)
- `experiments.csv` (attached)

## Setup Instructions

### 1. Choose an Email Provider

**Gmail (Recommended):**
1. Go to Google Account → Security → 2-Step Verification → App passwords
2. Generate app password for "Mail"
3. Note: Your regular password won't work, you need an app password

**Outlook/Office365:**
- Use `outlook.office365.com` for IMAP
- May need to enable "Less secure app access" or use app password

**University Email:**
- Check with IT department for IMAP settings
- May need VPN or special configuration

### 2. Configure the Agent

Edit `scripts/email_agent.py` and set:

```python
EMAIL_USER = "your.email@gmail.com"      # Your email address
EMAIL_PASS = "xxxx xxxx xxxx xxxx"       # App password (16 chars with spaces)
IMAP_SERVER = "imap.gmail.com"            # IMAP server
SMTP_SERVER = "smtp.gmail.com"            # SMTP server
SMTP_PORT = 587                           # SMTP port (usually 587 or 465)
```

### 3. Test the Agent

Run once manually:
```bash
cd "D:\Desktop\AI PROJECT\...\MacrospinCodeEle_Simulation"
python scripts\email_agent.py --test
```

This tests command parsing without connecting to email.

### 4. Set Up Automation

**Option A: Cron/Scheduled Task (Check every 5 minutes)**

On Windows:
1. Open Task Scheduler
2. Create Basic Task → Name: "Resonance Email Agent"
3. Trigger: Every 5 minutes
4. Action: Start a program
5. Program: `python`
6. Arguments: `"D:\Desktop\AI PROJECT\...\scripts\email_agent.py"`

**Option B: Run manually when needed**

Just run:
```bash
python scripts\email_agent.py
```

### 5. Share with Professor

Send this template email:

```
Subject: STT-MRAM Resonance Finder - Remote Access

Dear Professor,

You can now control the resonance finder remotely by emailing:
    your.email@gmail.com

Commands:
- "find resonance" - Run search
- "find resonance with h-dc 20" - Change DC field to 20 mT
- "find resonance with k-u 8.0e+05" - Change anisotropy
- "test frequency 5.5e8" - Test specific frequency
- "status" - Get current results
- "help" - See all commands

Results (plot + data) will be emailed back automatically.

Best regards,
[Your name]
```

## Security Notes

⚠️ **Important:**
- Use an **app password**, not your main password
- Consider creating a dedicated email account for this
- The email agent only reads UNSEEN emails (marks them as read after processing)
- Anyone with the email address can send commands (use with trusted users only)

## Troubleshooting

**"Authentication failed"**
- Check if using app password (not regular password)
- Verify 2FA is enabled (required for Gmail app passwords)

**"Connection refused"**
- Check firewall settings
- Verify IMAP/SMTP servers are correct

**"No new commands" but emails exist**
- The agent only reads UNSEEN emails
- If emails were already opened, they won't be processed
- Mark as unread or send new email

## File Locations

After setup:
- Agent script: `scripts/email_agent.py`
- Configuration: Edit lines 25-29 in `email_agent.py`
- Logs: Output appears in console (can redirect to file if needed)
