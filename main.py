import os

if os.path.exists("downloads"):
    for f in os.listdir("downloads"):
        try:
            os.remove(os.path.join("downloads", f))
        except:
            pass
from bot import TrackRemoverBot

if __name__ == "__main__":
    app = TrackRemoverBot()
    app.run()
