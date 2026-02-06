import sys
import os
sys.path.append(os.getcwd())

try:
    import app.main
    print("Import successful")
except Exception as e:
    import traceback
    traceback.print_exc()
