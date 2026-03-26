#!/usr/bin/env python3
"""
台本ファイルをGoogle Driveにアップロードするスクリプト

使い方:
  python3 upload_to_drive.py <output_dir> [--folder-name <フォルダ名>]

例:
  python3 upload_to_drive.py output/マインドセット講座
  python3 upload_to_drive.py output/マインドセット講座 --folder-name "台本/マインドセット講座"
"""

import os
import sys
import json
import argparse
from pathlib import Path
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# ファイルパス設定
SCRIPT_DIR = Path(__file__).parent
TOKEN_PATH = SCRIPT_DIR / "drive_token.json"
SCOPES = ["https://www.googleapis.com/auth/drive.file"]


def get_credentials():
    """認証情報を取得・更新する"""
    token_data = json.loads(TOKEN_PATH.read_text())

    creds = Credentials(
        token=token_data.get("token"),
        refresh_token=token_data.get("refresh_token"),
        token_uri=token_data.get("token_uri"),
        client_id=token_data.get("client_id"),
        client_secret=token_data.get("client_secret"),
        scopes=SCOPES,
    )

    # トークンが期限切れの場合はリフレッシュ
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        token_data["token"] = creds.token
        TOKEN_PATH.write_text(json.dumps(token_data, indent=2))

    return creds


def get_or_create_folder(service, folder_name, parent_id=None):
    """Google Drive上のフォルダを取得または作成する"""
    query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    if parent_id:
        query += f" and '{parent_id}' in parents"

    results = service.files().list(q=query, fields="files(id, name)").execute()
    files = results.get("files", [])

    if files:
        return files[0]["id"]

    # フォルダを新規作成
    metadata = {
        "name": folder_name,
        "mimeType": "application/vnd.google-apps.folder",
    }
    if parent_id:
        metadata["parents"] = [parent_id]

    folder = service.files().create(body=metadata, fields="id").execute()
    print(f"  フォルダを作成しました: {folder_name}")
    return folder["id"]


def upload_file(service, file_path, folder_id):
    """ファイルをGoogle Driveにアップロードし、Googleドキュメントに変換する"""
    file_path = Path(file_path)
    # 拡張子を除いたファイル名をドキュメント名にする
    doc_name = file_path.stem
    media = MediaFileUpload(str(file_path), mimetype="text/plain")
    metadata = {
        "name": doc_name,
        "mimeType": "application/vnd.google-apps.document",
        "parents": [folder_id],
    }

    # 既存ファイルの確認
    query = f"name='{doc_name}' and '{folder_id}' in parents and trashed=false and mimeType='application/vnd.google-apps.document'"
    results = service.files().list(q=query, fields="files(id, name)").execute()
    existing = results.get("files", [])

    if existing:
        # 上書き更新
        file = service.files().update(
            fileId=existing[0]["id"],
            media_body=media,
        ).execute()
        print(f"  更新: {doc_name}")
    else:
        # 新規アップロード（Googleドキュメントに変換）
        file = service.files().create(
            body=metadata,
            media_body=media,
            fields="id",
        ).execute()
        print(f"  アップロード: {doc_name}")

    return file["id"]


def main():
    parser = argparse.ArgumentParser(description="台本をGoogle Driveにアップロード")
    parser.add_argument("output_dir", help="アップロードするディレクトリ（例: output/マインドセット講座）")
    parser.add_argument("--folder-name", help="Google Drive上のフォルダ名（省略時はディレクトリ名を使用）")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    if not output_dir.exists():
        print(f"エラー: ディレクトリが見つかりません: {output_dir}")
        sys.exit(1)

    md_files = sorted(output_dir.glob("*.md"))
    if not md_files:
        print(f"エラー: .mdファイルが見つかりません: {output_dir}")
        sys.exit(1)

    folder_name = args.folder_name or output_dir.name
    print(f"Google Driveにアップロード中...")
    print(f"  フォルダ: {folder_name}")
    print(f"  ファイル数: {len(md_files)}本")

    creds = get_credentials()
    service = build("drive", "v3", credentials=creds)

    folder_id = get_or_create_folder(service, folder_name)

    for file_path in md_files:
        upload_file(service, str(file_path), folder_id)

    print(f"\n完了！Google Driveの「{folder_name}」フォルダに保存されました。")


if __name__ == "__main__":
    main()
