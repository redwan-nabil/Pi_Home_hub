import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import os
import time
import threading
import subprocess
from PyPDF2 import PdfReader, PdfWriter

# --- CONFIGURATION ---
BOT_TOKEN = 'Your_Telegram_Bot_Token_Here'
ADMIN_ID = 123456789  # Replace with your Telegram user ID 
PRINTER_NAME = 'Your_CUPS_Printer_Name_Here'  # Replace with your CUPS printer name

bot = telebot.TeleBot(BOT_TOKEN)

# Dictionaries to track user progress and files
user_states = {}
jobs = {}

print("🚀 Business Print/Scan Bot is Online!")

# --- TEXT TEMPLATES ---
PAYMENT_TEXT = """Please make your payment first using one of the following methods:
Bkash/Nagad: your mobile number (Bkash/Nagad)
Bank A/C: your bank account number (Bank A/C)
Name: your name (as reference)
Branch: your branch name (as reference)

After paying, please reply with the mobile number or bank A/C number you used to send the money."""

PRINT_PRESETS = """★ Printing Preferences
Page Size: A4
Quality: Standard (Plain 80gsm paper)
Pages: All pages in your PDF will be printed.

Note: You cannot change these settings here. If you need custom preferences, please contact the admin directly: t.me/Redwan_Nabil2003.

Please choose your color preference to proceed:"""

SCAN_PRESETS = """★ Scanning Preferences
Format: PDF
Size: A4
Color: Full Color
Resolution: 600 DPI (High Quality)
Price: 3৳ per scan

Note: You cannot change these settings here. If you need custom preferences, please contact the admin directly: t.me/Redwan_Nabil2003 (@Redwan_Nabil2003).

Are you sure you want to submit your documents to the admin?"""


# --- FEATURE: PRINTER STATUS CHECKER ---
def is_printer_online():
    try:
        status = subprocess.check_output(f"lpstat -p {PRINTER_NAME}", shell=True, stderr=subprocess.STDOUT).decode('utf-8').lower()
        if "disabled" in status or "unplugged" in status or "not connected" in status or "offline" in status:
            return False
        return True
    except:
        return False

def wait_for_printer_and_resume(user_id, job_id, job_type):
    job = jobs.get(job_id)
    bot.send_message(ADMIN_ID, f"🔔 **ATTENTION ADMIN!**\nCustomer '{job['name']}' wants to {job_type}.\nPlease turn ON your printer/scanner!", parse_mode="Markdown")
    bot.send_message(user_id, "⚠️ Printer currently off. Please wait...")
    
    while not is_printer_online():
        time.sleep(5)
        
    bot.send_message(user_id, "✅ Printer turned on, start processing now.")
    
    if job_type == 'print':
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton("🎨 Color (6৳/pg)", callback_data=f"sure_print_color_{job_id}"),
            InlineKeyboardButton("⚫⚪ B/W (4৳/pg)", callback_data=f"sure_print_bw_{job_id}")
        )
        markup.add(InlineKeyboardButton("❌ Cancel", callback_data=f"cancel_job_{job_id}"))
        bot.send_message(user_id, PRINT_PRESETS, reply_markup=markup)
    elif job_type == 'scan':
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("Yes", callback_data=f"sure_scan_{job_id}"),
                   InlineKeyboardButton("No", callback_data=f"cancel_scan_{job_id}"))
        bot.send_message(user_id, SCAN_PRESETS, reply_markup=markup)


# --- START AND GROUP HANDLING ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Welcome! Just send me a PDF file to start printing, or type /scan to request a scan.")

@bot.message_handler(commands=['print'])
def handle_print_command(message):
    if message.chat.type in ['group', 'supergroup']:
        bot.reply_to(message, "Please check your inbox, I sent you a message!")
    try:
        bot.send_message(message.from_user.id, "Please submit your PDF file now (ensure it is in .pdf format).")
    except Exception:
        bot.reply_to(message, "⚠️ Please start a private message with me first by clicking the Start button!")

