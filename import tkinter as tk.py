import tkinter as tk
from tkinter import messagebox

class TicTacToe:
    def __init__(self, root):
        self.root = root
        self.root.title("Tic-Tac-Toe")
        
        # Initialize game variables
        self.current_player = "X"
        self.board = [""] * 9  # 3x3 board initialized as empty
        
        # Create buttons for the game grid
        self.buttons = [tk.Button(root, text="", font=('normal', 40), width=5, height=2, 
                                  command=lambda i=i: self.on_button_click(i)) 
                        for i in range(9)]
        
        # Arrange buttons on the grid (3x3)
        for i, button in enumerate(self.buttons):
            row = i // 3
            col = i % 3
            button.grid(row=row, column=col)
        
    def on_button_click(self, i):
        if self.board[i] == "" and not self.check_winner():
            self.board[i] = self.current_player
            self.buttons[i].config(text=self.current_player)
            if self.check_winner():
                messagebox.showinfo("Game Over", f"Player {self.current_player} wins!")
                self.reset_game()
            else:
                self.current_player = "O" if self.current_player == "X" else "X"

    def check_winner(self):
        # Check all winning combinations
        winning_combinations = [
            (0, 1, 2), (3, 4, 5), (6, 7, 8),  # Horizontal
            (0, 3, 6), (1, 4, 7), (2, 5, 8),  # Vertical
            (0, 4, 8), (2, 4, 6)               # Diagonal
        ]
        
        for (a, b, c) in winning_combinations:
            if self.board[a] == self.board[b] == self.board[c] != "":
                return True
        # Check if the board is full (Draw)
        if "" not in self.board:
            messagebox.showinfo("Game Over", "It's a Draw!")
            self.reset_game()
            return False
        return False

    def reset_game(self):
        # Reset the game state
        self.board = [""] * 9
        for button in self.buttons:
            button.config(text="")
        self.current_player = "X"


if __name__ == "__main__":
    root = tk.Tk()
    game = TicTacToe(root)
    root.mainloop()