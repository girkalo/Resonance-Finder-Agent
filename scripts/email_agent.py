#!/usr/bin/env python3
"""
Email Agent for STT-MRAM Resonance Finder.

Checks email inbox for commands, executes them, sends results back.

Supported commands:
- "help" - List all commands with descriptions
- "status" - Get experiment status + resonance curve diagram
- "find resonance" - Run full search with current params
- "find resonance with h-dc 20" - Change DC field, then search
- "find resonance with k-u 8.0e+05" - Change anisotropy, then search  
- "find resonance with damping 0.01" - Change damping, then search
- "find resonance with h-dc 20 k-u 7.5e+05 damping 0.01" - Multiple params
- "test frequency 5.5e8" - Run single experiment
- "target q-factor 20" - Find parameters to achieve Q-factor of 20

Results include:
- Resonance curve diagram (PNG attachment)
- experiments.csv with all runs + agent thinking stage
- Summary with peak frequency, amplitude, Q-factor
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
import pandas as pd
import numpy as np

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


# ============================================================================
# EMAIL UTILITIES
# ============================================================================

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


# ============================================================================
# COMMAND PARSING
# ============================================================================

def parse_command(body):
    """Parse command from email body."""
    body_lower = body.lower().strip()
    
    # "help"
    if re.search(r'^help$', body_lower) or re.search(r'commands', body_lower):
        return {'cmd': 'help'}
    
    # "target q-factor X" - Find parameters for target Q-factor
    q_match = re.search(r'target\s+q[\s-]?factor\s+(\d+\.?\d*)', body_lower)
    if q_match:
        return {
            'cmd': 'target_qfactor',
            'q_target': float(q_match.group(1))
        }
    
    # "find resonance" with optional parameters
    if re.search(r'find\s+resonance', body_lower):
        # Parse multiple parameters
        h_dc = re.search(r'h-dc\s+(\d+\.?\d*)', body_lower)
        k_u = re.search(r'k-u\s+([\d.e+-]+)', body_lower)
        damping = re.search(r'damping\s+(\d+\.?\d*)', body_lower)
        
        return {
            'cmd': 'find_resonance',
            'h_dc': float(h_dc.group(1)) if h_dc else None,
            'k_u': float(k_u.group(1)) if k_u else None,
            'damping': float(damping.group(1)) if damping else None
        }
    
    # "test frequency X"
    freq_match = re.search(r'test\s+frequency\s+([\d.e+-]+)', body_lower)
    if freq_match:
        return {
            'cmd': 'test_frequency',
            'freq': float(freq_match.group(1))
        }
    
    # "status" or "results" or "diagram"
    if re.search(r'^(status|results|diagram|summary)$', body_lower) or \
       re.search(r'(get|send|show)\s+(plot|results|status|diagram)', body_lower):
        return {'cmd': 'status'}
    
    return {'cmd': 'unknown', 'raw': body}


# ============================================================================
# COMMAND EXECUTION
# ============================================================================

def update_parameters(params):
    """Update one or more parameters before running."""
    results = []
    
    if params.get('h_dc') is not None:
        script = os.path.join(PROJECT_DIR, 'scripts', 'update_dc_field.py')
        r = subprocess.run(['python', script, str(params['h_dc'])], 
                         capture_output=True, text=True, cwd=PROJECT_DIR)
        results.append(f"H_DC: {params['h_dc']} mT {'✓' if r.returncode == 0 else '✗'}")
    
    if params.get('k_u') is not None:
        script = os.path.join(PROJECT_DIR, 'scripts', 'update_anisotropy.py')
        r = subprocess.run(['python', script, str(params['k_u'])], 
                         capture_output=True, text=True, cwd=PROJECT_DIR)
        results.append(f"K_u: {params['k_u']:.3e} J/m³ {'✓' if r.returncode == 0 else '✗'}")
    
    if params.get('damping') is not None:
        script = os.path.join(PROJECT_DIR, 'scripts', 'update_damping.py')
        r = subprocess.run(['python', script, str(params['damping'])], 
                         capture_output=True, text=True, cwd=PROJECT_DIR)
        results.append(f"α (damping): {params['damping']} {'✓' if r.returncode == 0 else '✗'}")
    
    return results


def run_command(cmd_info):
    """Execute command and return results."""
    cmd = cmd_info['cmd']
    
    if cmd == 'find_resonance':
        # Update parameters first (if specified)
        param_updates = update_parameters(cmd_info)
        
        # Run the resonance search
        script = os.path.join(PROJECT_DIR, 'scripts', 'find_resonance.py')
        result = subprocess.run(['python', script], 
                               capture_output=True, text=True, cwd=PROJECT_DIR)
        
        return {
            'success': result.returncode == 0,
            'output': result.stdout,
            'error': result.stderr if result.stderr else None,
            'param_updates': param_updates,
            'attachments': [PLOT_FILE] if os.path.exists(PLOT_FILE) else [],
            'data_file': DATA_FILE if os.path.exists(DATA_FILE) else None
        }
    
    elif cmd == 'test_frequency':
        freq = cmd_info['freq']
        script = os.path.join(PROJECT_DIR, 'scripts', 'run_experiment.py')
        result = subprocess.run(['python', script, f'{freq:.3e}'], 
                               capture_output=True, text=True, cwd=PROJECT_DIR)
        
        return {
            'success': result.returncode == 0,
            'output': result.stdout,
            'error': result.stderr if result.stderr else None,
            'attachments': [],
            'data_file': None
        }
    
    elif cmd == 'target_qfactor':
        # Q-factor parameter optimization
        q_target = cmd_info['q_target']
        return run_qfactor_optimization(q_target)
    
    elif cmd == 'status':
        return get_status()
    
    elif cmd == 'help':
        return {'success': True, 'output': get_help_text(), 'attachments': []}
    
    else:
        return {
            'success': False,
            'output': None,
            'error': f"Unknown command: {cmd_info.get('raw', 'N/A')}\n\nSend 'help' for command list."
        }


def run_qfactor_optimization(q_target):
    """
    Find parameters to achieve target Q-factor.
    Q-factor = f_res / Δf (resonance frequency / linewidth)
    
    Strategy: Vary damping (α) to control linewidth
    - Lower damping → Higher Q (sharper resonance)
    - Higher damping → Lower Q (broader resonance)
    
    Also consider: H_DC affects resonance frequency
    """
    body = f"Q-Factor Target: {q_target}\n"
    body += "=" * 60 + "\n\n"
    
    # Read current experiments to understand current Q
    if not os.path.exists(DATA_FILE):
        return {
            'success': False,
            'output': None,
            'error': "No experiment data found. Run 'find resonance' first."
        }
    
    # Load data
    df = pd.read_csv(DATA_FILE)
    if len(df) == 0:
        return {
            'success': False,
            'output': None,
            'error': "Empty experiment data."
        }
    
    # Calculate current Q from best experiment
    # Q = f_res / FWHM (approximation)
    best_idx = df['amplitude'].idxmax()
    f_peak = df.loc[best_idx, 'frequency']
    amp_peak = df.loc[best_idx, 'amplitude']
    
    # Estimate FWHM from data around peak
    threshold = amp_peak * 0.5
    fwhm_points = df[df['amplitude'] >= threshold]
    if len(fwhm_points) >= 2:
        fwhm = fwhm_points['frequency'].max() - fwhm_points['frequency'].min()
        current_q = f_peak / fwhm if fwhm > 0 else float('inf')
    else:
        current_q = None
    
    body += f"Current Status:\n"
    body += f"  Peak frequency: {f_peak/1e6:.2f} MHz\n"
    body += f"  Current Q-factor: {current_q:.2f if current_q else 'N/A'}\n"
    body += f"  Target Q-factor: {q_target}\n\n"
    
    # Recommend damping adjustment
    if current_q and current_q < q_target:
        # Need higher Q → lower damping
        rec_damping = 0.01  # Suggest lower damping
        action = "Lower damping to sharpen resonance peak"
    elif current_q and current_q > q_target:
        # Need lower Q → higher damping
        rec_damping = 0.05  # Suggest higher damping
        action = "Increase damping to broaden resonance peak"
    else:
        rec_damping = 0.02
        action = "Run baseline measurement first"
    
    body += f"Recommended Action:\n"
    body += f"  {action}\n"
    body += f"  Suggested damping (α): {rec_damping}\n\n"
    body += f"Command to run:\n"
    body += f"  'find resonance with damping {rec_damping}'\n\n"
    body += f"Note: This will search for resonance with new damping parameter.\n"
    body += f"Then check Q-factor with 'status' command.\n"
    
    return {
        'success': True,
        'output': body,
        'attachments': [PLOT_FILE] if os.path.exists(PLOT_FILE) else [],
        'data_file': DATA_FILE if os.path.exists(DATA_FILE) else None
    }


def get_status():
    """Get current experiment status with summary."""
    body = "STT-MRAM Resonance Finder - Status Report\n"
    body += "=" * 60 + "\n\n"
    
    # Load and analyze experiments.csv
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        
        # Add stage column if not present (backward compatibility)
        if 'stage' not in df.columns:
            # Infer stage from frequency spacing
            df = df.sort_values('frequency')
            df['freq_diff'] = df['frequency'].diff().abs()
            df['stage'] = df['freq_diff'].apply(lambda x: 'coarse' if x > 20e6 else 'fine')
        
        body += "SUMMARY:\n"
        body += f"  Total experiments: {len(df)}\n"
        
        # Count by stage
        stage_counts = df['stage'].value_counts().to_dict() if 'stage' in df.columns else {}
        for stage, count in stage_counts.items():
            body += f"  - {stage} stage: {count} runs\n"
        
        # Peak results
        if len(df) > 0 and 'amplitude' in df.columns:
            best_idx = df['amplitude'].idxmax()
            f_peak = df.loc[best_idx, 'frequency']
            amp_peak = df.loc[best_idx, 'amplitude']
            
            body += f"\nPEAK RESONANCE:\n"
            body += f"  Frequency: {f_peak/1e6:.2f} MHz\n"
            body += f"  Amplitude (Mz): {amp_peak:.6f}\n"
            
            # Calculate Q-factor if we have linewidth data
            threshold = amp_peak * 0.5
            fwhm_points = df[df['amplitude'] >= threshold]
            if len(fwhm_points) >= 2:
                fwhm = fwhm_points['frequency'].max() - fwhm_points['frequency'].min()
                q_factor = f_peak / fwhm if fwhm > 0 else 0
                body += f"  Q-factor: {q_factor:.2f}\n"
        
        body += "\n"
    else:
        body += "No experiment data found.\n\n"
    
    body += "ATTACHMENTS:\n"
    body += "  1. resonance_curve.png - Resonance curve diagram\n"
    body += "  2. experiments.csv - All experiment data with stages\n\n"
    
    body += "Next steps:\n"
    body += "  - 'find resonance' - Run new search\n"
    body += "  - 'target q-factor 20' - Optimize for specific Q\n"
    
    return {
        'success': True,
        'output': body,
        'attachments': [PLOT_FILE] if os.path.exists(PLOT_FILE) else [],
        'data_file': DATA_FILE if os.path.exists(DATA_FILE) else None
    }


def get_help_text():
    """Get comprehensive help text with all commands."""
    return """STT-MRAM Resonance Finder - Command Guide
