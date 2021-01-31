from __future__ import print_function
import pickle
import os
import io

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload


class GoogleDrive:
    CREDENTIALS_PATH = os.getenv("CREDENTIALS_PATH" "credentials.json")

    def __init__(self):
        """Shows basic usage of the Drive v3 API.
           Prints the names and ids of the first 10 files the user has access to. """
        # If modifying these scopes, delete the file token.pickle.
        SCOPES = ['https://www.googleapis.com/auth/drive']

        creds = None
        # The file token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.CREDENTIALS_PATH, SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)

        self.service = build('drive', 'v3', credentials=creds)

    def upload_file(self, filename: str, path: str, folder_id: str):
        media = MediaFileUpload(f"{path}")
        response = self.service.files().list(
            q=f"name='{filename}' and parents='{folder_id}'",
            spaces='drive',
            fields='nextPageToken, files(id, name)',
            pageToken=None).execute()
        if len(response['files']) == 0:
            file_metadata = {
                'name': filename,
                'parents': [folder_id]
            }
            file = self.service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        else:
            for file in response.get('files', []):
                # Process change
                update_file = self.service.files().update(
                    fileId=file.get('id'),
                    media_body=media,
                ).execute()

    def get_list_files_ids_in_folder(self, folder_id: str) -> list:
        page_token = None
        while True:
            response = self.service.files().list(q=f"'{folder_id}' in parents and trashed=false",
                                                 spaces='drive',
                                                 fields='nextPageToken, files(id, name, size, webContentLink)',
                                                 pageToken=page_token).execute()
            page_token = response.get('nextPageToken', None)
            if page_token is None:
                break
        files = response.get('files', [])
        files.sort(key=lambda file: file['name'], reverse=True)
        return files

    def download_file(self, file_id: str, path: str):
        request = self.service.files().get_media(fileId=file_id)
        fh = io.FileIO(path, mode='wb')
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            # progress
