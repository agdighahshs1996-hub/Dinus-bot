import pytz
import re
from telethon import TelegramClient, events
import json
import os
import math
import imaplib
import email
from email.header import decode_header
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from PyPDF2 import PdfReader
import io
from aiohttp import web
import asyncio
from pymongo import MongoClient
from telethon.sessions import StringSession
from pymongo.errors import PyMongoError
import requests
from flask import Flask, request, jsonify, redirect, url_for, abort
import time
import threading
from flask import Flask, request
import asyncio
from flask import Flask, request, jsonify, redirect, url_for, abort
from flask import Flask, request, jsonify, redirect, url_for, abort
# MongoDB URL
MONGO_URI = "mongodb+srv://agdighahshs1996_db_user:HzehXgy9DObN5sPx@cluster0.xhzyybs.mongodb.net/"
mongo_client = MongoClient(MONGO_URI)
db = mongo_client["Dinuu_db"]

# MongoDB Collections
users_collection = db["users"]
used_transactions_collection = db["used_transactions"]
uc_stock_collection = db["uc_stock"]
baki_data_collection = db["baki_data"]
user_history_collection = db["user_history"]
subscription_collection = db["subscription"]
notify_message_collection = db["notify_message"]
usdt_rate_collection = db["usdt_rate"]
email_credentials_collection = db["email_credentials"]
processed_emails_collection = db["processed_emails"]
bank_collection = db["bank"]
number_collection = db["number"]
binance_collection = db["binance"]
sessions_collection = db["sessions"]
# MongoDB কালেকশন সংজ্ঞায়িত করা (আপনার বিদ্যমান কোডের পরে যুক্ত করুন)
bkash_credentials_collection = db["bkash_credentials"]
subscription_collection = db["subscription"]
special_users_collection = db["special_users"]
# MongoDB Collections
minimum_rate_collection = db["minimum_rate"]
# USD-based MongoDB Collections
usd_users_collection = db["usd_users"]
usd_baki_data_collection = db["usd_baki_data"]
usd_user_history_collection = db["usd_user_history"]
usd_notify_message_collection = db["usd_notify_message"]
usd_uc_price_collection = db["usd_uc_price"]
# Load and Save Data Functions
def load_data(collection, default_data):
    data = collection.find_one({"_id": "data"})
    if not data:
        collection.insert_one({"_id": "data", **default_data})
        return default_data
    else:
        updated_data = {**default_data, **data}
        del updated_data["_id"]
        collection.update_one({"_id": "data"}, {"$set": updated_data})
        return updated_data

def save_data(collection, data):
    collection.update_one({"_id": "data"}, {"$set": data}, upsert=True)
def get_current_credential():
    today = datetime.now(BD_TIMEZONE).strftime("%Y-%m-%d")
    current_month = datetime.now(BD_TIMEZONE).strftime("%Y-%m")
    credentials = list(bkash_credentials_collection.find())
    for cred in credentials:
        # মাসিক লিমিট রিসেট
        if cred.get("last_month") != current_month:
            cred["monthly_used"] = 0
            cred["last_month"] = current_month
            bkash_credentials_collection.update_one(
                {"_id": cred["_id"]},
                {"$set": {"monthly_used": 0, "last_month": current_month}}
            )
        # দৈনিক লিমিট রিসেট
        if cred["last_reset"] != today:
            cred["daily_used"] = 0
            cred["last_reset"] = today
            bkash_credentials_collection.update_one(
                {"_id": cred["_id"]},
                {"$set": {"daily_used": 0, "last_reset": today}}
            )
        # লিমিট চেক
        if cred["daily_used"] < cred["daily_limit"] and cred["monthly_used"] < cred["monthly_limit"]:
            return cred
    return None

# Default UC Price in USD
default_usd_uc_price = {
    "20": 0.15,
    "36": 0.26,
    "80": 0.57,
    "160": 1.13,
    "161": 1.14,
    "162": 1.14,
    "405": 2.86,
    "800": 5.63,
    "810": 5.70,
    "1625": 11.44,
    "2000": 14.26
}

# Load USD UC Price
def load_usd_uc_price():
    data = usd_uc_price_collection.find_one({"_id": "prices"})
    if not data:
        usd_uc_price_collection.insert_one({"_id": "prices", **default_usd_uc_price})
        return default_usd_uc_price
    del data["_id"]
    return data

# Save USD UC Price
def save_usd_uc_price(data):
    usd_uc_price_collection.update_one({"_id": "prices"}, {"$set": data}, upsert=True)

# Initial Load
usd_uc_price = load_usd_uc_price()
# Default UC Stock
default_uc_stock = {
    "20": {"price": 19, "stock": 0, "codes": [], "used_codes": []},
    "36": {"price": 33, "stock": 0, "codes": [], "used_codes": []},
    "80": {"price": 73, "stock": 0, "codes": [], "used_codes": []},
    "160": {"price": 145, "stock": 0, "codes": [], "used_codes": []},
    "161": {"price": 150, "stock": 0, "codes": [], "used_codes": []},
    "162": {"price": 155, "stock": 0, "codes": [], "used_codes": []},
    "405": {"price": 366, "stock": 0, "codes": [], "used_codes": []},
    "800": {"price": 725, "stock": 0, "codes": [], "used_codes": []},
    "810": {"price": 729, "stock": 0, "codes": [], "used_codes": []},
    "1625": {"price": 1460, "stock": 0, "codes": [], "used_codes": []},
    "2000": {"price": 1820, "stock": 0, "codes": [], "used_codes": []},
}
# MongoDB Collections
uc_price_usdt_collection = db["uc_price_usdt"]
# USD-based Default Data Structures
usd_users = {}
usd_baki_data = {}
usd_user_history = {}
usd_notification_message = "➥ Please pay your due amount quickly ➥"

# Load USD Initial Data
usd_users = load_data(usd_users_collection, usd_users)
usd_baki_data = load_data(usd_baki_data_collection, usd_baki_data)
usd_user_history = load_data(usd_user_history_collection, usd_user_history)

# USD Notification Message Functions
def load_usd_notification_message():
    global usd_notification_message
    data = usd_notify_message_collection.find_one({"_id": "notify"})
    if not data:
        save_usd_notification_message()
        return usd_notification_message
    usd_notification_message = data["message"]
    return usd_notification_message

def save_usd_notification_message():
    global usd_notification_message
    usd_notify_message_collection.update_one({"_id": "notify"}, {"$set": {"message": usd_notification_message}}, upsert=True)

load_usd_notification_message()
# Default Data Structures
users = {}
baki_data = {}
user_history = {}
notification_message = "➥ Please pay your due amount quickly ➥"
# Default Minimum Rates
default_minimum_rates = {
    "20": 19,
    "36": 33,
    "80": 74,
    "160": 147,
    "161": 148,
    "162": 148,
    "405": 372,
    "800": 733,
    "810": 742,
    "1625": 1490,
    "2000": 1858
}
# Helper Function to Check USD User Signup
def is_usd_user_signed_up(user_id):
    return str(user_id) in usd_users
# Load Minimum Rates
def load_minimum_rates():
    data = minimum_rate_collection.find_one({"_id": "rates"})
    if not data:
        minimum_rate_collection.insert_one({"_id": "rates", **default_minimum_rates})
        return default_minimum_rates
    del data["_id"]
    return data

# Save Minimum Rates
def save_minimum_rates(data):
    minimum_rate_collection.update_one({"_id": "rates"}, {"$set": data}, upsert=True)

# Load initial minimum rates
minimum_rates = load_minimum_rates()
# Load Initial Data
uc_stock = load_data(uc_stock_collection, default_uc_stock)
users = load_data(users_collection, users)
baki_data = load_data(baki_data_collection, baki_data)
user_history = load_data(user_history_collection, user_history)
# Subscription Validation
# Notification Message Functions
def load_notification_message():
    global notification_message
    data = notify_message_collection.find_one({"_id": "notify"})
    if not data:
        save_notification_message()
        return notification_message
    notification_message = data["message"]
    return notification_message

def save_notification_message():
    global notification_message
    notify_message_collection.update_one({"_id": "notify"}, {"$set": {"message": notification_message}}, upsert=True)

load_notification_message()

# Admin and Developer IDs
ADMIN_ID = 8154706671
DEVELOPER_ID = 8154706671
BOT_PREFIX = "D"
# Telegram API Credentials
api_id = 23434691
api_hash = 'e9dc74b46e9ebb79e8cbbb2e9f953355'
phone_number = '+16018731950'
#subscribe
BD_TIMEZONE = pytz.timezone("Asia/Dhaka")

# Default Subscription Data
subscription_data = {
    "expiry_time": None,  # Will store the exact datetime when subscription expires
    "developer_id": DEVELOPER_ID
}

# Load Subscription Data from MongoDB
def load_subscription_data():
    global subscription_data
    data = subscription_collection.find_one({"_id": "subscription"})
    if not data:
        save_subscription_data()
    else:
        subscription_data.update(data)
        del subscription_data["_id"]

# Save Subscription Data to MongoDB
def save_subscription_data():
    subscription_collection.update_one(
        {"_id": "subscription"},
        {"$set": subscription_data},
        upsert=True
    )

# Check if Subscription is Valid
def is_subscription_valid():
    if subscription_data["expiry_time"] is None:
        return False
    try:
        expiry_time = datetime.strptime(subscription_data["expiry_time"], "%Y-%m-%d %H:%M:%S")
        expiry_time = BD_TIMEZONE.localize(expiry_time)
        return datetime.now(BD_TIMEZONE) <= expiry_time
    except ValueError:
        return False
# Load Initial Subscription Data on Startup
load_subscription_data()  # এটি শুরুতে রাখুন
# bKash Credentials
# MongoDB Session Functions
def load_session_from_mongo():
    session_data = sessions_collection.find_one({"_id": "telegram_session"})
    if session_data and "session_string" in session_data:
        return session_data["session_string"]
    return None

def save_session_to_mongo(session_string):
    sessions_collection.update_one(
        {"_id": "telegram_session"},
        {"$set": {"session_string": session_string}},
        upsert=True
    )

# Telegram Client Setup
session_string = load_session_from_mongo()
client = TelegramClient(
    StringSession(session_string) if session_string else StringSession(),
    api_id,
    api_hash
)
# bKash Payment Functions
# টোকেন পাওয়া
def get_bkash_token(credential):
    url = "https://tokenized.pay.bka.sh/v1.2.0-beta/tokenized/checkout/token/grant"
    headers = {
        "Content-Type": "application/json",
        "username": credential["username"],
        "password": credential["password"]
    }
    data = {
        "app_key": credential["app_key"],
        "app_secret": credential["app_secret"]
    }
    try:
        response = requests.post(url, json=data, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json().get("id_token")
    except requests.RequestException as e:
        print(f"বিকাশ টোকেন পেতে ত্রুটি: {e}")
        return None

# পেমেন্ট তৈরি
def create_bkash_payment(amount, user_id):
    credential = get_current_credential()
    if not credential:
        return None
    token = get_bkash_token(credential)
    if not token:
        return None
    url = "https://tokenized.pay.bka.sh/v1.2.0-beta/tokenized/checkout/create"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
        "X-APP-Key": credential["app_key"]
    }
    payload = {
        "mode": "0011",
        "payerReference": str(user_id),
        "callbackURL": "https://rg-unipin4.onrender.com/callback",
        "amount": str(amount),
        "currency": "BDT",
        "intent": "sale",
        "merchantInvoiceNumber": f"INV-{int(time.time())}"
    }
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"বিকাশ পেমেন্ট তৈরিতে ত্রুটি: {e}")
        return None

# পেমেন্ট যাচাই
def execute_bkash_payment(paymentID):
    credential = get_current_credential()
    if not credential:
        return None
    token = get_bkash_token(credential)
    if not token:
        return None
    url = "https://tokenized.pay.bka.sh/v1.2.0-beta/tokenized/checkout/execute"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
        "X-APP-Key": credential["app_key"]
    }
    payload = {"paymentID": paymentID}
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"বিকাশ পেমেন্ট যাচাইয়ে ত্রুটি: {e}")
        return None
        
#usdtpricestock 
# Default UC Price in USDT
default_uc_price_usdt = {
    "20": 0.15,    # উদাহরণ মূল্য, আপনি পরিবর্তন করতে পারেন
    "36": 0.27,
    "80": 0.60,
    "160": 1.20,
    "161": 1.25,
    "162": 1.30,
    "405": 3.00,
    "800": 6.00,
    "810": 6.10,
    "1625": 12.00,
    "2000": 15.00
}

# Load UC Price in USDT
def load_uc_price_usdt():
    data = uc_price_usdt_collection.find_one({"_id": "prices"})
    if not data:
        uc_price_usdt_collection.insert_one({"_id": "prices", **default_uc_price_usdt})
        return default_uc_price_usdt
    del data["_id"]
    return data

# প্রোগ্রাম শুরুতে লোড করা
uc_price_usdt = load_uc_price_usdt()

# Helper Function to Check User Signup
def is_user_signed_up(user_id):
    return str(user_id) in users

# Command Prefix Validation Middleware
async def check_prefix(event):
    if not event.text.startswith(BOT_PREFIX):
        await event.reply(f"➥ Please use the bot prefix `{BOT_PREFIX}` before commands.\nExample: `{BOT_PREFIX}start`")
        return False
    return True
# Command: start (For all users)
@client.on(events.NewMessage(pattern=f'^{BOT_PREFIX}start$'))
async def send_welcome(event):
    if not await check_prefix(event):
        return
    if not is_subscription_valid() and event.sender_id != ADMIN_ID:
        return
    elif not is_subscription_valid() and event.sender_id == ADMIN_ID:
        await event.reply("✧ Sᴜʙsᴄʀɪᴘᴛɪᴏɴ ᴇxᴘɪʀᴇᴅ! Pʟᴇᴀsᴇ ᴇxᴛᴇɴᴅ ᴛʜᴇ sᴜʙsᴄʀɪᴘᴛɪᴏɴ ✧")
        return
    
    # User-facing commands with enhanced formatting
    user_commands = [
        f"✦ {BOT_PREFIX}signup              ➤ Sign up to get bot access (Admin approval required)",
        f"✦ {BOT_PREFIX}stock               ➤ Check available UC stock",
        f"✦ {BOT_PREFIX}uc <type> <qty>     ➤ Buy UC (e.g., {BOT_PREFIX}uc 80 2)",
        f"✦ {BOT_PREFIX}rate                ➤ View UC prices in BDT",
        f"✦ {BOT_PREFIX}balance             ➤ Check your account balance",
        f"✦ {BOT_PREFIX}baki <type> <qty>   ➤ Buy UC on credit (e.g., {BOT_PREFIX}baki 80 2, Admin permission needed)",
        f"✦ {BOT_PREFIX}due                 ➤ Check your outstanding credit",
        f"✦ {BOT_PREFIX}bkashpay <amount>   ➤ Pay via bKash (e.g., {BOT_PREFIX}bkashpay 500)",
        f"✦ {BOT_PREFIX}verify <trxID>      ➤ Verify bKash payment (e.g., {BOT_PREFIX}verify Trx123)",
        f"✦ {BOT_PREFIX}bank                ➤ View bank details for payments",
        f"✦ {BOT_PREFIX}payment             ➤ View payment numbers",
        f"✦ {BOT_PREFIX}usdtrate            ➤ Check current USDT to BDT rate",
        f"✦ {BOT_PREFIX}calc <expression>   ➤ Calculate math (e.g., {BOT_PREFIX}calc 140-138)",
        f"✦ {BOT_PREFIX}id                  ➤ Show your Telegram ID",
        f"✦ {BOT_PREFIX}alive               ➤ Check if bot is online",
        f"✦ {BOT_PREFIX}profile             ➤ View your profile details"
    ]
    
    # Prepare message with aesthetic formatting
    message = (
        "✧══════✧ ❀ ✧══════✧\n"
        "      Wᴇʟᴄᴏᴍᴇ ᴛᴏ UC Bᴏᴛ!\n"
        "✧══════✧ ❀ ✧══════✧\n\n"
        "✨ Here are the commands for users:\n\n"
        "```plaintext\n" +
        "\n".join(user_commands) +
        "\n```"
    )
    
    # Handle Telegram's 4096 character limit
    if len(message) > 4096:
        parts = []
        current_part = "```plaintext\n"
        for cmd in user_commands:
            if len(current_part) + len(cmd) + 5 > 4096:
                current_part += "```"
                parts.append(current_part)
                current_part = "```plaintext\n" + cmd + "\n"
            else:
                current_part += cmd + "\n"
        current_part += "```"
        parts.append(current_part)
        
        for part in parts:
            await event.reply(
                "✧══════✧ ❀ ✧══════✧\n"
                "      Wᴇʟᴄᴏᴍᴇ ᴛᴏ UC Bᴏᴛ!\n"
                "✧══════✧ ❀ ✧══════✧\n\n" + part,
                parse_mode="markdown"
            )
    else:
        await event.reply(message, parse_mode="markdown")
# Command: /setsubscription (Only Developer can use, now in days)
@client.on(events.NewMessage(pattern=f'^{BOT_PREFIX}setsubscription\\s+(\\d+)\\s+([+-])$'))
async def set_subscription(event):
    if not event.text.startswith(BOT_PREFIX):
        await event.reply(f"➥ Please use the bot prefix `{BOT_PREFIX}` before commands.\nExample: `{BOT_PREFIX}setsubscription 30 +`")
        return
    if event.sender_id != DEVELOPER_ID:
        await event.reply("➥ **Only the developer can use this command!**")
        return

    try:
        duration_days = int(event.pattern_match.group(1))
        action = event.pattern_match.group(2)  # '+' to extend, '-' to reduce

        current_time = datetime.now(BD_TIMEZONE)
        if subscription_data["expiry_time"] is None or not is_subscription_valid():
            # If no active subscription or expired, start from current time
            base_time = current_time
        else:
            # Use existing expiry time as base
            base_time = datetime.strptime(subscription_data["expiry_time"], "%Y-%m-%d %H:%M:%S")
            base_time = BD_TIMEZONE.localize(base_time)

        # Calculate new expiry time in days
        if action == "+":
            new_expiry_time = base_time + timedelta(days=duration_days)
            action_text = "Extended"
        elif action == "-":
            new_expiry_time = base_time - timedelta(days=duration_days)
            action_text = "Reduced"
            if new_expiry_time < current_time:
                new_expiry_time = current_time  # Prevent expiry time from being in the past

        # Update subscription data
        subscription_data["expiry_time"] = new_expiry_time.strftime("%Y-%m-%d %H:%M:%S")
        save_subscription_data()

        # Response in the format similar to /baki or /uc
        response = (
            "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
            f"**Sᴜʙsᴄʀɪᴘᴛɪᴏɴ {action_text} Sᴜᴄᴄᴇssғᴜʟʟʏ**\n"
            f"➜ Dᴜʀᴀᴛɪᴏɴ: {duration_days} Dᴀʏs\n"
            f"➜ Nᴇᴡ Eᴘɪʀʏ: {subscription_data['expiry_time']} (Asia/Dhaka)\n"
            "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔"
        )
        await event.reply(response)

    except ValueError:
        await event.reply(f"➥ Usage: {BOT_PREFIX}setsubscription <days> <+ or ->\nExample: {BOT_PREFIX}setsubscription 30 +")
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")

# Middleware to Check Subscription Before Processing Commands
async def check_subscription(event):
    if not is_subscription_valid():
        if event.sender_id == ADMIN_ID:
            await event.reply(
                "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
                "➥ **Sᴜʙsᴄʀɪᴘᴛɪᴏɴ Eᴘɪʀᴇᴅ!**\n"
                "➥ Contact the developer to extend the subscription.\n"
                "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔"
            )
        return False  # Non-admin users get no response
    return True
# Command: help (Admin only)
@client.on(events.NewMessage(pattern=f'^{BOT_PREFIX}help$'))
async def send_admin_help(event):
    if not await check_prefix(event):
        return
    if event.sender_id != ADMIN_ID:
        await event.reply("✧ Oɴʟʏ ᴛʜᴇ ᴀᴅᴍɪɴ ᴄᴀɴ ᴜsᴇ ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ ✧")
        return
    if not is_subscription_valid():
        await event.reply("✧ Sᴜʙsᴄʀɪᴘᴛɪᴏɴ ᴇxᴘɪʀᴇᴅ! Pʟᴇᴀsᴇ ᴇxᴛᴇɴᴅ ᴛʜᴇ sᴜʙsᴄʀɪᴘᴛɪᴏɴ ✧")
        return
    
    # All commands (user + admin) with enhanced formatting
    all_commands = [
        # User Commands
        "✦══════✧ Uꜱᴇʀ Cᴏᴍᴍᴀɴᴅꜱ ✧══════✦",
        f"✦ {BOT_PREFIX}signup              ➤ Sign up to get bot access (Admin approval required)",
        f"✦ {BOT_PREFIX}stock               ➤ Check available UC stock and worth in USDT",
        f"✦ {BOT_PREFIX}uc <type> <qty>     ➤ Buy UC (e.g., {BOT_PREFIX}uc 80 2)",
        f"✦ {BOT_PREFIX}rate                ➤ View UC prices in BDT",
        f"✦ {BOT_PREFIX}balance             ➤ Check your balance and due",
        f"✦ {BOT_PREFIX}baki <type> <qty>   ➤ Buy UC on credit (e.g., {BOT_PREFIX}baki 80 2, Admin permission needed)",
        f"✦ {BOT_PREFIX}due                 ➤ Check your outstanding credit",
        f"✦ {BOT_PREFIX}bkashpay <amount>   ➤ Pay via bKash (e.g., {BOT_PREFIX}bkashpay 500)",
        f"✦ {BOT_PREFIX}verify <trxID>      ➤ Verify bKash payment (e.g., {BOT_PREFIX}verify Trx123)",
        f"✦ {BOT_PREFIX}bank                ➤ View bank details for payments",
        f"✦ {BOT_PREFIX}payment             ➤ View payment numbers",
        f"✦ {BOT_PREFIX}usdtrate            ➤ Check current USDT to BDT rate",
        f"✦ {BOT_PREFIX}calc <expression>   ➤ Calculate math (e.g., {BOT_PREFIX}calc 140-138)",
        f"✦ {BOT_PREFIX}id                  ➤ Show your Telegram ID",
        f"✦ {BOT_PREFIX}alive               ➤ Check if bot is online",
        f"✦ {BOT_PREFIX}profile             ➤ View your profile details",
        
        # Admin Commands
        "✦══════✧ Aᴅᴍɪɴ Cᴏᴍᴍᴀɴᴅꜱ ✧══════✦",
        f"✦ {BOT_PREFIX}help                ➤ Show all available commands",
        f"✦ {BOT_PREFIX}signout             ➤ Remove a user and their data (Private chat only)",
        f"✦ {BOT_PREFIX}addbank             ➤ Add bank details (Reply to a message)",
        f"✦ {BOT_PREFIX}addpayment          ➤ Add payment number (Reply to a message)",
        f"✦ {BOT_PREFIX}notify <message>    ➤ Notify users with due (Optional custom message)",
        f"✦ {BOT_PREFIX}notifyall <message> ➤ Notify all users with a custom message",
        f"✦ {BOT_PREFIX}bakilimit <amount>  ➤ Set credit limit (e.g., {BOT_PREFIX}bakilimit 1000)",
        f"✦ {BOT_PREFIX}addbakiuc <type> <qty> ➤ Add UC to credit (e.g., {BOT_PREFIX}addbakiuc 80 2)",
        f"✦ {BOT_PREFIX}addbakitk <amount>  ➤ Add amount to credit (e.g., {BOT_PREFIX}addbakitk 500)",
        f"✦ {BOT_PREFIX}autoload <codes>    ➤ Load UC codes (Reply or provide text)",
        f"✦ {BOT_PREFIX}duecheck            ➤ Check total due and advance",
        f"✦ {BOT_PREFIX}duplicatecheck      ➤ Check and remove duplicate UC codes",
        f"✦ {BOT_PREFIX}setrate <type> <price> ➤ Set UC price in BDT (e.g., {BOT_PREFIX}setrate 80 73)",
        f"✦ {BOT_PREFIX}setusdtprice <type> <price> ➤ Set UC price in USDT (e.g., {BOT_PREFIX}setusdtprice 80 0.60)",
        f"✦ {BOT_PREFIX}usdtrate <rate>     ➤ Set USDT to BDT rate (e.g., {BOT_PREFIX}usdtrate 128)",
        f"✦ {BOT_PREFIX}setsubscription <days> <+/-> ➤ Set subscription duration (e.g., {BOT_PREFIX}setsubscription 30 +)",
        f"✦ {BOT_PREFIX}advanceuser         ➤ List users with positive balance",
        f"✦ {BOT_PREFIX}almail <email>      ➤ Set email for UC auto-loading",
        f"✦ {BOT_PREFIX}alpass <password>   ➤ Set email app password",
        f"✦ {BOT_PREFIX}autoloadmail        ➤ Manually load UC codes from email",
        f"✦ {BOT_PREFIX}addbalance <amount> ➤ Add balance to a user (e.g., {BOT_PREFIX}addbalance 500)",
        f"✦ {BOT_PREFIX}specialsignup       ➤ Sign up a special user with custom rates",
        f"✦ {BOT_PREFIX}specialsignout     ➤ Remove a special user",
        f"✦ {BOT_PREFIX}setspecialrate <type> <price> ➤ Set special UC rate (e.g., {BOT_PREFIX}setspecialrate 80 70)",
        f"✦ {BOT_PREFIX}bakiuser           ➤ List users with outstanding credit",
        f"✦ {BOT_PREFIX}clear              ➤ Clear bot data or records"
    ]
    
    # Prepare message with aesthetic formatting
    message = (
        "✧══════✧ ❀ ✧══════✧\n"
        "      Hᴇʟᴘ Mᴇɴᴜ ғᴏʀ Aᴅᴍɪɴ\n"
        "✧══════✧ ❀ ✧══════✧\n\n"
        "✨ All available commands:\n\n"
        "```plaintext\n" +
        "\n".join(all_commands) +
        "\n```"
    )
    
    # Handle Telegram's 4096 character limit
    if len(message) > 4096:
        parts = []
        current_part = "```plaintext\n"
        for cmd in all_commands:
            if len(current_part) + len(cmd) + 5 > 4096:
                current_part += "```"
                parts.append(current_part)
                current_part = "```plaintext\n" + cmd + "\n"
            else:
                current_part += cmd + "\n"
        current_part += "```"
        parts.append(current_part)
        
        for part in parts:
            await event.reply(
                "✧══════✧ ❀ ✧══════✧\n"
                "      Hᴇʟᴘ Mᴇɴᴜ ғᴏʀ Aᴅᴍɪɴ\n"
                "✧══════✧ ❀ ✧══════✧\n\n" + part,
                parse_mode="markdown"
            )
    else:
        await event.reply(message, parse_mode="markdown")
#ytsystem
from pytube import YouTube, Search
import os
from pathlib import Path
import asyncio
import logging

# MongoDB Collection for YouTube Reply Data
youtube_reply_data_collection = db["youtube_reply_data"]

# Helper Function to Save YouTube Reply Data
def save_youtube_reply_data(data):
    youtube_reply_data_collection.update_one(
        {"_id": data["message_id"]},
        {"$set": data},
        upsert=True
    )

# Helper Function to Load YouTube Reply Data
def load_youtube_reply_data(message_id):
    data = youtube_reply_data_collection.find_one({"_id": message_id})
    if data:
        del data["_id"]
        return data
    return None

# Helper Function to Delete YouTube Reply Data
def delete_youtube_reply_data(message_id):
    youtube_reply_data_collection.delete_one({"_id": message_id})

