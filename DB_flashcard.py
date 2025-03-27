import customtkinter as ctk
import sys
import sqlite3
import openai
import os


if len(sys.argv)>1:
    username = sys.argv[1]
else:
    username = "eamon"


class User:
    def __init__(self):
        self.name = username
        self.sql = SQLmanager()
        self.score = self.load_score()
    def load_score(self):
        self.sql.cursor.execute("SELECT user_score FROM flashcard_users WHERE name = ?",(username,))
        score = self.sql.cursor.fetchone()
        if score:
            score = score[0]
            self.score = score
        else:
            print("error with loading score")
    def __str__(self):
        return f"Name: {self.name} ID: {self.score}"


class SQLmanager:
    def __init__(self):
        self.connector = sqlite3.connect("database.db")
        self.cursor = self.connector.cursor()

        self.user_info = self.load_user(username)

    def load_user(self,name):
        self.cursor.execute("SELECT * FROM flashcard_users WHERE name = ?", (name,))
        user_data = self.cursor.fetchone()
        return user_data
    
    def get_sets(self):
        self.cursor.execute("SELECT * FROM flashcard_sets WHERE user_id = ?", (self.user_info[0],))
        sets = self.cursor.fetchall()
        return sets
    
    def add_set(self,title):
        self.cursor.execute("INSERT INTO flashcard_sets(user_id,set_name) VALUES(?,?)",(self.user_info[0],title))
        self.connector.commit()
    
    def add_flashcard(self,title,question,answer):
        self.cursor.execute("SELECT id FROM flashcard_sets WHERE set_name = ?",(title,))
        identity = self.cursor.fetchone()
        if identity:
            #takes identity out of tuple and just implements the int of the key for flashcard_set
            identity = identity[0]
            self.cursor.execute("INSERT INTO flashcards(set_id,question,answer) VALUES (?,?,?)",(identity,question,answer))
            self.connector.commit()
        else:
            print("error")
    
    def load_past_convo(self):
        self.cursor.execute("SELECT user,assistant FROM chat_bot WHERE user_id = ?",(self.user_info[0],))
        conversations = self.cursor.fetchall()
        if conversations:
            return conversations
        else:
            print("No previous conversations")
            pass

    def save_convo(self,user,assistant):
        self.cursor.execute("INSERT INTO chat_bot(user_id,user,assistant) VALUES (?,?,?)",(self.user_info[0],user,assistant))
        self.connector.commit()

    def get_flashcard(self,title):
        self.cursor.execute("SELECT id FROM flashcard_sets WHERE set_name = ?",(title,))
        set = self.cursor.fetchone()
        if set:
            set = set[0]
            self.cursor.execute("SELECT question,answer FROM flashcards WHERE set_id = ?",(set,))
            flashcards = self.cursor.fetchall()
        else:
            print("error with get_flashcard")
        return flashcards
    def update_score(self):
        self.cursor.execute("SELECT user_score FROM flashcard_users WHERE name = ?",(username,))
        score = self.cursor.fetchone()
        if score:
            # returns tuple then converts it into the integer so it can then be incremented
            score = score[0]
            score +=1
            self.cursor.execute("UPDATE flashcard_users SET user_score = ? WHERE name = ?",(score,username))
            self.connector.commit()
        else:
            print("error with updating score")
        return score
    def update_card(self):
        self.cursor.execute("SELECT from flashcards where")
    




