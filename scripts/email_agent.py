#!/usr/bin/env python3
"""
Email Agent for STT-MRAM Resonance Finder.

Checks email inbox for commands, executes them, sends results back.

Supported commands:
- "find resonance" - Run full search with current params
- "find resonance with h-dc 20" - Change DC field, then search
- "find resonance with k-u 8.0e+05" - Change anisotropy, then search
- "test frequency 5.5e8" - Run single experiment
- "status" - Send current plot and summary
- "help" - List commands
"""

import os
import sys
import re
import subprocess
import smtplib
import imaplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from pathlib import Path

# Configuration - MODIFY THESE
EMAIL_USER = "resonanceagent@gmail.com"  # TODO: Set your email
EMAIL_PASS = "zxey ftkv qgaz leje"     # TODO: Set app password
IMAP_SERVER = "imap.gmail.com"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# Project paths
PROJECT_DIR = r"D:\Desktop\AI PROJECT\MacrospinExample_STTFMR_Hx10mT\MacrospinCodeEle_Simulation"
WORKSPACE_DIR = r"C:\Users\girka\.openclaw\workspace"
PLOT_FILE = os.path.join(PROJECT_DIR, "resonance_curve.png")
DATA_FILE = os.path.join(PROJECT_DIR, "input", "logs", "experiments.csv")


def send_email(to, subject, body, attachments=None):
    """Send email with optional attachments."""
    msg = MIMEMultipart()
    msg['From'] = EMAIL_USER
    msg['To'] = to
    msg['Subject'] = subject
    
    msg.attach(MIMEText(body, 'plain'))
    
    # Attach files
    if attachments:
        for filepath in attachments:
            if os.path.exists(filepath):
                with open(filepath, 'rb') as f:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f'attachment; filename={os.path.basename(filepath)}')
                msg.attach(part)
    
    # Send
    server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
    server.starttls()
    server.login(EMAIL_USER, EMAIL_PASS)
    server.send_message(msg)
    server.quit()
    print(f"[EMAIL] Sent to {to}: {subject}")


def check_emails():
    """Check inbox for new commands."""
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL_USER, EMAIL_PASS)
        mail.select('inbox')
        
        # Search for unread emails
        _, messages = mail.search(None, 'UNSEEN')
        email_ids = messages[0].split()
        
        commands = []
        for eid in email_ids:
            _, msg_data = mail.fetch(eid, '(RFC822)')
            raw_email = msg_data[0][1]
            email_msg = email.message_from_bytes(raw_email)
            
            sender = email_msg['From']
            subject = email_msg['Subject']
            
            # Get body
            body = ""
            if email_msg.is_multipart():
                for part in email_msg.walk():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload(decode=True).decode()
                        break
            else:
                body = email_msg.get_payload(decode=True).decode()
            
            commands.append({
                'from': sender,
                'subject': subject,
                'body': body,
                'id': eid
            })
        
        mail.close()
        mail.logout()
        return commands
    
    except Exception as e:
        print(f"[ERROR] Email check failed: {e}")
        return []


def parse_command(body):
    """Parse command from email body."""
    body_lower = body.lower().strip()
    
    # "find resonance"
    if re.search(r'find resonance', body_lower):
        h_dc = re.search(r'h-dc\s+(\d+)', body_lower)
        k_u = re.search(r'k-u\s+([\d.e+]+)', body_lower)
        
        return {
            'cmd': 'find_resonance',
            'h_dc': float(h_dc.group(1)) if h_dc else None,
            'k_u': float(k_u.group(1)) if k_u else None
        }
    
    # "test frequency X"
    freq_match = re.search(r'test frequency\s+([\d.e+]+)', body_lower)
    if freq_match:
        return {
            'cmd': 'test_frequency',
            'freq': float(freq_match.group(1))
        }
    
    # "status"
    if re.search(r'^status$', body_lower) or re.search(r'send (plot|results)', body_lower):
        return {'cmd': 'status'}
    
    # "help"
    if re.search(r'help', body_lower):
        return {'cmd': 'help'}
    
    return {'cmd': 'unknown', 'raw': body}