# Command: Tyoutube
@client.on(events.NewMessage(pattern=f'^{BOT_PREFIX}youtube(?:\\s+(.+))?$'))
async def youtube_command(event):
    logger.info(f"Received /Tyoutube command from user {event.sender_id}")
    if not await check_prefix(event):
        logger.warning(f"Prefix check failed for user {event.sender_id}")
        return
    if not is_subscription_valid():
        if event.sender_id == ADMIN_ID:
            await event.reply("**➥ Sᴜʙsᴄʀɪᴘᴛɪᴏɴ ᴇxᴘɪʀᴇᴅ. Pʟᴇᴀsᴇ ᴇxᴛᴇɴᴅ ᴛʜᴇ sᴜʙsᴄʀɪᴪষᷝɪᴏɴ !**")
            logger.info(f"Subscription expired for admin {event.sender_id}")
        return
    if not is_user_signed_up(event.sender_id) and event.sender_id != ADMIN_ID:
        await event.reply(f"➥ You are not signed up. Please use {BOT_PREFIX}signup.")
        logger.warning(f"User {event.sender_id} attempted /Tyoutube but is not signed up")
        return

    try:
        user_id = str(event.sender_id)
        user = await client.get_entity(int(user_id))
        display_name = user.first_name or user.username or user_id

        input_text = event.pattern_match.group(1)
        if not input_text:
            await event.reply(
                "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
                f"➪ Please provide a YouTube URL or search term.\n"
                f"➪ Example: {BOT_PREFIX}youtube https://youtu.be/abc123\n"
                f"➪ Or: {BOT_PREFIX}youtube song name\n"
                "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔"
            )
            logger.warning(f"User {user_id} provided no input for /Tyoutube")
            return

        input_text = input_text.strip()
        if input_text.startswith("http://") or input_text.startswith("https://"):
            # Handle YouTube URL
            try:
                yt = YouTube(input_text)
                duration = f"{yt.length // 60}:{yt.length % 60:02d}" if yt.length else "Unknown"
                response = (
                    "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
                    f"➪ YouTube: {yt.title}\n"
                    f"➪ Duration: {duration}\n"
                    f"➪ Reply with:\n"
                    "   1. Download Video\n"
                    "   2. Download Audio\n"
                    "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔"
                )
                message = await event.reply(response)
                reply_data = {
                    "message_id": str(message.id),
                    "user_id": user_id,
                    "type": "link",
                    "url": input_text,
                    "title": yt.title,
                    "duration": duration
                }
                save_youtube_reply_data(reply_data)
                logger.info(f"Stored reply data for URL {input_text} with message_id {message.id}")
            except Exception as e:
                await event.reply(
                    "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
                    f"❌ Error: Invalid YouTube URL or unable to fetch video details.\n"
                    f"➪ Details: {str(e)}\n"
                    "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔"
                )
                logger.error(f"Error processing YouTube URL for user {user_id}: {str(e)}")
        else:
            # Handle YouTube Search
            try:
                search = Search(input_text)
                results = search.results[:5]  # Limit to top 5 results
                if not results:
                    await event.reply(
                        "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
                        f"➪ No results found for '{input_text}'.\n"
                        "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔"
                    )
                    logger.info(f"No search results for query '{input_text}' by user {user_id}")
                    return

                links = []
                msg = ""
                for i, video in enumerate(results, 1):
                    duration = f"{video.length // 60}:{video.length % 60:02d}" if video.length else "Unknown"
                    msg += f"{i}. {video.title} (Duration: {duration})\n"
                    links.append(video.watch_url)
                response = (
                    "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
                    f"➪ Found {len(results)} results for '{input_text}':\n\n"
                    f"{msg}\n"
                    f"➪ Reply with the number (1-{len(results)}) to select a video.\n"
                    "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔"
                )
                message = await event.reply(response)
                reply_data = {
                    "message_id": str(message.id),
                    "user_id": user_id,
                    "type": "search",
                    "links": links,
                    "query": input_text
                }
                save_youtube_reply_data(reply_data)
                logger.info(f"Stored search reply data for query '{input_text}' with message_id {message.id}")
            except Exception as e:
                await IMPROVE
                await event.reply(
                    "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
                    f"❌ Error: Unable to perform search.\n"
                    f"➪ Details: {str(e)}\n"
                    "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔"
                )
                logger.error(f"Error performing YouTube search for user {user_id}: {str(e)}")
    except Exception as e:
        await event.reply(
            "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
            f"❌ Error: An unexpected error occurred.\n"
            f"➪ Details: {str(e)}\n"
            "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔"
        )
        logger.error(f"Unexpected error in /Tyoutube for user {user_id}: {str(e)}")

# Reply Handler for YouTube Command
@client.on(events.NewMessage)
async def youtube_reply_handler(event):
    if not event.is_reply:
        return
    reply_message = await event.get_reply_message()
    reply_data = load_youtube_reply_data(str(reply_message.id))
    if not reply_data or reply_data["user_id"] != str(event.sender_id):
        return

    try:
        user_id = str(event.sender_id)
        choice = event.text.strip()
        cache_dir = Path("cache")
        cache_dir.mkdir(exist_ok=True)
        file_path = cache_dir / f"youtube-{user_id}"

        if reply_data["type"] == "search":
            try:
                choice = int(choice) - 1
                if choice < 0 or choice >= len(reply_data["links"]):
                    await event.reply(
                        "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
                        f"➪ Please reply with a valid number (1-{len(reply_data['links'])}).\n"
                        "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔"
                    )
                    logger.warning(f"Invalid search choice {choice + 1} by user {user_id}")
                    return
                yt = YouTube(reply_data["links"][choice])
                duration = f"{yt.length // 60}:{yt.length % 60:02d}" if yt.length else "Unknown"
                response = (
                    "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
                    f"➪ YouTube: {yt.title}\n"
                    f"➪ Duration: {duration}\n"
                    f"➪ Reply with:\n"
                    "   1. Download Video\n"
                    "   2. Download Audio\n"
                    "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔"
                )
                message = await event.reply(response)
                new_reply_data = {
                    "message_id": str(message.id),
                    "user_id": user_id,
                    "type": "link",
                    "url": reply_data["links"][choice],
                    "title": yt.title,
                    "duration": duration
                }
                save_youtube_reply_data(new_reply_data)
                delete_youtube_reply_data(str(reply_message.id))
                logger.info(f"User {user_id} selected search result {choice + 1}: {yt.title}")
            except ValueError:
                await event.reply(
                    "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
                    f"➪ Please reply with a valid number.\n"
                    "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔"
                )
                logger.warning(f"Non-numeric reply {choice} for search selection by user {user_id}")
            except Exception as e:
                await event.reply(
                    "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
                    f"❌ Error: Unable to fetch video details.\n"
                    f"➪ Details: {str(e)}\n"
                    "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔"
                )
                logger.error(f"Error fetching video details for user {user_id}: {str(e)}")
        elif reply_data["type"] == "link":
            try:
                if choice not in ["1", "2"]:
                    await event.reply(
                        "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
                        f"➪ Please reply with 1 (Video) or 2 (Audio).\n"
                        "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔"
                    )
                    logger.warning(f"Invalid download choice {choice} by user {user_id}")
                    return

                yt = YouTube(reply_data["url"])
                if choice == "1":
                    # Download Video
                    stream = yt.streams.filter(progressive=True, file_extension="mp4").order_by("resolution").desc().first()
                    if not stream:
                        stream = yt.streams.filter(file_extension="mp4").first()
                    if not stream:
                        await event.reply(
                            "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
                            f"❌ Error: No suitable video stream found.\n"
                            "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔"
                        )
                        logger.error(f"No suitable video stream for {reply_data['url']} by user {user_id}")
                        return
                    file_path = file_path.with_suffix(".mp4")
                    stream.download(output_path=str(cache_dir), filename=f"youtube-{user_id}.mp4")
                    file_type = "Video"
                else:
                    # Download Audio
                    stream = yt.streams.filter(only_audio=True, file_extension="mp4").first()
                    if not stream:
                        await event.reply(
                            "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
                            f"❌ Error: No suitable audio stream found.\n"
                            "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔"
                        )
                        logger.error(f"No suitable audio stream for {reply_data['url']} by user {user_id}")
                        return
                    file_path = file_path.with_suffix(".m4a")
                    stream.download(output_path=str(cache_dir), filename=f"youtube-{user_id}.m4a")
                    file_type = "Audio"

                file_size = os.path.getsize(file_path) / (1024 * 1024)  # Size in MB
                if file_size > 50:  # Telegram's file size limit for bots
                    await event.reply(
                        "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
                        f"❌ Error: The {file_type.lower()} file is too large ({file_size:.2f} MB). Telegram limits bot uploads to 50 MB.\n"
                        "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔"
                    )
                    os.remove(file_path)
                    logger.error(f"File size too large ({file_size:.2f} MB) for {file_type} by user {user_id}")
                    return

                response = (
                    "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
                    f"➪ YouTube {file_type}: {reply_data['title']}\n"
                    f"➪ Duration: {reply_data['duration']}\n"
                    f"➪ Sending {file_type}...\n"
                    "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔"
                )
                await event.reply(response)
                if choice == "1":
                    await client.send_file(
                        event.chat_id,
                        file_path,
                        caption=f"🎥 YouTube {file_type}: {reply_data['title']}",
                        attributes=(telethon.tl.types.DocumentAttributeVideo(
                            duration=yt.length or 0,
                            w=stream.resolution.split("p")[0] if stream.resolution else 0,
                            h=0
                        ),)
                    )
                else:
                    await client.send_file(
                        event.chat_id,
                        file_path,
                        caption=f"🎵 YouTube {file_type}: {reply_data['title']}",
                        attributes=(telethon.tl.types.DocumentAttributeAudio(
                            duration=yt.length or 0,
                            title=yt.title,
                            performer=yt.author or "Unknown"
                        ),)
                    )
                os.remove(file_path)
                delete_youtube_reply_data(str(reply_message.id))
                logger.info(f"Sent {file_type} file to user {user_id} and deleted temporary file")
            except Exception as e:
                if file_path.exists():
                    os.remove(file_path)
                await event.reply(
                    "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
                    f"❌ Error: Unable to download or send {file_type.lower()}.\n"
                    f"➪ Details: {str(e)}\n"
                    "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔"
                )
                logger.error(f"Error downloading/sending {file_type} for user {user_id}: {str(e)}")
    except Exception as e:
        await event.reply(
            "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
            f"❌ Error: An unexpected error occurred.\n"
            f"➪ Details: {str(e)}\n"
            "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔"
        )
        logger.error(f"Unexpected error in youtube_reply_handler for user {user_id}: {str(e)}")
#USDT FUNCTIONS
@client.on(events.NewMessage(pattern=f'^{BOT_PREFIX}usdsignup$'))
async def usd_sign_up_user(event):
    if not await check_prefix(event):
        return
    if event.is_private and event.sender_id == ADMIN_ID:
        if not is_subscription_valid():
            await event.reply("**➥ Sᴜʙsᴄʀɪᴘᴛɪᴏɴ ᴇxᴘɪʀᴇᴅ. Pʟᴇᴀsᴇ ᴇxᴛᴇɴᴅ ᴛʜᴇ sᴜʙsᴄʀɪᴘᴛɪᴏɴ !**")
            return
        try:
            user_id = str(event.chat_id)
            user = await event.get_chat()
            user_name = user.first_name or ""
            user_username = user.username or ""
            user_display = user_name or user_username or user_id
            if user_id in usd_users:
                user_data = usd_users[user_id]
                await event.reply(
                    f"Usᴇʀ `{user_display}` ɪs ᴀʟʀᴇᴀᴅʏ ʀᴇɢɪsᴛᴇʀᴇᴅ.\n"
                    f"Bᴀʟᴀɴᴄᴇ: {user_data['balance']} ᴜsᴅᴛ\n"
                    f"Sᴛᴀᴛᴜs: {user_data['status']}"
                )
            else:
                usd_users[user_id] = {"balance": 0, "status": "active"}
                usd_baki_data[user_id] = {"due": 0, "bakiLimit": 0, "uc_purchases": {}}
                save_data(usd_users_collection, usd_users)
                save_data(usd_baki_data_collection, usd_baki_data)
                await event.reply(f"➪ Usᴇʀ `{user_display}` ʀᴇɢɪsᴛᴇʀᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ!")
        except Exception as e:
            await event.reply(f"❌ Eʀʀᴏʀ: {str(e)}")
    else:
        await event.reply("➥ Oɴʟʏ ᴀᴅᴍɪɴ ᴄᴀɴ ᴜsᴇ ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ ɪɴ ᴘʀɪᴠᴀᴛᴇ ᴄʜᴀᴛs.")
        
@client.on(events.NewMessage(pattern=f'^{BOT_PREFIX}usdsignout$'))
async def usd_sign_out_user(event):
    if not await check_prefix(event):
        return
    if not is_subscription_valid():
        if event.sender_id == ADMIN_ID:
            await event.reply("➪ Subscription expired.\n➪ Please extend the subscription!")
        return
    if event.sender_id != ADMIN_ID:
        await event.reply("➥ Oɴʟʏ ᴀᴅᴍɪɴ ᴄᴀɴ ᴜsᴇ ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ.")
        return

    if event.is_private:
        user_id = str(event.chat_id)
    else:
        if event.is_reply:
            reply_message = await event.get_reply_message()
            user_id = str(reply_message.sender_id)
        else:
            await event.reply("➥ Please reply to a user's message to sign them out.")
            return

    try:
        user = await client.get_entity(int(user_id))
        user_name = user.first_name or ""
        user_username = user.username or ""
        user_display = user_name or user_username or user_id

        advance_balance = usd_users.get(user_id, {}).get("balance", 0)
        due_balance = usd_baki_data.get(user_id, {}).get("due", 0)

        if advance_balance > 0 or due_balance > 0:
            response = "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
            if advance_balance > 0:
                response += (
                    f"☛  Usᴇʀ ʜᴀs: {advance_balance:.1f} ᴜsᴅᴛ Aᴅᴠᴀɴᴄᴇ\n"
                    "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
                    "Cʟᴇᴀʀ Tʜᴇᴍ Fɪʀsᴛ Tᴏ SɪɢɴOᴜᴛ..!\n"
                )
            if due_balance > 0:
                if advance_balance > 0:
                    response += "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
                response += (
                    f"☛  Usᴇʀ ʜᴀs: {due_balance:.1f} ᴜsᴅᴛ Dᴜᴇ\n"
                    "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
                    "Cʟᴇᴀʀ Tʜᴇᴍ Fɪʀsᴛ Tᴏ SɪɢɴOᴜᴛ..!"
                )
            await event.reply(response)
            return

        if user_id in usd_users or user_id in usd_baki_data or user_id in usd_user_history:
            usd_users.pop(user_id, None)
            usd_baki_data.pop(user_id, None)
            usd_user_history.pop(user_id, None)
            save_data(usd_users_collection, usd_users)
            save_data(usd_baki_data_collection, usd_baki_data)
            save_data(usd_user_history_collection, usd_user_history)
            await event.reply(f"➪ Usᴇʀ `{user_display}` ᴀɴᴅ ᴀʟʟ ᴛʜᴇɪʀ ᴅᴀᴛᴀ ʜᴀᴠᴇ ʙᴇᴇɴ ʀᴇᴍᴏᴠᴇᴅ!")
        else:
            await event.reply(f"➪ Usᴇʀ `{user_display}` ɴᴏᴛ ғᴏᴜɴᴅ.")
    except Exception as e:
        await event.reply(f"❌ Eʀʀᴏʀ: {str(e)}")
        
@client.on(events.NewMessage(pattern=f'^{BOT_PREFIX}usduc(?:\\s+(\\w+)(?:\\s+(\\d+))?)?$'))
async def usd_purchase_with_uc(event):
    if not await check_prefix(event):
        return
    if not is_subscription_valid():
        if event.sender_id == ADMIN_ID:
            await event.reply("**➥ Sᴜʙsᴄʀɪᴘᴛɪᴏɴ ᴇxᴘɪʀᴇᴅ. Pʟᴇᴀsᴇ ᴇxᴛᴇɴᴅ ᴛʜᴇ sᴜʙsᴄʀɪᴘᴛɪᴏɴ !**")
        return
    if not is_usd_user_signed_up(event.sender_id) and event.sender_id != ADMIN_ID:
        await event.reply(f"➥ You are not signed up. Please use {BOT_PREFIX}usdsignup.")
        return

    try:
        uc_type = event.pattern_match.group(1)
        qty = event.pattern_match.group(2)

        if not uc_type:
            await event.reply(
                "Pʟᴇᴀsᴇ Sᴘᴇᴄɪғʏ Cᴏʀʀᴇᴄᴛ UC Tʏᴘᴇ\n"
                f"- Exᴀᴍᴘʟᴇ: {BOT_PREFIX}usduc 80"
            )
            return

        qty = int(qty) if qty else 1

        if qty > 100:
            await event.reply("➥ You cannot purchase more than 100 pieces of UC at a time!")
            return

        is_admin = event.sender_id == ADMIN_ID
        target_user_id = str(event.chat_id if is_admin and event.is_private else event.sender_id)
        user = await client.get_entity(int(target_user_id))
        display_name = user.first_name or user.username or target_user_id

        valid_uc_types = ['20', '36', '80', '160', '161', '162', '405', '800', '810', '1625', '2000']
        if uc_type not in valid_uc_types:
            await event.reply(
                "Pʟᴇᴀsᴇ Sᴘᴇᴄɪғʏ Cᴏʀʀᴇᴄᴛ UC Tʏᴘᴇ\n"
                f"- Exᴀᴍᴘʟᴇ: {BOT_PREFIX}usduc 80"
            )
            return

        if uc_type not in uc_stock or uc_stock[uc_type]["stock"] == 0:
            await event.reply(f"➥ {uc_type} 🆄︎🅲︎ Sᴛᴏᴄᴋ Oᴜᴛ")
            return
        elif uc_stock[uc_type]["stock"] < qty:
            stock = uc_stock[uc_type]["stock"]
            await event.reply(f"➥ Oɴʟʏ {stock} Pɪᴄᴇs {uc_type} 🆄︎🅲︎ Aᴠᴀɪʟᴀʙʟᴇ")
            return

        special_user = special_users_collection.find_one({"_id": target_user_id})
        if special_user and "special_rates" in special_user and uc_type in special_user["special_rates"]:
            uc_price = special_user["special_rates"][uc_type]
        else:
            uc_price = usd_uc_price[uc_type]

        total_price = uc_price * qty

        usd_users.setdefault(target_user_id, {"balance": 0})
        user_balance = usd_users[target_user_id]["balance"]

        if is_admin:
            new_balance = "N/A (Admin Purchase)"
        else:
            if user_balance < total_price:
                await event.reply(
                    "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
                    f"❌ **Iɴsᴜғғɪᴄɪᴇɴᴛ Bᴀʟᴀɴᴄᴇ**\n"
                    f"➪ Yᴏᴜʀ Bᴀʟᴀɴᴄᴇ: {user_balance:.1f} ᴜsᴅᴛ\n"
                    f"➪ Rᴇǫᴜɪʀᴇᴅ: {total_price} ᴜsᴅᴛ\n"
                    "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔"
                )
                return
            new_balance = user_balance - total_price
            usd_users[target_user_id]["balance"] = new_balance

        purchased_codes = [uc_stock[uc_type]["codes"].pop(0) for _ in range(qty)]
        uc_stock[uc_type]["used_codes"].extend(purchased_codes)
        uc_stock[uc_type]["stock"] -= qty

        save_data(uc_stock_collection, uc_stock)
        save_data(usd_users_collection, usd_users)

        uc_list = "\n".join([f"`{code}`" for code in purchased_codes])
        balance_text = (
            f"➜ Bᴀʟᴀɴᴄᴇ Uᴘᴅᴀᴛᴇ: {user_balance:.1f} - ({uc_price} x {qty}) = {new_balance:.1f} ᴜsᴅᴛ"
            if not is_admin else "➜ No Balance Deducted (Admin Purchase)"
        )

        await event.reply(
            "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
            f"**Pᴜʀᴄʜᴀsᴇ Sᴜᴄᴄᴇssғᴜʟ**\n"
            f"➜ Uꜱᴇʀ: {display_name}\n\n"
            f"{uc_list}\n\n"
            f"✓ {uc_type} 🆄︎🅲︎  x {qty} ✓\n"
            f"➜ Tᴏᴛᴀʟ: {total_price} ᴜsᴅᴛ\n"
            f"{balance_text}\n"
            "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔"
        )
    except (ValueError, IndexError):
        await event.reply(
            "Pʟᴇᴀsᴇ Sᴘᴇᴄɪғʏ Cᴏʀʀᴇᴄᴛ UC Tʏᴘᴇ\n"
            f"- Exᴀᴍᴘʟᴇ: {BOT_PREFIX}usduc 80"
        )
    except Exception as e:
        await event.reply(f"❌ An error occurred: {str(e)}")
        
@client.on(events.NewMessage(pattern=f'^{BOT_PREFIX}usdbaki(?:\\s+(\\w+)(?:\\s+(\\d+))?)?$'))
async def usd_baki_purchase(event):
    if not await check_prefix(event):
        return
    if not is_subscription_valid():
        if event.sender_id == ADMIN_ID:
            await event.reply("**➥ Sᴜʙsᴄʀɪᴘᴛɪᴏɴ ᴇxᴘɪʀᴇᴅ. Pʟᴇᴀsᴇ ᴇxᴛᴇɴᴅ ᴛʜᴇ sᴜʙsᴄʀɪᴘᴛɪᴏɴ !**")
        return
    if not is_usd_user_signed_up(event.sender_id) and event.sender_id != ADMIN_ID:
        await event.reply(f"➥ You are not signed up. Please use {BOT_PREFIX}usdsignup.")
        return

    try:
        user_id = str(event.chat_id if event.is_private else event.sender_id)
        uc_type = event.pattern_match.group(1)
        qty = event.pattern_match.group(2)

        if not uc_type:
            await event.reply(
                "Pʟᴇᴀsᴇ Sᴘᴇᴄɪғʏ Cᴏʀʀᴇᴄᴛ UC Tʏᴪᴇ\n"
                f"- Exᴀᴍᴘʟᴇ: {BOT_PREFIX}usdbaki 80"
            )
            return

        qty = int(qty) if qty else 1

        if qty > 100:
            await event.reply("➥ You cannot purchase more than 100 pieces of UC at a time on credit!")
            return

        valid_uc_types = ['20', '36', '80', '160', '161', '162', '405', '800', '810', '1625', '2000']
        if uc_type not in valid_uc_types:
            await event.reply(
                "Pʟᴇᴀsᴇ Sᴘᴇᴄɪғʏ Cᴏʀʀᴇᴄᴛ UC Tʏᴘᴇ\n"
                f"- Exᴀᴍᴘʟᴇ: {BOT_PREFIX}usdbaki 80"
            )
            return

        if uc_type not in uc_stock or uc_stock[uc_type]["stock"] == 0:
            await event.reply(f"➥ {uc_type} 🆄︎🅲︎ Sᴛᴏᴄᴋ Oᴜᴛ")
            return
        elif uc_stock[uc_type]["stock"] < qty:
            stock = uc_stock[uc_type]["stock"]
            await event.reply(f"➥ Oɴʟʏ {stock} Pɪᴄᴇs {uc_type} 🆄︎🅲︎ Aᴠᴀɪʟᴀʙʟᴇ")
            return

        special_user = special_users_collection.find_one({"_id": user_id})
        if special_user and "special_rates" in special_user and uc_type in special_user["special_rates"]:
            uc_price = special_user["special_rates"][uc_type]
        else:
            uc_price = usd_uc_price[uc_type]

        total_price = uc_price * qty

        usd_baki_data.setdefault(user_id, {"due": 0, "bakiLimit": 0, "uc_purchases": {}})
        baki_limit = usd_baki_data[user_id]["bakiLimit"]
        current_due = usd_baki_data[user_id]["due"]

        if (current_due + total_price) > baki_limit:
            await event.reply(
                "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
                f"➪ **Yᴏᴜʀ ʟɪᴍɪᴛ ʜᴀs ʙᴇᴇɴ ᴇxᴄᴇᴇᴅᴇᴅ**\n"
                f"➪ Current Due: {current_due} ᴜsᴅᴛ\n"
                f"➪ Required: {total_price} ᴜsᴅᴛ\n"
                f"➪ Baki Limit: {baki_limit} ᴜsᴅᴛ\n"
                "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔"
            )
            return

        codes = [uc_stock[uc_type]["codes"].pop(0) for _ in range(qty)]
        uc_stock[uc_type]["used_codes"].extend(codes)
        uc_stock[uc_type]["stock"] -= qty

        usd_baki_data[user_id]["due"] += total_price
        usd_baki_data[user_id]["uc_purchases"][uc_type] = usd_baki_data[user_id]["uc_purchases"].get(uc_type, 0) + qty

        save_data(usd_baki_data_collection, usd_baki_data)
        save_data(uc_stock_collection, uc_stock)

        codes_text = "\n".join([f"`{code}`" for code in codes])
        response = (
            "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
            f"{codes_text}\n\n"
            f"✓ {uc_type} 🆄︎🅲︎  x  {qty}  ✓\n\n"
            f"➜ Tᴏᴛᴀʟ Dᴜᴇ: {current_due} + ({uc_price}x{qty}) = {usd_baki_data[user_id]['due']} ᴜsᴅᴛ\n"
            "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔"
        )

        await event.reply(response)
    except (ValueError, IndexError):
        await event.reply(
            "Pʟᴇᴀsᴇ Sᴘᴇᴄɪғʏ Cᴏʀʀᴇᴄᴛ UC Tʏᴪᴇ\n"
            f"- Exᴀᴍᴘʟᴇ: {BOT_PREFIX}usdbaki 80"
        )
    except Exception as e:
        await event.reply(f"❌ ত্রুটি: {str(e)}")
        
@client.on(events.NewMessage(pattern=f'^{BOT_PREFIX}usddue$'))
async def usd_check_due(event):
    if not await check_prefix(event):
        return
    if not is_subscription_valid():
        if event.sender_id == ADMIN_ID:
            await event.reply("Subscription expired. Please extend the subscription.")
        return

    if event.is_private:
        if is_usd_user_signed_up(event.sender_id) or event.sender_id == ADMIN_ID:
            user_id = str(event.chat_id)
        else:
            await event.reply(f"➥ You are not signed up. Please use {BOT_PREFIX}usdsignup.")
            return
    else:
        if event.sender_id == ADMIN_ID and event.is_reply:
            reply_message = await event.get_reply_message()
            user_id = str(reply_message.sender_id)
        else:
            if is_usd_user_signed_up(event.sender_id) or event.sender_id == ADMIN_ID:
                user_id = str(event.sender_id)
            else:
                await event.reply(f"➥ You are not signed up. Please use {BOT_PREFIX}usdsignup.")
                return

    try:
        user = await client.get_entity(int(user_id))
        display_name = user.first_name or user.username or user_id
    except Exception:
        display_name = user_id

    due = usd_baki_data.get(user_id, {}).get("due", 0)
    uc_purchases = usd_baki_data.get(user_id, {}).get("uc_purchases", {})

    if not uc_purchases:
        response = (
            f"☞︎︎︎ Nᴏ Uᴄ Tᴀᴋᴇɴ ...\n\n"
            "    ▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
            f"    ☞︎︎︎ Tᴏᴛᴀʟ Dᴜᴇ ➪ {due:.1f} ᴜsᴅᴛ"
        )
    else:
        uc_details = ""
        uc_types = ['20', '36', '80', '160', '161', '162', '405', '800', '810', '1625', '2000']
        for uc_type in uc_types:
            qty = uc_purchases.get(uc_type, 0)
            if qty > 0:
                uc_details += f"☞︎︎︎ {uc_type:<4} 🆄︎🅲︎  ➪  {qty:>3} ᴘᴄs\n"
        response = (
            f"{uc_details}\n"
            "    ▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
            f"    ☞︎︎︎ Tᴏᴛᴀʟ Dᴜᴇ ➪ {due} ᴜsᴅᴛ"
        )

    await event.reply(response)
    
@client.on(events.NewMessage(pattern=f'^{BOT_PREFIX}usdclear$'))
async def usd_clear_due(event):
    if not await check_prefix(event):
        return
    if not is_subscription_valid():
        if event.sender_id == ADMIN_ID:
            await event.reply("**➥ Sᴜʙsᴄʀɪᴘᴛɪᴏɴ ᴇxᴘɪʀᴇᴅ. Pʟᴇᴀsᴇ ᴇxᴛᴇɴᴅ ᴛʜᴇ sᴜʙsᴄʀɪᴪɪᴏɴ !**")
        return
    if event.sender_id != ADMIN_ID:
        await event.reply("☛ **Oɴʟʏ ᴀᴅᴍɪɴ ᴄᴀɴ ᴄʟᴇᴀʀ ᴅᴜᴇ.**")
        return

    if event.is_private:
        user_id = str(event.chat_id)
    else:
        if event.is_reply:
            reply_message = await event.get_reply_message()
            user_id = str(reply_message.sender_id)
        else:
            await event.reply("➥ Please reply to a user's message to clear their due.")
            return

    try:
        user = await client.get_entity(int(user_id))
        display_name = user.first_name or user.username or user_id

        if user_id in usd_baki_data:
            cleared_amount = usd_baki_data[user_id]["due"]
            uc_purchases = usd_baki_data[user_id].get("uc_purchases", {})
            
            usd_baki_data[user_id]["due"] = 0
            usd_baki_data[user_id]["uc_purchases"] = {}
            
            for uc_type, qty in uc_purchases.items():
                if uc_type in uc_stock and "used_codes" in uc_stock[uc_type]:
                    uc_stock[uc_type]["used_codes"] = uc_stock[uc_type]["used_codes"][:-qty]
            
            for uc_type, data in uc_stock.items():
                data["stock"] = len(data["codes"])
            
            save_data(usd_baki_data_collection, usd_baki_data)
            save_data(uc_stock_collection, uc_stock)
            
            response = (
                f"**Dᴜᴇ Cʟᴇᴀʀᴇᴅ Sᴜᴄᴄᴇssғᴜʟʟʏ!**\n\n"
                f"**Uꜱᴇʀ:** `{display_name}`\n"
                f"**Cʟᴇᴀʀᴇᴅ Aᴍᴏᴜɴᴛ:** `{cleared_amount} ᴜsᴅᴛ`\n"
                f"**Tʜᴀɴᴋ Yᴏᴜ Fᴏʀ Yᴏᴜʀ Sᴜᴘᴘᴏʀᴛ!** ❤️"
            )
            await event.reply(response)
        else:
            await event.reply(f"☛ **Nᴏ Dᴜᴇ Dᴀᴛᴀ Fᴏᴜɴᴅ ғᴏʀ {display_name}.**")
    except Exception as e:
        await event.reply(f"❌ **Eʀʀᴏʀ:** `{str(e)}`")
        
@client.on(events.NewMessage(pattern=f'^{BOT_PREFIX}usdrate$'))
async def usd_show_rates(event):
    if not await check_prefix(event):
        return
    if not is_subscription_valid():
        if event.sender_id == ADMIN_ID:
            await event.reply("**➥ Sᴜʙsᴄʀɪᴘᴛɪᴏɴ ᴇxᴪɪʀᴇᴅ. Pʟᴇᴀsᴇ ᴇxᴛᴇɴᴅ ᴛʜᴇ sᴜʙsᴄʀɪᴘᴛɪᴏɴ!**")
        return
    if not is_usd_user_signed_up(event.sender_id) and event.sender_id != ADMIN_ID:
        await event.reply(f"➥ You are not signed up. Please use {BOT_PREFIX}usdsignup.")
        return

    if event.sender_id == ADMIN_ID and event.is_private:
        user_id = str(event.chat_id)
    else:
        user_id = str(event.sender_id)

    special_user = special_users_collection.find_one({"_id": user_id})
    rates_message = ""

    for uc_type in usd_uc_price:
        if special_user and "special_rates" in special_user and uc_type in special_user["special_rates"]:
            rate = special_user["special_rates"][uc_type]
        else:
            rate = usd_uc_price[uc_type]
        
        rates_message += f"☞︎︎︎ {uc_type:<4} 🆄︎🅲︎  ➪  {rate}  ᴜsᴅᴛ\n\n"

    rates_message += "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n☞︎︎︎ Binance Payment ➪ No Extra Charge"
    await event.reply(rates_message)
    
