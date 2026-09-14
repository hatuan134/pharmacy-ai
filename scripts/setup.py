"""Run from any directory. Generate local secrets without overwriting existing files."""
from pathlib import Path
import secrets
root=Path(__file__).resolve().parents[1]
def create(path, content):
    if path.exists(): print(f'Giữ nguyên: {path.relative_to(root)}')
    else:
        path.write_text(content,encoding='utf-8')
        print(f'Đã tạo: {path.relative_to(root)}')
create(root/'.env',f'POSTGRES_USER=pharmacy\nPOSTGRES_PASSWORD={secrets.token_urlsafe(24)}\nPOSTGRES_DB=pharmacy\n')
values=dict(line.split('=',1) for line in (root/'.env').read_text().splitlines() if '=' in line and not line.startswith('#'))
from urllib.parse import quote_plus
password=quote_plus(values['POSTGRES_PASSWORD'])
username=quote_plus(values.get('POSTGRES_USER','pharmacy'))
database=quote_plus(values.get('POSTGRES_DB','pharmacy'))
create(root/'backend'/'.env',f'DATABASE_URL=postgresql+psycopg://{username}:{password}@localhost:5432/{database}\nSECRET_KEY={secrets.token_urlsafe(48)}\nGEMINI_API_KEY=\nGEMINI_MODEL=gemini-3.8-flash\nCORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173\nCOOKIE_SECURE=false\n')
print('Tiếp theo: docker compose up -d db. Xem README.md để chạy backend/frontend.')
