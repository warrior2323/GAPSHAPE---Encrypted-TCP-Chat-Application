import tkinter
from tkinter import scrolledtext, simpledialog, messagebox
from client_logic import Client 
import socket

class ChatGUI:



    def __init__(self, master):
        self.master = master
        master.withdraw()

        self.splash_screen = tkinter.Toplevel()
        self.splash_screen.title("Loading....",)
        self.splash_screen.geometry("300x200")
        self.splash_screen.overrideredirect(True)        
        self.photo1=tkinter.PhotoImage(file="cpp/CGS DOUBT/Gemini_Generated_Image_krfeq7krfeq7krfe.png")
        Label=tkinter.Label(self.splash_screen,image=self.photo1)
        Label.pack()
        

        window_width = 500
        window_height = 500

        screen_width = self.splash_screen.winfo_screenwidth()
        screen_height = self.splash_screen.winfo_screenheight()

        center_x = int(screen_width/2 - window_width / 2)
        center_y = int(screen_height/2 - window_height / 2)

        self.splash_screen.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')

        self.splash_screen.after(2000,self.username_box)


    def username_box(self):
        self.splash_screen.destroy()


        self.username = simpledialog.askstring("Username", "Please enter your username", parent=self.master)
        if not self.username:
            self.master.destroy()
            return
        else:
            self.main_gui_built()   

    def main_gui_built(self):

        self.master.deiconify()
        self.master.title(f"GAPSHAPE - {self.username}")
        self.master.geometry("700x550")

        self.chat_area = scrolledtext.ScrolledText(self.master, wrap=tkinter.WORD, state='disabled', font=("Helvetica", 11))
        self.chat_area.pack(padx=10, pady=10, fill=tkinter.BOTH, expand=True)

        self.chat_area.tag_configure('my_message', justify='right', background="#D0E7BF", rmargin=10)
        self.chat_area.tag_configure('their_message', justify='left', background="#BBC1F1", lmargin1=5, lmargin2=5)
        self.chat_area.tag_configure('system', foreground='blue', justify='center', font=("Helvetica", 9, "italic"))
        self.chat_area.tag_configure('private', foreground='#343434', background='#FFFACD', lmargin1=5, lmargin2=5) # Yellow for private

        input_frame = tkinter.Frame(self.master)
        input_frame.pack(fill=tkinter.X, padx=10, pady=5)
        
        self.msg_entry = tkinter.Entry(input_frame, font=("Helvetica", 11))
        self.msg_entry.pack(side=tkinter.LEFT, fill=tkinter.X, expand=True)
        self.msg_entry.bind("<Return>", self.send_message_handler)
        
        send_button = tkinter.Button(input_frame, text="Send",command=self.send_message_handler)
        send_button.pack(side=tkinter.RIGHT)

        callbacks = {
            'on_message_received': self.display_message,
            'on_system_message': lambda msg: self.display_message(msg, tag='system'),
            'on_disconnected': self.show_disconnected_error,
        }
        self.logic = Client(callbacks)
        
        server_ip = socket.gethostbyname(socket.gethostname())
        if not self.logic.connect(server_ip, 5050, self.username):
            messagebox.showerror("Connection Failed", f"Could not connect to the server at {server_ip}:5050.")
            self.master.destroy()
        
        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)

    def send_message_handler(self, event=None):
        message = self.msg_entry.get()
        if not message:
            return
            
        self.msg_entry.delete(0, tkinter.END)

        if message.startswith('/privatemsg'):
             parts = message.split(' ', 2)
             if len(parts) == 3:
                 recipient, private_msg = parts[1], parts[2]
                 self.logic.send_private_message(recipient, private_msg)
                 self.display_message(f"[You to {recipient}]: {private_msg}", tag='private')
             else:
                 self.display_message("[SYSTEM] Invalid format. Use: /privatemsg <user> <message>", tag='system')
        elif message == "/quit":
            self.logic.disconnect()
        else:
            self.logic.send_public_message(message)
            self.display_message(f"[{self.username}]: {message}")
        
    def display_message(self, msg_text, tag=None):
        self.chat_area.config(state='normal')

        if tag is None:
            if msg_text.startswith(f"[{self.username}]"):
                tag = 'my_message'
            elif msg_text.startswith("[SERVER]"):
                tag='system'
            elif msg_text.startswith("[Private from") or msg_text.startswith("[You to"):
                 tag = 'private'
            else:
                tag = 'their_message'

        self.chat_area.insert(tkinter.END, f"{msg_text}\n", tag)
        self.chat_area.config(state='disabled')
        self.chat_area.yview(tkinter.END)

    def show_disconnected_error(self):
        if self.master.winfo_exists():
            messagebox.showinfo("Disconnected", "You have been disconnected from the server.")
            self.master.destroy()

    def on_closing(self):
        self.logic.disconnect()
        self.master.destroy()

if __name__ == "__main__":
    root = tkinter.Tk()
    app = ChatGUI(root)
    root.mainloop()#That line, if __name__ == "__main__":, is a standard and very important convention in Python. It's the designated starting point for a script.

#In simple terms, the code inside this if block will only run when you execute this file directly from the terminal (e.g., python gui.py). It will not run if this file is imported as a module into another Python script.