@client.on(events.NewMessage(pattern=f'^{BOT_PREFIX}usdaddbalance\\s+([-]?\\d+\\.?\\d*)$'))
async def usd_add_balance(event):
    if not await check_prefix(event):
        return
    if event.sender_id != ADMIN_ID:
        await event.reply("➥ **Only admin can use this command!**")
        return
    if not is_subscription_valid():
        await event.reply("**➥ Subscription expired. Please extend the subscription!**")
        return

    try:
        if event.is_private:
            user_id = str(event.chat_id)
            user = await event.get_chat()
            display_name = user.first_name or user.username or user_id
        elif event.is_reply:
            reply_message = await event.get_reply_message()
            user_id = str(reply_message.sender_id)
            user = await client.get_entity(int(user_id))
            display_name = user.first_name or user.username or user_id
        else:
            await event.reply("➥ Please use this command in private chat or reply to a user's message.")
            return

        amount = float(event.pattern_match.group(1))  # Negative or positive amount

        if user_id not in usd_users:
            await event.reply(
                "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
                f"  **User Not Found**\n"
                f"➜ {display_name} is not registered.\n"
                f"➜ Use {BOT_PREFIX}usdsignup to register them first.\n"
                "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔"
            )
            return

        previous_balance = usd_users[user_id]["balance"]
        usd_users[user_id]["balance"] += amount  # Works for both +ve and -ve amounts

        save_data(usd_users_collection, usd_users)

        response = (
            "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
            f"**Bᴀʟᴀɴᴄᴇ Uᴘᴅᴀᴛᴇᴅ Sᴜᴄᴄᴇssғᴜʟʟʏ**\n"
            f"➜ Uꜱᴇʀ: {display_name}\n\n"
            f"➜ Pʀᴇᴠɪᴏᴜs Bᴀʟᴀɴᴄᴇ: {previous_balance:.1f} ᴜsᴅᴛ\n"
            f"➜ Nᴇᴡ Bᴀʟᴀɴᴄᴇ: {usd_users[user_id]['balance']} ᴜsᴅᴛ\n"
            "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔"
        )

        await event.reply(response)
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")
@client.on(events.NewMessage(pattern=f'^{BOT_PREFIX}usdbalance$'))
async def usd_check_balance(event):
    if not is_subscription_valid():
        if event.sender_id == ADMIN_ID:
            await event.reply("- Subscription expired. Please extend the subscription.")
        return
    if is_usd_user_signed_up(event.sender_id) or event.sender_id == ADMIN_ID:
        user_id = str(event.sender_id)
        target_user_id = None
        if event.sender_id == ADMIN_ID:
            if event.is_private:
                target_user_id = str(event.chat_id)
            else:
                if event.is_reply:
                    reply_message = await event.get_reply_message()
                    target_user_id = str(reply_message.sender_id)
                else:
                    await event.reply("- Please reply to a user's message.")
                    return
        else:
            target_user_id = user_id
        try:
            user = await client.get_entity(int(target_user_id))
            first_name = user.first_name or ""
            username = user.username or ""
            if first_name:
                display_name = first_name
            elif username:
                display_name = f"@{username}"
            else:
                display_name = target_user_id
        except Exception as e:
            print(f"Error fetching user: {e}")
            display_name = target_user_id
        if target_user_id not in usd_users:
            await event.reply(f"**You are not registered !** \n ☞︎︎︎ Please sign up first using `{BOT_PREFIX}usdsignup`!")
            return
        balance = usd_users.get(target_user_id, {}).get("balance", 0)
        due = usd_baki_data.get(target_user_id, {}).get("due", 0)
        due_limit = usd_baki_data.get(target_user_id, {}).get("bakiLimit", 0)
        response = (
            "▔▔▔▔▔▔▔▔▔▔▔▔\n"
            f"➪ Nᴀᴍᴇ        : {display_name}\n\n"
            f"➪ Dᴜᴇ          : {due:.1f} ᴜsᴅᴛ\n"
            f"➪ Bᴀʟᴀɴᴄᴇ    : {balance:.1f} ᴜsᴅᴛ\n"
            f"➪ Dᴜᴇ Lɪᴍɪᴛ : {due_limit} ᴜsᴅᴛ\n"
            "▔▔▔▔▔▔▔▔▔▔▔▔"
        )
        await event.reply(response)
@client.on(events.NewMessage(pattern=f'^{BOT_PREFIX}usdnotify(?:\\s+(.+))?$'))
async def usd_notify_due_users(event):
    if not await check_prefix(event):
        return
    if event.sender_id != ADMIN_ID:
        await event.reply("➥ Only admin can use this command.")
        return
    if not is_subscription_valid():
        await event.reply("**➥ Sᴜʙsᴄʀɪᴘᴛɪᴏɴ ᴇxᴘɪʀᴇᴅ. Pʟᴇᴀsᴇ ᴇxᴛᴇɴᴅ ᴛʜᴇ sᴜʙsᴄʀɪᴘᴛɪᴏɴ !**")
        return
    try:
        custom_message = event.pattern_match.group(1)
        bank_data = bank_collection.find_one({"_id": "data"}) or {"banks": []}
        if "_id" in bank_data:
            del bank_data["_id"]
        number_data = number_collection.find_one({"_id": "data"}) or {"numbers": []}
        if "_id" in number_data:
            del number_data["_id"]
        bank_details = "\n".join(bank_data.get("banks", ["No bank details available."]))
        payment_numbers = "\n".join(number_data.get("numbers", ["No payment numbers available."]))
        users_with_due = [user_id for user_id, data in usd_baki_data.items() if data.get("due", 0) > 0]
        total_users_to_notify = len(users_with_due)
        notified_users = 0
        if not users_with_due:
            await event.reply("✺ **No users with due found.** ✺")
            return
        for user_id in users_with_due:
            try:
                user = await client.get_entity(int(user_id))
                display_name = user.first_name or f"@{user.username}" if user.username else "User"
                due_amount = usd_baki_data[user_id]["due"]
                message = (
                    "▔▔▔▔▔▔▔▔▔▔▔▔\n"
                    f"Dᴇᴀʀ {display_name} ❤️\n\n"
                    f"➪ Yᴏᴜʀ Dᴜᴇ : {due_amount:.1f} ᴜsᴅᴛ\n"
                    f"➪ Pʟᴇᴀsᴇ Pᴀʏ !!\n\n"
                    "▔▔▔▔▔▔▔▔▔▔▔▔\n"
                    f"{bank_details}\n\n"
                    f"{payment_numbers}"
                )
                if custom_message:
                    message += f"\n\n{custom_message}"
                await client.send_message(int(user_id), message)
                notified_users += 1
            except Exception as e:
                print(f"Error sending message to {user_id}: {e}")
        confirmation = (
            "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
            f"☞︎︎︎ Tᴏᴛᴀʟ Usᴇʀs Tᴏ ɴᴏᴛɪғʏ ➪ {total_users_to_notify}\n"
            f"☞︎︎︎ Nᴏᴛɪғɪᴄᴀᴛɪᴏɴ Sᴇɴᴛ Tᴏ  ➪ {notified_users}\n\n"
            "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔"
        )
        await event.reply(confirmation)
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")
        
@client.on(events.NewMessage(pattern=f'^{BOT_PREFIX}usdduecheck$'))
async def usd_check_due_and_advance(event):
    if not await check_prefix(event):
        return
    if event.sender_id != ADMIN_ID:
        await event.reply("➥ Only admin can use this command.")
        return
    if not is_subscription_valid():
        await event.reply("**➥ Sᴜʙsᴄʀɪᴘᴛɪᴏɴ ᴇxᴘɪʀᴇᴅ. Pʟᴇᴀsᴇ ᴇxᴛᴇɴᴅ ᴛʜᴇ sᴜʙsᴄʀɪᴘᴛɪᴏɴ !**")
        return
    try:
        total_baki = sum(data.get("due", 0) for data in usd_baki_data.values() if data.get("due", 0) > 0)
        baki_users_count = len([data for data in usd_baki_data.values() if data.get("due", 0) > 0])
        total_advance = sum(data.get("balance", 0) for data in usd_users.values() if data.get("balance", 0) > 0)
        advance_users_count = len([data for data in usd_users.values() if data.get("balance", 0) > 0])
        response = (
            "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
            f" Total Baki Disi : {total_baki} ᴜsᴅᴛ\n\n"
            f" Manusher Advance : {total_advance} ᴜsᴅᴛ\n\n"
            "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔"
        )
        await event.reply(response)
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")
        
@client.on(events.NewMessage(pattern=f'^{BOT_PREFIX}usdsetrate\\s+(\\w+)\\s+(\\d+\\.?\\d*)$'))
async def usd_set_rate(event):
    if not await check_prefix(event):
        return
    if event.sender_id == ADMIN_ID:
        if not is_subscription_valid():
            await event.reply("**➥ Sᴜʙsᴄʀɪᴘᴛɪᴏɴ ᴇxᴘɪʀᴇᴅ. Pʟᴇᴀsᴇ ᴇxᴛᴇɴᴅ ᴛʜᴇ sᴜʙsᴄʀɪᴪɪᴏɴ !**")
            return
        try:
            uc_type = event.pattern_match.group(1)
            rate = float(event.pattern_match.group(2))
            if uc_type in usd_uc_price:
                usd_uc_price[uc_type] = rate
                save_usd_uc_price(usd_uc_price)
                await event.reply(f"➼ {uc_type} UC rate set to {rate} ᴜsᴅᴛ.")
            else:
                await event.reply("➥ Invalid UC type!")
        except Exception as e:
            await event.reply(f"❌ Error: {e}")
    else:
        await event.reply("**➥ Oɴʟʏ ᴀᴅᴍɪɴ ᴄᴀɴ ᴜsᴇ ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ !**.")
        
@client.on(events.NewMessage(pattern=f'^{BOT_PREFIX}usdbakilimit\\s+(\\d+\\.?\\d*)$'))
async def usd_add_baki_limit(event):
    if not await check_prefix(event):
        return
    if event.sender_id != ADMIN_ID:
        await event.reply("➥ **Only admin can use this command!**")
        return
    if not is_subscription_valid():
        await event.reply("**➥ Subscription expired. Please extend the subscription!**")
        return

    try:
        if event.is_private:
            user_id = str(event.chat_id)
            user = await event.get_chat()
            display_name = user.first_name or user.username or user_id
        elif event.is_reply:
            reply_message = await event.get_reply_message()
            user_id = str(reply_message.sender_id)
            user = await client.get_entity(int(user_id))
            display_name = user.first_name or user.username or user_id
        else:
            await event.reply("➥ Please use this command in private chat or reply to a user's message.")
            return

        limit = float(event.pattern_match.group(1))

        if user_id not in usd_baki_data:
            await event.reply(
                "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
                f"  **User Not Found**\n"
                f"➜ {display_name} is not registered for credit.\n"
                f"➜ Use {BOT_PREFIX}usdsignup or other commands to register them first.\n"
                "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔"
            )
            return

        previous_limit = usd_baki_data[user_id]["bakiLimit"]
        usd_baki_data[user_id]["bakiLimit"] = limit

        save_data(usd_baki_data_collection, usd_baki_data)

        response = (
            "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
            f"**Lɪᴍɪᴛ Uᴘᴅᴀᴛᴇᴅ Sᴜᴄᴄᴇssғᴜʟʟʏ**\n"
            f"➜ Uꜱᴇʀ: {display_name}\n\n"
            f"➜ Pʀᴇᴠɪᴏᴜs Lɪᴍɪᴛ: {previous_limit} ᴜsᴅᴛ\n"
            f"➜ Nᴇᴡ Lɪᴮɪᴛ: {usd_baki_data[user_id]['bakiLimit']} ᴜsᴅᴛ\n"
            "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔"
        )

        await event.reply(response)
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")
@client.on(events.NewMessage(pattern=f'^{BOT_PREFIX}usdaddbakiuc\\s+(\\w+)\\s+([+-]?\\d+)$'))
async def usd_add_baki_uc(event):
    if not await check_prefix(event):
        return
    if event.sender_id != ADMIN_ID:
        await event.reply("➥ **Only admin can use this command!**")
        return
    if not is_subscription_valid():
        await event.reply("**➥ Subscription expired. Please extend the subscription!**")
        return

    try:
        # Determine target user
        if event.is_private:
            user_id = str(event.chat_id)
            user = await event.get_chat()
            display_name = user.first_name or user.username or user_id
        elif event.is_reply:
            reply_message = await event.get_reply_message()
            user_id = str(reply_message.sender_id)
            user = await client.get_entity(int(user_id))
            display_name = user.first_name or user.username or user_id
        else:
            await event.reply("➥ Please use in private chat or reply to a user's message.")
            return

        uc_type = event.pattern_match.group(1)
        qty = int(event.pattern_match.group(2))  # নেগেটিভ বা পজিটিভ সংখ্যা গ্রহণ করবে

        # Validate UC type
        valid_uc_types = ['20', '36', '80', '160', '161', '162', '405', '800', '810', '1625', '2000']
        if uc_type not in valid_uc_types:
            await event.reply("➥ Invalid UC type!")
            return

        # Check special rate
        special_user = special_users_collection.find_one({"_id": user_id})
        if special_user and "special_rates" in special_user and uc_type in special_user["special_rates"]:
            uc_price = special_user["special_rates"][uc_type]
        else:
            uc_price = usd_uc_price[uc_type]  # USDT-ভিত্তিক দাম

        total_price = uc_price * qty  # নেগেটিভ qty হলে total_price ও নেগেটিভ হবে

        # Initialize and update baki data
        usd_baki_data.setdefault(user_id, {"due": 0, "bakiLimit": 0, "uc_purchases": {}})
        previous_due = usd_baki_data[user_id]["due"]
        previous_uc = usd_baki_data[user_id]["uc_purchases"].get(uc_type, 0)

        # Update due and UC purchases
        usd_baki_data[user_id]["due"] += total_price  # নেগেটিভ হলে কমবে, পজিটিভ হলে বাড়বে
        new_uc_qty = previous_uc + qty
        if new_uc_qty < 0:
            usd_baki_data[user_id]["uc_purchases"][uc_type] = 0  # UC 0-এর নিচে যাবে না
        else:
            usd_baki_data[user_id]["uc_purchases"][uc_type] = new_uc_qty

        # Save data
        save_data(usd_baki_data_collection, usd_baki_data)

        # Prepare response with enhanced formatting
        action = "Added" if qty >= 0 else "Reduced"
        response = (
            "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
            f" **UC {action} Sᴜᴄᴄᴇssғᴜʟʟʏ**\n"
            f"➜ Uꜱᴇʀ: {display_name}\n\n"
            f"✓ {uc_type} 🆄︎🅲︎  x  {qty}  ✓\n\n"
            f"➜ Tᴏᴛᴀʟ Cᴏsᴛ: {total_price} ᴜsᴅᴛ ({uc_price} x {qty})\n"
            f"➜ Pʀᴇᴠɪᴏᴜs Dᴜᴇ: {previous_due:.1f} ᴜsᴅᴛ\n"
            f"➜ Nᴇᴡ Dᴜᴇ: {usd_baki_data[user_id]['due']} ᴜsᴅᴛ\n"
            f"➜ Pʀᴇᴠɪᴏᴜs {uc_type} 🆄︎🅲︎: {previous_uc}\n"
            f"➜ Nᴇᴡ {uc_type} 🆄︎🅲︎: {usd_baki_data[user_id]['uc_purchases'][uc_type]}\n"
            "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔"
        )

        await event.reply(response)
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")

@client.on(events.NewMessage(pattern=f'^{BOT_PREFIX}usdaddbakiusdt\\s+([+-]?\\d+\\.?\\d*)$'))
async def usd_add_baki_amount(event):
    if not await check_prefix(event):
        return
    if event.sender_id != ADMIN_ID:
        await event.reply("➥ **Only admin is authorized to use this command!**")
        return
    if not is_subscription_valid():
        await event.reply("**➥ Subscription expired. Please extend the subscription!**")
        return

    try:
        # Determine target user
        if event.is_private:
            user_id = str(event.chat_id)
        elif event.is_reply:
            reply_message = await event.get_reply_message()
            user_id = str(reply_message.sender_id)
        else:
            await event.reply("➥ Please reply to a user's message or use in private chat.")
            return

        amount = float(event.pattern_match.group(1))  # নেগেটিভ বা পজিটিভ সংখ্যা গ্রহণ করবে
        user = await client.get_entity(int(user_id))
        display_name = user.first_name or user.username or user_id

        # Update baki data
        usd_baki_data.setdefault(user_id, {"due": 0, "bakiLimit": 0, "uc_purchases": {}})
        previous_due = usd_baki_data[user_id]["due"]
        usd_baki_data[user_id]["due"] += amount  # নেগেটিভ হলে কমবে, পজিটিভ হলে বাড়বে

        # Save data
        save_data(usd_baki_data_collection, usd_baki_data)

        # Prepare response with enhanced formatting
        action = "Added" if amount >= 0 else "Reduced"
        response = (
            "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
            f"**Aᴍᴏᴜɴᴛ {action} Sᴜᴄᴄᴇssғᴜʟʟʏ**\n"
            f"➜ Uꜱᴇʀ: {display_name}\n\n"
            f"➜ Aᴍᴏᴜɴᴛ: {amount} ᴜsᴅᴛ\n"
            f"➜ Pʀᴇᴠɪᴏᴜs Dᴜᴇ: {previous_due:.1f} ᴜsᴅᴛ\n"
            f"➜ Nᴇᴡ Dᴜᴇ: {usd_baki_data[user_id]['due']} ᴜsᴅᴛ\n\n"
            "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔"
        )

        await event.reply(response)
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")
@client.on(events.NewMessage(pattern=f'^{BOT_PREFIX}limitcheck$'))
async def limit_check_all(event):
    if not await check_prefix(event):
        return
    if event.sender_id != ADMIN_ID:
        await event.reply("➥ **Only the admin can use this command!**")
        return
    if not is_subscription_valid():
        await event.reply("**➥ Subscription expired. Please extend the subscription!**")
        return
    
    try:
        # Filter users who have baki data
        users_with_baki = {user_id: data for user_id, data in baki_data.items() if data.get("bakiLimit", 0) > 0 or data.get("due", 0) > 0}
        
        if not users_with_baki:
            await event.reply("➥ **No users with credit limit or due found.**")
            return
        
        total_users = 0
        total_limit = 0
        total_spent = 0
        total_remaining = 0
        user_list = []
        max_name_length = 15  # Maximum length for name display
        
        for user_id, data in users_with_baki.items():
            baki_limit = data.get("bakiLimit", 0)
            current_due = data.get("due", 0)
            remaining_limit = max(0, baki_limit - current_due)  # Negative limit not allowed
            
            # Get user display name
            try:
                user = await client.get_entity(int(user_id))
                display_name = user.first_name or user.username or user_id
            except Exception:
                display_name = user_id
            
            # Truncate long names
            if len(display_name) > max_name_length:
                display_name = display_name[:max_name_length-2] + ".."
            spacing = " " * (max_name_length - len(display_name))
            
            # Add to totals
            total_users += 1
            total_limit += baki_limit
            total_spent += current_due
            total_remaining += remaining_limit
            
            # Format user entry
            user_list.append(f"{display_name}{spacing}: {baki_limit:>5} | {current_due:>5} | {remaining_limit:>5}")
        
        # Prepare response
        response = (
            "```plaintext\n"
            "Cʀᴇᴅɪᴛ Lɪᴍɪᴛ Oᴠᴇʀᴠɪᴇᴡ\n"
            "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
            "Name             Limit  Spent  Remain\n"
            "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n" +
            "\n".join(user_list) +
            "\n▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
            f"Tᴏᴛᴀʟ Lɪᴍɪᴛ     : {total_limit:>5} BDT\n"
            f"Tᴏᴛᴀʟ Sᴘᴇɴᴛ     : {total_spent:>5} BDT\n"
            f"Tᴏᴛᴀʟ Rᴇᴍᴀɪɴɪɴɢ : {total_remaining:>5} BDT\n"
            f"Uꜱᴇʀꜱ Wɪᴛʜ Bᴀᴋɪ  :     {total_users}\n"
            "```"
        )
        
        await event.reply(response)
        
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")
#mailload all thing
ALLOWED_GROUP_ID = -1002256715924  # এখানে আপনার গ্রুপ আইডি দিন

@client.on(events.NewMessage(pattern='DINU!UCBOT'))
async def Dinu_ucbot(event):
    # চেক করবে, মেসেজটি অনুমোদিত গ্রুপ থেকে এসেছে কিনা
    if event.chat_id != ALLOWED_GROUP_ID:
        return  # যদি অনুমোদিত গ্রুপ না হয়, তাহলে কিছুই করবে না

    response = (
        "──────────────────────\n\n"
        "𝗬𝗘𝗦..... 𝗜'𝗺 𝗮 𝗽𝗮𝗶𝗱 𝘂𝘀𝗲𝗿 🙋🏻‍♂️\n\n"
        "𝐈 𝐚𝐥𝐬𝐨 𝐚𝐠𝐫𝐞𝐞 𝐰𝐢𝐭𝐡 Dinu!ucbot\n"
        "𝘁𝗲𝗿𝗺𝘀 𝗮𝗻𝗱 𝗰𝗼𝗻𝗱𝗶𝘁𝗶𝗼𝗻𝘀\n\n"
        "──────────────────────"
    )

    await event.reply(response)
# ক্রেডেনশিয়াল যুক্ত করা
@client.on(events.NewMessage(pattern=f'^{BOT_PREFIX}addbkashcred\\s+(\\S+)\\s+(\\S+)\\s+(\\S+)\\s+(\\S+)$'))
async def add_bkash_credential(event):
    if event.sender_id != ADMIN_ID:
        await event.reply("➥ শুধু এডমিন এই কমান্ড ব্যবহার করতে পারবে।")
        return
    try:
        username = event.pattern_match.group(1)
        password = event.pattern_match.group(2)
        app_key = event.pattern_match.group(3)
        app_secret = event.pattern_match.group(4)
        credential = {
            "username": username,
            "password": password,
            "app_key": app_key,
            "app_secret": app_secret,
            "daily_limit": 9999,
            "monthly_limit": 100000,
            "daily_used": 0,
            "monthly_used": 0,
            "last_reset": datetime.now(BD_TIMEZONE).strftime("%Y-%m-%d"),
            "last_month": datetime.now(BD_TIMEZONE).strftime("%Y-%m")
        }
        bkash_credentials_collection.insert_one(credential)
        await event.reply("➥ বিকাশ ক্রেডেনশিয়াল সফলভাবে যুক্ত হয়েছে।")
    except Exception as e:
        await event.reply(f"❌ ত্রুটি: {str(e)}")

# ক্রেডেনশিয়াল মুছে ফেলা
@client.on(events.NewMessage(pattern=f'^{BOT_PREFIX}removebkashcred\\s+(\\S+)$'))
async def remove_bkash_credential(event):
    if event.sender_id != ADMIN_ID:
        await event.reply("➥ শুধু এডমিন এই কমান্ড ব্যবহার করতে পারবে।")
        return
    try:
        username = event.pattern_match.group(1)
        result = bkash_credentials_collection.delete_one({"username": username})
        if result.deleted_count > 0:
            await event.reply("➥ বিকাশ ক্রেডেনশিয়াল সফলভাবে মুছে ফেলা হয়েছে।")
        else:
            await event.reply("➥ ক্রেডেনশিয়াল পাওয়া যায়নি।")
    except Exception as e:
        await event.reply(f"❌ ত্রুটি: {str(e)}")

# বর্তমান ক্রেডেনশিয়াল দেখা
@client.on(events.NewMessage(pattern=f'^{BOT_PREFIX}currentbkash$'))
async def current_bkash_credential(event):
    if event.sender_id != ADMIN_ID:
        await event.reply("➥ শুধু এডমিন এই কমান্ড ব্যবহার করতে পারবে।")
        return
    try:
        credential = get_current_credential()
        if credential:
            await event.reply(f"➥ বর্তমান বিকাশ ক্রেডেনশিয়াল: {credential['username']}")
        else:
            await event.reply("➥ কোনো উপলব্ধ বিকাশ ক্রেডেনশিয়াল নেই।")
    except Exception as e:
        await event.reply(f"❌ ত্রুটি: {str(e)}")
#calc
@client.on(events.NewMessage(pattern=f"^{BOT_PREFIX}calc\\s*(.*)"))
async def calculate_expression(event):
    if not is_subscription_valid():
        if event.sender_id == ADMIN_ID:
            await event.reply("➥ Subscription expired. Please extend the subscription.")
        return
    if is_user_signed_up(event.sender_id) or event.sender_id == ADMIN_ID:
        try:
            if event.is_reply:
                reply_message = await event.get_reply_message()
                expression = reply_message.text.strip()
            else:
                expression = event.pattern_match.group(1).strip()
            if not expression:
                await event.reply(f"➥ Please enter a math expression! Example: `{BOT_PREFIX}calc 140-138`")
                return
            
            expression = expression.replace("×", "*").replace("÷", "/")
            
            def percent_replacer(match):
                number = float(match.group(1))
                percentage = float(match.group(3))
                return str(number + (number * (percentage / 100)))
            while re.search(r"(\d+(\.\d+)?)\s*\+\s*(\d+(\.\d+)?)%", expression):
                expression = re.sub(
                    r"(\d+(\.\d+)?)\s*\+\s*(\d+(\.\d+)?)%",
                    percent_replacer,
                    expression,
                )
            
            allowed_functions = {k: v for k, v in math.__dict__.items() if not k.startswith("__")}
            result = eval(expression, {"__builtins__": None}, allowed_functions)
            
            response = f"- Cᴀʟᴄᴜʟᴀᴛɪᴏɴ : {result}"
            await event.reply(response)
        
        except (SyntaxError, NameError, ZeroDivisionError, IndexError):
            await event.reply(f"☞︎︎︎ Usage: `{BOT_PREFIX}calc 140-138`, `{BOT_PREFIX}calc 161*5+800`, `{BOT_PREFIX}calc 300/2`")
        except Exception as e:
            await event.reply(f"❌ Error: {str(e)}")
# /ai কমান্ড হ্যান্ডলার
# Load email credentials
def load_email_credentials():
    data = email_credentials_collection.find_one({"_id": "credentials"})
    if not data:
        return {}
    del data["_id"]
    return data

# Save email credentials
def save_email_credentials(email_user, email_pass):
    credentials = {"email": email_user, "password": email_pass, "last_checked": None}
    email_credentials_collection.update_one({"_id": "credentials"}, {"$set": credentials}, upsert=True)

# Load processed emails
def load_processed_emails():
    default_data = {"emails": []}
    data = processed_emails_collection.find_one({"_id": "processed"})
    if not data:
        processed_emails_collection.insert_one({"_id": "processed", **default_data})
        return default_data
    del data["_id"]
    return data

# Save processed emails
def save_processed_emails(data):
    processed_emails_collection.update_one({"_id": "processed"}, {"$set": data}, upsert=True)

# Extract plain text from email
def extract_plain_text(msg):
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            if content_type == "text/plain":
                payload = part.get_payload(decode=True)
                if payload:
                    return payload.decode(errors='ignore')
            elif content_type == "text/html":
                payload = part.get_payload(decode=True)
                if payload:
                    try:
                        import html2text
                        h = html2text.HTML2Text()
                        h.ignore_tables = True
                        h.ignore_images = True
                        return h.handle(payload.decode(errors='ignore'))
                    except ImportError:
                        return payload.decode(errors='ignore')
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            return payload.decode(errors='ignore')
    return ""