================================================================

QUICK START:
1. Send "help" to see this guide
2. Send "status" to see current results + diagram
3. Send "find resonance" to run a full search

COMMANDS:
----------------------------------------------------------------

help
  → Shows this command guide
  → Use this anytime you're unsure what to do

status
  → Returns: resonance curve diagram (PNG)
  → Returns: experiments.csv with all data + thinking stages
  → Summary: peak frequency, amplitude, Q-factor
  → Shows: count of coarse vs fine stage runs

find resonance
  → Runs full resonance search with CURRENT parameters
  → Process: coarse search (300-900 MHz, wide steps)
           → identify peak region
           → fine search (zoom around peak)
  → Returns: diagram, CSV, summary (same as status)
  → Thinking stages tracked: 'coarse', 'fine', 'zoom'

find resonance with <parameters>
  → Changes parameters FIRST, then runs search
  → Can combine multiple parameters in one command

  Examples:
  "find resonance with h-dc 20"
    → Set DC field to 20 mT, then search
    
  "find resonance with k-u 7.5e+05"
    → Set anisotropy K_u, then search
    
  "find resonance with damping 0.01"
    → Set damping (α), then search
    → Lower damping (0.01) = sharper peak, higher Q
    → Higher damping (0.05) = broader peak, lower Q
    
  "find resonance with h-dc 20 k-u 7.5e+05 damping 0.01"
    → Sets ALL three parameters at once
    → Then runs resonance search

