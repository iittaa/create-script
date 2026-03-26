#!/usr/bin/env python3
"""
Google Drive書き込み権限の初回認証スクリプト
初回のみ実行してください。
"""

import json
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow

SCRIPT_DIR = Path(__file__).parent
OAUTH_KEYS_PATH = Path("/Users/kosukeitamoto/.nvm/versions/node/v24.14.1/lib/node_modules/gcp-oauth.keys.json")
TOKEN_PATH = SCRIPT_DIR / "drive_token.json"

SCOPES = ["https://www.googleapis.com/auth/drive.file"]

def main():
    flow = InstalledAppFlow.from_client_secrets_file(str(OAUTH_KEYS_PATH), SCOPES)
    creds = flow.run_local_server(port=0)

    token_data = {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": list(creds.scopes),
    }
    TOKEN_PATH.write_text(json.dumps(token_data, indent=2))
    print(f"認証成功！トークンを保存しました: {TOKEN_PATH}")

if __name__ == "__main__":
    main()