class Flashcardmanager:

    def __init__(self):
        self.sql = SQLmanager()
        self.title = []
        self.set_list = []
        self.index = 0
        self.id_card_dic = {}

        self.users_past_conversations=[]
        self.current_conversations = []

    #loads title for all sites
    def load_sets(self):
        sets = self.sql.get_sets()
        if sets:
            name = []
            for x in sets:
                name.append(x[1:3])
            return name       
        else:
            return "No sets"
    
    def create_set(self,title):
        self.title.append(title)
        self.sql.add_set(title)
    
    def add_pair(self,question,answer):
        if len(self.title)>0:
            self.sql.add_flashcard(self.title[0],question,answer)
        else:
            print("Enter title first")

    #loads individual set
    def load_set(self,title):
        questions = self.sql.get_flashcard(title)

        #loads set from data base and then appends individual parts of each tuple into the list. Otherwise the tuple of question and answer would be added
        for x in questions:
            self.set_list.append(x[0])
            self.set_list.append(x[1])

    
    def practice_output(self):
        if self.index<len(self.set_list):
            return self.set_list[self.index]
        elif self.index == len(self.set_list):
            self.sql.update_score()
            return "You have reached the end of the set press again to keep practicing"
        else:
            self.index = 0
            return self.set_list[self.index]
    def increase_index(self):
        self.index += 1 
    
    def AI_init(self):
        conversations = self.sql.load_past_convo()
        if conversations:
            for chat in conversations:
                self.users_past_conversations.append({"role":"user","content":chat[0]})
                self.users_past_conversations.append({"role":"assistant","content":chat[0]})


                

        
        
    def AI_update(self,text,textbox):
        openai.api_key = os.getenv("OPENAI_API_KEY")
        textbox.configure(state="normal")
        textbox.insert("end",f"\n{text}\n\n")
        textbox.insert("end",f"\nPiensamiento...\n")
        messages = [
            {"role":"system","content":"You are a fluent Spanish speaker designed to assist learners in practicing Spanish. Your primary objective is to respond in Spanish whenever possible, reserving English primarily for providing feedback if the user specifically requests it. Allow the user to guide the direction of the conversation and only use attached information if the user is talking about something relating to it. Otherwise just respond to user."}
        ]
        if len(self.users_past_conversations)<5:
            messages.extend(self.users_past_conversations)
        else:
            messages.extend(self.users_past_conversations[-5:])
        messages.extend(self.current_conversations)
        message = text
        user_message = {"role":"user","content":message}

        

        response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=messages
        )

        chat_message = response['choices'][0]['message']['content']
        self.current_conversations.append({"role": "assistant", "content": chat_message})
        self.current_conversations.append(user_message)

        

        textbox.insert("end",f"\n\n{chat_message}\n\n")
        textbox.configure(state="disabled")
        self.sql.save_convo(message,chat_message)

        


    #resets the flashcard manager class so that when a user is done practicing and whats to practice a new set there isnt a clash of loaded sets
    def clear(self):
        self.title.clear()
        self.set_list.clear()
        self.index = 0
        self.users_past_conversations.clear()
        self.current_conversations.clear()

class App:
    
    def __init__(self,window):
        self.window=window
        self.window.title("Flashcard")
        self.window.geometry("1000x800")

        self.container = ctk.CTkFrame(self.window)
        self.container.pack(fill="both",expand = True)
        self.container.grid_rowconfigure(0,weight=1)
        self.container.grid_columnconfigure(0,weight=1)

        self.manager = Flashcardmanager()
        self.sql = SQLmanager()
        self.user = User()
        self.frames= {}

        #pass class of flashcard and user aswell as its own functions (show_frame) to other pages so that they can be used there keeping one state for all instances
        for F in (Homepage, Createpage, Practicepage, delPage,Setpage,modPage,AIPage):

            frame = F(self.container, self, self.manager,self.user) 

            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")
            
        self.show_frame(Homepage)
    #switch frame function. Takes the argument of page and then checks the dictionary to see which frame it is then it raises that frame to the top.
    def show_frame(self,page):
        frame = self.frames[page]
        #if the frame is homepage runs the update_text() function on the homepage.
        if isinstance(frame, Homepage):
            frame.update_text()
        self.frames[page].tkraise()
    def close_app(self):
        self.window.destroy()
        self.sql.connector.close()
    
