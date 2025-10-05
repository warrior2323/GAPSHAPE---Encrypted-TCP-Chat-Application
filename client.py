
import socket
import threading
from cryptography.fernet import Fernet
import sys
import rsa
import datetime
import tkinter
from tkinter import scrolledtext , simpledialog



(public_key, private_key) =rsa.newkeys(2048)
public_key_pem = public_key.save_pkcs1().decode('utf-8')

PUBLIC_KEYS_CACHE={}#cache for other user's public keys
SESSION_KEYS={}#cache for symmetric session key

HEADER = 64
PORT = 5050
FORMAT='utf-8'
DISCONNECT_MESSAGE="/quit"
SERVER=socket.gethostbyname(socket.gethostname())
ADDR=(SERVER,PORT)

client=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
client.connect(ADDR)




def send(msg):
    message=msg.encode(FORMAT)
    msg_length=len(message)
    send_length = str(msg_length).encode(FORMAT)
    send_length+=b' '*(HEADER-len(send_length))
    client.send(send_length)
    client.send(message)

try:

    prompt = client.recv(2048).decode(FORMAT)
    print(prompt, end='') 
except socket.timeout:
    print("Error: Server did not send a prompt in time. Exiting.")
    client.close()
    exit()
except Exception as e:
    print(f"An error occurred while receiving prompt: {e}")
    client.close()
    exit()


username = input() 
send(username)
#immediately i will also send the public key.
send(public_key_pem)

def recieve():
    while True:
        try:
            msg_length = client.recv(HEADER).decode(FORMAT)
            if msg_length:

                msg_length = int(msg_length)
                msg = client.recv(msg_length).decode(FORMAT)

                now=datetime.datetime.now()
                time_stamp=now.strftime("%Y-%m-%d %H:%M")
            
                parts=msg.split(' ',2)
                command=parts[0]

                if command=="/key" and len(parts) == 3:
                    username,key_pem = parts[1] , parts[2]
                    PUBLIC_KEYS_CACHE[username] = rsa.PublicKey.load_pkcs1(key_pem.encode('utf-8'))
                    print(f"[{time_stamp}] [INFO] Recieved public key for {username} .")
            
                elif command == "/privatemsg" and len(parts)==3:
                    sender,content= parts[1],parts[2]
                    content_parts =content.split(' ',1)
                    msg_type,data= content_parts[0], content_parts[1]

                    if msg_type =="SESSION_KEY":
                        encrypted_session_key= bytes.fromhex(data)
                        session_key = rsa.decrypt(encrypted_session_key,private_key)
                        SESSION_KEYS[sender]= session_key
                        print(f"\n[{time_stamp}] [SECURE] Secure session established with {sender}.")
                    elif msg_type =="MESSAGE":
                        if sender in SESSION_KEYS:
                            f=Fernet(SESSION_KEYS[sender])
                            decrypted_msg = f.decrypt(bytes.fromhex(data)).decode(FORMAT)
                            print(f"\n[{time_stamp}] [private from {sender}]: {decrypted_msg}")
                        else:
                            print(f"\n[{time_stamp}] [ERROR] Recieved a private message from {sender} but no session key is established.")
                else:
                    print("\n"+f"[{time_stamp}]"+ msg)

        except (ConnectionResetError, ConnectionAbortedError):
            print("\n[ERROR] Disconnected from the server.")
            break
        except Exception as e:

            print(f"\n[RECEIVE ERROR] An error occurred: {e}")





recieve_thread=threading.Thread(target=recieve)
recieve_thread.start()


connected = True
while connected:

    msg = input("Enter Message (or /quit to disconnect): ")



    

    if msg == DISCONNECT_MESSAGE:
        send(msg)
        connected=False
        break 


    elif msg.startswith("/privatemsg"):
        parts = msg.split(' ', 2)
        if len(parts) == 3:
            recipient, message = parts[1], parts[2]
            now = datetime.datetime.now()
            time_stamp = now.strftime("%Y-%m-%d %H:%M")


            if recipient not in SESSION_KEYS:
                if recipient not in PUBLIC_KEYS_CACHE:
                    print(f"[{time_stamp}] [INFO] Public key for '{recipient}' not cached. Requesting from server...")
                    send(f"/getkey {recipient}")
                    print(f"[{time_stamp}] [INFO] Please wait a moment for the key to arrive, then try sending your message again.")
                    continue 


                recipient_public_key = PUBLIC_KEYS_CACHE[recipient]
                session_key = Fernet.generate_key()
                SESSION_KEYS[recipient] = session_key
                
                encrypted_session_key = rsa.encrypt(session_key, recipient_public_key)
                send(f"/privatemsg {recipient} SESSION_KEY {encrypted_session_key.hex()}")
                print(f"[{time_stamp}] [SECURE] Sent a secure session key to {recipient}.")

 
            f = Fernet(SESSION_KEYS[recipient])
            encrypted_message = f.encrypt(message.encode(FORMAT))
            send(f"/privatemsg {recipient} MESSAGE {encrypted_message.hex()}")
            print(f"[{time_stamp}] [SECURE] Private message sent to {recipient}.")
        else:
            print("[ERROR] Invalid /privatemsg format. Use: /privatemsg <recipient> <message>")

    else:
        send(msg)


client.close()
print("You have been disconnected.")

