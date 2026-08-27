DEBUG = True
TESTING = False

SERVER = "dev"
DB_HOST = "mongodb://localhost:27017"
DB_NAME = "glydb"
DB_USERNAME = "xxx"
DB_PASSWORD = "xxx"
DATA_PATH = "/Volumes/disk2/data/shared/glygen"
LOG_PATH = "/Volumes/disk2/data/shared/glygen/logs"
MAX_CONTENT_LENGTH = 16 * 1000 * 1000

TOTP_INTERVAL = 3600

MAIL_SERVER = "xxx"
MAIL_PORT = 25
MAIL_USE_TLS = False
MAIL_USE_SSL = False
MAIL_SENDER = "xxx"
MAIL_USERNAME = None
MAIL_PASSWORD = None



SECRET_KEY = "xxxx"
JWT_SECRET_KEY = "xxxx"
SESSION_COOKIE_SECURE = True
JWT_TOKEN_LOCATION = ['cookies']
JWT_COOKIE_SECURE = False
JWT_ACCESS_COOKIE_PATH = '/'
JWT_REFRESH_COOKIE_PATH = '/'
JWT_COOKIE_CSRF_PROTECT = True
JWT_CSRF_IN_COOKIES = False


#using rykahsay's token now, please chenge to glygener github token
GITHUB_TOKEN = "xxx"
GITHUB_ASSIGNEE = "xxxxxx"
AISEARCH_TOKEN = "xxx"
    



