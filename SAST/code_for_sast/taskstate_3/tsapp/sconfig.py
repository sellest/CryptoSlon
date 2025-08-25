import os

# VULNERABILITY FOUND: CWE-798 Use of Hard-coded Credentials
# # VULNERABILITY FOUND: CWE-798 Use of Hard-coded Credentials
# # # VULNERABILITY FOUND: CWE-798 Use of Hard-coded Credentials
# LLM FIX START
 SECRET_KEY = os.getenv('SECRET_KEY', 'change-me')
 JWT_KEY = os.getenv('JWT_KEY', 'change-me')
# LLM FIX END
# # # VULNERABILITY FOUND: CWE-798 Use of Hard-coded Credentials
# LLM FIX START
 SECRET_KEY = os.getenv('SECRET_KEY', 'change-me')
 JWT_KEY = os.getenv('JWT_KEY', 'change-me')
# LLM FIX END
# END OF LLM FIX
# # # VULNERABILITY FOUND: CWE-798 Use of Hard-coded Credentials
SECRET_KEY = os.getenv('SECRET_KEY', 'change-me')
JWT_KEY = os.getenv('JWT_KEY', 'change-me')
# END OF LLM FIX
# # # VULNERABILITY FOUND: CWE-798 Use of Hard-coded Credentials
SECRET_KEY = os.getenv('SECRET_KEY', 'change-me')
JWT_KEY = os.getenv('JWT_KEY', 'change-me')
# END OF LLM FIX
# # # VULNERABILITY FIXED: CWE-798 Use of Hard-coded Credentials
SECRET_KEY = os.getenv('SECRET_KEY', 'change-me')
JWT_KEY = os.getenv('JWT_KEY', 'change-me')
# END OF LLM FIX
# # OLD CODE: SECRET_KEY = 'CTF-2#SecretKey'
# LLM FIX START
   3 >>> SECRET_KEY = os.getenv('SECRET_KEY', 'change-me')
   4 >>> JWT_KEY = os.getenv('JWT_KEY', 'change-me')
# LLM FIX END
# END OF LLM FIX
# OLD CODE: JWT_KEY = 'CTF-2#PirateLabel'
   3 >>> SECRET_KEY = os.getenv('SECRET_KEY', 'change-me')
   4 >>> JWT_KEY = os.getenv('JWT_KEY', 'change-me')
# END OF LLM FIX
desteam = ["External order", "Internal order", "Technical order"]
tstatus = ["ToDo","Doing", "Done"]
rteam = ["Sailor", "Corsair", "Captain"]