class Homepage(ctk.CTkFrame):

    def __init__(self,parent,controller,manager,user):
        super().__init__(parent)
        self.controller = controller
        self.manager = manager
        self.user = user
        welcome_label = ctk.CTkLabel(self,text="Welcome to flashcard",font=("Arial",50),height=100,width=200)
        welcome_label.pack()

        self.score_label = ctk.CTkLabel(self,text=f"Your score is: {user.score}")
        self.score_label.place(x=50,y=50)

        create_button = ctk.CTkButton(self,text="Create a new set",command=lambda:controller.show_frame(Createpage),font=("Arial",16),width=100,height=50)
        create_button.pack(pady=25)

        practice_button=ctk.CTkButton(self,text="Practice old sets",command=lambda:controller.show_frame(Practicepage),font=("Arial",16),width=60,height=50)
        practice_button.pack(pady=25)

        del_button = ctk.CTkButton(self,text="Modify old sets",command=lambda:controller.show_frame(delPage),font=("Arial",16),width=60,height=50)
        del_button.pack(pady=25)

        close_button = ctk.CTkButton(self,text="Exit app",font=("Arial",20),width=125,height=50,command=lambda: controller.close_app())
        close_button.pack(pady=25)

        view_sets_label = ctk.CTkLabel(self,text="Your sets: ",width=200,height=20,font=("Arial",30))
        view_sets_label.place(x=120,y=110)

        self.view_made_sets = ctk.CTkTextbox(self,width=200,height=200)
        self.view_made_sets.insert("1.0",manager.load_sets())
        self.view_made_sets.configure(state="disabled")
        self.view_made_sets.place(x=150,y=150)

        chat_bot_button = ctk.CTkButton(self,text="Press to practice with an AI",height=20,command=lambda:[controller.show_frame(AIPage),manager.AI_init()])
        chat_bot_button.place(x=150,y=450)

        #updates the text in self.view_made_sets so that when a user makes a new set they dont have to reset it to see the option
    def update_text(self):
        self.view_made_sets.configure(state="normal")
        self.view_made_sets.delete("1.0","end")
        self.view_made_sets.insert("1.0",self.manager.load_sets())
        self.view_made_sets.configure(state="disabled")
        self.user.load_score()
        self.score_label.configure(text=f"Your score is: {self.user.score}")

class Createpage(ctk.CTkFrame):
    def __init__(self,parent,controller,manager,user):
        super().__init__(parent)
        self.controller = controller
        self.manager = manager
        self.user=user
        welcome_create = ctk.CTkLabel(self,text="Start Creating a Set by Entering the Title of it!")
        welcome_create.pack()
        

        new_set_title = ctk.CTkEntry(self)
        new_set_title.pack()

        enter_title = ctk.CTkButton(self,text="Enter",command=lambda:[manager.create_set(new_set_title.get()),new_set_title.delete(0,"end")])
        enter_title.pack()

        word_label = ctk.CTkLabel(self,text="Enter word below")
        word_label.place(x=100,y=325)

        word = ctk.CTkEntry(self,width=200,height=50)
        word.place(x=100,y=350)

        def_label = ctk.CTkLabel(self,text="Enter the response below")
        def_label.place(x=700,y=325)

        definition = ctk.CTkEntry(self,width=200,height=50)
        definition.place(x=700,y=350)

        #gets the words and then deletes the text from the text box so its ready for the next pair
        enter = ctk.CTkButton(self,text="Enter",font=("Arial",40),command=lambda:[manager.add_pair(word.get(),definition.get()),word.delete(0,"end"),definition.delete(0,"end")])
        enter.place(x=425,y=450)

        returnButton = ctk.CTkButton(self,text="Return home",command=lambda:[controller.show_frame(Homepage),manager.clear()])
        returnButton.place(x=750,y=750)

class Practicepage(ctk.CTkFrame):
    def __init__(self,parent,controller,manager,user):
        super().__init__(parent)
        self.controller = controller
        self.manager = manager
        self.user =user
        set_textbox=ctk.CTkTextbox(self,width=200,height=200)
        set_textbox.insert("1.0",manager.load_sets())
        set_textbox.configure(state="disabled")
        set_textbox.pack()

        choice_label = ctk.CTkLabel(self,text="Enter the name of the set you want to practice. Double check spelling!")
        choice_label.pack()

        user_entry = ctk.CTkEntry(self)
        user_entry.pack()

        #gets the choice of practice and then loads the set while also switching to the set page
        get_button = ctk.CTkButton(self,text="Enter",command=lambda:[manager.load_set(user_entry.get()),controller.show_frame(Setpage),user_entry.delete(0,"end"),controller.frames[Setpage].load_text()])
        get_button.pack()

        returnButton = ctk.CTkButton(self,text="Return home",command=lambda:[controller.show_frame(Homepage),manager.clear()])
        returnButton.place(x=750,y=750)

