import socket
import threading
import rsa
import datetime
import json

#storing the data into a json file;

JSON_FILE='messglog.json'
JSON_LOCK=threading .Lock()

def read_json_file():
    
    try:
        with open(JSON_FILE,'r') as fobj:
            data=json.load(fobj)
    except(FileNotFoundError,json.JSONDecodeError):
        data={"connections_joined": [] , "messages": [],"room_details": [] ,"connections_left": []}
    return data

def write_json_file(data):
     with open(JSON_FILE,'w') as fobj: 
        json.dump(data,fobj,indent=4) 

def store_message(msg,username,conn):
    with JSON_LOCK:
        data=read_json_file()
        now=datetime.datetime.now()
        time_stamp=now.strftime("%Y-%m-%d %H:%M")
        room=CLIENT_ROOMS[conn]
        add={
        'timestamp' : time_stamp,
        'message' : msg,
        'room' : room,
        'username' : username,

 }

        data['messages'].append(add)
        write_json_file(data)


def store_connections_joined(username,id):
    with JSON_LOCK:
        data=read_json_file()
        now=datetime.datetime.now()
        time_stamp=now.strftime("%Y-%m-%d %H:%M")

        add={
        'timestamp' : time_stamp,
        'username' : username,
        
        'STATUS' : 'joined'
    }
        data['connections_joined'].append(add)
        write_json_file(data)

def store_connections_left(username,id):
    with JSON_LOCK:
        data=read_json_file()
        now=datetime.datetime.now()
        time_stamp=now.strftime("%Y-%m-%d %H:%M")

        add={
        'timestamp' : time_stamp,
        'username' : username,
        
        'STATUS' : 'disconnected'
    }
        data['connections_left'].append(add)
        write_json_file(data)

def prev_msg(conn):
    with JSON_LOCK:
        data=read_json_file()
    with USER_LOCK:
        room=CLIENT_ROOMS[conn]
    n=len(data["messages"])
    recentmsg=[]
    count=0
    for i in range(n):
        if data["messages"][n-i-1]['room']==room:
            recentmsg.append(data["messages"][n-i-1])
            count+=1
            if count==10:
                break
    for message_data in reversed(recentmsg):
        timestamp = message_data['timestamp']
        msgg = message_data['message']
        username = message_data['username']
        room=message_data['room']
        send_message(f"[{timestamp}] [{room}] [{username}] - {msgg}",conn)

HEADER=64
PORT = 5050

"""we can also write server = "  26.42.66.110" by this will be a hard code and if some one access it on another
 device it will use the same set ip address"""

SERVER = socket.gethostbyname(socket.gethostname())
ADDR=(SERVER,PORT)
FORMAT='utf-8'
DISCONNECT_MESSAGE="/quit"
ACTIVE_CONNECTIONS_MESSAGE="/list"
CLIENT_CONNECTIONS={}    #making a global list of all the connected users
CLIENTS={}
CHAT_ROOMS={"common":[]}
CLIENT_ROOMS={}
USER_LOCK = threading.Lock()# added this because my list will get corrupted if two users leave or enter at the same time




server = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
server.bind(ADDR)



    

def send_message(msg,conn):
    message=msg.encode(FORMAT)
    msg_length=len(message)
    send_length = str(msg_length).encode(FORMAT)
    send_length+=b' '*(HEADER-len(send_length))
    conn.send(send_length)
    conn.send(message)





def active(conn):
    message1=f"[SERVER] : The total number of active connections on the server are : {len(CLIENT_CONNECTIONS)}"
    message2="[SERVER] These are the active users : "
    with USER_LOCK:
        send_message(message1,conn)
        send_message(message2,conn)
        for value in CLIENT_CONNECTIONS.values():
            send_message(value,conn)


def knowrooms(conn):
    send_message("[SERVER] These are the rooms where you can find interested people in, Right now!",conn)
    for i in CHAT_ROOMS:
        send_message(i,conn)

def broadcast(msg,conn,client_tag,time_stamp):
    full_msg=f"[{time_stamp} {client_tag} : {msg}]"
    room=CLIENT_ROOMS[conn]
    with USER_LOCK:
        for i in CHAT_ROOMS[room]:
            if i!=conn:
                send_message(full_msg,i)
        