# --- AUTOMATIC FILE CATCHER ---
@bot.message_handler(content_types=['document'])
def handle_document(message):
    user_id = message.from_user.id
    
    if not message.document.file_name.lower().endswith('.pdf'):
        bot.send_message(user_id, "⚠️ Invalid file format. Please submit a valid PDF file.")
        return

    bot.send_message(user_id, "📥 Document received! Downloading...")
    
    file_info = bot.get_file(message.document.file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    file_path = f"/home/redwannabil/print_{message.message_id}.pdf"
    
    with open(file_path, 'wb') as new_file:
        new_file.write(downloaded_file)
        
    # --- MAGIC FIX: BLANK PAGE INJECTION ---
    try:
        reader = PdfReader(file_path)
        total_pages = len(reader.pages)
        
        # If the document has an odd number of pages (e.g., 5), we add a blank 6th page.
        # This guarantees the Admin never has to separate sheets and never forgets the last page!
        if total_pages > 1 and total_pages % 2 != 0:
            writer = PdfWriter()
            for page in reader.pages:
                writer.add_page(page)
            
            # Add a blank page matching the exact size of the last page
            last_page = reader.pages[-1]
            writer.add_blank_page(width=last_page.mediabox.width, height=last_page.mediabox.height)
            
            with open(file_path, "wb") as f:
                writer.write(f)
            
            total_pages += 1 # Now it's perfectly even!
            
    except Exception as e:
        print("PDF Read Error:", e)
        total_pages = 1
        
    job_id = str(message.message_id)
    jobs[job_id] = {'user_id': user_id, 'file_path': file_path, 'type': 'print', 'name': message.from_user.first_name, 'total_pages': total_pages}
    user_states[user_id] = {'current_job': job_id}
    
    if is_printer_online():
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton("🎨 Color (6৳/pg)", callback_data=f"sure_print_color_{job_id}"),
            InlineKeyboardButton("⚫⚪ B/W (4৳/pg)", callback_data=f"sure_print_bw_{job_id}")
        )
        markup.add(InlineKeyboardButton("❌ Cancel", callback_data=f"cancel_job_{job_id}"))
        bot.send_message(user_id, PRINT_PRESETS, reply_markup=markup)
    else:
        threading.Thread(target=wait_for_printer_and_resume, args=(user_id, job_id, 'print')).start()

@bot.message_handler(content_types=['photo', 'video', 'audio', 'voice'])
def handle_wrong_format(message):
    bot.send_message(message.from_user.id, "⚠️ Please send your document as a **File** (.pdf) to print it, not as a photo or video.", parse_mode="Markdown")

# --- THE SCAN WORKFLOW ---
@bot.message_handler(commands=['scan'])
def handle_scan_command(message):
    if message.chat.type in ['group', 'supergroup']:
        bot.reply_to(message, "Please check your inbox, I sent you a message!")
        
    try:
        user_id = message.from_user.id
        job_id = str(message.message_id)
        jobs[job_id] = {'user_id': user_id, 'type': 'scan', 'name': message.from_user.first_name}
        
        if is_printer_online():
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("Yes", callback_data=f"sure_scan_{job_id}"),
                       InlineKeyboardButton("No", callback_data=f"cancel_scan_{job_id}"))
            bot.send_message(user_id, SCAN_PRESETS, reply_markup=markup)
        else:
            threading.Thread(target=wait_for_printer_and_resume, args=(user_id, job_id, 'scan')).start()
            
    except Exception:
        bot.reply_to(message, "⚠️ Please start a private message with me first!")

