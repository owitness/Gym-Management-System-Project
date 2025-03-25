from flask_caching import Cache

cache = Cache(config={
    'CACHE_TYPE': 'redis',
    'CACHE_REDIS_URL': 'redis://localhost:6379/0',
    'CACHE_DEFAULT_TIMEOUT': 300  # 5 minutes default timeout
})

# Cache keys
MEMBERSHIP_CACHE_KEY = 'membership:{}'  # membership:user_id
CLASS_SCHEDULE_CACHE_KEY = 'classes:schedule'
USER_PROFILE_CACHE_KEY = 'user:{}'  # user:user_id 