def run_command(cmd_info):
    """Execute command and return results."""
    cmd = cmd_info['cmd']
    
    if cmd == 'find_resonance':
        args = []
        if cmd_info.get('h_dc'):
            args.extend(['--h-dc', str(cmd_info['h_dc'])])
        if cmd_info.get('k_u'):
            args.extend(['--k-u', str(cmd_info['k_u'])])
        
        script = os.path.join(PROJECT_DIR, 'scripts', 'find_resonance.py')
        result = subprocess.run(['python', script] + args, capture_output=True, text=True, cwd=PROJECT_DIR)
        
        return {
            'success': result.returncode == 0,
            'output': result.stdout,
            'error': result.stderr if result.stderr else None
        }
    
    elif cmd == 'test_frequency':
        freq = cmd_info['freq']
        script = os.path.join(PROJECT_DIR, 'scripts', 'run_experiment.py')
        result = subprocess.run(['python', script, f'{freq:.3e}'], capture_output=True, text=True, cwd=PROJECT_DIR)
        
        return {
            'success': result.returncode == 0,
            'output': result.stdout,
            'error': result.stderr if result.stderr else None
        }
    
    elif cmd == 'status':
        # Read experiments.csv
        summary = "Current experiment status:\n\n"
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r') as f:
                lines = f.readlines()
                summary += f"Total experiments: {len(lines) - 1}\n"
                if len(lines) > 1:
                    summary += f"Last experiment: {lines[-1]}"
        
        return {
            'success': True,
            'output': summary,
            'attachments': [PLOT_FILE] if os.path.exists(PLOT_FILE) else []
        }
    
    elif cmd == 'help':
        help_text = """STT-MRAM Resonance Finder - Command Help

Commands:
1. "find resonance" - Run full resonance search
2. "find resonance with h-dc 20" - Search with 20 mT DC field
3. "find resonance with k-u 8.0e+05" - Search with new anisotropy
4. "test frequency 5.5e8" - Run single experiment at 550 MHz
5. "status" - Get current results and plot
6. "help" - Show this message

Examples:
- "find resonance with h-dc 15" (change DC field to 15 mT)
- "find resonance with h-dc 20 k-u 7.5e+05" (change both)
- "test frequency 5.42e8" (test specific frequency)

Results include:
- Peak resonance frequency (MHz)
- Maximum Mz amplitude
- Q-factor
- Resonance curve plot
"""
        return {'success': True, 'output': help_text}
    
    else:
        return {
            'success': False,
            'output': None,
            'error': f"Unknown command: {cmd_info.get('raw', 'N/A')}\n\nSend 'help' for command list."
        }


def format_results(cmd, result):
    """Format results for email."""
    if not result['success']:
        return f"Command failed:\n\n{result.get('error', 'Unknown error')}"
    
    if cmd == 'find_resonance':
        # Extract key results from output
        output = result['output']
        body = "STT-MRAM Resonance Search Complete\n"
        body += "=" * 60 + "\n\n"
        
        # Configuration info
        body += "CONFIGURATION:\n"
        body += "- System: MacrospinLLG STT-MRAM Simulation\n"
        body += "- Search Range: 300-900 MHz (coarse), peak region (fine)\n"
        body += "- DC Field: See experiment log for exact value used\n"
        body += "- Anisotropy (K_u): See LayerFree_parameters.txt\n\n"
        
        # Parse final results section
        if 'FINAL RESULTS' in output:
            lines = output.split('FINAL RESULTS')[1].split('=' * 60)[0].strip()
            body += "RESULTS:\n"
            body += lines + "\n\n"
        
        body += "Full log attached.\n"
        
        return body
    
    elif cmd == 'test_frequency':
        return f"Experiment complete:\n\n{result['output']}"
    
    else:
        return result['output']


def main():
    print(f"\n{'='*60}")
    print(f"Email Agent for STT-MRAM Resonance Finder")
    print(f"Time: {datetime.now().isoformat()}")
    print(f"{'='*60}\n")
    
    # Check for emails
    print("[CHECK] Checking for new emails...")
    emails = check_emails()
    
    if not emails:
        print("[CHECK] No new commands.")
        return
    
    print(f"[CHECK] Found {len(emails)} new command(s)")
    
    for msg in emails:
        print(f"\n[PROCESS] From: {msg['from']}")
        print(f"[PROCESS] Subject: {msg['subject']}")
        
        # Parse command
        cmd_info = parse_command(msg['body'])
        print(f"[PROCESS] Command: {cmd_info['cmd']}")
        
        # Run command
        result = run_command(cmd_info)
        
        # Format response
        body = format_results(cmd_info['cmd'], result)
        
        # Send response
        attachments = result.get('attachments', [])
        if cmd_info['cmd'] == 'find_resonance' and os.path.exists(PLOT_FILE):
            attachments.append(PLOT_FILE)
        if os.path.exists(DATA_FILE):
            attachments.append(DATA_FILE)
        
        subject = f"Re: {msg['subject']}" if not msg['subject'].startswith('Re:') else msg['subject']
        send_email(msg['from'], subject, body, attachments)
    
    print(f"\n{'='*60}")
    print("Email processing complete.")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    # Allow manual testing
    if len(sys.argv) > 1 and sys.argv[1] == '--test':
        # Test parsing
        test_cases = [
            "find resonance",
            "find resonance with h-dc 20",
            "find resonance with k-u 8.0e+05",
            "test frequency 5.5e8",
            "status",
            "help"
        ]
        for test in test_cases:
            print(f"\nInput: '{test}'")
            print(f"Parsed: {parse_command(test)}")
    else:
        main()