# --- INLINE BUTTON CLICKS ---
@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    data = call.data.split('_')
    job_id = data[-1]
    action = "_".join(data[:-1]) 
    job = jobs.get(job_id)

    if not job:
        bot.answer_callback_query(call.id, "This job has expired.")
        return

    user_id = job['user_id']

    if action in ["sure_print_color", "sure_print_bw"]:
        is_color = "color" in action
        job['color_pref'] = "Color" if is_color else "Black & White"
        job['cups_color'] = "COLOR" if is_color else "MONO"
        
        bot.edit_message_text(f"Great! You selected **{job['color_pref']}**.", chat_id=user_id, message_id=call.message.message_id, parse_mode="Markdown")
        
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton("📄 One-Sided", callback_data=f"duplex_one_{job_id}"),
            InlineKeyboardButton("📑 Both-Sided", callback_data=f"duplex_both_{job_id}")
        )
        bot.send_message(user_id, "Do you want to print on one side or both sides of the paper?", reply_markup=markup)
        
    elif action in ["duplex_one", "duplex_both"]:
        job['duplex'] = "Both-Sided" if "both" in action else "One-Sided"
        bot.edit_message_text(f"Great! You selected **{job['duplex']}**.", chat_id=user_id, message_id=call.message.message_id, parse_mode="Markdown")
        
        bot.send_message(user_id, PAYMENT_TEXT)
        user_states[user_id] = {'state': 'WAITING_FOR_PAYMENT', 'current_job': job_id}
        
    elif action == "sure_scan":
        bot.edit_message_text("Great!", chat_id=user_id, message_id=call.message.message_id)
        bot.send_message(user_id, PAYMENT_TEXT)
        user_states[user_id] = {'state': 'WAITING_FOR_PAYMENT', 'current_job': job_id}

    elif action == "cancel_job":
        bot.edit_message_text("Print cancelled.", chat_id=user_id, message_id=call.message.message_id)
        if os.path.exists(job['file_path']):
            os.remove(job['file_path'])
            
    elif action == "cancel_scan":
        bot.edit_message_text("Scan request cancelled.", chat_id=user_id, message_id=call.message.message_id)

    # Admin verifies payment
    elif action == "admin_payyes":
        new_status = f"✅ Payment verified for {job['name']}."
        try:
            bot.edit_message_caption(new_status, chat_id=ADMIN_ID, message_id=call.message.message_id)
        except:
            bot.edit_message_text(new_status, chat_id=ADMIN_ID, message_id=call.message.message_id)
        
        bot.send_message(user_id, "Admin is processing your request...")
        
        if job['type'] == 'print':
            bot.send_message(ADMIN_ID, f"🖨️ Sending to printer as {job['color_pref']}, {job.get('duplex', 'One-Sided')}...")
            bot.send_message(user_id, f"✅ Payment verified! Your document is printing now in {job['color_pref']} ({job.get('duplex', 'One-Sided')}).")
            
            if job.get('duplex') == 'Both-Sided':
                total_pages = job.get('total_pages', 1)
                
                if total_pages == 1:
                    # Fallback to 1-sided if they requested both-sided on a 1 page document
                    os.system(f"lp -d {PRINTER_NAME} -o media=A4 -o sides=one-sided -o Ink={job['cups_color']} -o fit-to-page '{job['file_path']}'")
                    time.sleep(5) 
                    try:
                        if os.path.exists(job['file_path']):
                            os.remove(job['file_path'])
                    except: pass
                    bot.send_message(user_id, "🎉 Your print is ready! You can collect it now.")
                else:
                    # Print Odd Pages First
                    os.system(f"lp -d {PRINTER_NAME} -o media=A4 -o page-set=odd -o Ink={job['cups_color']} -o fit-to-page '{job['file_path']}'")
                    
                    # Generate explicit list of even pages
                    even_pages = [str(i) for i in range(2, total_pages + 1, 2)]
                    job['even_pages_list'] = ",".join(even_pages)
                    
                    markup = InlineKeyboardMarkup()
                    markup.add(InlineKeyboardButton("✅ Done (Print Even Pages)", callback_data=f"admin_flippage_{job_id}"))
                    
                    # Thanks to the blank page injection, the instructions are incredibly simple!
                    bot.send_message(ADMIN_ID, f"⚠️ **BOTH-SIDED PRINT PAUSED**\n\nThe odd pages are printing now.\n1. Take the printed stack.\n2. Swap/Reverse the ENTIRE stack.\n3. Put it back in the tray.\n\nClick 'Done' when ready to print even pages.", parse_mode="Markdown", reply_markup=markup)
            else:
                # Normal One-Sided Print
                os.system(f"lp -d {PRINTER_NAME} -o media=A4 -o sides=one-sided -o Ink={job['cups_color']} -o fit-to-page '{job['file_path']}'")
                time.sleep(5)
                try:
                    if os.path.exists(job['file_path']):
                        os.remove(job['file_path'])
                except: pass
                bot.send_message(user_id, "🎉 Your print is ready! You can collect it now.")
                
        elif job['type'] == 'scan':
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("✅ Start Scanning", callback_data=f"admin_startscan_{job_id}"),
                       InlineKeyboardButton("❌ Refuse", callback_data=f"admin_refuse_{job_id}"))
            bot.send_message(ADMIN_ID, f"🔔 Payment received. Place {job['name']}'s document on the scanner and click Start.", reply_markup=markup)

    # --- ADMIN FLIPS PAGE BUTTON ---
    elif action == "admin_flippage":
        bot.edit_message_text("🖨️ Sending even pages to printer...", chat_id=ADMIN_ID, message_id=call.message.message_id)
        
        even_pages_list = job.get('even_pages_list', 'even')
        # Use exact list of pages in reverse order to stop CUPS from padding blank pages
        os.system(f"lp -d {PRINTER_NAME} -o media=A4 -P {even_pages_list} -o outputorder=reverse -o Ink={job['cups_color']} -o fit-to-page '{job['file_path']}'")
        
        time.sleep(5) 
        
        try:
            if os.path.exists(job['file_path']):
                os.remove(job['file_path'])
        except: pass
        
        bot.send_message(user_id, "🎉 Your both-sided print is ready! You can collect it now.")
        bot.send_message(ADMIN_ID, "✅ Both-sided job complete.")

    elif action == "admin_payno":
        new_status = f"❌ Payment rejected for {job['name']}."
        try:
            bot.edit_message_caption(new_status, chat_id=ADMIN_ID, message_id=call.message.message_id)
        except:
            bot.edit_message_text(new_status, chat_id=ADMIN_ID, message_id=call.message.message_id)
            
        bot.send_message(user_id, "❌ Your payment could not be verified. Please try again or contact the admin.\n\n" + PAYMENT_TEXT)
        user_states[user_id] = {'state': 'WAITING_FOR_PAYMENT', 'current_job': job_id}

    # Admin Scan Handling
    elif action == "admin_startscan":
        bot.edit_message_text("⏳ Scanning started...", chat_id=ADMIN_ID, message_id=call.message.message_id)
        bot.send_message(user_id, "✅ Admin has started the scanner. Please wait...")
        
        scan_file = f"/tmp/scanned_{job_id}.pdf"
        
        def run_scanner():
            os.system(f"scanimage --mode Color --resolution 600 -x 210 -y 297 --format=pdf > {scan_file}")
            
        def show_progress():
            msg = bot.send_message(user_id, "Scan progress: 10%")
            time.sleep(15)
            bot.edit_message_text("Scan progress: 50%", chat_id=user_id, message_id=msg.message_id)
            scanner_thread.join() 
            bot.edit_message_text("Scan complete! Uploading...", chat_id=user_id, message_id=msg.message_id)
            
            try:
                with open(scan_file, 'rb') as doc:
                    bot.send_document(user_id, doc, timeout=300)
                bot.send_message(ADMIN_ID, "✅ Scan sent to user.")
            except:
                bot.send_message(user_id, "❌ File too large for Telegram. Admin will send it manually.")
            
            if os.path.exists(scan_file):
                os.remove(scan_file)

        scanner_thread = threading.Thread(target=run_scanner)
        progress_thread = threading.Thread(target=show_progress)
        scanner_thread.start()
        progress_thread.start()