class delPage(ctk.CTkFrame):
    def __init__(self,parent,controller,manager,user):
        super().__init__(parent)
        self.controller = controller
        self.manager = manager
        self.user = user

        #text box with users sets
        set_textbox = ctk.CTkTextbox(self,width=200,height = 200)
        set_textbox.insert("1.0",manager.load_sets())
        set_textbox.configure(state="disabled")
        set_textbox.pack(pady=30)

        choice = ctk.CTkEntry(self)
        choice.pack()

        enter = ctk.CTkButton(self,text="enter",command=lambda:[manager.load_set(choice.get()),choice.delete(0,"end"),controller.show_frame(modPage),controller.frames[modPage].update_text()])
        enter.pack(pady=20)

class modPage(ctk.CTkFrame):
    def __init__(self,parent,controller,manager,user):
        super().__init__(parent)
        self.controller = controller
        self.manager = manager
        self.user = user

        self.set_textbox = ctk.CTkTextbox(self,width=400,height=400)
        self.set_textbox.configure(state="disabled")
        self.set_textbox.pack(pady=60)

        self.choice_label = ctk.CTkLabel(self,text="Enter the number of the card you want to edit")
        self.choice_label.pack()

        self.choice = ctk.CTkEntry(self)
        self.choice.pack()

        self.enter = ctk.CTkButton(self,text="Enter",command=lambda:[self.change_textbox(self.choice.get()),self.choice.delete(0,"end")])
        self.enter.pack()

    def update_text(self):
        if self.manager.set_list:

            self.set_textbox.configure(state="normal")
            self.set_textbox.insert("1.0",["".join(f"{index}-{val}\n" for index,val in enumerate(self.manager.set_list))])
            self.set_textbox.configure(state = "disabled")
    
    def change_textbox(self,num):
        #IN WORK
        try:
            num = int(num)
        except ValueError:
            print("bad input")
        for index,val in enumerate(self.manager.set_list):
            if num == index:
                self.choice_label.pack_forget()
                self.enter.pack_forget()
                self.set_textbox.configure(state="normal")
                self.set_textbox.delete("1.0","end")
                self.set_textbox.insert("1.0",val)


class Setpage(ctk.CTkFrame):
    def __init__(self,parent,controller,manager,user):
        super().__init__(parent)
        self.controller = controller
        self.manager = manager
        self.user =user

        self.card = ctk.CTkButton(self,width=700,height=500,text=" ",command=lambda:[manager.increase_index(),self.load_text()])
        self.card.pack(pady=100)
    
        

        returnButton = ctk.CTkButton(self,text="Return home",command=lambda:[controller.show_frame(Homepage),manager.clear()])
        returnButton.place(x=750,y=750)
    #checks to see if there is words and since the only way to get to this page is if their is a succesful practice page choice then this will automatically load the set the user chose
    def load_text(self):
        if self.manager.set_list:
            self.card.configure(text=self.manager.practice_output())    

class AIPage(ctk.CTkFrame):
    def __init__(self,parent,controller,manager,user):
        super().__init__(parent)
        self.controller = controller
        self.manager = manager
        self.user =user

        self.chat_box = ctk.CTkTextbox(self,height=400,width=400)
        self.chat_box.insert("1.0","Begin chatting to practice\n")
        self.chat_box.configure(state="disabled")
        self.chat_box.pack(pady=30)


        label = ctk.CTkLabel(self,text="Type in the box below and hit enter to chat!")
        label.pack(pady=10)

        query= ctk.CTkEntry(self,width=400,height=40)
        query.pack()
        
        enter = ctk.CTkButton(self,text="Enter",command=lambda:[manager.AI_update(query.get(),self.chat_box),query.delete(0,"end")])
        enter.pack(pady=10)

        home = ctk.CTkButton(self,text="Return Home",command=lambda:[controller.show_frame(Homepage),manager.clear()])
        home.place(x=750,y=750)


    def update_text(self):
        pass


if __name__ == "__main__":
    window = ctk.CTk()
    app = App(window)
    window.mainloop()