def handle_join_room(conn,room,client_tag):
    print(f'{client_tag} has joined {room} room')
    send_message(f"[SERVER] You have entered {room} room , Enjoy talking with similar interested people",conn)
    with USER_LOCK:
        if room in CHAT_ROOMS:
            for i in CHAT_ROOMS[room]:
                if i!=conn:
                    send_message(f"[SERVER] {client_tag} has joined the {room} room",i)

        else:
                
            CHAT_ROOMS[room]=[]

        previous_room=CLIENT_ROOMS[conn]
        CHAT_ROOMS[previous_room].remove(conn)
        for i in CHAT_ROOMS[previous_room]:
            send_message(f"[SERVER] {client_tag} left the room {previous_room}.",i)
        CLIENT_ROOMS[conn]=room
        CHAT_ROOMS[room].append(conn)
    prev_msg(conn)

def private_message(reciever_username,senders_username,msg,senders_conn):
    recv_conn=None
    with USER_LOCK:
        
        for conn,user_tag in CLIENT_CONNECTIONS.items():
            if user_tag==reciever_username:
                recv_conn=conn
                break
        if recv_conn==None:
            send_message(f"[SERVER] {reciever_username} is not online . PLs try after they come online! ",senders_conn)
            return 
        if CLIENTS[recv_conn]['status']!='DO NOT DISTURB':
            send_message(f"/privatemsg {senders_username} {msg}",recv_conn)
        else:
            send_message(f"[SERVER] {reciever_username} is set to 'Do Not Disturb' and may not see your message.",senders_conn)