# --- PAYMENT TEXT HANDLING ---
@bot.message_handler(func=lambda message: True)
def handle_text(message):
    user_id = message.from_user.id
    state_info = user_states.get(user_id)

    if message.text.startswith('/'):
        return

    if state_info and state_info.get('state') == 'WAITING_FOR_PAYMENT':
        payment_num = message.text
        job_id = state_info.get('current_job')
        job = jobs.get(job_id)
        
        bot.send_message(user_id, "⏳ Sending payment details to admin...")
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("Yes", callback_data=f"admin_payyes_{job_id}"),
                   InlineKeyboardButton("No", callback_data=f"admin_payno_{job_id}"))
        
        job_type_str = f"Print ({job.get('color_pref', 'PDF')} | {job.get('duplex', 'One-Sided')})" if job['type'] == 'print' else "Scan"          
        admin_msg = f"📥 {job_type_str} Request from '{job['name']}'\nPayment Details: '{payment_num}'\n\nVerify payment?"

        if job['type'] == 'print':
            with open(job['file_path'], 'rb') as doc:
                bot.send_document(ADMIN_ID, doc, caption=admin_msg, reply_markup=markup)
        else:
            bot.send_message(ADMIN_ID, admin_msg, reply_markup=markup)
        
        user_states[user_id] = {'state': 'IDLE'}

bot.infinity_polling()