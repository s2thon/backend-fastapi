import os
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from dotenv import load_dotenv

# .env dosyasındaki değişkenleri yükle
load_dotenv()

# .env dosyasından güvenlik ayarlarını oku
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

# FastAPI'ye gelen isteklerde "Authorization: Bearer <token>" başlığını aramasını söyleyen standart araç
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class UserClaims:
    """Token'dan çıkarılan kullanıcı bilgilerini tutan basit bir veri sınıfı."""
    def __init__(self, user_id: str, roles: list[str]):
        self.user_id = user_id
        self.roles = roles

def get_current_user_claims(token: str = Depends(oauth2_scheme)) -> UserClaims:
    """
    Gelen JWT'yi çözer, doğrular ve içindeki kullanıcı kimliğini ('sub') ve rollerini ('roles') döndürür.
    Token geçersizse veya yoksa otomatik olarak 401 Unauthorized hatası fırlatır.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Token'ı gizli anahtar ve algoritma ile çöz
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Spring Boot genellikle kullanıcı kimliğini 'sub' (subject) claim'inde tutar.
        user_id = payload.get("sub")
        # Spring Security genellikle rolleri 'roles' veya 'authorities' claim'inde tutar.
        # Token'ınızda rol bilgisi varsa, bu şekilde alabilirsiniz.
        roles = payload.get("roles", [])

        if user_id is None:
            raise credentials_exception
            
        return UserClaims(user_id=str(user_id), roles=roles)
        
    except JWTError:
        raise credentials_exception