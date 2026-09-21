#!/usr/bin/env python3
import os
import subprocess
import threading
import customtkinter as ctk
from tkinter import filedialog, messagebox

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class ADBManagerLinux(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Gerenciador ADB - Linux")
        self.geometry("600x520")
        self.resizable(False, False)

        self.selected_apk = ""
        self.selected_file = ""

        self.create_widgets()
        self.check_device()

    def create_widgets(self):
        # Header / Status do Dispositivo
        self.header_frame = ctk.CTkFrame(self)
        self.header_frame.pack(fill="x", padx=20, pady=15)

        self.lbl_status = ctk.CTkLabel(
            self.header_frame, 
            text="Status: Verificando dispositivo...", 
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.lbl_status.pack(side="left", padx=15, pady=10)

        self.btn_refresh = ctk.CTkButton(
            self.header_frame, 
            text="Atualizar", 
            width=100, 
            command=self.check_device
        )
        self.btn_refresh.pack(side="right", padx=15, pady=10)

        # Tabview para organizar as funções
        self.tabview = ctk.CTkTabview(self, width=560, height=360)
        self.tabview.pack(padx=20, pady=10)

        self.tab_apk = self.tabview.add("Instalar APK")
        self.tab_push = self.tabview.add("Enviar Arquivo")

        self.setup_apk_tab()
        self.setup_push_tab()

        # Barra de Status Geral
        self.lbl_log = ctk.CTkLabel(self, text="Aguardando ação...", font=ctk.CTkFont(size=12))
        self.lbl_log.pack(pady=10)

    # --- ABA 1: INSTALAR APK ---
    def setup_apk_tab(self):
        lbl_title = ctk.CTkLabel(
            self.tab_apk, 
            text="Selecione um aplicativo (.apk) para instalar", 
            font=ctk.CTkFont(size=13)
        )
        lbl_title.pack(pady=15)

        self.btn_select_apk = ctk.CTkButton(
            self.tab_apk, 
            text="Escolher Arquivo APK", 
            command=self.select_apk
        )
        self.btn_select_apk.pack(pady=10)

        self.lbl_apk_path = ctk.CTkLabel(
            self.tab_apk, 
            text="Nenhum arquivo selecionado", 
            text_color="gray"
        )
        self.lbl_apk_path.pack(pady=5)

        self.chk_reinstall = ctk.CTkCheckBox(self.tab_apk, text="Substituir se já existir (-r)")
        self.chk_reinstall.pack(pady=15)
        self.chk_reinstall.select()

        self.btn_install = ctk.CTkButton(
            self.tab_apk, 
            text="Instalar APK", 
            fg_color="#2b8a3e", 
            hover_color="#237032", 
            command=self.start_install_thread
        )
        self.btn_install.pack(pady=15)

    # --- ABA 2: ENVIAR ARQUIVOS ---
    def setup_push_tab(self):
        lbl_title = ctk.CTkLabel(
            self.tab_push, 
            text="Enviar arquivo para o armazenamento interno do celular", 
            font=ctk.CTkFont(size=13)
        )
        lbl_title.pack(pady=10)

        self.btn_select_file = ctk.CTkButton(
            self.tab_push, 
            text="Escolher Arquivo", 
            command=self.select_file
        )
        self.btn_select_file.pack(pady=10)

        self.lbl_file_path = ctk.CTkLabel(
            self.tab_push, 
            text="Nenhum arquivo selecionado", 
            text_color="gray"
        )
        self.lbl_file_path.pack(pady=5)

        lbl_dest = ctk.CTkLabel(self.tab_push, text="Pasta de destino no Android:")
        lbl_dest.pack(pady=(10, 2))

        self.entry_dest = ctk.CTkEntry(self.tab_push, width=350)
        self.entry_dest.insert(0, "/sdcard/Download/")
        self.entry_dest.pack(pady=5)

        self.btn_push = ctk.CTkButton(
            self.tab_push, 
            text="Enviar Arquivo", 
            fg_color="#2b8a3e", 
            hover_color="#237032", 
            command=self.start_push_thread
        )
        self.btn_push.pack(pady=20)

    # --- EXECUÇÃO ADB EM LINUX ---
    def run_adb_command(self, args):
        """Executa o comando ADB de forma nativa no Linux."""
        try:
            result = subprocess.run(
                ["adb"] + args,
                capture_output=True,
                text=True
            )
            return result.stdout.strip(), result.stderr.strip()
        except FileNotFoundError:
            return "", "Erro: O comando 'adb' não está instalado ou não foi encontrado no PATH."

    def check_device(self):
        stdout, stderr = self.run_adb_command(["devices"])
        
        if "não foi encontrado" in stderr:
            self.lbl_status.configure(text="Status: ADB não instalado", text_color="red")
            return False

        lines = [line for line in stdout.split('\n') if line.strip()]

        if len(lines) > 1:
            device_info = lines[1].split()
            if len(device_info) >= 2 and device_info[1] == "device":
                self.lbl_status.configure(text=f"Dispositivo: {device_info[0]}", text_color="#2b8a3e")
                return True
            elif device_info[1] == "unauthorized":
                self.lbl_status.configure(text="Status: Aceite a depuração no celular", text_color="orange")
                return False

        self.lbl_status.configure(text="Status: Nenhum celular detectado", text_color="red")
        return False

    def select_apk(self):
        path = filedialog.askopenfilename(filetypes=[("Arquivos APK", "*.apk")])
        if path:
            self.selected_apk = path
            self.lbl_apk_path.configure(text=os.path.basename(path), text_color="white")

    def select_file(self):
        path = filedialog.askopenfilename()
        if path:
            self.selected_file = path
            self.lbl_file_path.configure(text=os.path.basename(path), text_color="white")

    def start_install_thread(self):
        threading.Thread(target=self.install_apk, daemon=True).start()

    def install_apk(self):
        if not self.check_device():
            messagebox.showwarning("Aviso", "Conecte um dispositivo Android via USB.")
            return

        if not self.selected_apk:
            messagebox.showwarning("Aviso", "Selecione um arquivo APK primeiro.")
            return

        self.lbl_log.configure(text="Instalando APK... Aguarde.")
        self.btn_install.configure(state="disabled")

        cmd = ["install"]
        if self.chk_reinstall.get():
            cmd.append("-r")
        cmd.append(self.selected_apk)

        stdout, stderr = self.run_adb_command(cmd)

        if "Success" in stdout or "Success" in stderr:
            self.lbl_log.configure(text="APK instalado com sucesso!")
            messagebox.showinfo("Sucesso", "O aplicativo foi instalado com sucesso!")
        else:
            self.lbl_log.configure(text="Falha na instalação.")
            messagebox.showerror("Erro", f"Erro ao instalar o APK:\n{stderr or stdout}")

        self.btn_install.configure(state="normal")

    def start_push_thread(self):
        threading.Thread(target=self.push_file, daemon=True).start()

    def push_file(self):
        if not self.check_device():
            messagebox.showwarning("Aviso", "Conecte um dispositivo Android via USB.")
            return

        if not self.selected_file:
            messagebox.showwarning("Aviso", "Selecione um arquivo para enviar.")
            return

        dest = self.entry_dest.get().strip()
        if not dest:
            messagebox.showwarning("Aviso", "Informe a pasta de destino no dispositivo.")
            return

        self.lbl_log.configure(text="Enviando arquivo... Aguarde.")
        self.btn_push.configure(state="disabled")

        stdout, stderr = self.run_adb_command(["push", self.selected_file, dest])

        if "pushed" in stdout or "pushed" in stderr or not stderr:
            self.lbl_log.configure(text="Arquivo enviado com sucesso!")
            messagebox.showinfo("Sucesso", f"Arquivo enviado para:\n{dest}")
        else:
            self.lbl_log.configure(text="Falha ao enviar arquivo.")
            messagebox.showerror("Erro", f"Erro ao enviar arquivo:\n{stderr or stdout}")

        self.btn_push.configure(state="normal")

if __name__ == "__main__":
    app = ADBManagerLinux()
    app.mainloop()
