"""
ChessPair — USCF Swiss Tournament Pairing Software
Entry point: launches the GUI application.
"""
import sys
from app.gui import TournamentApp

if __name__ == "__main__":
    app = TournamentApp()
    app.mainloop()