def handle_client(conn, addr):
    print(f"[NEW CONNECTION] {addr} connected")

    flag=True
    while flag:
    
        prompt_message = "Enter your username and press Enter: ".encode(FORMAT)
        conn.send(prompt_message)

        try:
            msg_length = conn.recv(HEADER).decode(FORMAT)
            if not msg_length:
                conn.close()
                return
        
            msg_length = int(msg_length)
            username = conn.recv(msg_length).decode(FORMAT)
            count=0
            with USER_LOCK:
                if username in CLIENT_CONNECTIONS.values():
                    count=1
                    
            if count==0:
                public_key_length=conn.recv(HEADER).decode(FORMAT)
                if not public_key_length:
                    conn.close()
                    return 
                public_key_pem=conn.recv(int(public_key_length)).decode(FORMAT)

                print(f"[IDENTITY] {addr} identified as {username}")
                now=datetime.datetime.now()
                time_stamp =now.strftime("%Y-%m-%d %H:%M")
                client_tag = username
                store_connections_joined(client_tag,conn)
                with USER_LOCK: 
                    CLIENT_CONNECTIONS[conn]=client_tag
                    CLIENTS[conn]={'username':username, 'public_key':public_key_pem,'status':'ONLINE'}#initially status is set to online 
                    CLIENT_ROOMS[conn]="common"
                    CHAT_ROOMS['common'].append(conn)
                flag=False  
                broadcast(f"{client_tag} joined the chat !!!",conn,client_tag,time_stamp)     
            else:
                mesg="This username is already occupied , try joining with another username"
                send_message(mesg,conn)



                
        


        
        except Exception as e:
            print(f"[ERROR] Could not get username from {addr}: {e}")
            conn.close()
            return


    connected = True
    welcome_message = f"[SERVER] Welcome to the server {client_tag} "
    send_message(welcome_message,conn)
    User_manual=f'''[SERVER] following are the features of this server:  \n     /list--> TO see all the clients on the server. [SYNTAX- /list] \n     /knowrooms-->To know the rooms in which people are currently \n     /privatemsg--> to send the msg to a particluar client. [SYNTAX- /privatemsg <recievers_username> <message>]. \n     /manual-->get manual [SYNTAX- /manual] \n     /join-->to join a room of your interest.[SYNTAX- /join <room>]. \n     /status--> To apply a status from ["ONLINE","AWAY","DO NOT DISTURB","BUSY"] [SYNTAX- /status <stat_us>] \n     /quit-->disconnect [SYNTAX- /quit]     ''' 
    send_message(User_manual,conn)
    prev_msg(conn)
    while connected:

        try:
            msg_length = conn.recv(HEADER).decode(FORMAT)
            if msg_length:
                msg_length = int(msg_length)
                msg = conn.recv(msg_length).decode(FORMAT)
                now=datetime.datetime.now()
                time_stamp =now.strftime("%Y-%m-%d %H:%M")
                


                if msg.startswith('/privatemsg'):
                    parts=msg.split(' ',2) #2 are the maximum number of maxsplits()
                    if len(parts)<3:
                        send_message("[SERVER] INVALID ATTEMPT TO SEND PRIVATE MESSAGE",conn)
                    
                    else:
                        privat_message=parts[2]
                        reciever_username=parts[1]

                        private_message(reciever_username,client_tag,privat_message,conn)

                elif msg == DISCONNECT_MESSAGE:
                    connected = False
                    msg1="[SERVER] Thankyou ! for visiting the SERVER "
                    msg2="[SERVER] Visit again, This server is always open for you "
                    send_message(msg1,conn)
                    send_message(msg2,conn)
                    broadcast(f"{client_tag} disconnected from the server!",conn,client_tag,time_stamp)
                    store_connections_left(client_tag,conn)
                    with USER_LOCK:
                        
                        del CLIENT_CONNECTIONS[conn]
                        del CLIENTS[conn]
                        room=CLIENT_ROOMS[conn]
                        del CLIENT_ROOMS[conn]
                        CHAT_ROOMS[room].remove(conn)


                elif msg.startswith("/knowrooms"):
                    knowrooms(conn)
                elif msg.startswith("/manual"):
                    send_message(User_manual,conn)

                elif msg.startswith("/join"):
                    parts=msg.split()
                    if len(parts)==2:
                        handle_join_room(conn,parts[1],client_tag)

                    


                elif msg.startswith("/status"):
                    parts=msg.split(' ',1)
                    VALID_STATUS=["ONLINE","AWAY","DO NOT DISTURB","BUSY"]
                    
                    if len(parts)==2 and parts[1] in VALID_STATUS:
                        new_status=parts[1]
                        with USER_LOCK:
                            CLIENTS[conn]['status']=new_status
                        status_msg=f"[SERVER] your status has been updated to {new_status}"
                        send_message(status_msg,conn)
                        notification=f"{client_tag} is now {new_status}"
                        broadcast(notification,conn,client_tag,time_stamp)
                        
                    else:
                        error_msg="[SERVER] Incorrect use of /status. type /status <status> where status can be [ONLINE,AWAY,DO NOT DISTURB] to update your status."
                        send_message(error_msg,conn)

                elif msg.startswith('/getkey'):
                    parts=msg.split(' ',1)
                    target_user=parts[1]
                    target_conn=0
                    with USER_LOCK:
                        for conn_ in CLIENT_CONNECTIONS:
                            if CLIENT_CONNECTIONS[conn_]==target_user:
                                target_conn=conn_
                                break
                    if target_conn!=0:
                        key_to_send=CLIENTS[target_conn]['public_key']
                        send_message(f"/key {target_user} {key_to_send}",conn)
                    else:
                        send_message(f"[SERVER] [ERROR] Not able to find '{target_user}' on the server. Hope he joins soon. ",conn)

                elif msg.startswith("/list"):
                    active(conn)
                                   
                else:
                    broadcast(msg,conn,client_tag,time_stamp)
                    store_message(msg,client_tag,conn)


                    


                print(f"[{time_stamp} {client_tag}] : {msg}")

                if msg == ACTIVE_CONNECTIONS_MESSAGE:
                    active(conn)
                
            else:

                connected = False
        
        except ConnectionResetError:
            connected = False 
            broadcast(f"{client_tag} disconnected from the server!",conn,client_tag,time_stamp)
            store_connections_left(client_tag,conn)
            with USER_LOCK:
                del CLIENT_CONNECTIONS[conn]
                del CLIENTS[conn]
                room=CLIENT_ROOMS[conn]
                del CLIENT_ROOMS[conn]
                CHAT_ROOMS[room].remove(conn)



            
        except Exception as e:
            print(f"[ERROR] Communication error with {client_tag}: {e}")
            connected = False


    print(f"[{time_stamp} {client_tag}] Disconnected.")
    conn.close()


def start():
    server.listen()
    print(f"[LISTENING] server is listening on {SERVER}")
    while True:
        conn,addr=server.accept()   #conn is an object here to handle the client
        thread=threading.Thread(target= handle_client,args=(conn,addr))
        thread.start()
        print(f"[ACTIVE CONNECTIONS] -->   {threading.active_count()-1}")



        
print("[STARTING] Server is going to Start ! ")
start()
