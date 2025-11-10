from environs import Env

# environs kutubxonasidan foydalanish
env = Env()
env.read_env()

# .env fayl ichidan quyidagilarni o'qiymiz
BOT_TOKEN = env.str("BOT_TOKEN")  # Bot Token
ADMINS = list(map(int,env.list("ADMINS")))  # adminlar ro'yxati
CHANNEL_ID = env.str("MY_CHANNEL_ID")
CHANNEL_USERNAME = env.str("CHANNEL_USERNAME")
EXIT_CHANNEL_ID = env.str("EXIT_CHANNEL_ID")
