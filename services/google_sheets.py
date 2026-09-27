import os
import json
import asyncio
import discord
from typing import Optional, List, Dict, Any
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from sqlalchemy.orm import Session
from database import VerificationSubmission, User, Log
from config import GOOGLE_CREDENTIALS_FILE, GOOGLE_SHEET_ID, GOOGLE_SHEET_NAME, VERIFICATION_SYNC_INTERVAL

class GoogleSheetsService:
    REQUIRED_HEADERS = ["Timestamp", "Discord Username"]
    
    def __init__(self, db: Session, guild_id: int, guild=None):
        self.db = db
        self.guild_id = guild_id
        self.guild = guild
        self.service = None
        self.sheet_id = GOOGLE_SHEET_ID
        self.sheet_name = GOOGLE_SHEET_NAME
        self._header_map: Dict[str, int] = {}
        self._initialized = False
    
    def _get_credentials(self):
        if not os.path.exists(GOOGLE_CREDENTIALS_FILE):
            raise FileNotFoundError(f"Google credentials file not found: {GOOGLE_CREDENTIALS_FILE}")
        
        with open(GOOGLE_CREDENTIALS_FILE, 'r') as f:
            creds_data = json.load(f)
        
        if creds_data.get("type") != "service_account":
            raise ValueError(
                "Invalid credentials format: Expected service account credentials (type: 'service_account'), "
                "but got OAuth 2.0 client credentials. Please create a service account in Google Cloud Console "
                "and download the JSON key file."
            )
        
        required_fields = ["client_email", "token_uri", "private_key", "project_id"]
        missing = [f for f in required_fields if f not in creds_data]
        if missing:
            raise ValueError(f"Service account credentials missing required fields: {', '.join(missing)}")
        
        credentials = service_account.Credentials.from_service_account_file(
            GOOGLE_CREDENTIALS_FILE,
            scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
        )
        return credentials
    
    def initialize(self) -> bool:
        try:
            credentials = self._get_credentials()
            self.service = build('sheets', 'v4', credentials=credentials)
            self._initialized = True
            print(f"Google Sheets service initialized successfully for guild {self.guild_id}")
            return True
        except FileNotFoundError as e:
            print(f"Google Sheets init error: {e}")
            return False
        except ValueError as e:
            print(f"Google Sheets credentials error: {e}")
            return False
        except Exception as e:
            print(f"Failed to initialize Google Sheets service: {e}")
            return False
    
    def _find_header_indices(self, headers: List[str]) -> Dict[str, int]:
        header_map = {}
        for i, header in enumerate(headers):
            normalized = header.strip().lower()
            for required in self.REQUIRED_HEADERS:
                if normalized == required.strip().lower():
                    header_map[required] = i
        return header_map
    
    def _validate_headers(self, headers: List[str]) -> bool:
        self._header_map = self._find_header_indices(headers)
        return all(req in self._header_map for req in self.REQUIRED_HEADERS)
    
    async def fetch_sheet_data(self) -> Optional[List[List[Any]]]:
        if not self._initialized:
            if not self.initialize():
                return None
        
        try:
            range_name = f"'{self.sheet_name}'!A:Z"
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.sheet_id,
                range=range_name
            ).execute()
            
            values = result.get('values', [])
            print(f"Guild {self.guild_id}: Fetched {len(values)} rows from sheet '{self.sheet_name}'")
            return values
        except HttpError as e:
            print(f"Google Sheets API error: {e}")
            return None
        except Exception as e:
            print(f"Error fetching sheet data: {e}")
            return None
    
    async def sync_verifications(self) -> Dict[str, int]:
        stats = {
            "rows_checked": 0,
            "new_submissions": 0,
            "verified_users": 0,
            "invalid_submissions": 0,
            "duplicates": 0,
            "errors": 0
        }
        
        if not self._initialized:
            if not self.initialize():
                print(f"Guild {self.guild_id}: Google Sheets service not initialized, skipping sync")
                stats["errors"] = -1  # Indicate init failure
                return stats
        
        data = await self.fetch_sheet_data()
        if not data:
            print(f"Guild {self.guild_id}: No data returned from Google Sheets")
            stats["errors"] = -1
            return stats
        if len(data) < 2:
            print(f"Guild {self.guild_id}: Sheet has no data rows (only headers or empty)")
            return stats
        
        headers = data[0]
        print(f"Guild {self.guild_id}: Sheet headers found: {headers}")
        if not self._validate_headers(headers):
            missing = [req for req in self.REQUIRED_HEADERS if req not in self._header_map]
            print(f"Guild {self.guild_id}: Invalid headers - missing required columns: {missing}")
            self._log_error(f"Invalid headers in Google Sheet. Required: {self.REQUIRED_HEADERS}, Found: {headers}")
            stats["errors"] = len(data) - 1
            return stats
        
        rows = data[1:]
        stats["rows_checked"] = len(rows)
        print(f"Guild {self.guild_id}: Processing {len(rows)} rows from Google Sheet")
        
        for row_idx, row in enumerate(rows, start=2):
            try:
                result = await self._process_row(row_idx, row)
                if result == "new":
                    stats["new_submissions"] += 1
                elif result == "verified":
                    stats["verified_users"] += 1
                elif result == "duplicate":
                    stats["duplicates"] += 1
                elif result == "invalid":
                    stats["invalid_submissions"] += 1
            except Exception as e:
                print(f"Error processing row {row_idx}: {e}")
                stats["errors"] += 1
        
        return stats
    
    async def _process_row(self, row_number: int, row: List[Any]) -> str:
        existing = self.db.query(VerificationSubmission).filter(
            VerificationSubmission.guild_id == self.guild_id,
            VerificationSubmission.sheet_row_number == row_number
        ).first()
        
        if existing:
            return "duplicate"
        
        timestamp = self._get_cell(row, "Timestamp")
        username = self._get_cell(row, "Discord Username")
        
        discord_id = None
        
        # Try username matching (case-insensitive)
        if username and self.guild:
            username_lower = username.lower().strip()
            for member in self.guild.members:
                if member.name.lower() == username_lower or (member.display_name and member.display_name.lower() == username_lower):
                    discord_id = member.id
                    break
        
        if not discord_id:
            submission = VerificationSubmission(
                guild_id=self.guild_id,
                sheet_row_number=row_number,
                timestamp=timestamp,
                discord_username=username,
                discord_id=None,
                status="invalid",
                error="Missing Discord User ID and user not found in guild"
            )
            self.db.add(submission)
            self.db.commit()
            return "invalid"
        
        submission = VerificationSubmission(
            guild_id=self.guild_id,
            sheet_row_number=row_number,
            timestamp=timestamp,
            discord_username=username,
            discord_id=discord_id,
            status="processed"
        )
        self.db.add(submission)
        
        user = self.db.query(User).filter(
            User.guild_id == self.guild_id,
            User.discord_id == discord_id
        ).first()
        
        if user:
            if not user.verified:
                user.verified = True
                user.verified_at = datetime.utcnow()
                user.discord_username = username
                self._log_action("user_verified", discord_id, details=f"Verified via Google Sheets row {row_number}")
                self.db.commit()
                return "verified"
            elif user.discord_username != username:
                user.discord_username = username
                self.db.commit()
                return "verified"
        else:
            user = User(
                guild_id=self.guild_id,
                discord_id=discord_id,
                discord_username=username,
                verified=True,
                verified_at=datetime.utcnow()
            )
            self.db.add(user)
            self._log_action("user_verified", discord_id, details=f"Verified via Google Sheets row {row_number} (new user)")
            self.db.commit()
            return "verified"
        
        self.db.commit()
        return "new"
    
    def _get_cell(self, row: List[Any], header: str) -> Optional[str]:
        idx = self._header_map.get(header)
        if idx is not None and idx < len(row):
            return str(row[idx]).strip() if row[idx] else None
        return None
    
    def _log_action(self, action: str, discord_id: int, staff_id: int = None, ticket_id: int = None, details: str = None):
        log = Log(
            guild_id=self.guild_id,
            action=action,
            discord_id=discord_id,
            staff_id=staff_id,
            ticket_id=ticket_id,
            details=details
        )
        self.db.add(log)
    
    def _log_error(self, error: str):
        self._log_action("verification_error", None, details=error)

async def process_sheet_for_guild(guild_id: int, guild=None) -> dict:
    from database import get_db
    db = next(get_db())
    try:
        service = GoogleSheetsService(db, guild_id, guild)
        return await service.sync_verifications()
    finally:
        db.close()


async def start_verification_sync(bot, interval: int = VERIFICATION_SYNC_INTERVAL):
    while True:
        try:
            for guild in bot.guilds:
                db = next(get_db())
                sheets_service = GoogleSheetsService(db, guild.id, guild)
                stats = await sheets_service.sync_verifications()
                print(f"Guild {guild.id} verification sync: {stats}")
        except Exception as e:
            print(f"Verification sync error: {e}")
        await asyncio.sleep(interval)