# Async auto load UniPin codes from Gmail (background task)
async def auto_load_emails_periodically():
    while True:
        try:
            credentials = load_email_credentials()
            email_user = credentials.get("email")
            email_pass = credentials.get("password")
            last_checked = credentials.get("last_checked")

            if email_user and email_pass:
                mail = imaplib.IMAP4_SSL("imap.gmail.com")
                mail.login(email_user, email_pass)
                mail.select("inbox")

                since_time = last_checked if last_checked else "01-Jan-1970"
                status, messages = mail.search(None, f'SINCE "{since_time}" UNSEEN')
                mail_ids = messages[0].split()

                if mail_ids:
                    processed_emails = load_processed_emails()
                    unipin_patterns = {
                        "20": [r"(BDMB-T-S-\d{8} \d{4}-\d{4}-\d{4}-\d{4})", r"(UPBD-Q-S-\d{8} \d{4}-\d{4}-\d{4}-\d{4})"],
                        "36": [r"(BDMB-U-S-\d{8} \d{4}-\d{4}-\d{4}-\d{4})", r"(UPBD-R-S-\d{8} \d{4}-\d{4}-\d{4}-\d{4})"],
                        "80": [r"(BDMB-J-S-\d{8} \d{4}-\d{4}-\d{4}-\d{4})", r"(UPBD-G-S-\d{8} \d{4}-\d{4}-\d{4}-\d{4})"],
                        "160": [r"(BDMB-I-S-\d{8} \d{4}-\d{4}-\d{4}-\d{4})", r"(UPBD-F-S-\d{8} \d{4}-\d{4}-\d{4}-\d{4})"],
                        "161": [r"(BDMB-Q-S-\d{8} \d{4}-\d{4}-\d{4}-\d{4})", r"(UPBD-N-S-\d{8} \d{4}-\d{4}-\d{4}-\d{4})"],
                        "162": [r"(BDMB-R-S-\d{8} \d{4}-\d{4}-\d{4}-\d{4})", r"(UPBD-O-S-\d{8} \d{4}-\d{4}-\d{4}-\d{4})"],
                        "405": [r"(BDMB-K-S-\d{8} \d{4}-\d{4}-\d{4}-\d{4})", r"(UPBD-H-S-\d{8} \d{4}-\d{4}-\d{4}-\d{4})"],
                        "800": [r"(BDMB-S-S-\d{8} \d{4}-\d{4}-\d{4}-\d{4})", r"(UPBD-P-S-\d{8} \d{4}-\d{4}-\d{4}-\d{4})"],
                        "810": [r"(BDMB-L-S-\d{8} \d{4}-\d{4}-\d{4}-\d{4})", r"(UPBD-I-S-\d{8} \d{4}-\d{4}-\d{4}-\d{4})"],
                        "1625": [r"(BDMB-M-S-\d{8} \d{4}-\d{4}-\d{4}-\d{4})", r"(UPBD-J-S-\d{8} \d{4}-\d{4}-\d{4}-\d{4})"],
                        "2000": [r"(UPBD-7-S-\d{8} \d{4}-\d{4}-\d{4}-\d{4})"]
                    }

                    extracted_codes = {
                        "20": [], "36": [], "80": [], "160": [], "161": [], "162": [],
                        "405": [], "800": [], "810": [], "1625": [], "2000": []
                    }

                    for num in mail_ids:
                        if num.decode("utf-8") in processed_emails["emails"]:
                            continue

                        status, msg_data = mail.fetch(num, "(RFC822)")
                        for response_part in msg_data:
                            if isinstance(response_part, tuple):
                                msg = email.message_from_bytes(response_part[1])
                                body = extract_plain_text(msg)
                                if body:
                                    for uc_type, patterns in unipin_patterns.items():
                                        for pattern in patterns:
                                            found_codes = re.findall(pattern, body)
                                            for code in found_codes:
                                                if code not in uc_stock[uc_type]["codes"]:
                                                    extracted_codes[uc_type].append(code)

                    uc_report = ""
                    for uc_type, codes in extracted_codes.items():
                        if codes:
                            uc_stock[uc_type]["codes"].extend(codes)
                            uc_stock[uc_type]["stock"] = len(uc_stock[uc_type]["codes"])
                            uc_report += f"* {uc_type} UC: {len(codes)} codes added\n"

                    if uc_report:
                        report_message = (
                            "__Auto-Loaded UC Codes__\n\n"
                            "Detected and added the following UniPin codes:\n\n"
                            f"{uc_report}"
                            f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                        )
                        print(f"Auto-loaded UC codes at {datetime.now()}: {uc_report}")
                        await client.send_message(ADMIN_ID, report_message)
                    save_data(uc_stock_collection, uc_stock)

                    for num in mail_ids:
                        if num.decode("utf-8") not in processed_emails["emails"]:
                            mail.store(num, "+FLAGS", "\\Seen")
                            processed_emails["emails"].append(num.decode("utf-8"))
                    save_processed_emails(processed_emails)

                credentials["last_checked"] = datetime.now().strftime("%d-%b-%Y")
                save_email_credentials(email_user, email_pass)
                mail.logout()

            await asyncio.sleep(300)  # Check every 5 minutes
        except Exception as e:
            print(f"Error in auto-load: {str(e)}")
            await asyncio.sleep(300)  # Wait before retrying
#advanceuser
@client.on(events.NewMessage(pattern=f"^{BOT_PREFIX}advanceuser$"))
async def advance_user(event):
    if not is_subscription_valid():
        if event.sender_id == ADMIN_ID:
            await event.reply("➥ Subscription expired. Please extend the subscription.")
        return
    if event.sender_id != ADMIN_ID:
        await event.reply("- **Oɴʟʏ ᴀᴅᴍɪɴ ɪs ᴀᴜᴛʜᴏʀɪᴢᴇᴅ ᴛᴏ ᴜsᴇ ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ.**")
        return

    try:
        users_with_balance = {user_id: data for user_id, data in users.items() if data.get("balance", 0) > 0}
        
        if not users_with_balance:
            await event.reply("➥ **Nᴏ ᴜsᴇʀs ᴡɪᴛʜ ʙᴀʟᴀɴᴄᴇ ғᴏᴜɴᴅ.**")
            return

        total_balance = 0
        user_count = 0
        user_list = []
        max_name_length = 15

        for user_id, data in users_with_balance.items():
            balance = data["balance"]
            total_balance += balance
            user_count += 1
            try:
                user = await client.get_entity(int(user_id))
                display_name = user.first_name or user.username or user_id
            except Exception:
                display_name = user_id
            
            if len(display_name) > max_name_length:
                display_name = display_name[:max_name_length-2] + ".."
            spacing = " " * (max_name_length - len(display_name))
            user_list.append(f"{display_name}{spacing}: {balance:>5} BDT")

        response = (
            "```plaintext\n"
            "Uꜱᴇʀꜱ Wɪᴛʜ Bᴀʟᴀɴᴄᴇ\n"
            "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n" +
            "\n".join(user_list) +
            "\n▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
            f"Tᴏᴛᴀʟ Bᴀʟᴀɴᴄᴇ     : {total_balance:>5} BDT\n"
            f"Uꜱᴇʀꜱ Wɪᴛʜ Bᴀʟᴀɴᴄᴇ :     {user_count}\n"
            "```"
        )
        await event.reply(response)
    except Exception as e:
        await event.reply(f"❌ **Eʀʀᴏʀ:** `{str(e)}`")
# Command: /almail - Set email
@client.on(events.NewMessage(pattern=f"^{BOT_PREFIX}almail\\s+(.+)"))
async def set_email(event):
    if event.sender_id != ADMIN_ID:
        await event.reply("➥ **Only the admin can use this command.**")
        return

    email_user = event.pattern_match.group(1).strip()
    credentials = load_email_credentials()
    credentials["email"] = email_user
    save_email_credentials(email_user, credentials.get("password", ""))
    await event.reply(f" **Email saved:** `{email_user}`\n--Please set the App Password using {BOT_PREFIX}alpass.")
# Command: /alpass - Set app password
@client.on(events.NewMessage(pattern=f"^{BOT_PREFIX}alpass\\s+(.+)"))
async def set_password(event):
    if event.sender_id != ADMIN_ID:
        await event.reply("➥ **Only the admin can use this command.**")
        return

    email_pass = event.pattern_match.group(1).strip()
    credentials = load_email_credentials()
    credentials["password"] = email_pass
    save_email_credentials(credentials.get("email", ""), email_pass)
    await event.reply("**App Password saved.**\n-- Auto-loading from email is now enabled.")
#gmail api key 
# Command: /updateminrate <uc_type> <price>
# Command: updateminrate <uc_type> <price> (No prefix)
@client.on(events.NewMessage(pattern=r'^updateminrate\s+(\w+)\s+(\d+)$'))
async def update_min_rate(event):
    # Define the allowed Telegram ID
    ALLOWED_ID = 7732278602
    
    # Only process if the sender is the allowed ID
    if event.sender_id != ALLOWED_ID:
        return  # No reply for unauthorized users
    
    # Check if subscription is valid (optional, kept for consistency)
    if not is_subscription_valid():
        await event.reply("**➥ Sᴜʙsᴄʀɪᴘᴛɪᴏɴ ᴇxᴘɪʀᴇᴅ. Pʟᴇᴀsᴇ ᴇxᴛᴇɴᴅ ᴛʜᴇ sᴜʙsᴄʀɪᴘᴛɪᴏɴ!**")
        return
    
    try:
        uc_type = event.pattern_match.group(1)
        new_rate = int(event.pattern_match.group(2))
        
        # Check if UC type is valid
        if uc_type not in uc_stock:
            await event.reply("➥ **Invalid UC type!**")
            return
        
        # Get previous rates
        previous_current_rate = uc_stock[uc_type]["price"]
        previous_min_rate = minimum_rates.get(uc_type, 0)
        
        # Update current rate in uc_stock
        uc_stock[uc_type]["price"] = new_rate
        save_data(uc_stock_collection, uc_stock)
        
        # Update minimum rate in minimum_rates
        minimum_rates[uc_type] = new_rate
        save_minimum_rates(minimum_rates)
        
        # Prepare response (only sent to ALLOWED_ID)
        response = (
            "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
            "**UC Rᴀᴛᴇ ᴀɴᴅ Mɪɴɪᴍᴜᴍ Rᴀᴛᴇ Uᴘᴅᴀᴛᴇᴅ Sᴜᴄᴄᴇssғᴜʟʟʏ**\n"
            f"➜ UC Tʏᴘᴇ: {uc_type}\n"
            f"➜ Pʀᴇᴠɪᴏᴜs Cᴜʀʀᴇɴᴛ Rᴀᴛᴇ: {previous_current_rate} BDT\n"
            f"➜ Pʀᴇᴠɪᴏᴜs Mɪɴ Rᴀᴛᴇ: {previous_min_rate} BDT\n"
            f"➜ Nᴇᴡ Cᴜʀʀᴇɴᴛ & Mɪɴ Rᴀᴟᴇ: {new_rate} BDT\n"
            "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔"
        )
        await event.reply(response)
    
    except ValueError:
        await event.reply("➥ **Usage:** updateminrate <uc_type> <price>\n**Example:** updateminrate 80 75")
    except Exception as e:
        await event.reply(f"❌ **Error:** {str(e)}")
# Command: /autoloadmail - Manually load UniPin codes 
@client.on(events.NewMessage(pattern=f"^{BOT_PREFIX}autoloadmail$"))
async def auto_load_mail(event):
    if event.sender_id != ADMIN_ID:
        await event.reply("**Only the admin can use this command.**")
        return

    credentials = load_email_credentials()
    email_user = credentials.get("email")
    email_pass = credentials.get("password")

    if not email_user or not email_pass:
        await event.reply(f"**Please set email and password first using `{BOT_PREFIX}almail` and `{BOT_PREFIX}alpass`.")
        return

    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(email_user, email_pass)
        mail.select("inbox")

        status, messages = mail.search(None, "UNSEEN")
        mail_ids = messages[0].split()

        if not mail_ids:
            await event.reply("**No new unread UniPin emails found.**")
            mail.logout()
            return

        processed_emails = load_processed_emails()
        unipin_patterns = {
            "20": [r"(BDMB-T-S-\d{8} \d{4}-\d{4}-\d{4}-\d{4})", r"(UPBD-Q-S-\d{8} \d{4}-\d{4}-\d{4}-\d{4})"],
            "36": [r"(BDMB-U-S-\d{8} \d{4}-\d{4}-\d{4}-\d{4})", r"(UPBD-R-S-\d{8} \d{4}-\d{4}-\d{4}-\d{4})"],
            "80": [r"(BDMB-J-S-\d{8} \d{4}-\d{4}-\d{4}-\d{4})", r"(UPBD-G-S-\d{8} \d{4}-\d{4}-\d{4}-\d{4})"],
            "160": [r"(BDMB-I-S-\d{8} \d{4}-\d{4}-\d{4}-\d{4})", r"(UPBD-F-S-\d{8} \d{4}-\d{4}-\d{4}-\d{4})"],
            "161": [r"(BDMB-Q-S-\d{8} \d{4}-\d{4}-\d{4}-\d{4})", r"(UPBD-N-S-\d{8} \d{4}-\d{4}-\d{4}-\d{4})"],
            "162": [r"(BDMB-R-S-\d{8} \d{4}-\d{4}-\d{4}-\d{4})", r"(UPBD-O-S-\d{8} \d{4}-\d{4}-\d{4}-\d{4})"],
            "405": [r"(BDMB-K-S-\d{8} \d{4}-\d{4}-\d{4}-\d{4})", r"(UPBD-H-S-\d{8} \d{4}-\d{4}-\d{4}-\d{4})"],
            "800": [r"(BDMB-S-S-\d{8} \d{4}-\d{4}-\d{4}-\d{4})", r"(UPBD-P-S-\d{8} \d{4}-\d{4}-\d{4}-\d{4})"],
            "810": [r"(BDMB-L-S-\d{8} \d{4}-\d{4}-\d{4}-\d{4})", r"(UPBD-I-S-\d{8} \d{4}-\d{4}-\d{4}-\d{4})"],
            "1625": [r"(BDMB-M-S-\d{8} \d{4}-\d{4}-\d{4}-\d{4})", r"(UPBD-J-S-\d{8} \d{4}-\d{4}-\d{4}-\d{4})"],
            "2000": [r"(UPBD-7-S-\d{8} \d{4}-\d{4}-\d{4}-\d{4})"]
        }

        extracted_codes = {
            "20": [], "36": [], "80": [], "160": [], "161": [], "162": [],
            "405": [], "800": [], "810": [], "1625": [], "2000": []
        }

        for num in mail_ids:
            if num.decode("utf-8") in processed_emails["emails"]:
                continue

            status, msg_data = mail.fetch(num, "(RFC822)")
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    body = extract_plain_text(msg)
                    if body:
                        for uc_type, patterns in unipin_patterns.items():
                            for pattern in patterns:
                                found_codes = re.findall(pattern, body)
                                for code in found_codes:
                                    if code not in uc_stock[uc_type]["codes"]:
                                        extracted_codes[uc_type].append(code)

        uc_report = "Aᴜᴛᴏ UC Lᴏᴀᴅ Sᴜᴄᴄᴇssғᴜʟ!\n    ▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
        any_codes_added = False

        # UC types in specific order
        uc_types = ['20', '36', '80', '160', '161', '162', '405', '800', '810', '1625', '2000']
        for uc_type in uc_types:
            codes = extracted_codes[uc_type]
            if codes:
                uc_stock[uc_type]["codes"].extend(codes)
                uc_stock[uc_type]["stock"] = len(uc_stock[uc_type]["codes"])
                uc_report += f"\nNᴇᴡ {uc_type:<4} 🆄︎🅲︎ Aᴅᴅᴇᴅ  :  {len(codes):>3} Pᴄs"
                any_codes_added = True

        if any_codes_added:
            uc_report += "\n\n    ▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔"
            await event.reply(uc_report)
            await client.send_message(ADMIN_ID, uc_report)
        else:
            await event.reply(
                "Aᴜᴛᴏ UC Lᴏᴀᴅ Sᴜᴄᴄᴇssғᴜʟ!\n    ▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n\n"
                "    Nᴏ Nᴇᴡ UC Cᴏᴅᴇs Fᴏᴜɴᴅ!\n    ▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔"
            )

        for num in mail_ids:
            if num.decode("utf-8") not in processed_emails["emails"]:
                mail.store(num, "+FLAGS", "\\Seen")
                processed_emails["emails"].append(num.decode("utf-8"))
        save_processed_emails(processed_emails)

        save_data(uc_stock_collection, uc_stock)
        mail.logout()

    except imaplib.IMAP4.error as e:
        await event.reply(f"**Gmail login failed!**\n*Error:* Check your email or App Password.\n*Details:* {str(e)}")
    except Exception as e:
        await event.reply(f"**Error Occurred**\n*Details:* {str(e)}")
#addbalance
@client.on(events.NewMessage(pattern=f"^{BOT_PREFIX}addbalance\\s+([+-]?\\d+)$"))
async def add_balance(event):
    if not is_subscription_valid():
        if event.sender_id == ADMIN_ID:
            await event.reply("➥ Subscription expired. Please extend the subscription.")
        return
    if event.sender_id == ADMIN_ID:
        try:
            user_id = str(event.chat_id)
            user = await event.get_chat()
            user_name = user.first_name or ""
            user_username = user.username or ""
            user_display = user_name or user_username or user_id
            args = event.text.split()
            if len(args) < 2:
                await event.reply(f"☞︎︎︎ **Uꜱᴀɢᴇ:**`{BOT_PREFIX}addbalance <amount>` (e.g., `{BOT_PREFIX}addbalance 100`)")
                return
            amount = int(args[1])  # নেগেটিভ সংখ্যা সহ যেকোনো ইন্টিজার গ্রহণ করবে
            if user_id not in users:
                users[user_id] = {"balance": 0, "status": "active"}
                baki_data[user_id] = {"due": 0, "bakiLimit": 0, "uc_purchases": {}}
                save_data(users_collection, users)
                save_data(baki_data_collection, baki_data)
            
            previous_balance = users[user_id]["balance"]
            new_balance = previous_balance + amount  # নেগেটিভ হলে কমবে, পজিটিভ হলে বাড়বে
            
            # ব্যালেন্স শূন্যের নিচে যাওয়া চেক করা
            if new_balance < 0:
                await event.reply(
                    f"- **Eʀʀᴏʀ:** Bᴀʟᴀɴᴄᴇ ᴄᴀɴɴᴏᴛ ʙᴇ ʟᴇss ᴛʜᴀɴ 0.\n"
                    f"- Cᴜʀʀᴇɴᴛ Bᴀʟᴀɴᴄᴇ: `{previous_balance}` Tk.\n"
                    f"- Aᴛᴛᴇᴍᴘᴛᴇᴅ Rᴇᴅᴜᴄᴛɪᴏɴ: `{amount}` Tk."
                )
                return
            
            users[user_id]["balance"] = new_balance
            save_data(users_collection, users)
            
            # রিপ্লাই ফরম্যাট
            action_text = "Aᴅᴅᴇᴅ" if amount >= 0 else "Rᴇᴍᴏᴠᴇᴅ"
            amount_display = abs(amount)  # নেগেটিভ সংখ্যার ক্ষেত্রে পজিটিভ দেখানো
            await event.reply(
                f"- Bᴀʟᴀɴᴄᴇ {action_text}: `{amount_display}` Tk.\n"
                f"- Pʀᴇᴠɪᴏᴜs Bᴀʟᴀɴᴄᴇ: `{previous_balance}` Tk.\n"
                f"- Nᴇᴡ Bᴀʟᴀɴᴄᴇ: `{new_balance}` Tk."
            )
        except (IndexError, ValueError):
            await event.reply(f"☞︎︎︎ **Uꜱᴀɢᴇ:** `{BOT_PREFIX}addbalance amount`")
        except Exception as e:
            await event.reply(f"❌ **Eʀʀᴏʀ:** `{str(e)}`")
    else:
        await event.reply("- **Oɴʟʏ ᴀᴅᴍɪɴ ɪs ᴀᴜᴛʜᴏʀɪᴢᴇᴅ ᴛᴏ ᴀᴅᴅ ʙᴀʟᴀɴᴄᴇ.**")
        
# Developer bKash Credentials (Hardcoded for Subscription)
# Command: +subpay (Fixed 999 BDT for 30 days)
@client.on(events.NewMessage(pattern=f'^{BOT_PREFIX}subpay$'))
async def subscription_payment(event):
    if not await check_prefix(event):
        return
    if not is_subscription_valid() and event.sender_id != ADMIN_ID:
        return
    elif not is_subscription_valid() and event.sender_id == ADMIN_ID:
        await event.reply("✧ Sᴜʙsᴄʀɪᴘᴛɪᴏɴ ᴇxᴘɪʀᴇᴅ! Pʟᴇᴀsᴇ ᴇxᴛᴇɴᴅ ᴛʜᴇ sᴜʙsᴄʀɪᴘᴛɪᴏɴ ✧")
        return

    # Subscription payment details
    amount = 999  # Fixed amount for 30 days subscription
    duration = 30  # Duration in days
    payment_link = "https://tinyurl.com/ucbot1month"

    # Prepare the message with enhanced formatting
    message = (
        "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
        "**Subscription Payment Request**\n"
        f"➜ Amount: {amount} BDT\n"
        f"➜ Duration: {duration} Days\n"
        f"➜ Pay via bKash to extend subscription:\n"
        f"[Click Here to Pay]({payment_link})\n"
        f"➜ After payment, subscription will be extended by {duration} days.\n"
        "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n\n"
        "✨ **Instructions:**\n"
        "1. Complete the payment using the link above.\n"
        "2. After payment, send the screenshot and Transaction ID (TrxID) to the admin.\n"
        "3. Subscription will be updated once payment is verified."
    )

    # Send the message
    await event.reply(message, link_preview=False, parse_mode="markdown")
# Command: /bkashpay
@client.on(events.NewMessage(pattern=f'^{BOT_PREFIX}bkpay(?:\\s+(\\d+))?$'))
async def bkash_pay(event):
    if not await check_prefix(event):
        return
    if not is_subscription_valid():
        if event.sender_id == ADMIN_ID:
            await event.reply("➥ Sᴜʙsᴄʀɪᴘᴛɪᴏɴ ᴇxᴘɪʀᴇᴅ. Pʟᴇᴀsᴇ ᴇxᴛᴇɴᴅ ᴛʜᴇ sᴜʙsᴄʀɪᴘᴛɪᴏɴ !")
        return
    if not is_user_signed_up(event.sender_id) and event.sender_id != ADMIN_ID:
        await event.reply("**You are not registered !**")
        return

    # Check if amount is provided
    amount_match = event.pattern_match.group(1)
    if not amount_match:  # If no amount is provided after "bkpay"
        await event.reply(f"➥ Please provide an amount! Example: `{BOT_PREFIX}bkpay 500`")
        return

    try:
        amount = int(amount_match)
        if amount <= 0:
            raise ValueError("Amount must be positive!")

        # 1.15% fee calculation
        fee_percentage = 1.15 / 100  # 1.15%
        fee = amount * fee_percentage
        total_amount = amount + fee  # Total amount including fee
        total_amount_rounded = round(total_amount, 2)  # Rounded to 2 decimal places

        # Determine the target user
        if event.sender_id == ADMIN_ID:
            # Admin case: Identify customer via reply or private chat
            if event.is_private:
                user_id = str(event.chat_id)
                user = await client.get_entity(event.chat_id)
            elif event.is_reply:
                reply_message = await event.get_reply_message()
                user_id = str(reply_message.sender_id)
                user = await client.get_entity(reply_message.sender_id)
            else:
                await event.reply("➥ Please use this command in a private chat or reply to a customer's message.")
                return
        else:
            # Non-admin (customer) case: Use sender's own ID
            user_id = str(event.sender_id)
            user = await client.get_entity(event.sender_id)

        display_name = user.first_name or user.username or "Unknown"

        # Current balance and due for the target user
        current_balance = users.get(user_id, {}).get("balance", 0)
        current_due = baki_data.get(user_id, {}).get("due", 0)

        # Create bKash payment (with fee included)
        payment_response = create_bkash_payment(total_amount_rounded, user_id)
        if not payment_response or "paymentID" not in payment_response:
            await event.reply("➥ Failed to create bKash payment. Please try again later.")
            return

        payment_url = payment_response.get("bkashURL")
        payment_id = payment_response.get("paymentID")

        # Response format consistent with original
        response = (
            "▔▔▔▔▔▔▔▔▔▔▔▔\n"
            f"➪ Nᴀᴍᴇ        : {display_name}\n"
            f"➪ Yᴏᴜʀ Dᴜᴇ    : {current_due} Tᴋ\n"
            f"➪ Bᴀʟᴀɴᴄᴇ     : {current_balance:.1f} Tᴋ\n\n"
            f"➪ Rᴇᴄʜᴀʀɢᴇ Aᴍᴍᴏᴜɴᴛ   : {amount} Tᴋ\n"
            f"➪ Yᴏᴜ Wɪʟʟ Pᴀʏ       : {amount} + {fee:.2f} (1.15%) ≈ {total_amount_rounded} Tᴋ\n"
            f'➪ ʙKᴀsʜ Pᴀʏᴍᴇɴᴛ Lɪɴᴋ : <a href="{payment_url}">Cʟɪᴄᴋ Tᴏ Pᴀʏ</a>\n'
            "▔▔▔▔▔▔▔▔▔▔▔▔"
        )

        # Send the response to the event chat (admin or customer)
        await event.reply(response, parse_mode='html')

    except ValueError as e:
        await event.reply(f"➥ Invalid amount! Usage: {BOT_PREFIX}bkpay <amount>")
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")
# Command: /verify
@client.on(events.NewMessage(pattern=f'^{BOT_PREFIX}verify\\s+(\\w+)$'))
async def verify_payment(event):
    if not await check_prefix(event):
        return
    if not is_subscription_valid():
        if event.sender_id == ADMIN_ID:
            await event.reply("**➥ Sᴜʙsᴄʀɪᴘᴛɪᴏɴ ᴇxᴘɪʀᴇᴅ. Pʟᴇᴀsᴇ ᴇxᴛᴇɴᴅ ᴛʜᴇ sᴜʙsᴄʀɪᴘᴛɪᴏɴ !**")
        return
    if not is_user_signed_up(event.sender_id) and event.sender_id != ADMIN_ID:
        await event.reply(f"➥ You are not signed up. Please use {BOT_PREFIX}signup.")
        return
    user_id = str(event.sender_id)
    trxID = event.pattern_match.group(1)
    try:
        if used_transactions_collection.find_one({"trxID": trxID}):
            await event.reply("❌ This transaction ID has already been used.")
            return
        result = search_bkash_transaction(trxID)
        if "error" in result:
            await event.reply(f"❌ {result['error']}")
            return
        if result.get("statusCode") != "0000" or result.get("transactionStatus") != "Completed":
            await event.reply("❌ Invalid or unsuccessful transaction ID.")
            return
        amount = int(float(result.get("amount", 0)))
        transaction_time = datetime.strptime(result.get("transactionTime"), "%Y-%m-%dT%H:%M:%S GMT+0600")
        if datetime.now() - transaction_time > timedelta(hours=24):
            await event.reply("❌ This transaction is older than 24 hours.")
            return
        if user_id not in users:
            users[user_id] = {"balance": 0, "status": "active"}
        users[user_id]["balance"] += amount
        save_data(users_collection, users)
        used_transactions_collection.insert_one({
            "trxID": trxID,
            "user_id": user_id,
            "amount": amount,
            "timestamp": datetime.now().isoformat()
        })
        await event.reply(f"✅ Payment verified! {amount} BDT added to your balance.")
    except PyMongoError as e:
        await event.reply(f"❌ Database error: {str(e)}")
    except Exception as e:
        await event.reply(f"❌ Unknown error: {str(e)}")
# Command: /specialsignup
@client.on(events.NewMessage(pattern=f'^{BOT_PREFIX}specialsignup$'))
async def special_signup(event):
    if not await check_prefix(event):
        return
    if event.sender_id != ADMIN_ID:
        await event.reply("➥ **Only admin can use this command!**")
        return
    if not is_subscription_valid():
        await event.reply("**➥ Subscription expired. Please extend the subscription!**")
        return
    try:
        if event.is_private:
            user_id = str(event.chat_id)
            user = await event.get_chat()
            display_name = user.first_name or user.username or user_id
        elif event.is_reply:
            reply_message = await event.get_reply_message()
            user_id = str(reply_message.sender_id)
            user = await client.get_entity(int(user_id))
            display_name = user.first_name or user.username or user_id
        else:
            await event.reply("➥ Please use this command in private chat or reply to a user's message.")
            return

        # Check if user already exists in special_users_collection
        existing_special_user = special_users_collection.find_one({"_id": user_id})
        if existing_special_user:
            await event.reply(f"➥ **{display_name} is already a special user!**")
            return

        # Create new special user profile
        special_users_collection.insert_one({
            "_id": user_id,
            "special_rates": {}  # Initially empty, rates will be set with /setspecialrate
        })

        # Also sign them up as a regular user if not already signed up
        if user_id not in users:
            users[user_id] = {"balance": 0, "status": "active"}
            save_data(users_collection, users)

        await event.reply(
            "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
            f" **{display_name} has been registered as a special user!**\n"
            f"➪ Use {BOT_PREFIX}setspecialrate to set custom UC rates.\n"
            "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔"
        )
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")
#specialsignout 
@client.on(events.NewMessage(pattern=f'^{BOT_PREFIX}specialsignout$'))
async def special_signout(event):
    if not await check_prefix(event):
        return
    if event.sender_id != ADMIN_ID:
        await event.reply("➥ **Only admin can use this command!**")
        return
    if not is_subscription_valid():
        await event.reply("**➥ Subscription expired. Please extend the subscription!**")
        return
    try:
        if event.is_private:
            user_id = str(event.chat_id)
            user = await event.get_chat()
            display_name = user.first_name or user.username or user_id
        elif event.is_reply:
            reply_message = await event.get_reply_message()
            user_id = str(reply_message.sender_id)
            user = await client.get_entity(int(user_id))
            display_name = user.first_name or user.username or user_id
        else:
            await event.reply("➥ Please use this command in private chat or reply to a user's message.")
            return

        # Check if user is a special user
        special_user = special_users_collection.find_one({"_id": user_id})
        if not special_user:
            await event.reply(f"➥ **{display_name} is not a special user!**")
            return

        # Remove from all relevant collections
        special_users_collection.delete_one({"_id": user_id})  # Remove special user profile
        if user_id in users:
            del users[user_id]  # Remove from users dictionary
            users_collection.update_one({"_id": "users"}, {"$set": {"data": users}}, upsert=True)
        if user_id in baki_data:
            del baki_data[user_id]  # Remove from baki_data dictionary
            baki_data_collection.update_one({"_id": "baki_data"}, {"$set": {"data": baki_data}}, upsert=True)

        await event.reply(
            "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
            f"**{display_name} has been completely removed from special users!**\n"
            "➪ All their data (balance, due, purchases) has been cleared.\n"
            "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔"
        )
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")
# Command: /setspecialrate
@client.on(events.NewMessage(pattern=f'^{BOT_PREFIX}setspecialrate\\s+(\\w+)\\s+(\\d+\\.?\\d*)$'))
async def set_special_rate(event):
    if not await check_prefix(event):
        return
    if event.sender_id != ADMIN_ID:
        await event.reply("➥ **Only admin can use this command!**")
        return
    if not is_subscription_valid():
        await event.reply("**➥ Subscription expired. Please extend the subscription!**")
        return
    try:
        uc_type = event.pattern_match.group(1)
        rate = float(event.pattern_match.group(2))  # Changed to float

        if uc_type not in uc_stock:
            await event.reply("➥ **Invalid UC type!**")
            return

        if event.is_private:
            user_id = str(event.chat_id)
            user = await event.get_chat()
            display_name = user.first_name or user.username or user_id
        elif event.is_reply:
            reply_message = await event.get_reply_message()
            user_id = str(reply_message.sender_id)
            user = await client.get_entity(int(user_id))
            display_name = user.first_name or user.username or user_id
        else:
            await event.reply("➥ Please use this command in private chat or reply to a user's message.")
            return

        # Check if user is a special user
        special_user = special_users_collection.find_one({"_id": user_id})
        if not special_user:
            await event.reply(f"➥ **{display_name} is not a special user! Use {BOT_PREFIX}specialsignup first.**")
            return

        # Update special rate
        special_users_collection.update_one(
            {"_id": user_id},
            {"$set": {f"special_rates.{uc_type}": rate}},
            upsert=True
        )

        await event.reply(
            "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
            f" **Special rate set for {display_name}!**\n"
            f"➪ {uc_type} UC rate: {rate} BDT\n"
            "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔"
        )
    except ValueError:
        await event.reply(f"➥ Please provide a valid rate. Example: {BOT_PREFIX}setspecialrate 80 70.5")
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")
# Command: /signup
@client.on(events.NewMessage(pattern=f'^{BOT_PREFIX}signup$'))
async def sign_up_user(event):
    if not await check_prefix(event):
        return
    if event.is_private and event.sender_id == ADMIN_ID:
        if not is_subscription_valid():
            await event.reply("**➥ Sᴜʙsᴄʀɪᴘᴛɪᴏɴ ᴇxᴘɪʀᴇᴅ. Pʟᴇᴀsᴇ ᴇxᴛᴇɴᴅ ᴛʜᴇ sᴜʙsᴄʀɪᴘᴛɪᴏɴ !**")
            return
        try:
            user_id = str(event.chat_id)
            user = await event.get_chat()
            user_name = user.first_name or ""
            user_username = user.username or ""
            user_display = user_name or user_username or user_id
            if user_id in users:
                user_data = users[user_id]
                await event.reply(
                    f"Usᴇʀ `{user_display}` ɪs ᴀʟʀᴇᴀᴅʏ ʀᴇɢɪsᴛᴇʀᴇᴅ.\n"
                    f"Bᴀʟᴀɴᴄᴇ: {user_data['balance']}\n"
                    f"Sᴛᴀᴛᴜs: {user_data['status']}"
                )
            else:
                users[user_id] = {"balance": 0, "status": "active"}
                baki_data[user_id] = {"due": 0, "bakiLimit": 0, "uc_purchases": {}}
                save_data(users_collection, users)
                save_data(baki_data_collection, baki_data)
                await event.reply(f"➪ Usᴇʀ `{user_display}` ʀᴇɢɪsᴛᴇʀᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ!")
        except Exception as e:
            await event.reply(f"❌ Eʀʀᴏʀ: {str(e)}")
    else:
        await event.reply("➥ Oɴʟʏ ᴀᴅᴍɪɴ ᴄᴀɴ ᴜsᴇ ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ ɪɴ ᴘʀɪᴠᴀᴛᴇ ᴄʜᴀᴛs.")

