"""Assign the first staff profile to an existing Firebase Authentication user."""
import argparse,os
from datetime import datetime,timezone
from pathlib import Path
from dotenv import load_dotenv
BASE=Path(__file__).resolve().parent;load_dotenv(BASE/'.env')
parser=argparse.ArgumentParser();parser.add_argument('--email',required=True);args=parser.parse_args()
import firebase_admin
from firebase_admin import auth,credentials,firestore
credential=Path(os.environ['FIREBASE_CREDENTIALS'])
if not credential.is_absolute():credential=BASE/credential
app=firebase_admin.initialize_app(credentials.Certificate(str(credential)))
u=auth.get_user_by_email(args.email,app=app)
firestore.client(app).collection('pengguna').document(u.uid).set(dict(uid=u.uid,email=u.email,nama=u.display_name or 'Petugas Dinas',role='petugas',disabled=False,createdAt=datetime.now(timezone.utc)),merge=True)
print('Profil petugas pertama siap. Masuk menggunakan email dan password yang dibuat di Firebase Console.')