test frequency <freq>
  → Runs SINGLE experiment at specific frequency
  → Example: "test frequency 5.42e8" (542 MHz)
  → Returns: single run result
  → Use for: quick check, verification

target q-factor <number>
  → Calculates parameters needed for target Q-factor
  → Example: "target q-factor 20"
  → Returns: recommended damping value
  → Note: Q = f_res / linewidth (higher damping = lower Q)
  → Then run: "find resonance with damping <value>"

WHAT YOU GET IN EVERY RESPONSE:
----------------------------------------------------------------
1. Resonance curve diagram (PNG attachment)
   → Plot of amplitude vs frequency
   → Shows the full resonance peak
   
2. experiments.csv (attachment)
   → All experiment runs with columns:
     - frequency (Hz)
     - amplitude (Mz)
     - stage (thinking strategy: coarse/fine/zoom)
     - timestamp
     
3. Text summary
   → Peak frequency in MHz
   → Maximum amplitude (Mz)
   → Q-factor (if calculable)
   → Count of experiments by stage

UNDERSTANDING STAGES (thinking strategies):
----------------------------------------------------------------
coarse  → Wide frequency range, big steps (find general region)
fine    → Narrower range, smaller steps (focus on peak)
zoom    → Very narrow, very small steps (pinpoint exact peak)