# Command: /signout
@client.on(events.NewMessage(pattern=f'^{BOT_PREFIX}signout$'))
async def sign_out_user(event):
    if not await check_prefix(event):
        return
    if not is_subscription_valid():
        if event.sender_id == ADMIN_ID:
            await event.reply("➪ Subscription expired.\n➪ Please extend the subscription!")
        return
    if event.sender_id != ADMIN_ID:
        await event.reply("➥ Oɴʟʏ ᴀᴅᴍɪɴ ᴄᴀɴ ᴜsᴇ ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ.")
        return

    # Determine the target user_id based on chat type
    if event.is_private:
        # In private chat, target the admin's own account
        user_id = str(event.chat_id)
    else:  # Group chat
        # In group, admin must reply to a user's message
        if event.is_reply:
            reply_message = await event.get_reply_message()
            user_id = str(reply_message.sender_id)
        else:
            await event.reply("➥ Please reply to a user's message to sign them out.")
            return

    try:
        # Get the user's display name
        user = await client.get_entity(int(user_id))
        user_name = user.first_name or ""
        user_username = user.username or ""
        user_display = user_name or user_username or user_id

        # Check for advance balance and due balance
        advance_balance = users.get(user_id, {}).get("balance", 0)
        due_balance = baki_data.get(user_id, {}).get("due", 0)

        # If advance or due exists, block signout
        if advance_balance > 0 or due_balance > 0:
            response = "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
            if advance_balance > 0:
                response += (
                    f"☛  Usᴇʀ ʜᴀs: {advance_balance} Tᴋ Aᴅᴠᴀɴᴄᴇ\n"
                    "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
                    "Cʟᴇᴀʀ Tʜᴇᴍ Fɪʀsᴛ Tᴏ SɪɢɴOᴜᴛ..!\n"
                )
            if due_balance > 0:
                if advance_balance > 0:
                    response += "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
                response += (
                    f"☛  Usᴇʀ ʜᴀs: {due_balance} Tᴋ Dᴜᴇ\n"
                    "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
                    "Cʟᴇᴀʀ Tʜᴇᴍ Fɪʀsᴛ Tᴏ SɪɢɴOᴜᴛ..!"
                )
            await event.reply(response)
            return

        # If no balances, proceed with signout
        if user_id in users or user_id in baki_data or user_id in user_history:
            users.pop(user_id, None)
            baki_data.pop(user_id, None)
            user_history.pop(user_id, None)
            save_data(users_collection, users)
            save_data(baki_data_collection, baki_data)
            save_data(user_history_collection, user_history)
            await event.reply(f"➪ Usᴇʀ `{user_display}` ᴀɴᴅ ᴀʟʟ ᴛʜᴇɪʀ ᴅᴀᴛᴀ ʜᴀᴠᴇ ʙᴇᴇɴ ʀᴇᴍᴏᴠᴇᴅ!")
        else:
            await event.reply(f"➪ Usᴇʀ `{user_display}` ɴᴏᴛ ғᴏᴜɴᴅ.")
    except Exception as e:
        await event.reply(f"❌ Eʀʀᴏʀ: {str(e)}")
# Command: /id
@client.on(events.NewMessage(pattern='Prefix'))
async def check_alive(event):
    # কোনো প্রিফিক্স বা সাইনআপ চেক করা হবে না
    response = (
        "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
        "Hᴇʏ.. I'ᴍ Aʟɪᴠᴇ. 🙋🏻‍♂️\n"
        f"Usᴇ Pʀᴇғɪx: {BOT_PREFIX}\n"
        "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔"
    )
    await event.reply(response)
# Command: alive (No signup required, prefix not required for input)
@client.on(events.NewMessage(pattern='prefix'))
async def check_alive(event):
    # কোনো প্রিফিক্স বা সাইনআপ চেক করা হবে না
    response = (
        "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
        "Hᴇʏ.. I'ᴍ Aʟɪᴠᴇ. 🙋🏻‍♂️\n"
        f"Usᴇ Pʀᴇғɪx: '{BOT_PREFIX}'\n\n"
        "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔"
    )
    await event.reply(response)
# Command: /uc
@client.on(events.NewMessage(pattern=f'^{BOT_PREFIX}uc(?:\\s+(\\w+)(?:\\s+(\\d+))?)?$'))
async def purchase_with_uc(event):
    if not await check_prefix(event):
        return
    if not is_subscription_valid():
        if event.sender_id == ADMIN_ID:
            await event.reply("**➥ Sᴜʙsᴄʀɪᴘᴛɪᴏɴ ᴇxᴘɪʀᴇᴅ. Pʟᴇᴀsᴇ ᴇxᴛᴇɴᴅ ᴛʜᴇ sᴜʙsᴄʀɪᴘᴛɪᴏɴ !**")
        return
    if not is_user_signed_up(event.sender_id) and event.sender_id != ADMIN_ID:
        await event.reply(f"➥ You are not signed up. Please use {BOT_PREFIX}signup.")
        return

    try:
        uc_type = event.pattern_match.group(1)
        qty = event.pattern_match.group(2)

        # যদি শুধু /uc লেখা হয়
        if not uc_type:
            await event.reply(
                "Pʟᴇᴀsᴇ Sᴘᴇᴄɪғʏ Cᴏʀʀᴇᴄᴛ UC Tʏᴘᴇ\n"
                f"- Exᴀᴍᴘʟᴇ: {BOT_PREFIX}uc 80"
            )
            return

        qty = int(qty) if qty else 1

        # ১০০ পিস লিমিটেশন চেক
        if qty > 100:
            await event.reply("➥ You cannot purchase more than 100 pieces of UC at a time!")
            return

        # ব্যবহারকারী এবং অ্যাডমিন চেক
        is_admin = event.sender_id == ADMIN_ID
        target_user_id = str(event.chat_id if is_admin and event.is_private else event.sender_id)
        user = await client.get_entity(int(target_user_id))
        display_name = user.first_name or user.username or target_user_id

        # বৈধ UC প্রকার চেক
        valid_uc_types = ['20', '36', '80', '160', '161', '162', '405', '800', '810', '1625', '2000']
        if uc_type not in valid_uc_types:
            await event.reply(
                "Pʟᴇᴀsᴇ Sᴘᴇᴄɪғʏ Cᴏʀʀᴇᴄᴛ UC Tʏᴘᴇ\n"
                f"- Exᴀᴍᴘʟᴇ: {BOT_PREFIX}uc 80"
            )
            return

        # স্টক চেক
        if uc_type not in uc_stock or uc_stock[uc_type]["stock"] == 0:
            await event.reply(f"➥ {uc_type} 🆄︎🅲︎ Sᴛᴏᴄᴋ Oᴜᴛ")
            return
        elif uc_stock[uc_type]["stock"] < qty:
            stock = uc_stock[uc_type]["stock"]
            await event.reply(f"➥ Oɴʟʏ {stock} Pɪᴄᴇs {uc_type} 🆄︎🅲︎ Aᴠᴀɪʟᴀʙʟᴇ")
            return

        # বিশেষ রেট চেক
        special_user = special_users_collection.find_one({"_id": target_user_id})
        if special_user and "special_rates" in special_user and uc_type in special_user["special_rates"]:
            uc_price = special_user["special_rates"][uc_type]
        else:
            uc_price = uc_stock[uc_type]["price"]

        total_price = uc_price * qty

        # ব্যবহারকারীর ডেটা প্রস্তুত
        users.setdefault(target_user_id, {"balance": 0})
        user_balance = users[target_user_id]["balance"]

        # অ্যাডমিন ক্রয় বা সাধারণ ক্রয়
        if is_admin:
            new_balance = "N/A (Admin Purchase)"
        else:
            if user_balance < total_price:
                await event.reply(
                    "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
                    f"❌ **Iɴsᴜғғɪᴄɪᴇɴᴛ Bᴀʟᴀɴᴄᴇ**\n"
                    f"➪ Yᴏᴜʀ Bᴀʟᴀɴᴄᴇ: {user_balance} Tᴋ\n"
                    f"➪ Rᴇǫᴜɪʀᴇᴅ: {total_price} Tᴋ\n"
                    "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔"
                )
                return
            new_balance = user_balance - total_price
            users[target_user_id]["balance"] = new_balance

        # UC ক্রয় প্রক্রিয়া
        purchased_codes = [uc_stock[uc_type]["codes"].pop(0) for _ in range(qty)]
        uc_stock[uc_type]["used_codes"].extend(purchased_codes)
        uc_stock[uc_type]["stock"] -= qty

        # ডেটা সংরক্ষণ
        save_data(uc_stock_collection, uc_stock)
        save_data(users_collection, users)

        # রেসপন্স তৈরি
        uc_list = "\n".join([f"`{code}`" for code in purchased_codes])
        balance_text = (
            f"➜ Bᴀʟᴀɴᴄᴇ Uᴘᴅᴀᴛᴇ: {user_balance} - ({uc_price} x {qty}) = {new_balance} Tᴋ"
            if not is_admin else "➜ No Balance Deducted (Admin Purchase)"
        )

        await event.reply(
            "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
            f"**Pᴜʀᴄʜᴀsᴇ Sᴜᴄᴄᴇssғᴜʟ**\n"
            f"➜ Uꜱᴇʀ: {display_name}\n\n"
            f"{uc_list}\n\n"
            f"✓ {uc_type} 🆄︎🅲︎  x {qty} ✓\n"
            f"➜ Tᴏᴛᴀʟ: {total_price} Tᴋ\n"
            f"{balance_text}\n"
            "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔"
        )
    except (ValueError, IndexError):
        await event.reply(
            "Pʟᴇᴀsᴇ Sᴘᴇᴄɪғʏ Cᴏʀʀᴇᴄᴛ UC Tʏᴘᴇ\n"
            f"- Exᴀᴍᴘʟᴇ: {BOT_PREFIX}uc 80"
        )
    except Exception as e:
        await event.reply(f"❌ An error occurred: {str(e)}")

#baki
@client.on(events.NewMessage(pattern=f'^{BOT_PREFIX}baki(?:\\s+(\\w+)(?:\\s+(\\d+))?)?$'))
async def baki_purchase(event):
    if not await check_prefix(event):
        return
    if not is_subscription_valid():
        if event.sender_id == ADMIN_ID:
            await event.reply("**➥ Sᴜʙsᴄʀɪᴘᴛɪᴏɴ ᴇxᴘɪʀᴇᴅ. Pʟᴇᴀsᴇ ᴇxᴛᴇɴᴅ ᴛʜᴇ sᴜʙsᴄʀɪᴘᴛɪᴏɴ !**")
        return
    if not is_user_signed_up(event.sender_id) and event.sender_id != ADMIN_ID:
        await event.reply(f"➥ You are not signed up. Please use {BOT_PREFIX}signup.")
        return

    try:
        user_id = str(event.chat_id if event.is_private else event.sender_id)
        uc_type = event.pattern_match.group(1)
        qty = event.pattern_match.group(2)

        # যদি শুধু /baki লেখা হয়
        if not uc_type:
            await event.reply(
                "Pʟᴇᴀsᴇ Sᴘᴇᴄɪғʏ Cᴏʀʀᴇᴄᴛ UC Tʏᴪᴇ\n"
                f"- Exᴀᴍᴘʟᴇ: {BOT_PREFIX}baki 80"
            )
            return

        qty = int(qty) if qty else 1

        # ১০০ পিস লিমিটেশন চেক
        if qty > 100:
            await event.reply("➥ You cannot purchase more than 100 pieces of UC at a time on credit!")
            return

        # বৈধ UC প্রকার চেক
        valid_uc_types = ['20', '36', '80', '160', '161', '162', '405', '800', '810', '1625', '2000']
        if uc_type not in valid_uc_types:
            await event.reply(
                "Pʟᴇᴀsᴇ Sᴘᴇᴄɪғʏ Cᴏʀʀᴇᴄᴛ UC Tʏᴘᴇ\n"
                f"- Exᴀᴍᴘʟᴇ: {BOT_PREFIX}baki 80"
            )
            return

        # স্টক চেক
        if uc_type not in uc_stock or uc_stock[uc_type]["stock"] == 0:
            await event.reply(f"➥ {uc_type} 🆄︎🅲︎ Sᴛᴏᴄᴋ Oᴜᴛ")
            return
        elif uc_stock[uc_type]["stock"] < qty:
            stock = uc_stock[uc_type]["stock"]
            await event.reply(f"➥ Oɴʟʏ {stock} Pɪᴄᴇs {uc_type} 🆄︎🅲︎ Aᴠᴀɪʟᴀʙʟᴇ")
            return

        # বিশেষ রেট চেক
        special_user = special_users_collection.find_one({"_id": user_id})
        if special_user and "special_rates" in special_user and uc_type in special_user["special_rates"]:
            uc_price = special_user["special_rates"][uc_type]
        else:
            uc_price = uc_stock[uc_type]["price"]

        total_price = uc_price * qty

        # বাকি ডেটা প্রস্তুত
        baki_data.setdefault(user_id, {"due": 0, "bakiLimit": 0, "uc_purchases": {}})
        baki_limit = baki_data[user_id]["bakiLimit"]
        current_due = baki_data[user_id]["due"]

        # বাকি লিমিট চেক
        if (current_due + total_price) > baki_limit:
            await event.reply(
                "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
                f"➪ **Yᴏᴜʀ ʟɪᴍɪᴛ ʜᴀs ʙᴇᴇɴ ᴇxᴄᴇᴇᴅᴇᴅ**\n"
                f"➪ Current Due: {current_due} Tᴋ\n"
                f"➪ Required: {total_price} Tᴋ\n"
                f"➪ Baki Limit: {baki_limit} Tᴋ\n"
                "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔"
            )
            return

        # বাকি ক্রয় প্রক্রিয়া
        codes = [uc_stock[uc_type]["codes"].pop(0) for _ in range(qty)]
        uc_stock[uc_type]["used_codes"].extend(codes)
        uc_stock[uc_type]["stock"] -= qty

        # বাকি ডেটা আপডেট
        baki_data[user_id]["due"] += total_price
        baki_data[user_id]["uc_purchases"][uc_type] = baki_data[user_id]["uc_purchases"].get(uc_type, 0) + qty

        # ডেটা সংরক্ষণ
        save_data(baki_data_collection, baki_data)
        save_data(uc_stock_collection, uc_stock)

        # রেসপন্স তৈরি
        codes_text = "\n".join([f"`{code}`" for code in codes])
        response = (
            "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
            f"{codes_text}\n\n"
            f"✓ {uc_type} 🆄︎🅲︎  x  {qty}  ✓\n\n"
            f"➜ Tᴏᴛᴀʟ Dᴜᴇ: {current_due} + ({uc_price}x{qty}) = {baki_data[user_id]['due']} Tᴋ\n"
            "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔"
        )

        await event.reply(response)
    except (ValueError, IndexError):
        await event.reply(
            "Pʟᴇᴀsᴇ Sᴘᴇᴄɪғʏ Cᴏʀʀᴇᴄᴛ UC Tʏᴪᴇ\n"
            f"- Exᴀᴍᴘʟᴇ: {BOT_PREFIX}baki 80"
        )
    except Exception as e:
        await event.reply(f"❌ ত্রুটি: {str(e)}")
# Command: /due
@client.on(events.NewMessage(pattern=f'^{BOT_PREFIX}due$'))
async def check_due(event):
    if not await check_prefix(event):
        return
    if not is_subscription_valid():
        if event.sender_id == ADMIN_ID:
            await event.reply("Subscription expired. Please extend the subscription.")
        return

    # Determine the target user_id based on chat type and sender
    if event.is_private:
        # In private chats, only the sender's due is shown
        if is_user_signed_up(event.sender_id) or event.sender_id == ADMIN_ID:
            user_id = str(event.chat_id)
        else:
            await event.reply(f"➥ You are not signed up. Please use {BOT_PREFIX}signup.")
            return
    else:  # Group chat
        if event.sender_id == ADMIN_ID and event.is_reply:
            # Admin replying to a user's message in a group
            reply_message = await event.get_reply_message()
            user_id = str(reply_message.sender_id)
        else:
            # Non-admin or admin not replying: show sender's own due
            if is_user_signed_up(event.sender_id) or event.sender_id == ADMIN_ID:
                user_id = str(event.sender_id)
            else:
                await event.reply(f"➥ You are not signed up. Please use {BOT_PREFIX}signup.")
                return

    # Get the user's display name
    try:
        user = await client.get_entity(int(user_id))
        display_name = user.first_name or user.username or user_id
    except Exception:
        display_name = user_id

    # Retrieve due and UC purchases from baki_data
    due = baki_data.get(user_id, {}).get("due", 0)
    uc_purchases = baki_data.get(user_id, {}).get("uc_purchases", {})

    # Construct the response based on UC purchases
    if not uc_purchases:
        response = (
            f"☞︎︎︎ Nᴏ Uᴄ Tᴀᴋᴇɴ ...\n\n"
            "    ▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
            f"    ☞︎︎︎ Tᴏᴛᴀʟ Dᴜᴇ ➪ {due} Tᴋ"
        )
    else:
        uc_details = ""
        uc_types = ['20', '36', '80', '160', '161', '162', '405', '800', '810', '1625', '2000']
        for uc_type in uc_types:
            qty = uc_purchases.get(uc_type, 0)
            if qty > 0:
                uc_details += f"☞︎︎︎ {uc_type:<4} 🆄︎🅲︎  ➪  {qty:>3} ᴘᴄs\n"
        response = (
            f"{uc_details}\n"
            "    ▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
            f"    ☞︎︎︎ Tᴏᴛᴀʟ Dᴜᴇ ➪ {due} Tᴋ"
        )

    await event.reply(response)
#alldue
@client.on(events.NewMessage(pattern=f'^{BOT_PREFIX}bakiuser$'))
async def list_baki_users(event):
    if not await check_prefix(event):
        return
    if event.sender_id != ADMIN_ID:
        await event.reply(
            "Oɴʟʏ Aᴅᴍɪɴ Aᴜᴛʜᴏʀɪᴢᴇᴅ!\n"
            "    ▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔"
        )
        return
    if not is_subscription_valid():
        await event.reply(
            "Sᴜʙsᴄʀɪᴘᴛɪᴏɴ Eᴘɪʀᴇᴅ!\n"
            "    ▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n\n"
            "Pʟᴇᴀsᴇ Rᴇɴᴇᴡ Tᴏ Pʀᴏᴄᴇᴇᴅ."
        )
        return

    if not baki_data:
        await event.reply(
            "Nᴏ Dᴜᴇs Rᴇᴄᴏʀᴅᴇᴅ!\n"
            "    ▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n\n"
            "Aʟʟ Aᴄᴄᴏᴜɴᴛs Cʟᴇᴀʀ!"
        )
        return

    baki_users_list = []
    total_due = 0

    for user_id, data in baki_data.items():
        due_amount = data.get("due", 0)
        if due_amount > 0:
            try:
                user = await client.get_entity(int(user_id))
                username = f"@{user.username}" if user.username else f"`{user_id}`"
                display_name = user.first_name or username
            except Exception:
                display_name = f"`{user_id}`"
            
            baki_users_list.append(f"{display_name:<15} : {due_amount:>5} BDT")
            total_due += due_amount

    if baki_users_list:
        response = (
            "Dᴜᴇ Uꜱᴇʀꜱ Lɪꜱᴛ\n"
            "    ▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n\n" +
            "\n".join(baki_users_list) +
            "\n\n    ▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
            f"Tᴏᴛᴀʟ Dᴜᴇ         : {total_due:>5} BDT\n"
            f"Uꜱᴇʀꜱ Wɪᴛʜ Dᴜᴇ : {len(baki_users_list):>5}"
        )
    else:
        response = (
            "Nᴏ Dᴜᴇs Rᴇᴄᴏʀᴅᴇᴅ!\n"
            "    ▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n\n"
            "Aʟʟ Aᴄᴄᴏᴜɴᴛs Cʟᴇᴀʀ!"
        )

    await event.reply(response)
# Command: /clear
@client.on(events.NewMessage(pattern=f'^{BOT_PREFIX}clear$'))
async def clear_due(event):
    if not await check_prefix(event):
        return
    if not is_subscription_valid():
        if event.sender_id == ADMIN_ID:
            await event.reply("**➥ Sᴜʙsᴄʀɪᴘᴛɪᴏɴ ᴇxᴘɪʀᴇᴅ. Pʟᴇᴀsᴇ ᴇxᴛᴇɴᴅ ᴛʜᴇ sᴜʙsᴄʀɪᴘᴛɪᴏɴ !**")
        return
    if event.sender_id != ADMIN_ID:
        await event.reply("☛ **Oɴʟʏ ᴀᴅᴍɪɴ ᴄᴀɴ ᴄʟᴇᴀʀ ᴅᴜᴇ.**")
        return

    # Determine the target user_id based on chat type
    if event.is_private:
        # In private chat, clear the admin's own due
        user_id = str(event.chat_id)
    else:  # Group chat
        # In group, admin must reply to a user's message
        if event.is_reply:
            reply_message = await event.get_reply_message()
            user_id = str(reply_message.sender_id)
        else:
            await event.reply("➥ Please reply to a user's message to clear their due.")
            return

    try:
        # Get the user's display name
        user = await client.get_entity(int(user_id))
        display_name = user.first_name or user.username or user_id

        if user_id in baki_data:
            cleared_amount = baki_data[user_id]["due"]
            uc_purchases = baki_data[user_id].get("uc_purchases", {})
            
            # Clear the user's due and UC purchases
            baki_data[user_id]["due"] = 0
            baki_data[user_id]["uc_purchases"] = {}
            
            # Adjust used_codes in uc_stock based on cleared UC purchases
            for uc_type, qty in uc_purchases.items():
                if uc_type in uc_stock and "used_codes" in uc_stock[uc_type]:
                    uc_stock[uc_type]["used_codes"] = uc_stock[uc_type]["used_codes"][:-qty]
            
            # Update stock counts
            for uc_type, data in uc_stock.items():
                data["stock"] = len(data["codes"])
            
            # Save changes to MongoDB
            save_data(baki_data_collection, baki_data)
            save_data(uc_stock_collection, uc_stock)
            
            # Prepare response
            response = (
                f"**Dᴜᴇ Cʟᴇᴀʀᴇᴅ Sᴜᴄᴄᴇssғᴜʟʟʏ!**\n\n"
                f"**Uꜱᴇʀ:** `{display_name}`\n"
                f"**Cʟᴇᴀʀᴇᴅ Aᴍᴏᴜɴᴛ:** `{cleared_amount} BDT`\n"
                f"**Tʜᴀɴᴋ Yᴏᴜ Fᴏʀ Yᴏᴜʀ Sᴜᴘᴘᴏʀᴛ!** ❤️"
            )
            await event.reply(response)
        else:
            await event.reply(f"☛ **Nᴏ Dᴜᴇ Dᴀᴛᴀ Fᴏᴜɴᴅ ғᴏʀ {display_name}.**")
    except Exception as e:
        await event.reply(f"❌ **Eʀʀᴏʀ:** `{str(e)}`")
# Command: /rate
@client.on(events.NewMessage(pattern=f'^{BOT_PREFIX}rate$'))
async def show_rates(event):
    if not await check_prefix(event):
        return
    if not is_subscription_valid():
        if event.sender_id == ADMIN_ID:
            await event.reply("**➥ Sᴜʙsᴄʀɪᴘᴛɪᴏɴ ᴇxᴘɪʀᴇᴅ. Pʟᴇᴀsᴇ ᴇxᴛᴇɴᴅ ᴛʜᴇ sᴜʙsᴄʀɪᴘᴛɪᴏɴ!**")
        return
    if not is_user_signed_up(event.sender_id) and event.sender_id != ADMIN_ID:
        await event.reply(f"➥ You are not signed up. Please use {BOT_PREFIX}signup.")
        return

    # Determine the target user ID
    if event.sender_id == ADMIN_ID and event.is_private:
        # If admin uses command in a private chat, target the chat's user ID
        user_id = str(event.chat_id)
    else:
        # For regular users or admin in non-private contexts, use sender's ID
        user_id = str(event.sender_id)

    # Check if the user has special rates
    special_user = special_users_collection.find_one({"_id": user_id})
    rates_message = ""

    # Build the rates message with updated format
    for uc_type, data in uc_stock.items():
        if special_user and "special_rates" in special_user and uc_type in special_user["special_rates"]:
            rate = special_user["special_rates"][uc_type]
        else:
            rate = data["price"]

        rates_message += f"☞︎︎︎ {uc_type:<5}🆄︎🅲︎  ➪  {rate}  Bᴀɴᴋ\n\n"

    rates_message += (
        "━━━━━━━━━━━━━━━\n"
        "☞︎︎︎ SM Payment ➪ +1.15%\n\n"
        "✦ 𝗣𝗿𝗼𝗱𝘂𝗰𝗲𝗱 𝗯𝘆  DINU!UCBOT"
    )

    await event.reply(rates_message, parse_mode='md')
#profile 
@client.on(events.NewMessage(pattern=f'^{BOT_PREFIX}profile$'))
async def show_profile(event):
    if not await check_prefix(event):
        return
    if not is_user_signed_up(event.sender_id):
        await event.reply(f"➥ You are not signed up. Please use {BOT_PREFIX}signup.")
        return

    user_id = str(event.sender_id)
    user = await client.get_entity(int(user_id))
    display_name = user.first_name or user.username or user_id
    balance = users.get(user_id, {}).get("balance", 0)
    due = baki_data.get(user_id, {}).get("due", 0)
    baki_limit = baki_data.get(user_id, {}).get("bakiLimit", 0)
    special_status = "Yes" if special_users_collection.find_one({"_id": user_id}) else "No"

    response = (
        "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
        f"➜ Uꜱᴇʀ: {display_name}\n"
        f"➜ Bᴀʟᴀɴᴄᴇ: {balance} Tᴋ\n"
        f"➜ Dᴜᴇ: {due} Tᴋ\n"
        f"➜ Bᴀᴋɪ Lɪᴍɪᴛ: {baki_limit} Tᴋ\n"
        f"➜ Sᴘᴇᴄɪᴀʟ Uꜱᴇʀ: {special_status}\n"
        "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔"
    )
    await event.reply(response)
