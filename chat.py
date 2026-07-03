import socket
import json
import threading
import sys
import argparse

def receive_messages(sock, my_name):
    while True:
        try:
            data = sock.recv(4096)
            if not data:
                print("\n[System] Połączenie zamknięte przez rozmówcę.")
                break
            
            #decode JSON payload
            payload = json.loads(data.decode('utf-8'))
            sender = payload.get("sender", "Nieznany")
            message = payload.get("message", "")
            
            if message == "/exit":
                print(f"\n[System] Użytkownik {sender} opuścił czat.")
                break
            
            #print
            print(f"\n[{sender}]: {message}")
            print(f"[{my_name}]: ", end="", flush=True)
        except Exception:
            break
    
    print("\n[System] Transmisja zakończona. Naciśnij Enter, aby wyjść.")
    sock.close()
    sys.exit(0)

def main():
    parser = argparse.ArgumentParser(description="chat P2P w Pythonie")
    parser.add_argument("--name", required=True, help="Twoja nazwa użytkownika")
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--listen", type=int, help="Port nasłuchiwania hosta")
    group.add_argument("--connect", help="Adres IP:PORT drugiego hosta (gościa)")
    
    args = parser.parse_args()
    my_name = args.name
    sock = None
    
    if args.listen:
        #host mode
        server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        # listen on all interfaces
        server_sock.bind(('0.0.0.0', args.listen))
        server_sock.listen(1)
        print(f"[System] Oczekiwanie na połączenie na porcie {args.listen}...")
        
        sock, addr = server_sock.accept()
        print(f"[System] Nawiązano połączenie z adresem: {addr[0]}:{addr[1]}")
        server_sock.close() # close the listening socket as we only accept one connection
        
    elif args.connect:
        #guest mode
        try:
            ip, port = args.connect.split(":")
            port = int(port)
        except ValueError:
            print("[Błąd] Niepoprawny format parametru --connect. Użyj IP:PORT (np. 192.168.1.50:5000)")
            sys.exit(1)
            
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print(f"[System] Łączenie z {ip}:{port}...")
        try:
            sock.connect((ip, port))
            print("[System] Połączenie nawiązane pomyślnie!")
        except Exception as e:
            print(f"[Błąd] Nie udało się połączyć: {e}")
            sys.exit(1)

    # async receive thread
    recv_thread = threading.Thread(target=receive_messages, args=(sock, my_name), daemon=True)
    recv_thread.start()
    
    # main loop for sending messages
    print(f"[System] Czat aktywny. Napisz wiadomość i wciśnij Enter. Wpisz '/exit' aby wyjść.")
    try:
        while True:
            msg = input(f"[{my_name}]: ")
            if not msg.strip():
                continue
            
            # json payload with sender and message
            payload = {
                "sender": my_name,
                "message": msg
            }
            
            # serialize to JSON and send
            sock.sendall(json.dumps(payload).encode('utf-8'))
            
            if msg == "/exit":
                print("[System] Zamykanie aplikacji...")
                break
    except (KeyboardInterrupt, EOFError):
        # ctrl+c interrupt or ctrl+d EOF
        try:
            sock.sendall(json.dumps({"sender": my_name, "message": "/exit"}).encode('utf-8'))
        except:
            pass
        print("\n[System] Przerwano działanie aplikacji sygnałem systemowym.")
    
    sock.close()
    print("[System] Do widzenia!")

if __name__ == "__main__":
    main()