Single runs from "test frequency" have no stage label.

PARAMETER EFFECTS:
----------------------------------------------------------------
h-dc (DC field)
  → Higher H_DC → Higher resonance frequency
  → Range: typically 5-50 mT

k-u (anisotropy)
  → Higher K_u → Higher resonance frequency
  → Format: scientific notation, e.g., 7.5e+05

damping (α)
  → Lower α (0.01) → Sharper peak, higher Q, slower decay
  → Higher α (0.05) → Broader peak, lower Q, faster decay
  → Default: 0.02

EXAMPLE WORKFLOWS:
----------------------------------------------------------------

1. Simple resonance search:
   → "find resonance"
   → Wait ~2-3 minutes
   → Get results with diagram

2. Change DC field, find new peak:
   → "find resonance with h-dc 15"
   → Peak will shift to different frequency

3. Optimize for high Q-factor:
   → "target q-factor 25"
   → Get recommended damping (e.g., 0.01)
   → "find resonance with damping 0.01"
   → Check Q in results

4. Multiple parameter sweep:
   → "find resonance with h-dc 20 k-u 8.0e+05"
   → Both parameters updated, then search

TIPS:
----------------------------------------------------------------
- Always start with "help" if unsure
- "status" is safe - just reports, doesn't run experiments
- Experiments take ~2-3 minutes each
- Attachments open in any spreadsheet (CSV) or image viewer (PNG)
- Q-factor optimization may need 2-3 iterations to dial in

================================================================
Questions? Reply with "help" anytime.
"""


# ============================================================================
# RESULT FORMATTING
# ============================================================================

def format_results(cmd, result):
    """Format results for email response."""
    if not result['success']:
        return f"Command failed:\n\n{result.get('error', 'Unknown error')}"
    
    if cmd == 'find_resonance':
        output = result['output']
        body = "STT-MRAM Resonance Search Complete\n"
        body += "=" * 60 + "\n\n"
        
        # Parameter updates
        if result.get('param_updates'):
            body += "PARAMETER UPDATES:\n"
            for update in result['param_updates']:
                body += f"  {update}\n"
            body += "\n"
        
        # Parse results from output
        if 'FINAL RESULTS' in output:
            final_section = output.split('FINAL RESULTS')[1].split('=' * 60)[0].strip()
            body += "FINAL RESULTS:\n"
            body += final_section + "\n\n"
        
        body += "ATTACHMENTS:\n"
        body += "  1. resonance_curve.png - Resonance curve diagram\n"
        body += "  2. experiments.csv - All runs with thinking stages\n\n"
        
        body += "Next: Send 'status' for detailed summary or 'help' for options."
        
        return body
    
    elif cmd == 'test_frequency':
        return f"Experiment Complete:\n\n{result['output']}"
    
    else:
        return result['output']


# ============================================================================
# MAIN
# ============================================================================

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
        
        # Build attachments list
        attachments = []
        if result.get('attachments'):
            attachments.extend(result['attachments'])
        if result.get('data_file'):
            attachments.append(result['data_file'])
        
        # Send response
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
            "help",
            "status",
            "find resonance",
            "find resonance with h-dc 20",
            "find resonance with k-u 8.0e+05",
            "find resonance with damping 0.01",
            "find resonance with h-dc 20 k-u 7.5e+05 damping 0.01",
            "test frequency 5.5e8",
            "target q-factor 20"
        ]
        for test in test_cases:
            print(f"\nInput: '{test}'")
            print(f"Parsed: {parse_command(test)}")
    else:
        main()