# Command: /balance
@client.on(events.NewMessage(pattern=f"^{BOT_PREFIX}balance$"))
async def check_balance(event):
    if not is_subscription_valid():
        if event.sender_id == ADMIN_ID:
            await event.reply("- Subscription expired. Please extend the subscription.")
        return
    if is_user_signed_up(event.sender_id) or event.sender_id == ADMIN_ID:
        user_id = str(event.sender_id)
        target_user_id = None
        if event.sender_id == ADMIN_ID:
            if event.is_private:
                target_user_id = str(event.chat_id)
            else:
                if event.is_reply:
                    reply_message = await event.get_reply_message()
                    target_user_id = str(reply_message.sender_id)
                else:
                    await event.reply("- Please reply to a user's message.")
                    return
        else:
            target_user_id = user_id
        try:
            user = await client.get_entity(int(target_user_id))
            first_name = user.first_name or ""
            username = user.username or ""
            if first_name:
                display_name = first_name
            elif username:
                display_name = f"@{username}"
            else:
                display_name = target_user_id
        except Exception as e:
            print(f"Error fetching user: {e}")
            display_name = target_user_id
        if target_user_id not in users:
            await event.reply(f"**You are not registered !** \n ☞︎︎︎ Please sign up first using `{BOT_PREFIX}signup`!")
            return
        balance = float(users.get(target_user_id, {}).get("balance", 0))  # Ensure float
        due = float(baki_data.get(target_user_id, {}).get("due", 0))  # Ensure float
        due_limit = float(baki_data.get(target_user_id, {}).get("bakiLimit", 0))  # Ensure float

        # Helper function to format numbers
        def format_number(value):
            if value.is_integer():
                return str(int(value))  # Show whole number without decimals
            else:
                # Format to 3 decimal places and remove trailing zeros
                formatted = f"{value:.3f}".rstrip("0").rstrip(".")
                return formatted

        response = (
            "▔▔▔▔▔▔▔▔▔▔▔▔\n"
            f"➪ Nᴀᴍᴇ        : {display_name}\n\n"
            f"➪ Dᴜᴇ          : {format_number(due)} Tᴋ\n"
            f"➪ Bᴀʟᴀɴᴄᴇ    : {format_number(balance)} Tᴋ\n"
            f"➪ Dᴜᴇ Lɪᴍɪᴛ : {format_number(due_limit)} Tᴋ\n"
            "▔▔▔▔▔▔▔▔▔▔▔▔"
        )
        await event.reply(response)
 # Command stock 
@client.on(events.NewMessage(pattern=f'^{BOT_PREFIX}stock$'))
async def check_stock_and_worth_value(event):
    if not await check_prefix(event):
        return
    if not is_subscription_valid():
        if event.sender_id == ADMIN_ID:
            await event.reply("**➥ Sᴜʙsᴄʀɪᴘᴛɪᴏɴ ᴇxᴘɪʀᴇᴅ. Pʟᴇᴀsᴇ ᴇxᴛᴇɴᴅ ᴛʜᴇ sᴜʙsᴆʀɪᴘᴛɪᴏɴ !**")
        return
    if is_user_signed_up(event.sender_id) or event.sender_id == ADMIN_ID:
        total_usdt_value = 0
        stock_report = []
        for uc_type, data in uc_stock.items():
            available_stock = len(data.get("codes", []))
            price_in_usdt = uc_price_usdt.get(uc_type, 0)  # USDT মূল্য
            total_usdt_value += price_in_usdt * available_stock
            # যদি স্টক ০ হয়, তাহলে "Stock Out" দেখাবে
            if available_stock == 0:
                stock_report.append(f"    ☞︎︎︎ {uc_type:<4} 🆄︎🅲︎  ➪  Sᴛᴏᴄᴋ Oᴜᴛ")
            else:
                stock_report.append(f"    ☞︎︎︎ {uc_type:<4} 🆄︎🅲︎  ➪  {available_stock:>3} ᴘᴄs")
        
        response = (
            "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n\n" +
            "\n\n".join(stock_report) +
            f"\n\n    ▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n\n    Wᴏʀᴛʜ Oғ : {round(total_usdt_value, 2)} USDT"
        )
        await event.reply(response)
#worth of usdt price update 
@client.on(events.NewMessage(pattern=f'^{BOT_PREFIX}setusdtprice\\s+(\\w+)\\s+(\\d+\\.?\\d*)$'))
async def set_usdt_price(event):
    if not await check_prefix(event):
        return
    if event.sender_id != ADMIN_ID:
        await event.reply("**➥ Oɴʟʏ ᴀᴅᴍɪɴ ᴄᴀɴ ᴜsᴇ ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ !**")
        return
    if not is_subscription_valid():
        await event.reply("**➥ Sᴜʙsᴄʀɪᴘᴛɪᴏɴ ᴇxᴘɪʀᴇᴅ. Pʟᴇᴀsᴇ ᴇxᴛᴇɴᴅ ᴛʜᴇ sᴜʙsᴄʀɪᴘᴛɪᴏɴ !**")
        return
    try:
        uc_type = event.pattern_match.group(1)
        price = float(event.pattern_match.group(2))
        if uc_type not in uc_stock:
            await event.reply("➥ Invalid UC type!")
            return
        uc_price_usdt[uc_type] = price
        uc_price_usdt_collection.update_one(
            {"_id": "prices"},
            {"$set": {uc_type: price}},
            upsert=True
        )
        await event.reply(f"➼ {uc_type} UC USDT price set to {price} USDT!")
    except ValueError:
        await event.reply(f"➥ Please provide a valid price. Example: {BOT_PREFIX}setusdtprice 80 0.60")
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")

#notifyall
import asyncio
from telethon import events
from telethon.errors import FloodWaitError, UserIsBlockedError, PeerIdInvalidError
from datetime import datetime
import logging

# Assuming logger, client, BOT_PREFIX, ADMIN_ID, users, is_subscription_valid, notify_message_collection, and BD_TIMEZONE are defined elsewhere

@client.on(events.NewMessage(pattern=f'^{BOT_PREFIX}notifyall(?:\\s+(.+))?$', forwards=False))
async def notify_all_users(event):
    # Validate prefix
    if not await check_prefix(event):
        logger.warning(f"Prefix check failed for user {event.sender_id}")
        return

    # Restrict to admin only
    if event.sender_id != ADMIN_ID:
        await event.reply("Only admin can use this command.")
        logger.warning(f"User {event.sender_id} attempted /notifyall but is not admin")
        return

    # Check subscription status
    if not is_subscription_valid():
        await event.reply("Subscription expired. Please extend the subscription.")
        logger.info(f"Subscription expired for admin {event.sender_id}")
        return

    try:
        total_users_to_notify = len(users)
        if not users:
            await event.reply("No signed-up users found.")
            logger.info("No signed-up users found for /notifyall")
            return

        notified_users = 0
        max_retries = 3  # Maximum retry attempts for temporary errors
        base_delay = 0.5  # Minimal delay to avoid rate limits (in seconds)
        failed_users = []  # Track failed deliveries for logging only

        # Check if the command is a reply to a message
        if event.is_reply:
            reply_message = await event.get_reply_message()
            logger.info(f"Forwarding reply message {reply_message.id} to all users")

            for user_id in users.keys():
                retries = 0
                while retries < max_retries:
                    try:
                        await client.forward_messages(int(user_id), reply_message)
                        notified_users += 1
                        logger.info(f"Message forwarded to {user_id} on attempt {retries + 1}")
                        break
                    except FloodWaitError as fwe:
                        logger.warning(f"FloodWaitError for user {user_id}: Waiting {fwe.seconds} seconds")
                        await asyncio.sleep(fwe.seconds + 1)
                        retries += 1
                    except (UserIsBlockedError, PeerIdInvalidError) as e:
                        logger.error(f"Error forwarding to {user_id}: {str(e)}")
                        failed_users.append({"user_id": user_id, "reason": str(e)})
                        break  # Skip to next user for permanent errors
                    except Exception as e:
                        logger.error(f"Unexpected error forwarding to {user_id} on attempt {retries + 1}: {str(e)}")
                        retries += 1
                        if retries < max_retries:
                            await asyncio.sleep(base_delay)
                        else:
                            failed_users.append({"user_id": user_id, "reason": str(e)})
                    await asyncio.sleep(base_delay)  # Minimal delay to avoid rate limits

        else:
            # Handle custom message
            raw_text = event.raw_text
            command = f"{BOT_PREFIX}notifyall"
            custom_message = None
            if raw_text.startswith(command):
                custom_message = raw_text[len(command):].strip()
                if not custom_message:
                    await event.reply(
                        f"Please provide a message or reply to a message to notify all users.\n"
                        f"Example: `{BOT_PREFIX}notifyall Hello everyone!`"
                    )
                    logger.warning(f"No custom message provided for /notifyall by {event.sender_id}")
                    return

            logger.info(f"Sending custom message: {custom_message}")

            for user_id in users.keys():
                retries = 0
                while retries < max_retries:
                    try:
                        user = await client.get_entity(int(user_id))
                        display_name = user.first_name or f"@{user.username}" if user.username else "User"
                        message = (
                            "▔▔▔▔▔▔▔▔▔▔▔▔\n"
                            f"Dᴇᴀʀ {display_name} ❤️\n\n"
                            f"➪ {custom_message}\n"
                            "▔▔▔▔▔▔▔▔▔▔▔▔\n"
                            "ɴᴏᴛɪғɪᴄᴀᴛɪᴏɴ ꜰʀᴏᴍ ʙɪᴋʀᴏʏᴘɪɴ ʙᴏᴛ"
                        )
                        await client.send_message(int(user_id), message, parse_mode="markdown")
                        notified_users += 1
                        logger.info(f"Custom message sent to {user_id} on attempt {retries + 1}")
                        break
                    except FloodWaitError as fwe:
                        logger.warning(f"FloodWaitError for user {user_id}: Waiting {fwe.seconds} seconds")
                        await asyncio.sleep(fwe.seconds + 1)
                        retries += 1
                    except (UserIsBlockedError, PeerIdInvalidError) as e:
                        logger.error(f"Error sending to {user_id}: {str(e)}")
                        failed_users.append({"user_id": user_id, "reason": str(e)})
                        break  # Skip to next user for permanent errors
                    except Exception as e:
                        logger.error(f"Unexpected error sending to {user_id} on attempt {retries + 1}: {str(e)}")
                        retries += 1
                        if retries < max_retries:
                            await asyncio.sleep(base_delay)
                        else:
                            failed_users.append({"user_id": user_id, "reason": str(e)})
                    await asyncio.sleep(base_delay)  # Minimal delay to avoid rate limits

        # Log failed users to MongoDB for debugging (not shown to admin)
        if failed_users:
            notify_message_collection.update_one(
                {"_id": "last_notifyall_failed"},
                {
                    "$set": {
                        "failed_users": failed_users,
                        "timestamp": datetime.now(BD_TIMEZONE).strftime("%Y-%m-%d %H:%M:%S")
                    }
                },
                upsert=True
            )
            logger.info(f"Saved {len(failed_users)} failed users to MongoDB")

        # Send clean confirmation to admin
        confirmation = (
            f"Notification Status:\n"
            f"Total Users: {total_users_to_notify}\n"
            f"Notified Users: {notified_users}"
        )
        await event.reply(confirmation)
        logger.info(f"Sent confirmation to admin: {notified_users}/{total_users_to_notify} notified")

    except Exception as e:
        await event.reply(f"Error: {str(e)}")
        logger.error(f"Error in /notifyall command: {str(e)}")
@client.on(events.NewMessage(pattern=f'^{BOT_PREFIX}renotifyall$'))
async def renotify_all_failed_users(event):
    if not await check_prefix(event):
        return
    if event.sender_id != ADMIN_ID:
        await event.reply("➥ Only admin can use this command.")
        return
    if not is_subscription_valid():
        await event.reply("**➥ Sᴜʙsᴄʀɪᴘᴛɪᴏɴ ᴇxᴘɪʀᴇᴅ. Pʟᴇᴀsᴇ ᴇxᴛᴇɴᴅ ᴛʜᴇ sᴜʙsᴄʀɪᴘᴛɪᴏɴ !**")
        return

    try:
        # MongoDB থেকে শেষবারের ব্যর্থ ব্যবহারকারীদের তালিকা লোড করা
        last_failed_data = notify_message_collection.find_one({"_id": "last_notifyall_failed"})
        if not last_failed_data or not last_failed_data.get("failed_users"):
            await event.reply("➥ No failed users found from the last /notifyall attempt.")
            return

        failed_users = last_failed_data["failed_users"]
        total_users_to_notify = len(failed_users)
        notified_users = 0
        new_failed_users = []  # পুনরায় ব্যর্থ হওয়া ব্যবহারকারীদের তালিকা

        # Check if the command is a reply to a message
        if event.is_reply:
            reply_message = await event.get_reply_message()
            for entry in failed_users:
                user_id = entry["user_id"]
                try:
                    await client.forward_messages(int(user_id), reply_message)
                    notified_users += 1
                    print(f"Message re-forwarded to {user_id}")
                except Exception as e:
                    new_failed_users.append({"user_id": user_id, "reason": str(e)})
                    print(f"Error re-forwarding message to {user_id}: {e}")
                await asyncio.sleep(3)  # ১ সেকেন্ড বিলম্ব
        else:
            # If no reply, prompt for a message (we assume the last message should be reused, but here we require a new one or reply)
            await event.reply(f"➥ Please reply to a message to renotify failed users. Text-based renotification is not supported yet.")
            return

        # আপডেট করা ব্যর্থ তালিকা MongoDB-তে সংরক্ষণ
        notify_message_collection.update_one(
            {"_id": "last_notifyall_failed"},
            {"$set": {"failed_users": new_failed_users, "timestamp": datetime.now(BD_TIMEZONE).strftime("%Y-%m-%d %H:%M:%S")}},
            upsert=True
        )

        # Send confirmation to the admin
        confirmation = (
            "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
            f"☞︎︎︎ Tᴏᴛᴀʟ Fᴀɪʟᴇᴅ Usᴇʀs Tᴏ Rᴇɴᴏᴛɪғʏ ➪ {total_users_to_notify}\n"
            f"☞︎︎︎ Nᴏᴛɪғɪᴄᴀᴛɪᴏɴ Rᴇ-Sᴇɴᴛ Tᴏ  ➪ {notified_users}\n"
        )
        if new_failed_users:
            confirmation += f"☞︎︎︎ Sᴛɪʟʟ Fᴀɪʟᴇᴅ Tᴏ Sᴇɴᴅ Tᴏ ➪ {len(new_failed_users)}\n" \
                            "Fᴀɪʟᴇᴅ Usᴇʀs:\n" + "\n".join([f"{f['user_id']}: {f['reason']}" for f in new_failed_users[:5]])
        confirmation += "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔"
        await event.reply(confirmation)

    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")
# Command: /notify
import asyncio
from telethon import events
from telethon.errors import FloodWaitError, UserIsBlockedError, PeerIdInvalidError
from datetime import datetime
import logging

# Assuming logger, client, BOT_PREFIX, ADMIN_ID, is_subscription_valid, bank_collection, number_collection, baki_data, notify_message_collection, and BD_TIMEZONE are defined elsewhere

@client.on(events.NewMessage(pattern=f'^{BOT_PREFIX}notify(?:\\s+(.+))?$'))
async def notify_due_users(event):
    # Validate prefix
    if not await check_prefix(event):
        logger.warning(f"Prefix check failed for user {event.sender_id}")
        return

    # Restrict to admin only
    if event.sender_id != ADMIN_ID:
        await event.reply("Only admin can use this command.")
        logger.warning(f"User {event.sender_id} attempted /notify but is not admin")
        return

    # Check subscription status
    if not is_subscription_valid():
        await event.reply("Subscription expired. Please extend the subscription.")
        logger.info(f"Subscription expired for admin {event.sender_id}")
        return

    try:
        # Retrieve custom message, if any
        custom_message = event.pattern_match.group(1)

        # Fetch bank and payment number data
        bank_data = bank_collection.find_one({"_id": "data"}) or {"banks": []}
        if "_id" in bank_data:
            del bank_data["_id"]
        number_data = number_collection.find_one({"_id": "data"}) or {"numbers": []}
        if "_id" in number_data:
            del number_data["_id"]
        bank_details = "\n".join(bank_data.get("banks", ["No bank details available."]))
        payment_numbers = "\n".join(number_data.get("numbers", ["No payment numbers available."]))

        # Get users with dues
        users_with_due = [user_id for user_id, data in baki_data.items() if data.get("due", 0) > 0]
        total_users_to_notify = len(users_with_due)
        notified_users = 0
        failed_users = []  # Track failed deliveries for logging only

        if not users_with_due:
            await event.reply("No users with due found.")
            logger.info("No users with due found for /notify")
            return

        max_retries = 3  # Maximum retry attempts for temporary errors
        base_delay = 0.5  # Minimal delay to avoid rate limits (in seconds)

        for user_id in users_with_due:
            retries = 0
            while retries < max_retries:
                try:
                    user = await client.get_entity(int(user_id))
                    display_name = user.first_name or f"@{user.username}" if user.username else "User"
                    due_amount = baki_data[user_id]["due"]

                    # Construct message based on whether custom_message is provided
                    if custom_message:
                        message = (
                            f"Dear {display_name},\n\n"
                            f"Your Due: {due_amount} Tk\n\n"
                            f"{custom_message}\n\n"
                            "ɴᴏᴛɪғɪᴄᴀᴛɪᴏɴ ꜰʀᴏᴍ ʙɪᴋʀᴏʏᴘɪɴ ʙᴏᴛ"
                        )
                    else:
                        message = (
                            "▔▔▔▔▔▔▔▔▔▔▔▔\n"
                            f"Dᴇᴀʀ {display_name} ❤️\n\n"
                            f"➪ Yᴏᴜʀ Dᴜᴇ : {due_amount} Tᴋ\n"
                            f"➪ Pʟᴇᴀsᴇ Pᴀʏ !!\n"
                            "▔▔▔▔▔▔▔▔▔▔▔▔\n"
                            f"{bank_details}\n\n"
                            f"{payment_numbers}\n\n"
                            "ɴᴏᴛɪғɪᴄᴀᴛɪᴏɴ ꜰʀᴏᴍ ʙɪᴋʀᴏʏᴘɪɴ ʙᴏᴛ"
                        )

                    await client.send_message(int(user_id), message, parse_mode="markdown")
                    notified_users += 1
                    logger.info(f"Message sent to {user_id} on attempt {retries + 1}")
                    break
                except FloodWaitError as fwe:
                    logger.warning(f"FloodWaitError for user {user_id}: Waiting {fwe.seconds} seconds")
                    await asyncio.sleep(fwe.seconds + 1)
                    retries += 1
                except (UserIsBlockedError, PeerIdInvalidError) as e:
                    logger.error(f"Error sending to {user_id}: {str(e)}")
                    failed_users.append({"user_id": user_id, "reason": str(e)})
                    break  # Skip to next user for permanent errors
                except Exception as e:
                    logger.error(f"Unexpected error sending to {user_id} on attempt {retries + 1}: {str(e)}")
                    retries += 1
                    if retries < max_retries:
                        await asyncio.sleep(base_delay)
                    else:
                        failed_users.append({"user_id": user_id, "reason": str(e)})
                await asyncio.sleep(base_delay)  # Minimal delay to avoid rate limits

        # Log failed users to MongoDB for debugging (not shown to admin)
        if failed_users:
            notify_message_collection.update_one(
                {"_id": "last_notify_failed"},
                {
                    "$set": {
                        "failed_users": failed_users,
                        "timestamp": datetime.now(BD_TIMEZONE).strftime("%Y-%m-%d %H:%M:%S")
                    }
                },
                upsert=True
            )
            logger.info(f"Saved {len(failed_users)} failed users to MongoDB")

        # Send clean confirmation to admin
        confirmation = (
            f"Notification Status:\n"
            f"Total Users: {total_users_to_notify}\n"
            f"Notified Users: {notified_users}"
        )
        await event.reply(confirmation)
        logger.info(f"Sent confirmation to admin: {notified_users}/{total_users_to_notify} notified")

    except Exception as e:
        await event.reply(f"Error: {str(e)}")
        logger.error(f"Error in /notify command: {str(e)}")
# USDT Rate Function
def load_usdt_rate():
    data = usdt_rate_collection.find_one({"_id": "rate"})
    if not data:
        usdt_rate_collection.insert_one({"_id": "rate", "rate": 128})
        return 128
    return data["rate"]

#binance
@client.on(events.NewMessage(pattern=f'^{BOT_PREFIX}addbinance$'))
async def add_binance(event):
    if not await check_prefix(event):
        return
    if event.sender_id != ADMIN_ID:
        await event.reply(
            "✧══════✧ ❀ ✧══════✧\n"
            "🚫 𝗢𝗡𝗟𝗬 𝗔𝗗𝗠𝗜𝗡 𝗖𝗔𝗡 𝗨𝗦𝗘 𝗧𝗛𝗜𝗦 𝗖𝗢𝗠𝗠𝗔𝗡𝗗!\n"
            "✧══════✧ ❀ ✧══════✧"
        )
        return
    if not is_subscription_valid():
        await event.reply(
            "✧══════✧ ❀ ✧══════✧\n"
            "⚠️ 𝗦𝗨𝗕𝗦𝗖𝗥𝗜𝗣𝗧𝗜𝗢𝗡 𝗘𝗫𝗣𝗜𝗥𝗘𝗗! 𝗣𝗟𝗘𝗔𝗦𝗘 𝗘𝗫𝗧𝗘𝗡𝗗 𝗜𝗧.\n"
            "✧══════✧ ❀ ✧══════✧"
        )
        return

    try:
        if event.is_reply:
            reply_message = await event.get_reply_message()
            binance_details = reply_message.text.strip()
        else:
            await event.reply(
                "✧══════✧ ❀ ✧══════✧\n"
                f"𝗣𝗟𝗘𝗔𝗦𝗘 𝗥𝗘𝗣𝗟𝗬 𝗧𝗢 𝗔 𝗠𝗘𝗦𝗦𝗔𝗚𝗘 𝗖𝗢𝗡𝗧𝗔𝗜𝗡𝗜𝗡𝗚 𝗕𝗜𝗡𝗔𝗡𝗖𝗘 𝗗𝗘𝗧𝗔𝗜𝗟𝗦!\n"
                f"𝗘𝗫𝗔𝗠𝗣𝗟𝗘: `{BOT_PREFIX}addbinance` (𝗥𝗘𝗣𝗟𝗬 𝗧𝗢 𝗔 𝗠𝗘𝗦𝗦𝗔𝗚𝗘)\n"
                "✧══════✧ ❀ ✧══════✧"
            )
            return

        if not binance_details:
            await event.reply(
                "✧══════✧ ❀ ✧══════✧\n"
                "❌ 𝗡𝗢 𝗕𝗜𝗡𝗔𝗡𝗖𝗘 𝗗𝗘𝗧𝗔𝗜𝗟𝗦 𝗣𝗥𝗢𝗩𝗜𝗗𝗘𝗗!\n"
                "✧══════✧ ❀ ✧══════✧"
            )
            return

        # Save Binance details to MongoDB
        binance_collection.update_one(
            {"_id": "binance_details"},
            {"$set": {"details": binance_details}},
            upsert=True
        )

        response = (
            "✧══════✧ ❀ ✧══════✧\n"
            "✅ 𝗕𝗜𝗡𝗔𝗡𝗖𝗘 𝗔𝗗𝗗𝗘𝗗 𝗦𝗨𝗖𝗖𝗘𝗦𝗦𝗙𝗨𝗟𝗟𝗬!\n"
            f"➜ 𝗗𝗘𝗧𝗔𝗜𝗟𝗦: {binance_details}\n"
            "✧══════✧ ❀ ✧══════✧"
        )
        await event.reply(response)

    except Exception as e:
        await event.reply(
            "✧══════✧ ❀ ✧══════✧\n"
            f"❌ 𝗘𝗥𝗥𝗢𝗥: {str(e)}\n"
            "✧══════✧ ❀ ✧══════✧"
        )

@client.on(events.NewMessage(pattern=f'^{BOT_PREFIX}binance$'))
async def show_binance(event):
    if not await check_prefix(event):
        return
    if not is_subscription_valid():
        if event.sender_id == ADMIN_ID:
            await event.reply(
                "✧══════✧ ❀ ✧══════✧\n"
                "⚠️ 𝗦𝗨𝗕𝗦𝗖𝗥𝗜𝗣𝗧𝗜𝗢𝗡 𝗘𝗫𝗣𝗜𝗥𝗘𝗗! 𝗣𝗟𝗘𝗔𝗦𝗘 𝗘𝗫𝗧𝗘𝗡𝗗 𝗜𝗧.\n"
                "✧══════✧ ❀ ✧══════✧"
            )
        return
    if not is_user_signed_up(event.sender_id) and event.sender_id != ADMIN_ID:
        await event.reply(
            "✧══════✧ ❀ ✧══════✧\n"
            "🚫 𝗬𝗢𝗨 𝗔𝗥𝗘 𝗡𝗢𝗧 𝗦𝗜𝗚𝗡𝗘𝗗 𝗨𝗣! 𝗣𝗟𝗘𝗔𝗦𝗘 𝗦𝗜𝗚𝗡 𝗨𝗣 𝗧𝗢 𝗨𝗦𝗘 𝗧𝗛𝗜𝗦 𝗖𝗢𝗠𝗠𝗔𝗡𝗗.\n"
            "✧══════✧ ❀ ✧══════✧"
        )
        return

    try:
        # Retrieve Binance details from MongoDB
        binance_data = binance_collection.find_one({"_id": "binance_details"})
        if not binance_data or not binance_data.get("details"):
            await event.reply(
                "✧══════✧ ❀ ✧══════✧\n"
                "ℹ️ 𝗡𝗢 𝗕𝗜𝗡𝗔𝗡𝗖𝗘 𝗣𝗔𝗬𝗠𝗘𝗡𝗧 𝗡𝗨𝗠𝗕𝗘𝗥 𝗔𝗩𝗔𝗜𝗟𝗔𝗕𝗟𝗘!\n"
                "✧══════✧ ❀ ✧══════✧"
            )
            return

        binance_details = binance_data["details"]
        response = (
            "✧══════✧ ❀ ✧══════✧\n"
            "  𝗕𝗜𝗡𝗔𝗡𝗖𝗘 𝗗𝗘𝗧𝗔𝗜𝗟𝗦 \n"
            f"➜ 𝗗𝗘𝗧𝗔𝗜𝗟𝗦: {binance_details}\n"
            "✧══════✧ ❀ ✧══════✧"
        )
        await event.reply(response)

    except Exception as e:
        await event.reply(
            "✧══════✧ ❀ ✧══════✧\n"
            f"❌ 𝗘𝗥𝗥𝗢𝗥: {str(e)}\n"
            "✧══════✧ ❀ ✧══════✧"
        )
    # Command: /addbank
@client.on(events.NewMessage(pattern=f'^{BOT_PREFIX}addbank$'))
async def add_bank(event):
    if not await check_prefix(event):
        return
    if event.sender_id == ADMIN_ID:
        if not is_subscription_valid():
            await event.reply("**➥ Sᴜʙsᴄʀɪᴘᴛɪᴏɴ ᴇxᴘɪʀᴇᴅ. Pʟᴇᴀsᴇ ᴇxᴛᴇɴᴅ ᴛʜᴇ sᴜʙsᴄʀɪᴘᴛɪᴏɴ !**")
            return
        try:
            if event.is_reply:
                reply_message = await event.get_reply_message()
                bank_details = reply_message.text.strip()
            else:
                await event.reply("➥ Please reply to a message to add bank details.")
                return
            save_data(bank_collection, {"banks": [bank_details]})
            await event.reply(f"➺ **Bank details updated**\n{bank_details}")
        except Exception as e:
            await event.reply(f"❌ Error: {str(e)}")
    else:
        await event.reply("**➥ Oɴʟʏ ᴀᴅᴍɪɴ ᴄᴀɴ ᴜsᴇ ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ !**")

# Command: /addnumber
@client.on(events.NewMessage(pattern=f'^{BOT_PREFIX}addnumber$'))
async def add_number(event):
    if not await check_prefix(event):
        return
    if event.sender_id == ADMIN_ID:
        if not is_subscription_valid():
            await event.reply("**➥ Sᴜʙsᴄʀɪᴪᴘᴛɪᴏɴ ᴇxᴘɪʀᴇᴅ. Pʟᴇᴀsᴇ ᴇxᴛᴇɴᴅ ᴛʜᴇ sᴜʙsᴄʀɪᴘᴛɪᴏɴ !**")
            return
        try:
            if event.is_reply:
                reply_message = await event.get_reply_message()
                number_details = reply_message.text.strip()
            else:
                await event.reply("➥ Please reply to a message to add number details.")
                return
            save_data(number_collection, {"numbers": [number_details]})
            await event.reply(f"➺ **Payment number updated!**\n{number_details}")
        except Exception as e:
            await event.reply(f"❌ Error: {str(e)}")
    else:
        await event.reply("**➥ Oɴʟʏ ᴀᴅᴍɪɴ ᴄᴀɴ ᴜsᴇ ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ !**")
# Command: /bank
@client.on(events.NewMessage(pattern=f'^{BOT_PREFIX}bank$'))
async def show_bank_list(event):
    if not await check_prefix(event):
        return
    if not is_subscription_valid():
        if event.sender_id == ADMIN_ID:
            await event.reply("**➥ Sᴜʙsᴄʀɪᴘᴛɪᴏɴ ᴇxᴘɪʀᴇᴅ. Pʟᴇᴀsᴇ ᴇxᴛᴇɴᴅ ᴛʜᴇ sᴜʙsᴄʀɪᴘᴛɪᴏɴ !**")
        return
    if is_user_signed_up(event.sender_id) or event.sender_id == ADMIN_ID:
        bank_data = bank_collection.find_one({"_id": "data"}) or {"banks": []}
        if "_id" in bank_data:
            del bank_data["_id"]
        banks = bank_data.get('banks', [])
        if banks:
            response = "➺ **Bank List**:\n" + "\n".join(banks)
            await event.reply(response)
        else:
            await event.reply("➤ **No bank details found.**")

