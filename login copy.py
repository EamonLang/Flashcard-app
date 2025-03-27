import customtkinter as ctk
import subprocess
import sqlite3
import _tkinter

class SQLmanager:

    def __init__(self):
        self.connector = sqlite3.connect("database.db")
        self.cursor = self.connector.cursor()
    

    def add_user(self,name,password):
        self.cursor.execute("INSERT INTO flashcard_users(name,password) VALUES(?,?)",(name,password))
        self.connector.commit()
    
    def check_user(self,name,password):
        self.cursor.execute("SELECT * FROM flashcard_users WHERE name = ? and password = ?",(name,password))
        results = self.cursor.fetchone()
        if results:
            
            self.connector.close()
            window.destroy()
            subprocess.call(["python","DB_flashcard.py",name])


class App:

    def __init__(self,window):
        self.window = window


        self.window.geometry("1000x800")
        self.window.title("Flashcard Login")

        self.container = ctk.CTkFrame(self.window)
        self.container.pack(fill="both",expand = True)
        self.container.grid_rowconfigure(0,weight=1)
        self.container.grid_columnconfigure(0,weight=1)

        self.manager = SQLmanager()

        self.frames = {}
        for F in (Homepage, Createpage):
            frame = F(self.container, self, self.manager) 
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")
            
        self.show_frame(Homepage)
    def show_frame(self,page):
        self.frames[page].tkraise()
    def close_app(self):
        self.window.destroy()
        self.manager.connector.close()
    def failure_button(self,page):
        if hasattr(self, 'window') and self.window is not None:
            try:
                if self.window.winfo_exists():  
                    button = ctk.CTkButton(page, text="Invalid username or password\nPress again to create a user",text_color="red",command=lambda: self.show_frame(Createpage),fg_color="black",hover_color="grey")
                    button.place(x=425, y=475)
            except _tkinter.TclError:
                pass

class Homepage(ctk.CTkFrame):
    def __init__(self,parent,controller,manager):
        super().__init__(parent)
        self.controller = controller
        self.manager = manager

        title = ctk.CTkLabel(self,text="Welcome to Flashcard",font=("Arial",50))
        title.pack(pady=10)
        subheading = ctk.CTkLabel(self,text="Sign in to begin",font=("Arial",25))
        subheading.pack()

        username = ctk.CTkEntry(self,width=200)
        username.insert(0,"Username:")
        username.place(x=425,y=300)

        password = ctk.CTkEntry(self,width=200)
        password.insert(0,"Password:")
        password.place(x=425,y=375)

        enter = ctk.CTkButton(self, text="Enter", width=200, command=lambda: [manager.check_user(username.get()[9:], password.get()[9:]),controller.failure_button(self)])
        enter.place(x=425,y=425)


class Createpage(ctk.CTkFrame):
    def __init__(self,parent,controller,manager):
        super().__init__(parent)
        self.controller = controller
        self.manager = manager

        header = ctk.CTkLabel(self,text="To create a new account enter a username and password",font=("Arial",30))
        header.pack(pady=10)

        Username = ctk.CTkEntry(self)
        Username.insert(0,"Username:")
        Username.pack(pady=10)

        password = ctk.CTkEntry(self)
        password.insert(0,"Password:")
        password.pack(pady=10)

        enter = ctk.CTkButton(self,text="Enter",command = lambda:[manager.add_user(Username.get()[9:],password.get()[9:]),controller.show_frame(Homepage)])
        enter.pack(pady=10)


if __name__ == "__main__":
    window = ctk.CTk()
    app = App(window)
    window.mainloop()