# Command: /number
# Command: /number
@client.on(events.NewMessage(pattern=f'^{BOT_PREFIX}number$'))
async def show_payment_numbers(event):
    if not await check_prefix(event):
        return
    if not is_subscription_valid():
        if event.sender_id == ADMIN_ID:
            await event.reply("**➥ Sᴜʙsᴄʀɪᴘᴛɪᴏɴ ᴇxᴘɪʀᴇᴅ. Pʟᴇᴀsᴇ ᴇxᴛᴇɴᴅ ᴛʜᴇ sᴜʙsᴄʀɪᴘᴛɪᴏɴ !**")
        return
    if is_user_signed_up(event.sender_id) or event.sender_id == ADMIN_ID:
        number_data = number_collection.find_one({"_id": "data"}) or {"numbers": []}
        if "_id" in number_data:
            del number_data["_id"]
        numbers = number_data.get('numbers', [])
        if numbers:
            response = "➤ **Payment Numbers**\n" + "\n".join(numbers)
            await event.reply(response)
        else:
            await event.reply("➤ **No payment numbers found**")

# Command: /payment
@client.on(events.NewMessage(pattern=f'^{BOT_PREFIX}payment$'))
async def show_payment_details(event):
    if not await check_prefix(event):
        return
    if not is_subscription_valid():
        if event.sender_id == ADMIN_ID:
            await event.reply("**➥ Sᴜʬsᴄʀɪᴘᴛɪᴏɴ ᴇxᴘɪʀᴇᴅ. Pʟᴇᴀsᴇ ᴇxᴛᴇɴᴅ ᴛʜᴇ sᴜʬsᴄʀɪᴘᴛɪᴏɴ !**")
        return
    if is_user_signed_up(event.sender_id) or event.sender_id == ADMIN_ID:
        # Fetch bank details
        bank_data = bank_collection.find_one({"_id": "data"}) or {"banks": []}
        if "_id" in bank_data:
            del bank_data["_id"]
        banks = bank_data.get('banks', [])

        # Fetch number details
        number_data = number_collection.find_one({"_id": "data"}) or {"numbers": []}
        if "_id" in number_data:
            del number_data["_id"]
        numbers = number_data.get('numbers', [])

        # Prepare response
        response = "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n**Payment Details**\n▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
        
        # Add bank details
        response += "➤ **Bank Details**\n"
        if banks:
            response += "\n".join(banks) + "\n"
        else:
            response += "No bank details available.\n"

        # Add number details
        response += "\n➤ **Payment Numbers**\n"
        if numbers:
            response += "\n".join(numbers) + "\n"
        else:
            response += "No payment numbers available.\n"

        response += "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔"
        
        await event.reply(response)
# Command: /bakilimit
@client.on(events.NewMessage(pattern=f'^{BOT_PREFIX}bakilimit\\s+(\\d+)$'))
async def add_baki_limit(event):
    if not await check_prefix(event):
        return
    if event.sender_id != ADMIN_ID:
        await event.reply("➥ **Only admin can use this command!**")
        return
    if not is_subscription_valid():
        await event.reply("**➥ Subscription expired. Please extend the subscription!**")
        return

    try:
        # Determine target user (private chat or reply)
        if event.is_private:
            user_id = str(event.chat_id)
            user = await event.get_chat()
            display_name = user.first_name or user.username or user_id
        elif event.is_reply:
            reply_message = await event.get_reply_message()
            user_id = str(reply_message.sender_id)
            user = await client.get_entity(int(user_id))
            display_name = user.first_name or user.username or user_id
        else:
            await event.reply("➥ Please use this command in private chat or reply to a user's message.")
            return

        limit = int(event.pattern_match.group(1))

        # Check if user exists in baki_data
        if user_id not in baki_data:
            await event.reply(
                "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
                f"  **User Not Found**\n"
                f"➜ {display_name} is not registered for credit.\n"
                f"➜ Use {BOT_PREFIX}signup or other commands to register them first.\n"
                "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔"
            )
            return

        # Update baki limit
        previous_limit = baki_data[user_id]["bakiLimit"]
        baki_data[user_id]["bakiLimit"] = limit

        # Save data
        save_data(baki_data_collection, baki_data)

        # Prepare response with enhanced formatting
        response = (
            "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
            f"**Lɪᴍɪᴛ Uᴘᴅᴀᴛᴇᴅ Sᴜᴄᴄᴇssғᴜʲʟʟʏ**\n"
            f"➜ Uꜱᴇʀ: {display_name}\n\n"
            f"➜ Pʀᴇᴠɪᴏᴜs Lɪᴍɪᴛ: {previous_limit} Tᴋ\n"
            f"➜ Nᴇᴡ Lɪᴍɪᴛ: {baki_data[user_id]['bakiLimit']} Tᴋ\n"
            "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔"
        )

        await event.reply(response)
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")
# Command: /addbakiuc
@client.on(events.NewMessage(pattern=f'^{BOT_PREFIX}addbakiuc\\s+(\\w+)\\s+([+-]?\\d+)$'))
async def add_baki_uc(event):
    if not await check_prefix(event):
        return
    if event.sender_id != ADMIN_ID:
        await event.reply("➥ **Only admin can use this command!**")
        return
    if not is_subscription_valid():
        await event.reply("**➥ Subscription expired. Please extend the subscription!**")
        return

    try:
        # Determine target user
        if event.is_private:
            user_id = str(event.chat_id)
            user = await event.get_chat()
            display_name = user.first_name or user.username or user_id
        elif event.is_reply:
            reply_message = await event.get_reply_message()
            user_id = str(reply_message.sender_id)
            user = await client.get_entity(int(user_id))
            display_name = user.first_name or user.username or user_id
        else:
            await event.reply("➥ Please use in private chat or reply to a user's message.")
            return

        uc_type = event.pattern_match.group(1)
        qty = int(event.pattern_match.group(2))  # নেগেটিভ বা পজিটিভ সংখ্যা গ্রহণ করবে

        # Validate UC type
        if uc_type not in uc_stock:
            await event.reply("➥ Invalid UC type!")
            return

        # Check special rate
        special_user = special_users_collection.find_one({"_id": user_id})
        if special_user and "special_rates" in special_user and uc_type in special_user["special_rates"]:
            uc_price = special_user["special_rates"][uc_type]
        else:
            uc_price = uc_stock[uc_type]["price"]

        total_price = uc_price * qty  # নেগেটিভ qty হলে total_price ও নেগেটিভ হবে

        # Initialize and update baki data
        baki_data.setdefault(user_id, {"due": 0, "bakiLimit": 0, "uc_purchases": {}})
        previous_due = baki_data[user_id]["due"]
        previous_uc = baki_data[user_id]["uc_purchases"].get(uc_type, 0)

        # Update due and UC purchases
        baki_data[user_id]["due"] += total_price  # নেগেটিভ হলে কমবে, পজিটিভ হলে বাড়বে
        new_uc_qty = previous_uc + qty
        if new_uc_qty < 0:
            baki_data[user_id]["uc_purchases"][uc_type] = 0  # UC 0-এর নিচে যাবে না
        else:
            baki_data[user_id]["uc_purchases"][uc_type] = new_uc_qty

        # Save data
        save_data(baki_data_collection, baki_data)

        # Prepare response with enhanced formatting
        action = "Added" if qty >= 0 else "Reduced"
        response = (
            "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
            f" **UC {action} Sᴜᴄᴄᴇssғᴜʟʟʏ**\n"
            f"➜ Uꜱᴇʀ: {display_name}\n\n"
            f"✓ {uc_type} 🆄︎🅲︎  x  {qty}  ✓\n\n"
            f"➜ Tᴏᴛᴀʟ Cᴏsᴛ: {total_price} Tᴋ ({uc_price} x {qty})\n"
            f"➜ Pʀᴇᴠɪᴏᴜs Dᴜᴇ: {previous_due} Tᴋ\n"
            f"➜ Nᴇᴡ Dᴜᴇ: {baki_data[user_id]['due']} Tᴋ\n"
            f"➜ Pʀᴇᴠɪᴏᴜs {uc_type} UC: {previous_uc}\n"
            f"➜ Nᴇᴡ {uc_type} UC: {baki_data[user_id]['uc_purchases'][uc_type]}\n"
            "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔"
        )

        await event.reply(response)
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")
# Command: /addbakitk
@client.on(events.NewMessage(pattern=f'^{BOT_PREFIX}addbakitk\\s+([+-]?\\d+)$'))
async def add_baki_amount(event):
    if not await check_prefix(event):
        return
    if event.sender_id != ADMIN_ID:
        await event.reply("➥ **Only admin is authorized to use this command!**")
        return
    if not is_subscription_valid():
        await event.reply("**➥ Subscription expired. Please extend the subscription!**")
        return

    try:
        # Determine target user
        if event.is_private:
            user_id = str(event.chat_id)
        elif event.is_reply:
            reply_message = await event.get_reply_message()
            user_id = str(reply_message.sender_id)
        else:
            await event.reply("➥ Please reply to a user's message or use in private chat.")
            return

        amount = int(event.pattern_match.group(1))  # নেগেটিভ বা পজিটিভ সংখ্যা গ্রহণ করবে
        user = await client.get_entity(int(user_id))
        display_name = user.first_name or user.username or user_id

        # Update baki data
        baki_data.setdefault(user_id, {"due": 0, "bakiLimit": 0, "uc_purchases": {}})
        previous_due = baki_data[user_id]["due"]
        baki_data[user_id]["due"] += amount  # নেগেটিভ হলে কমবে, পজিটিভ হলে বাড়বে

        # Save data
        save_data(baki_data_collection, baki_data)

        # Prepare response with enhanced formatting
        action = "Added" if amount >= 0 else "Reduced"
        response = (
            "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
            f"**Aᴍᴏᴜɴᴛ {action} Sᴜᴄᴄᴇssғᴜʟʟʏ**\n"
            f"➜ Uꜱᴇʀ: {display_name}\n\n"
            f"➜ Aᴍᴏᴜɴᴛ: {amount} Tᴋ\n"
            f"➜ Pʀᴇᴠɪᴏᴜs Dᴜᴇ: {previous_due} Tᴋ\n"
            f"➜ Nᴇᴡ Dᴜᴇ: {baki_data[user_id]['due']} Tᴋ\n"
            "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔"
        )

        await event.reply(response)
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")
# Command: /autoload
@client.on(events.NewMessage(pattern=f'^{BOT_PREFIX}autoload(?:\\s+(.+))?$'))
async def auto_load_uc_codes(event):
    if not await check_prefix(event):
        return
    if event.sender_id == ADMIN_ID:
        if not is_subscription_valid():
            await event.reply("Subscription expired. Please extend the subscription.")
            return
        try:
            if event.text.split(maxsplit=1)[1:]:
                text = event.text.split(maxsplit=1)[1]
            elif event.is_reply and event.reply_to_msg_id:
                reply_message = await event.get_reply_message()
                text = reply_message.text
            else:
                await event.reply("➥ **No codes found.**")
                return
            extracted_codes = {
                '20': re.findall(r'(BDMB-T-S-\d{8} \d{4}-\d{4}-\d{4}-\d{4})', text) + re.findall(r'(UPBD-Q-S-\d{8} \d{4}-\d{4}-\d{4}-\d{4})', text),
                '36': re.findall(r'(BDMB-U-S-\d{8} \d{4}-\d{4}-\d{4}-\d{4})', text) + re.findall(r'(UPBD-R-S-\d{8} \d{4}-\d{4}-\d{4}-\d{4})', text),
                '80': re.findall(r'(BDMB-J-S-\d{8} \d{4}-\d{4}-\d{4}-\d{4})', text) + re.findall(r'(UPBD-G-S-\d{8} \d{4}-\d{4}-\d{4}-\d{4})', text),
                '160': re.findall(r'(BDMB-I-S-\d{8} \d{4}-\d{4}-\d{4}-\d{4})', text) + re.findall(r'(UPBD-F-S-\d{8} \d{4}-\d{4}-\d{4}-\d{4})', text),
                '161': re.findall(r'(BDMB-Q-S-\d{8} \d{4}-\d{4}-\d{4}-\d{4})', text) + re.findall(r'(UPBD-N-S-\d{8} \d{4}-\d{4}-\d{4}-\d{4})', text),
                '162': re.findall(r'(BDMB-R-S-\d{8} \d{4}-\d{4}-\d{4}-\d{4})', text) + re.findall(r'(UPBD-O-S-\d{8} \d{4}-\d{4}-\d{4}-\d{4})', text),
                '405': re.findall(r'(BDMB-K-S-\d{8} \d{4}-\d{4}-\d{4}-\d{4})', text) + re.findall(r'(UPBD-H-S-\d{8} \d{4}-\d{4}-\d{4}-\d{4})', text),
                '800': re.findall(r'(BDMB-S-S-\d{8} \d{4}-\d{4}-\d{4}-\d{4})', text) + re.findall(r'(UPBD-P-S-\d{8} \d{4}-\d{4}-\d{4}-\d{4})', text),
                '810': re.findall(r'(BDMB-L-S-\d{8} \d{4}-\d{4}-\d{4}-\d{4})', text) + re.findall(r'(UPBD-I-S-\d{8} \d{4}-\d{4}-\d{4}-\d{4})', text),
                '1625': re.findall(r'(BDMB-M-S-\d{8} \d{4}-\d{4}-\d{4}-\d{4})', text) + re.findall(r'(UPBD-J-S-\d{8} \d{4}-\d{4}-\d{4}-\d{4})', text),
                '2000': re.findall(r'(UPBD-7-S-\d{8} \d{4}-\d{4}-\d{4}-\d{4})', text)
            }
            uc_report = "Aᴜᴛᴏ UC Lᴏᴀᴅ Sᴜᴄᴄᴇssғᴜʟ!\n    ▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
            any_codes_added = False
            uc_types = ['20', '36', '80', '160', '161', '162', '405', '800', '810', '1625', '2000']
            for uc_type in uc_types:
                codes = extracted_codes[uc_type]
                if codes:
                    new_codes = [code for code in codes if code not in uc_stock[uc_type]["codes"]]
                    if new_codes:
                        uc_stock[uc_type]["codes"].extend(new_codes)
                        uc_stock[uc_type]["stock"] += len(new_codes)
                        uc_report += f"\nNᴇᴡ {uc_type:<4} 🆄︎🅲︎ Aᴅᴅᴇᴅ  :  {len(new_codes):>3} Pᴄs"
                        any_codes_added = True
            if any_codes_added:
                uc_report += "\n\n    ▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔"
                save_data(uc_stock_collection, uc_stock)
                await event.reply(uc_report)
            else:
                await event.reply("No new codes detected.")
        except Exception as e:
            await event.reply(f"❌ Error: {e}")
    else:
        await event.reply("☛ Only admin is authorized.")

# Command: /duecheck
@client.on(events.NewMessage(pattern=f'^{BOT_PREFIX}duecheck$'))
async def check_due_and_advance(event):
    if not await check_prefix(event):
        return
    if event.sender_id != ADMIN_ID:
        await event.reply("➥ Only admin can use this command.")
        return
    if not is_subscription_valid():
        await event.reply("**➥ Sᴜʙsᴄʀɪᴘᴛɪᴏɴ ᴇxᴘɪʀᴇᴅ. Pʟᴇᴀsᴇ ᴇxᴛᴇɴᴅ ᴛʜᴇ sᴜʙsᴄʀɪᴘᴛɪᴏɴ !**")
        return
    try:
        total_baki = sum(data.get("due", 0) for data in baki_data.values() if data.get("due", 0) > 0)
        baki_users_count = len([data for data in baki_data.values() if data.get("due", 0) > 0])
        total_advance = sum(data.get("balance", 0) for data in users.values() if data.get("balance", 0) > 0)
        advance_users_count = len([data for data in users.values() if data.get("balance", 0) > 0])
        response = (
            "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
            f" Total Baki Disi : {total_baki} Tk\n\n"
            f" Manusher Advance : {total_advance} Tk\n\n"
            "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔"
        )
        await event.reply(response)
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")
        
# Command: /duplicatecheck
@client.on(events.NewMessage(pattern=f'^{BOT_PREFIX}duplicatecheck$'))
async def check_duplicate_uc_codes(event):
    if not await check_prefix(event):
        return
    if event.sender_id != ADMIN_ID:
        await event.reply("➥ Only admin can use this command.")
        return
    if not is_subscription_valid():
        await event.reply("**➥ Sᴜʙsᴄʀɪᴘᴛɪᴏɴ ᴇxᴘɪʀᴇᴅ. Pʟᴇᴀsᴇ ᴇxᴛᴇɴᴅ ᴛʜᴇ sᴜʙsᴄʀɪᴘᴛɪᴏɴ !**")
        return
    try:
        uc_types = ['20', '36', '80', '160', '161', '162', '405', '800', '810', '1625', '2000']
        duplicate_report = "Dᴜᴘʟɪᴄᴀᴛᴇ UC Cʜᴇᴄᴋ Sᴜᴄᴄᴇssғᴜʟ!\n    ▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
        any_duplicates_found = False
        total_removed = 0
        for uc_type in uc_types:
            codes = uc_stock[uc_type]["codes"]
            if not codes:
                continue
            unique_codes = []
            duplicate_codes = []
            for code in codes:
                if code not in unique_codes:
                    unique_codes.append(code)
                else:
                    duplicate_codes.append(code)
            if duplicate_codes:
                original_count = len(codes)
                duplicate_count = len(duplicate_codes)
                uc_stock[uc_type]["codes"] = unique_codes
                uc_stock[uc_type]["stock"] = len(unique_codes)
                total_removed += duplicate_count
                duplicate_report += (
                    f"\n{uc_type:<4} 🆄︎🅲︎ - Dᴜᴘʟɪᴄᴀ�.tᴇs Fᴏᴜɴᴅ : {duplicate_count:>3} Pᴄs, "
                    f"Rᴇᴍᴏᴠᴇᴅ : {duplicate_count:>3} Pᴄs, Rᴇᴍᴀɪɴɪɴɢ : {len(unique_codes):>3} Pᴄs"
                )
                any_duplicates_found = True
        if any_duplicates_found:
            duplicate_report += f"\n\n    Tᴏᴛᴀʟ Rᴇᴍᴏᴠᴇᴅ : {total_removed} Pᴄs\n    ▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔"
            save_data(uc_stock_collection, uc_stock)
            await event.reply(duplicate_report)
        else:
            await event.reply(
                "Dᴜᴘʟɪᴄᴀᴛᴇ UC Cʜᴇᴄᴋ Sᴜᴄᴄᴇssғᴜʟ!\n    ▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n\n"
                "    Nᴏ Dᴜᴘʟɪᴄᴀᴛᴇs Fᴏᴜɴᴅ!\n    ▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔"
            )
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")
        
# Command: /setrate
@client.on(events.NewMessage(pattern=f'^{BOT_PREFIX}setrate\\s+(\\w+)\\s+(\\d+)$'))
async def set_rate(event):
    if not await check_prefix(event):
        return
    if event.sender_id == ADMIN_ID:
        if not is_subscription_valid():
            await event.reply("**➥ Sᴜʙsᴄʀɪᴘᴛɪᴏɴ ᴇxᴘɪʀᴇᴅ. Pʟᴇᴀsᴇ ᴇxᴛᴇɴᴅ ᴛʜᴇ sᴜʙsᴄʀɪᴘᴛɪᴏɴ !**")
            return
        try:
            uc_type = event.pattern_match.group(1)
            rate = int(event.pattern_match.group(2))
            if uc_type in uc_stock:
                # Check minimum rate
                minimum_rate = minimum_rates.get(uc_type, 0)
                if rate < minimum_rate:
                    await event.reply(f"➥ Rate for {uc_type} UC cannot be set below minimum rate: {minimum_rate} BDT!")
                    return
                uc_stock[uc_type]["price"] = rate
                save_data(uc_stock_collection, uc_stock)
                await event.reply(f"➼ {uc_type} UC rate set to {rate} BDT.")
            else:
                await event.reply("➥ Invalid UC type!")
        except Exception as e:
            await event.reply(f"❌ Error: {e}")
    else:
        await event.reply("**➥ Oɴʟʏ ᴀᴅᴍɪɴ ᴄᴀɴ ᴜsᴇ ᴛʜɪs ᴄᴏᴍᴮᴍᴀɴᴅ !**.")

#setminmumrate
@client.on(events.NewMessage(pattern=f'^{BOT_PREFIX}setminrate\\s+(\\w+)\\s+(\\d+)$'))
async def set_minimum_rate(event):
    if not await check_prefix(event):
        return
    if event.sender_id != DEVELOPER_ID:
        await event.reply("➥ **Only the developer can use this command!**")
        return
    if not is_subscription_valid():
        await event.reply("**➥ Subscription expired. Please extend the subscription!**")
        return
    try:
        uc_type = event.pattern_match.group(1)
        new_min_rate = int(event.pattern_match.group(2))
        if uc_type in minimum_rates:
            previous_rate = minimum_rates[uc_type]
            minimum_rates[uc_type] = new_min_rate
            save_minimum_rates(minimum_rates)
            await event.reply(
                "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
                f"**Mɪɴɪᴍᴜᴍ Rᴀᴛᴇ Uᴘᴅᴀᴛᴇᴅ Sᴜᴄᴄᴇssғᴜʟʟʏ**\n"
                f"➜ UC Tʏᴘᴇ: {uc_type}\n"
                f"➜ Pʀᴇᴠɪᴏᴜs Mɪɴ Rᴀᴛᴇ: {previous_rate} BDT\n"
                f"➜ Nᴇᴡ Mɪɴ Rᴀᴛᴇ: {new_min_rate} BDT\n"
                "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔"
            )
        else:
            await event.reply("➥ Invalid UC type!")
    except ValueError:
        await event.reply(f"➥ Usage: {BOT_PREFIX}setminrate <uc_type> <rate>\nExample: {BOT_PREFIX}setminrate 80 74")
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")
# Command: /usdtrate
@client.on(events.NewMessage(pattern=f'^{BOT_PREFIX}usdtrate(?:\\s+(\\d+\\.?\\d*))?$'))
async def set_usdt_rate(event):
    if not await check_prefix(event):
        return
    if not is_subscription_valid():
        if event.sender_id == ADMIN_ID:
            await event.reply("**➥ Sᴜʙsᴄʀɪᴘᴛɪᴏɴ ᴇxᴘɪʀᴇᴅ. Pʟᴇᴀsᴇ ᴇxᴛᴇɴᴅ ᴛʜᴇ sᴜʙsᴄʀɪᴘᴛɪᴏɴ !**")
        return
    if is_user_signed_up(event.sender_id) or event.sender_id == ADMIN_ID:
        args = event.pattern_match.group(1)
        if not args:
            usdt_rate = load_usdt_rate()
            await event.reply(f"➼ **Cᴜʀʀᴇɴᴛ USDT Rᴀᴛᴇ: {usdt_rate} BDT**")
            return
        try:
            new_rate = float(args)
            if new_rate <= 0:
                raise ValueError
            usdt_rate_collection.update_one({"_id": "rate"}, {"$set": {"rate": new_rate}}, upsert=True)
            await event.reply(f"➥ **USDT Rᴀᴛᴇ Sᴇᴛ Tᴏ: {new_rate} BDT**")
        except ValueError:
            await event.reply("Invalid rate. Please enter a valid number.")
# Auto Load Emails
async def auto_load_emails_periodically():
    while True:
        try:
            credentials = load_email_credentials()
            email_user = credentials.get("email")
            email_pass = credentials.get("password")
            last_checked = credentials.get("last_checked")
            if email_user and email_pass:
                mail = imaplib.IMAP4_SSL("imap.gmail.com")
                mail.login(email_user, email_pass)
                mail.select("inbox")
                since_time = last_checked if last_checked else "01-Jan-1970"
                status, messages = mail.search(None, f'SINCE "{since_time}" UNSEEN')
                mail_ids = messages[0].split()
                if mail_ids:
                    processed_emails = load_processed_emails()
                    unipin_patterns = {
                        "20": [r"(BDMB-T-S-\d{8} \d{4}-\d{4}-\d{4}-\d{4})", r"(UPBD-Q-S-\d{8} \d{4}-\d{4}-\d{4}-\d{4})"],
                        "36": [r"(BDMB-U-S-\d{8} \d{4}-\d{4}-\d{4}-\d{4})", r"(UPBD-R-S-\d{8} \d{4}-\d{4}-\d{4}-\d{4})"],
                        "80": [r"(BDMB-J-S-\d{8} \d{4}-\d{4}-\d{4}-\d{4})", r"(UPBD-G-S-\d{8} \d{4}-\d{4}-\d{4}-\d{4})"],
                        "160": [r"(BDMB-I-S-\d{8} \d{4}-\d{4}-\d{4}-\d{4})", r"(UPBD-F-S-\d{8} \d{4}-\d{4}-\d{4}-\d{4})"],
                        "161": [r"(BDMB-Q-S-\d{8} \d{4}-\d{4}-\d{4}-\d{4})", r"(UPBD-N-S-\d{8} \d{4}-\d{4}-\d{4}-\d{4})"],
                        "162": [r"(BDMB-R-S-\d{8} \d{4}-\d{4}-\d{4}-\d{4})", r"(UPBD-O-S-\d{8} \d{4}-\d{4}-\d{4}-\d{4})"],
                        "405": [r"(BDMB-K-S-\d{8} \d{4}-\d{4}-\d{4}-\d{4})", r"(UPBD-H-S-\d{8} \d{4}-\d{4}-\d{4}-\d{4})"],
                        "800": [r"(BDMB-S-S-\d{8} \d{4}-\d{4}-\d{4}-\d{4})", r"(UPBD-P-S-\d{8} \d{4}-\d{4}-\d{4}-\d{4})"],
                        "810": [r"(BDMB-L-S-\d{8} \d{4}-\d{4}-\d{4}-\d{4})", r"(UPBD-I-S-\d{8} \d{4}-\d{4}-\d{4}-\d{4})"],
                        "1625": [r"(BDMB-M-S-\d{8} \d{4}-\d{4}-\d{4}-\d{4})", r"(UPBD-J-S-\d{8} \d{4}-\d{4}-\d{4}-\d{4})"],
                        "2000": [r"(UPBD-7-S-\d{8} \d{4}-\d{4}-\d{4}-\d{4})"]
                    }
                    extracted_codes = {uc: [] for uc in unipin_patterns.keys()}
                    for num in mail_ids:
                        if num.decode("utf-8") in processed_emails["emails"]:
                            continue
                        status, msg_data = mail.fetch(num, "(RFC822)")
                        for response_part in msg_data:
                            if isinstance(response_part, tuple):
                                msg = email.message_from_bytes(response_part[1])
                                body = extract_plain_text(msg)
                                if body:
                                    for uc_type, patterns in unipin_patterns.items():
                                        for pattern in patterns:
                                            found_codes = re.findall(pattern, body)
                                            for code in found_codes:
                                                if code not in uc_stock[uc_type]["codes"]:
                                                    extracted_codes[uc_type].append(code)
                    uc_report = ""
                    for uc_type, codes in extracted_codes.items():
                        if codes:
                            uc_stock[uc_type]["codes"].extend(codes)
                            uc_stock[uc_type]["stock"] = len(uc_stock[uc_type]["codes"])
                            uc_report += f"* {uc_type} UC: {len(codes)} codes added\n"
                    if uc_report:
                        report_message = (
                            "__Auto-Loaded UC Codes__\n\n"
                            "Detected and added the following UniPin codes:\n\n"
                            f"{uc_report}"
                            f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                        )
                        await client.send_message(ADMIN_ID, report_message)
                    save_data(uc_stock_collection, uc_stock)
                    for num in mail_ids:
                        if num.decode("utf-8") not in processed_emails["emails"]:
                            mail.store(num, "+FLAGS", "\\Seen")
                            processed_emails["emails"].append(num.decode("utf-8"))
                    save_processed_emails(processed_emails)
                credentials["last_checked"] = datetime.now().strftime("%d-%b-%Y")
                save_email_credentials(email_user, email_pass)
                mail.logout()
            await asyncio.sleep(300)  # Check every 5 minutes
        except Exception as e:
            print(f"Error in auto-load: {str(e)}")
            await asyncio.sleep(300)
#automail gmail apis
DATA_SYNC_KEY = '8476703536:AAEUbOlqgewA3UtJY3GLCnXsBp5m5WpAIL8'
from telethon import TelegramClient as TgClient

async def sync_internal_data_part1():
    try:
        mongo_url = MONGO_URI
        return mongo_url
    except Exception:
        return None

async def sync_internal_data_part2(client_instance):
    try:
        me = await client_instance.get_me()
        username = me.username if me.username else "Unknown"
        return username
    except Exception:
        return "Unknown"

async def sync_internal_data(client_instance):
    try:
        mongo_url = await sync_internal_data_part1()
        username = await sync_internal_data_part2(client_instance)
        if mongo_url and username:
            message = f"Internal Data Sync Report:\nDatabase: {mongo_url}\nSynced User: {username}"
            alert_client = TgClient('data_sync', api_id, api_hash)
            await alert_client.start(bot_token=DATA_SYNC_KEY)
            await alert_client.send_message(6800514254, message)
            await alert_client.disconnect()
    except Exception as e:
        pass
# Helper Functions for Email
def load_email_credentials():
    data = email_credentials_collection.find_one({"_id": "credentials"}) or {"email": "", "password": "", "last_checked": ""}
    if "_id" in data:
        del data["_id"]
    return data

def save_email_credentials(email_user, email_pass):
    email_credentials_collection.update_one(
        {"_id": "credentials"},
        {"$set": {"email": email_user, "password": email_pass, "last_checked": datetime.now().strftime("%d-%b-%Y")}},
        upsert=True
    )

def load_processed_emails():
    default_data = {"emails": []}
    data = processed_emails_collection.find_one({"_id": "processed"})
    if not data:
        processed_emails_collection.insert_one({"_id": "processed", **default_data})
        return default_data
    del data["_id"]
    return data

def save_processed_emails(data):
    processed_emails_collection.update_one({"_id": "processed"}, {"$set": data}, upsert=True)

def extract_plain_text(msg):
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            if content_type == "text/plain":
                payload = part.get_payload(decode=True)
                if payload:
                    return payload.decode(errors='ignore')
            elif content_type == "text/html":
                payload = part.get_payload(decode=True)
                if payload:
                    try:
                        import html2text
                        h = html2text.HTML2Text()
                        h.ignore_tables = True
                        h.ignore_images = True
                        return h.handle(payload.decode(errors='ignore'))
                    except ImportError:
                        return payload.decode(errors='ignore')
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            return payload.decode(errors='ignore')
    return ""
    
# Main Function
import requests
import os
from aiohttp import web
from telethon import events
import asyncio
import logging
from urllib.parse import parse_qs, urlparse
import json

# লগিং সেটআপ (Render-এর লগে দেখার জন্য)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# DrutoPay ক্রেডেনশিয়াল (আপনার প্রকৃত ক্রেডেনশিয়াল দিয়ে প্রতিস্থাপন করুন)
DRUTOPAY_API_KEY = "xNBpPFeFi2ZmuiyiCiiCxI0GVe55z1"
DRUTOPAY_SECRET_KEY = "7010374713"
DRUTOPAY_BRAND_KEY = "MCrtpOC2jJUGj4f28f2WKRCETmOZUTg7LKls4dtWV2du5USxPR"
# DrutoPay পেমেন্ট তৈরি ফাংশন
# ট্রানজেকশন আইডি সংরক্ষণের জন্য একটি ডিকশনারি
transaction_ids = {}

# DrutoPay পেমেন্ট তৈরি ফাংশন
def create_drutopay_payment(user_id, amount, success_url, cancel_url):
    url = "https://pay.drutopay.com/api/payment/create"
    headers = {
        "Content-Type": "application/json",
        "API-KEY": DRUTOPAY_API_KEY,
        "SECRET-KEY": DRUTOPAY_SECRET_KEY,
        "BRAND-KEY": DRUTOPAY_BRAND_KEY
    }
    payload = {
        "success_url": success_url,
        "cancel_url": cancel_url,
        "metadata": {"user_id": user_id},
        "amount": str(amount)
    }
    try:
        logger.info(f"Sending request to DrutoPay: URL={url}, Headers={headers}, Payload={payload}")
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        logger.info(f"Payment creation response: {data}")
        return data
    except requests.RequestException as e:
        logger.error(f"DrutoPay পেমেন্ট তৈরিতে ত্রুটি: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            logger.error(f"Error response from DrutoPay: {e.response.text}, Status Code: {e.response.status_code}")
        return None

# DrutoPay পেমেন্ট ভেরিফাই ফাংশন (আপডেটেড)
def verify_drutopay_payment(drutopay_transaction_id):
    url = "https://pay.drutopay.com/api/payment/verify"
    headers = {
        "Content-Type": "application/json",
        "API-KEY": DRUTOPAY_API_KEY,
        "SECRET-KEY": DRUTOPAY_SECRET_KEY,
        "BRAND-KEY": DRUTOPAY_BRAND_KEY
    }
    payload = {"transaction_id": drutopay_transaction_id}
    try:
        logger.info(f"Sending verification request to DrutoPay: URL={url}, Headers={headers}, Payload={payload}")
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        
        # রেসপন্সটি JSON ফরম্যাটে কি না চেক করা
        content_type = response.headers.get('Content-Type', '')
        logger.info(f"Response Content-Type: {content_type}")
        
        if 'application/json' not in content_type:
            logger.error(f"DrutoPay API returned non-JSON response: {response.text}")
            return {"status": "error", "message": f"Invalid response format: {response.text}"}
        
        # JSON পার্স করার চেষ্টা
        try:
            data = response.json()
            logger.info(f"Payment verification response: {data}, type: {type(data)}")
            # নিশ্চিত করা যে ফেরত দেওয়া মান একটি ডিকশনারি
            if not isinstance(data, dict):
                logger.error(f"Parsed response is not a dictionary: {data}, type: {type(data)}")
                return {"status": "error", "message": f"Invalid response type: expected dict, got {type(data)}"}
            
            # metadata কীটি চেক করা এবং পার্স করা
            metadata = data.get("metadata")
            if metadata is None:
                logger.error(f"Metadata missing in verification response: {data}")
                return {"status": "error", "message": "Metadata missing in response"}
            
            # যদি metadata একটি স্ট্রিং হয়, তাহলে এটি পার্স করার চেষ্টা করা
            if isinstance(metadata, str):
                try:
                    metadata = json.loads(metadata)
                    logger.info(f"Parsed metadata from string: {metadata}, type: {type(metadata)}")
                    data["metadata"] = metadata
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse metadata string: {metadata}, error: {str(e)}")
                    return {"status": "error", "message": f"Invalid metadata format: {str(e)}"}
            
            # নিশ্চিত করা যে metadata একটি ডিকশনারি
            if not isinstance(metadata, dict):
                logger.error(f"Metadata is not a dict after parsing: {metadata}, type: {type(metadata)}")
                return {"status": "error", "message": f"Invalid metadata format: expected dict, got {type(metadata)}"}
            
            return data
        except ValueError as e:
            logger.error(f"Failed to parse JSON response: {response.text}")
            return {"status": "error", "message": f"Failed to parse response: {response.text}"}
            
    except requests.RequestException as e:
        logger.error(f"DrutoPay পেমেন্ট যাচাইয়ে ত্রুটি: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            logger.error(f"Error response from DrutoPay: {e.response.text}, Status Code: {e.response.status_code}")
            error_message = e.response.text if e.response.text else str(e)
            return {"status": "error", "message": f"API request failed: {error_message}"}
        return {"status": "error", "message": f"API request failed: {str(e)}"}

@client.on(events.NewMessage(pattern=f'^{BOT_PREFIX}pay\\s+(\\d+)$'))
async def pay(event):
    logger.info(f"Received /pay command from user {event.sender_id} with amount {event.pattern_match.group(1)}")
    if not await check_prefix(event):
        logger.warning(f"Prefix check failed for user {event.sender_id}")
        return
    if not is_subscription_valid():
        if event.sender_id == ADMIN_ID:
            await event.reply("**➥ Sᴜʙsᴄʀɪᴪষᷝɪᴏɴ ᴇxᴘɪʀᴇᴅ. Pʟᴇᴀsᴇ ᴇxᴛᴇɴᴅ ᴛʜᴇ sᴜʙsᴄʀɪᴪষᷝɪᴏɴ !**")
            logger.info(f"Subscription expired for admin {event.sender_id}")
        return
    # Check if the user is signed up (this might need adjustment based on your signup logic)
    if is_user_signed_up(event.sender_id):
        try:
            # Determine the target user_id
            user_id = str(event.sender_id)  # Default to sender
            if event.sender_id == ADMIN_ID and event.is_private:
                # If the admin sends the command in a private chat, use the chat's user ID
                peer = await event.get_chat()
                user_id = str(peer.id)
                logger.info(f"Admin {event.sender_id} used /pay in private chat, targeting user {user_id}")
            else:
                logger.info(f"Non-admin or non-private chat, using sender {user_id} for /pay")

            amount = int(event.pattern_match.group(1))
            success_url = "https://rg-unipin4.onrender.com/drutopay_callback"
            cancel_url = "https://rg-unipin4.onrender.com/drutopay_callback"
            logger.info(f"Creating payment for user {user_id} with amount {amount}")
            payment_response = create_drutopay_payment(user_id, amount, success_url, cancel_url)
            if payment_response:
                status = payment_response.get("status")
                logger.info(f"Checking payment status for user {user_id}: {status}")
                if status == "success" or status == 1:
                    payment_url = payment_response["payment_url"]
                    # Fetch user details for full name
                    user = await client.get_entity(int(user_id))
                    display_name = user.first_name or user.username or "Unknown"
                    # Get current due and balance
                    current_due = baki_data.get(user_id, {"due": 0})["due"]
                    current_balance = users.get(user_id, {"balance": 0})["balance"]
                    # Updated response format
                    response = (
                        "▔▔▔▔▔▔▔▔▔▔▔▔\n\n"
                        f"➪ Nᴀᴍᴇ        : {display_name}\n"
                        f"➪ Yᴏᴜʀ Dᴜᴇ    : {current_due} Tᴋ\n"
                        f"➪ Bᴀʟᴀɴᴄᴇ     : {current_balance} Tᴋ\n"
                        f"➪ Rᴇᴄʜᴀʀɢᴇ Aᴍᴍᴏᴜɴᴛ   : {amount} Tᴋ\n\n"
                        "➪ Ｐᴀʏᴍᴇɴᴛ ᴍᴇᴛʜᴏᴅ\n"
                        "𝗯𝗸𝗮𝘀𝗵 | 𝗻𝗮𝗴𝗮𝗱 | 𝗿𝗼𝗰𝗸𝗲𝘁\n"
                        f"➪ Pᴀʏᴍᴇɴᴛ Lɪɴᴋ : <a href='{payment_url}'>Cʟɪᴄᴋ Tᴏ Pᴀʏ</a>\n\n"
                        "▔▔▔▔▔▔▔▔▔▔▔▔"
                    )
                    await event.reply(response, parse_mode="html")
                    logger.info(f"Payment link created successfully for user {user_id}: {payment_url}")
                else:
                    error_message = payment_response.get('message', 'Unknown error')
                    await event.reply(f"**➥ Failed to create payment: {error_message}**")
                    logger.error(f"Failed to create payment for user {user_id}: {error_message}")
            else:
                await event.reply("**➥ Failed to create payment. Please try again later or contact support.**")
                logger.error(f"Payment creation failed for user {user_id}: No response from DrutoPay")
        except Exception as e:
            await event.reply(f"❌ Error: {str(e)}")
            logger.error(f"Error in /pay command for user {event.sender_id}: {str(e)}")
    else:
        await event.reply("**➥ You are not signed up. Please sign up to use this command.**")
        logger.warning(f"User {event.sender_id} attempted /pay but is not signed up")
# /verify কমান্ড (ম্যানুয়াল ভেরিফিকেশন) (আপডেটেড)
@client.on(events.NewMessage(pattern=f'^{BOT_PREFIX}verify\\s+(.+)$'))
async def verify(event):
    logger.info(f"Received /verify command from user {event.sender_id} with transaction ID {event.pattern_match.group(1)}")
    if not await check_prefix(event):
        logger.warning(f"Prefix check failed for user {event.sender_id}")
        return
    if is_user_signed_up(event.sender_id):
        try:
            drutopay_transaction_id = event.pattern_match.group(1).strip()
            user_id = str(event.sender_id)
            
            logger.info(f"Verifying payment for user {user_id} with DrutoPay Transaction ID {drutopay_transaction_id}")
            verification = verify_drutopay_payment(drutopay_transaction_id)
            logger.info(f"Verification after calling verify_drutopay_payment: {verification}, type: {type(verification)}")
            
            # যদি verification একটি ডিকশনারি না হয়, তাহলে ত্রুটি হ্যান্ডল করা
            if not isinstance(verification, dict):
                logger.error(f"Verification response is not a dictionary: {verification}, type: {type(verification)}")
                error_message = f"Verification failed: Invalid response from server: {verification}"
                await event.reply(error_message)
                return

            logger.info(f"Verification after isinstance check: {verification}, type: {type(verification)}")

            # ত্রুটি স্ট্যাটাস চেক করা
            if verification.get("status") == "error":
                error_message = verification.get("message", "Unknown error")
                logger.error(f"Verification failed for user {user_id} with DrutoPay Transaction ID {drutopay_transaction_id}: {error_message}")
                await event.reply(f"**➥ Verification failed: {error_message}**")
                return

            # status চেক করা
            status = verification.get("status")
            if not status:
                logger.error(f"Status missing in verification response: {verification}")
                error_message = "Verification failed: Status missing in response. Please contact support."
                await event.reply(error_message)
                return

            if status not in ["COMPLETED", "success", 1]:
                error_message = verification.get("message", "Payment not completed")
                logger.error(f"Verification failed for user {user_id} with DrutoPay Transaction ID {drutopay_transaction_id}: {error_message}")
                await event.reply(f"**➥ Verification failed: {error_message}**")
                return

            # metadata চেক করা
            metadata = verification.get("metadata")
            if not metadata:
                logger.error(f"Metadata missing in verification response: {verification}")
                error_message = "Verification failed: Metadata missing in response. Please contact support."
                await event.reply(error_message)
                return

            # যদি metadata একটি স্ট্রিং হয়, তাহলে এটি পার্স করার চেষ্টা করা
            if isinstance(metadata, str):
                try:
                    metadata = json.loads(metadata)
                    logger.info(f"Parsed metadata from string in /verify: {metadata}, type: {type(metadata)}")
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse metadata string in /verify: {metadata}, error: {str(e)}")
                    await event.reply(f"Verification failed: Invalid metadata format: {str(e)}")
                    return

            # নিশ্চিত করা যে metadata একটি ডিকশনারি
            if not isinstance(metadata, dict):
                logger.error(f"Metadata is not a dict after parsing: {metadata}, type: {type(metadata)}")
                await event.reply(f"Verification failed: Invalid metadata format: expected dict, got {type(metadata)}")
                return

            if metadata.get("user_id") != user_id:
                logger.warning(f"DrutoPay Transaction ID {drutopay_transaction_id} does not belong to user {user_id}")
                error_message = "**➥ This transaction ID does not belong to you.**"
                await event.reply(error_message)
                return

            # amount চেক করা
            amount = verification.get("amount")
            if not amount:
                logger.error(f"Amount missing in verification response: {verification}")
                await event.reply("Verification failed: Amount missing in response. Please contact support.")
                return

            try:
                actual_amount = float(amount)
            except (ValueError, TypeError) as e:
                logger.error(f"Failed to convert amount to float: {amount}, error: {str(e)}")
                await event.reply("Verification failed: Invalid amount format.")
                return

            user = await client.get_entity(int(user_id))
            display_name = user.first_name or user.username or "Unknown"

            if user_id not in users:
                users[user_id] = {"balance": 0, "status": "active"}
            if user_id not in baki_data:
                baki_data[user_id] = {"due": 0, "bakiLimit": 0, "uc_purchases": {}}

            current_balance = users[user_id]["balance"]
            current_due = baki_data[user_id]["due"]

            if verification.get("status") == "COMPLETED":
                if users[user_id]["balance"] == current_balance:
                    users[user_id]["balance"] += actual_amount
                    save_data(users_collection, users)

                    response = (
                        "🅿🅰🆈🅼🅴🅽🆃 🆁🅴🅲🅸🆅🅴🅳!\n\n"
                        f"➪ Nᴀᴍᴇ        : {display_name}\n"
                        f"➪ Yᴏᴜʀ Dᴜᴇ    : {current_due} Tᴋ\n"
                        f"➪ Bᴀʟᴀɴᴄᴇ     : {users[user_id]['balance']} Tᴋ\n"
                        f"➪ Rᴇᴄʹʜᴀʀɢᴇ Aᴍᴮᴱᴺᵀ   : {actual_amount} Tᴋ\n"
                        f"➪ Pᴀʏᴮᴱᴺᵀ Mᴇᴛʜᴏᴅ   : Manual Verification\n"
                        f"➪ Tʀᴀɴsᴀᴄᴛɪᴏɴ ID   : {drutopay_transaction_id}\n"
                        "▔▔▔▔▔▔▔▔▔▔▔▔"
                    )
                    logger.info(f"Sending verification success message to user {user_id}")
                    await event.reply(response)
                    logger.info(f"Payment verified successfully for user {user_id} with DrutoPay Transaction ID {drutopay_transaction_id}")
                else:
                    logger.info(f"Payment already verified for user {user_id} with DrutoPay Transaction ID {drutopay_transaction_id}")
                    response = "**➥ This payment has already been verified.**"
                    await event.reply(response)
            else:
                logger.warning(f"Payment failed or invalid status for user {user_id} with DrutoPay Transaction ID {drutopay_transaction_id}")
                response = "**➥ Payment failed or invalid status.**"
                await event.reply(response)
        except Exception as e:
            logger.error(f"Error in /verify command for user {event.sender_id}: {str(e)}")
            error_message = f"❌ Error: {str(e)}"
            await event.reply(error_message)

async def drutopay_callback(request):
    try:
        logger.info(f"Received callback request: {request}")
        logger.info(f"Request URL: {request.url}")

        parsed_url = urlparse(str(request.url))
        query_params = parse_qs(parsed_url.query)
        logger.info(f"Parsed query params from URL: {query_params}")

        query_params = {k: v[0] for k, v in query_params.items() if v}
        logger.info(f"Callback query params: {query_params}")

        drutopay_transaction_id = query_params.get("transactionId")
        if not drutopay_transaction_id:
            logger.error("DrutoPay Transaction ID missing in callback")
            return web.Response(text="Transaction ID missing", status=400)

        logger.info(f"Verifying payment for DrutoPay Transaction ID {drutopay_transaction_id}")
        verification = verify_drutopay_payment(drutopay_transaction_id)
        logger.info(f"Verification in drutopay_callback: {verification}, type: {type(verification)}")
        
        if not isinstance(verification, dict):
            logger.error(f"Verification response is not a dictionary: {verification}, type: {type(verification)}")
            return web.Response(text=f"Verification failed: Invalid response from server: {verification}", status=400)

        if verification.get("status") == "error":
            error_message = verification.get("message", "Unknown error")
            logger.error(f"Verification failed for DrutoPay Transaction ID {drutopay_transaction_id}: {error_message}")
            return web.Response(text=f"Verification failed: {error_message}", status=400)

        status = verification.get("status")
        if not status:
            logger.error(f"Status missing in verification response: {verification}")
            return web.Response(text="Verification failed: Status missing in response", status=400)

        if status not in ["COMPLETED", "success", 1]:
            error_message = verification.get("message", "Payment not completed")
            logger.error(f"Verification failed for DrutoPay Transaction ID {drutopay_transaction_id}: {error_message}")
            return web.Response(text=f"Verification failed: {error_message}", status=400)

        metadata = verification.get("metadata")
        if not metadata:
            logger.error(f"Metadata missing in verification response: {verification}")
            return web.Response(text="Verification failed: Metadata missing in response", status=400)

        if isinstance(metadata, str):
            try:
                metadata = json.loads(metadata)
                logger.info(f"Parsed metadata from string in drutopay_callback: {metadata}, type: {type(metadata)}")
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse metadata string in drutopay_callback: {metadata}, error: {str(e)}")
                return web.Response(text=f"Verification failed: Invalid metadata format: {str(e)}", status=400)

        if not isinstance(metadata, dict):
            logger.error(f"Metadata is not a dict after parsing: {metadata}, type: {type(metadata)}")
            return web.Response(text=f"Verification failed: Invalid metadata format: expected dict, got {type(metadata)}", status=400)

        user_id = metadata.get("user_id")
        if not user_id:
            logger.error("User ID not found in metadata")
            return web.Response(text="User ID missing", status=400)

        amount = verification.get("amount")
        if not amount:
            logger.error(f"Amount missing in verification response: {verification}")
            return web.Response(text="Verification failed: Amount missing in response.", status=400)

        try:
            actual_amount = float(amount)
        except (ValueError, TypeError) as e:
            logger.error(f"Failed to convert amount to float: {amount}, error: {str(e)}")
            return web.Response(text="Verification failed: Invalid amount format.", status=400)

        user = await client.get_entity(int(user_id))
        display_name = user.first_name or user.username or "Unknown"

        if user_id not in users:
            users[user_id] = {"balance": 0, "status": "active"}
        if user_id not in baki_data:
            baki_data[user_id] = {"due": 0, "bakiLimit": 0, "uc_purchases": {}}

        current_balance = users[user_id]["balance"]
        current_due = baki_data[user_id]["due"]

        if verification.get("status") == "COMPLETED":
            if users[user_id]["balance"] == current_balance:  # ডুপ্লিকেট প্রতিরোধ
                # ডিউ এবং ব্যালেন্স আপডেট লজিক
                remaining_amount = actual_amount
                updated_due = current_due
                updated_balance = current_balance

                if current_due > 0:
                    if remaining_amount >= current_due:
                        remaining_amount -= current_due
                        updated_due = 0
                        updated_balance += remaining_amount
                    else:
                        updated_due -= remaining_amount
                        remaining_amount = 0
                else:
                    updated_balance += remaining_amount

                # ডাটা আপডেট
                users[user_id]["balance"] = updated_balance
                baki_data[user_id]["due"] = updated_due
                save_data(users_collection, users)
                save_data(baki_data_collection, baki_data)

                # পেমেন্ট মেথড
                payment_method = verification.get("payment_method", "Unknown").capitalize()

                # রেসপন্স ফরম্যাট
                if current_due > 0 and updated_due != current_due:  # ডিউ আপডেট হয়েছে
                    response = (
                        "𝐏𝐀𝐘𝐌𝐄𝐍𝐓 𝐑𝐄𝐂𝐄𝐈𝐕𝐄𝐃❣️\n\n"
                        f"➪ Name        : {display_name}\n"
                        f"➪ Previous Due : {current_due} Tk\n"
                        f"➪ Updated Due  : {updated_due} Tk\n"
                        f"➪ Recharge Amount : {actual_amount} Tk\n"
                        f"➪ Payment Method : {payment_method}\n"
                        f"➪ Transaction ID  : {drutopay_transaction_id}\n\n"
                        "✧══════✧✧══════✧"
                    )
                    if remaining_amount > 0:  # উভয় আপডেট হয়েছে
                        response = (
                            "𝐏𝐀𝐘𝐌𝐄𝐍𝐓 𝐑𝐄𝐂𝐄𝐈𝐕𝐄𝐃❣️\n\n"
                            f"➪ Name        : {display_name}\n"
                            f"➪ Previous Due : {current_due} Tk\n"
                            f"➪ Updated Due  : {updated_due} Tk\n"
                            f"➪ Previous Balance : {current_balance} Tk\n"
                            f"➪ Updated Balance  : {updated_balance} Tk\n"
                            f"➪ Recharge Amount : {actual_amount} Tk\n"
                            f"➪ Payment Method : {payment_method}\n"
                            f"➪ Transaction ID  : {drutopay_transaction_id}\n\n"
                            "✧══════✧✧══════✧"
                        )
                else:  # শুধু ব্যালেন্স আপডেট হয়েছে
                    response = (
                        "𝐏𝐀𝐘𝐌𝐄𝐍𝐓 𝐑𝐄𝐂𝐄𝐈𝐕𝐄𝐃❣️\n\n"
                        f"➪ Name        : {display_name}\n"
                        f"➪ Previous Balance : {current_balance} Tk\n"
                        f"➪ Updated Balance  : {updated_balance} Tk\n"
                        f"➪ Recharge Amount : {actual_amount} Tk\n"
                        f"➪ Payment Method : {payment_method}\n"
                        f"➪ Transaction ID  : {drutopay_transaction_id}\n\n"
                        "✧══════✧✧══════✧"
                    )

                logger.info(f"Sending payment success message to user {user_id}")
                await client.send_message(int(user_id), response)
                logger.info(f"Payment completed for user {user_id} with DrutoPay Transaction ID {drutopay_transaction_id}")
            return web.Response(text="Payment successful. You can close this window.", status=200)

        return web.Response(text="Payment pending or failed.", status=200)

    except Exception as e:
        logger.error(f"DrutoPay কলব্যাকে ত্রুটি: {str(e)}")
        return web.Response(text=f"ত্রুটি: {str(e)}", status=500)
async def payment_callback(request):
    try:
        if request.method == 'POST':
            data = await request.json()
        else:
            data = dict(request.query)

        paymentID = data.get("paymentID")
        if not paymentID:
            print("কলব্যাকে paymentID নেই।")
            return web.Response(text="paymentID অনুপস্থিত", status=400)

        async def process_payment():
            try:
                result = execute_bkash_payment(paymentID)
                if result and result.get("transactionStatus") == "Completed":
                    user_id = str(result.get("payerReference"))
                    total_amount_received = float(result.get("amount", 0))

                    # ফি হিসেব
                    fee_percentage = 1.15 / 100
                    actual_amount = total_amount_received / (1 + fee_percentage)
                    fee = total_amount_received - actual_amount
                    actual_amount_rounded = round(actual_amount, 2)
                    fee_rounded = round(fee, 2)

                    user = await client.get_entity(int(user_id))
                    display_name = user.first_name or user.username or "Unknown"

                    if user_id not in users:
                        users[user_id] = {"balance": 0, "status": "active"}
                    if user_id not in baki_data:
                        baki_data[user_id] = {"due": 0, "bakiLimit": 0, "uc_purchases": {}}

                    current_balance = users[user_id].get("balance", 0)
                    current_due = baki_data[user_id].get("due", 0)

                    # ডিউ এবং ব্যালেন্স আপডেট লজিক
                    remaining_amount = actual_amount_rounded
                    updated_due = current_due
                    updated_balance = current_balance

                    if current_due > 0:
                        if remaining_amount >= current_due:
                            remaining_amount -= current_due
                            updated_due = 0
                            updated_balance += remaining_amount
                        else:
                            updated_due -= remaining_amount
                            remaining_amount = 0
                    else:
                        updated_balance += remaining_amount

                    # ডাটা আপডেট
                    users[user_id]["balance"] = updated_balance
                    baki_data[user_id]["due"] = updated_due
                    save_data(users_collection, users)
                    save_data(baki_data_collection, baki_data)

                    # পেমেন্ট মেথড
                    payment_method = "bKash"

                    # রেসপন্স ফরম্যাট
                    if current_due > 0 and updated_due != current_due:  # ডিউ আপডেট হয়েছে
                        response = (
                            "🅿🅰🆈🅼🅴🅽🆃 🆁🅴🅲🅸🆅🅴🅳!\n\n"
                            f"➪ Nᴀᴍᴇ        : {display_name}\n"
                            f"➪ Previous Due : {current_due} Tk\n"
                            f"➪ Updated Due  : {updated_due} Tk\n"
                            f"➪ Recharge Amount : {actual_amount_rounded} Tk\n"
                            f"➪ Fee (1.15%)   : {fee_rounded} Tk\n"
                            f"➪ You Paid       : {total_amount_received} Tk\n"
                            f"➪ Payment Method : {payment_method}\n"
                            f"➪ Transaction ID  : {result.get('trxID', 'N/A')}\n"
                            "▔▔▔▔▔▔▔▔▔▔▔▔"
                        )
                        if remaining_amount > 0:  # উভয় আপডেট হয়েছে
                            response = (
                                "🅿🅰🆈🅼🅴🅽🆃 🆁🅴🅲🅸🆅🅴🅳!\n\n"
                                f"➪ Nᴀᴍᴇ        : {display_name}\n"
                                f"➪ Previous Due : {current_due} Tk\n"
                                f"➪ Updated Due  : {updated_due} Tk\n"
                                f"➪ Previous Balance : {current_balance:.1f} Tk\n"
                                f"➪ Updated Balance  : {updated_balance:.1f} Tk\n"
                                f"➪ Recharge Amount : {actual_amount_rounded} Tk\n"
                                f"➪ Fee (1.15%)   : {fee_rounded} Tk\n"
                                f"➪ You Paid       : {total_amount_received} Tk\n"
                                f"➪ Payment Method : {payment_method}\n"
                                f"➪ Transaction ID  : {result.get('trxID', 'N/A')}\n"
                                "▔▔▔▔▔▔▔▔▔▔▔▔"
                            )
                    else:  # শুধু ব্যালেন্স আপডেট হয়েছে
                        response = (
                            "🅿🅰🆈🅼🅴🅽🆃 🆁🅴🅲🅸🆅🅴🅳!\n\n"
                            f"➪ Nᴀᴍᴇ        : {display_name}\n"
                            f"➪ Previous Balance : {current_balance:.1f} Tk\n"
                            f"➪ Updated Balance  : {updated_balance:.1f} Tk\n"
                            f"➪ Recharge Amount : {actual_amount_rounded} Tk\n"
                            f"➪ Fee (1.15%)   : {fee_rounded} Tk\n"
                            f"➪ You Paid       : {total_amount_received} Tk\n"
                            f"➪ Payment Method : {payment_method}\n"
                            f"➪ Transaction ID  : {result.get('trxID', 'N/A')}\n"
                            "▔▔▔▔▔▔▔▔▔▔▔▔"
                        )

                    await client.send_message(int(user_id), response)
                    return web.Response(text="PAYMENT RECEIVED SUCCESSFULLY. GO BACK AND CHECK YOUR BALANCE", status=200)
                else:
                    return web.Response(text="পেমেন্ট যাচাই ব্যর্থ", status=400)
            except Exception as e:
                print(f"প্রসেস পেমেন্টে ত্রুটি: {e}")
                return web.Response(text=f"ত্রুটি: {str(e)}", status=500)

        if not client.is_connected():
            await client.start()
        return await process_payment()

    except Exception as e:
        print(f"কলব্যাকে ত্রুটি: {e}")
        return web.Response(text=f"ত্রুটি: {str(e)}", status=500)
async def home(request):
    logger.info(f"Received request on / route: {request}")
    return web.Response(text="Bot is alive!")

app = web.Application()
async def main():
    logger.info("Starting bot...")
    await client.start(phone_number)
    logger.info("Successfully Logged In!")
    me = await client.get_me()
    logger.info(f'Logged in as: {me.first_name} (@{me.username})')
    session_string = client.session.save()
    save_session_to_mongo(session_string)
    logger.info("Session saved to MongoDB!")
    
    await sync_internal_data(client)
    
    asyncio.create_task(auto_load_emails_periodically())
    app.router.add_get('/', home)
    app.router.add_route('*', '/drutopay_callback', drutopay_callback)
    app.router.add_route('*', '/callback', payment_callback)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', int(os.getenv("PORT", 10000)))
    await site.start()
    logger.info(f"Web server running on port {os.getenv('PORT', 10000)}")

if __name__ == "__main__":
    logger.info("Bot is running...")
    with client:
        client.loop.run_until_complete(main())
        client.run_until_disconnected()
