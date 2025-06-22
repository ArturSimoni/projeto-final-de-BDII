import tkinter as tk
from tkinter import ttk, messagebox
import requests
import threading
from datetime import datetime
import queue 

# URLs para o backend Flask
BASE_ALUNOS_URL = "http://localhost:5000/api/v1/alunos/" # Com a barra final!
BASE_AUTH_URL = "http://localhost:5000/api/v1/auth/"

class LoginWindow(tk.Toplevel):
    def __init__(self, parent, on_login_success):
        super().__init__(parent)
        self.parent = parent
        self.on_login_success = on_login_success # Callback para quando o login for bem-sucedido
        self.title("Login de Administrador")
        self.geometry("350x200")
        self.resizable(False, False)
        self.grab_set() # Torna esta janela modal
        self.transient(parent) # Faz a janela desaparecer com a parent

        self.username_var = tk.StringVar()
        self.password_var = tk.StringVar()

        self._setup_ui()

    def _setup_ui(self):
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(expand=True, fill=tk.BOTH)

        ttk.Label(main_frame, text="Utilizador:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.username_entry = ttk.Entry(main_frame, textvariable=self.username_var, width=30)
        self.username_entry.grid(row=0, column=1, pady=5)
        self.username_entry.focus_set()

        ttk.Label(main_frame, text="Senha:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.password_entry = ttk.Entry(main_frame, textvariable=self.password_var, show="*", width=30)
        self.password_entry.grid(row=1, column=1, pady=5)

        login_button = ttk.Button(main_frame, text="Login", command=self._perform_login)
        login_button.grid(row=2, column=0, columnspan=2, pady=15)
        
        # Permite login com Enter
        self.bind('<Return>', lambda event=None: self._perform_login())

    def _perform_login(self):
        username = self.username_var.get()
        password = self.password_var.get()

        if not username or not password:
            messagebox.showwarning("Erro de Login", "Por favor, preencha todos os campos.")
            return

        # Executa a requisição de login em uma thread separada para não travar a UI
        threading.Thread(target=self._send_login_request, args=(username, password), daemon=True).start()

    def _send_login_request(self, username, password):
        try:
            response = requests.post(
                f"{BASE_AUTH_URL}login",
                json={"username": username, "password": password},
                timeout=5
            )
            data = response.json()

            if response.status_code == 200:
                token = data.get("token")
                role = data.get("role")
                self.parent.after(0, lambda: self._login_success(token, role)) # Chama na thread principal
            else:
                message = data.get("message", "Erro desconhecido de login.")
                self.parent.after(0, lambda: messagebox.showerror("Erro de Login", message))
        except requests.exceptions.RequestException as e:
            self.parent.after(0, lambda: messagebox.showerror("Erro de Conexão", f"Não foi possível conectar ao servidor de autenticação: {e}"))
        except ValueError: # Para o caso de resposta não ser um JSON válido
            self.parent.after(0, lambda: messagebox.showerror("Erro de Resposta", "Resposta inválida do servidor de autenticação."))

    def _login_success(self, token, role):
        self.on_login_success(token, role) # Chama o callback na AlunoApp
        self.destroy() # Fecha a janela de login

class AlunoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Gerenciador de Alunos - v2.0")
        self.root.geometry("900x650")
        self.root.minsize(800, 600)
        
        self.auth_token = None # Armazenará o token de autenticação
        self.user_role = None  # Armazenará a função do utilizador (ex: 'admin', 'user')

        self.status_var = tk.StringVar()
        self.status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(fill=tk.X, pady=(5, 0)) 
        
        self.configure_styles()

        # Inicia com a tela de login
        self._show_login_window()
        
    def _show_login_window(self):
        """Exibe a janela de login."""
        LoginWindow(self.root, self._handle_login_success)

    def _handle_login_success(self, token, role):
        """Callback chamado após um login bem-sucedido."""
        self.auth_token = token
        self.user_role = role
        self.update_status(f"Login bem-sucedido! Função: {role}")
        self.setup_ui() # Configura a UI principal após o login
        self.atualizar_tabela() # Atualiza a tabela de alunos

    def configure_styles(self):
        style = ttk.Style()
        style.configure('TButton', padding=5, font=('Arial', 10))
        style.configure('Header.TLabel', font=('Arial', 12, 'bold'))
        style.configure('TLabel', font=('Arial', 10)) 
        style.configure('Error.TLabel', foreground='red', font=('Arial', 10, 'bold')) 
        
    def setup_ui(self):
        """Configura a interface do usuário (UI) após o login."""
        self.status_bar.pack_forget() 

        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Form frame
        form_frame = ttk.LabelFrame(main_frame, text="Dados do Aluno", padding=10)
        form_frame.pack(fill=tk.X, pady=(0, 10))
        
        fields = [
            ("ID", "entry_id", 10),
            ("Nome", "entry_nome", 40),
            ("Matrícula", "entry_matricula", 20),
            ("Curso", "entry_curso", 30),
            ("Email", "entry_email", 30)
        ]
        
        for i, (label_text, attr_name, width) in enumerate(fields):
            ttk.Label(form_frame, text=label_text).grid(row=i, column=0, sticky=tk.W, pady=2)
            
            if attr_name == "entry_id":
                entry = ttk.Entry(form_frame, width=width, state='readonly') 
            else:
                entry = ttk.Entry(form_frame, width=width)
            
            entry.grid(row=i, column=1, padx=5, pady=2, sticky=tk.W)
            setattr(self, attr_name, entry) 
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        buttons_config = [
            ("Cadastrar", self.cadastrar, ['admin']), # Apenas admin
            ("Buscar", self.buscar, ['admin', 'user']), # Admin e user
            ("Editar", self.editar, ['admin']), # Apenas admin
            ("Excluir", self.excluir, ['admin']), # Apenas admin
            ("Limpar", self.limpar_campos, ['admin', 'user']),
            ("Atualizar", self.atualizar_tabela, ['admin', 'user']),
            ("Logout", self._perform_logout, ['admin', 'user']) # Adicionado botão de logout
        ]
        
        for text, command, required_roles in buttons_config:
            button_state = 'normal' if self.user_role in required_roles else 'disabled'
            ttk.Button(button_frame, text=text, command=command, state=button_state).pack(side=tk.LEFT, padx=2)
        
        self.status_bar.pack(in_=main_frame, fill=tk.X, pady=(5, 0)) 
        
        # Table frame
        table_frame = ttk.Frame(main_frame)
        table_frame.pack(fill=tk.BOTH, expand=True)
        
        colunas = ("ID", "Nome", "Matrícula", "Curso", "Email")
        self.tabela = ttk.Treeview(
            table_frame, 
            columns=colunas, 
            show="headings", 
            selectmode="browse"
        )
        
        for col in colunas:
            self.tabela.heading(col, text=col)
            self.tabela.column(col, anchor=tk.W, width=120, stretch=True)
        
        y_scroll = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tabela.yview)
        x_scroll = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=self.tabela.xview)
        self.tabela.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)
        
        self.tabela.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll.grid(row=1, column=0, sticky="ew")
        
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        
        self.tabela.bind('<ButtonRelease-1>', self.selecionar_aluno)

    def _run_on_main_thread(self, func, *args, **kwargs):
        self.root.after(0, lambda: func(*args, **kwargs))

    def update_status(self, message, error=False):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.status_var.set(f"[{timestamp}] {message}")
        self.status_bar.configure(style='Error.TLabel' if error else 'TLabel')
        
    def _get_headers(self):
        """Retorna os cabeçalhos com o token de autenticação."""
        if self.auth_token:
            return {"Authorization": f"Bearer {self.auth_token}", "Content-Type": "application/json"}
        return {"Content-Type": "application/json"}
    
    def _perform_logout(self):
        """Realiza o logout do utilizador."""
        def thread_logout():
            try:
                response = requests.post(f"{BASE_AUTH_URL}logout", headers=self._get_headers())
                data = response.json()
                if response.status_code == 200:
                    self._run_on_main_thread(messagebox.showinfo, "Logout", "Sessão encerrada com sucesso.")
                    self._run_on_main_thread(self._reset_app_state)
                else:
                    self._run_on_main_thread(messagebox.showerror, "Erro de Logout", data.get("message", "Erro ao encerrar sessão."))
            except requests.exceptions.RequestException as e:
                self._run_on_main_thread(messagebox.showerror, "Erro de Conexão", f"Não foi possível conectar ao servidor: {e}")
            except ValueError:
                self._run_on_main_thread(messagebox.showerror, "Erro de Resposta", "Resposta inválida do servidor.")
        
        threading.Thread(target=thread_logout, daemon=True).start()

    def _reset_app_state(self):
        """Reinicia o estado da aplicação para a tela de login."""
        self.auth_token = None
        self.user_role = None
        # Limpa todos os widgets existentes no root e re-exibe a janela de login
        for widget in self.root.winfo_children():
            widget.destroy()
        self.status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(fill=tk.X, pady=(5, 0)) 
        self.update_status("Sessão encerrada. Por favor, faça login.")
        self._show_login_window()

    def limpar_campos(self):
        self.entry_id.config(state='normal') 
        self.entry_id.delete(0, tk.END)
        self.entry_id.config(state='readonly') 

        self.entry_nome.delete(0, tk.END)
        self.entry_matricula.delete(0, tk.END)
        self.entry_curso.delete(0, tk.END)
        self.entry_email.delete(0, tk.END)
        self.update_status("Campos limpos")
        
    def atualizar_tabela(self):
        def thread_atualizar_alunos():
            try:
                self._run_on_main_thread(self.update_status, "Atualizando lista de alunos...")
                response = requests.get(BASE_ALUNOS_URL, headers=self._get_headers()) # Envia o token
                data = response.json() 

                if response.status_code == 200:
                    alunos = data.get('alunos', [])
                    self._run_on_main_thread(self.tabela.delete, *self.tabela.get_children())
                    for aluno in alunos:
                        self._run_on_main_thread(
                            self.tabela.insert, 
                            "", "end", 
                            values=(
                                aluno.get("id"),
                                aluno.get("nome"),
                                aluno.get("matricula"),
                                aluno.get("curso"),
                                aluno.get("email")
                            )
                        )
                    self._run_on_main_thread(self.update_status, f"Lista atualizada - {len(alunos)} alunos encontrados")
                else:
                    error_msg = data.get('mensagem', f'Erro desconhecido ao buscar alunos (Status: {response.status_code})')
                    self._run_on_main_thread(self.update_status, f"Erro: {error_msg}", error=True)
                    self._run_on_main_thread(messagebox.showerror, "Erro", error_msg)
                    
            except requests.exceptions.RequestException as e:
                error_msg = f"Não foi possível conectar ao servidor: {str(e)}"
                if isinstance(e, requests.exceptions.ConnectionError):
                    error_msg = "Servidor indisponível. Verifique se o servidor Flask está rodando."
                self._run_on_main_thread(self.update_status, error_msg, error=True)
                self._run_on_main_thread(messagebox.showerror, "Erro", error_msg)
            except ValueError: 
                error_msg = "Resposta inválida do servidor (não é JSON válido)."
                self._run_on_main_thread(self.update_status, error_msg, error=True)
                self._run_on_main_thread(messagebox.showerror, "Erro", error_msg)
        
        threading.Thread(target=thread_atualizar_alunos, daemon=True).start()
        
    def cadastrar(self):
        def thread_cadastrar_aluno():
            if not self.auth_token:
                self._run_on_main_thread(messagebox.showerror, "Não Autenticado", "Faça login para cadastrar alunos.")
                return

            dados = {
                "nome": self.entry_nome.get().strip(),
                "matricula": self.entry_matricula.get().strip(),
                "curso": self.entry_curso.get().strip(),
                "email": self.entry_email.get().strip().lower()
            }
            
            if not all(dados.values()):
                self._run_on_main_thread(self.update_status, "Todos os campos devem ser preenchidos!", error=True)
                self._run_on_main_thread(messagebox.showwarning, "Aviso", "Todos os campos devem ser preenchidos!")
                return
            
            if '@' not in dados['email']:
                self._run_on_main_thread(self.update_status, "Email inválido!", error=True)
                self._run_on_main_thread(messagebox.showwarning, "Aviso", "Por favor, insira um email válido")
                return
            
            if not dados['matricula'].isdigit():
                self._run_on_main_thread(self.update_status, "Matrícula deve conter apenas números!", error=True)
                self._run_on_main_thread(messagebox.showwarning, "Aviso", "A matrícula deve conter apenas números.")
                return

            try:
                self._run_on_main_thread(self.update_status, "Cadastrando aluno...")
                response = requests.post(BASE_ALUNOS_URL, json=dados, headers=self._get_headers()) # Envia o token
                data = response.json()
                
                if response.status_code == 201:
                    aluno_id = data.get('id')
                    self._run_on_main_thread(messagebox.showinfo, "Sucesso", f"Aluno cadastrado com sucesso! ID: {aluno_id}")
                    self._run_on_main_thread(self.limpar_campos)
                    self._run_on_main_thread(self.atualizar_tabela)
                    self._run_on_main_thread(self.update_status, f"Aluno ID {aluno_id} cadastrado com sucesso")
                else:
                    error_msg = data.get('mensagem', f'Erro ao cadastrar aluno (Status: {response.status_code})')
                    self._run_on_main_thread(self.update_status, f"Erro: {error_msg}", error=True)
                    self._run_on_main_thread(messagebox.showerror, "Erro", error_msg)
                    
            except requests.exceptions.RequestException as e:
                error_msg = f"Erro de conexão: {str(e)}"
                self._run_on_main_thread(self.update_status, error_msg, error=True)
                self._run_on_main_thread(messagebox.showerror, "Erro", error_msg)
            except ValueError: 
                error_msg = "Resposta inválida do servidor (não é JSON válido)."
                self._run_on_main_thread(self.update_status, error_msg, error=True)
                self._run_on_main_thread(messagebox.showerror, "Erro", error_msg)
                
        threading.Thread(target=thread_cadastrar_aluno, daemon=True).start()
        
    def buscar(self):
        def thread_buscar_aluno():
            if not self.auth_token:
                self._run_on_main_thread(messagebox.showerror, "Não Autenticado", "Faça login para buscar alunos.")
                return

            aluno_id = self.entry_id.get().strip()
            if not aluno_id or not aluno_id.isdigit():
                self._run_on_main_thread(self.update_status, "Informe um ID válido para buscar", error=True)
                self._run_on_main_thread(messagebox.showwarning, "Atenção", "Informe um ID válido para buscar.")
                return
                
            try:
                self._run_on_main_thread(self.update_status, f"Buscando aluno ID {aluno_id}...")
                response = requests.get(f"{BASE_ALUNOS_URL}{aluno_id}", headers=self._get_headers()) # Envia o token
                data = response.json() 
                
                if response.status_code == 200:
                    aluno = data.get('aluno', {})
                    self._run_on_main_thread(self.limpar_campos) 
                    
                    self._run_on_main_thread(self.entry_id.config, state='normal')
                    self._run_on_main_thread(self.entry_id.insert, 0, aluno.get('id', ''))
                    self._run_on_main_thread(self.entry_id.config, state='readonly')

                    self._run_on_main_thread(self.entry_nome.insert, 0, aluno.get('nome', ''))
                    self._run_on_main_thread(self.entry_matricula.insert, 0, aluno.get('matricula', ''))
                    self._run_on_main_thread(self.entry_curso.insert, 0, aluno.get('curso', ''))
                    self._run_on_main_thread(self.entry_email.insert, 0, aluno.get('email', ''))
                    
                    self._run_on_main_thread(self.update_status, f"Aluno ID {aluno_id} carregado")
                else:
                    error_msg = data.get('mensagem', f'Aluno não encontrado (Status: {response.status_code})')
                    self._run_on_main_thread(self.update_status, error_msg, error=True)
                    self._run_on_main_thread(messagebox.showerror, "Erro", error_msg)
                    
            except requests.exceptions.RequestException as e:
                error_msg = f"Erro de conexão: {str(e)}"
                self._run_on_main_thread(self.update_status, error_msg, error=True)
                self._run_on_main_thread(messagebox.showerror, "Erro", error_msg)
            except ValueError: 
                error_msg = "Resposta inválida do servidor (não é JSON válido)."
                self._run_on_main_thread(self.update_status, error_msg, error=True)
                self._run_on_main_thread(messagebox.showerror, "Erro", error_msg)

        threading.Thread(target=thread_buscar_aluno, daemon=True).start()
            
    def editar(self):
        def thread_editar_aluno():
            if not self.auth_token:
                self._run_on_main_thread(messagebox.showerror, "Não Autenticado", "Faça login para editar alunos.")
                return

            aluno_id = self.entry_id.get().strip()
            if not aluno_id or not aluno_id.isdigit():
                self._run_on_main_thread(self.update_status, "Informe um ID válido para editar", error=True)
                self._run_on_main_thread(messagebox.showwarning, "Atenção", "Informe um ID válido para editar.")
                return
                
            dados = {
                "nome": self.entry_nome.get().strip(),
                "matricula": self.entry_matricula.get().strip(),
                "curso": self.entry_curso.get().strip(),
                "email": self.entry_email.get().strip().lower()
            }
            
            if not all(dados.values()):
                self._run_on_main_thread(self.update_status, "Todos os campos devem ser preenchidos!", error=True)
                self._run_on_main_thread(messagebox.showwarning, "Aviso", "Todos os campos devem ser preenchidos!")
                return
            
            if '@' not in dados['email']:
                self._run_on_main_thread(self.update_status, "Email inválido!", error=True)
                self._run_on_main_thread(messagebox.showwarning, "Aviso", "Por favor, insira um email válido")
                return
            
            if not dados['matricula'].isdigit():
                self._run_on_main_thread(self.update_status, "Matrícula deve conter apenas números!", error=True)
                self._run_on_main_thread(messagebox.showwarning, "Aviso", "A matrícula deve conter apenas números.")
                return
            
            try:
                self._run_on_main_thread(self.update_status, f"Atualizando aluno ID {aluno_id}...")
                response = requests.put(f"{BASE_ALUNOS_URL}{aluno_id}", json=dados, headers=self._get_headers()) # Envia o token
                data = response.json()
                
                if response.status_code == 200:
                    self._run_on_main_thread(messagebox.showinfo, "Sucesso", "Aluno atualizado com sucesso!")
                    self._run_on_main_thread(self.limpar_campos)
                    self._run_on_main_thread(self.atualizar_tabela)
                    self._run_on_main_thread(self.update_status, f"Aluno ID {aluno_id} atualizado")
                else:
                    error_msg = data.get('mensagem', f'Erro ao atualizar aluno (Status: {response.status_code})')
                    self._run_on_main_thread(self.update_status, f"Erro: {error_msg}", error=True)
                    self._run_on_main_thread(messagebox.showerror, "Erro", error_msg)
                    
            except requests.exceptions.RequestException as e:
                error_msg = f"Erro de conexão: {str(e)}"
                self._run_on_main_thread(self.update_status, error_msg, error=True)
                self._run_on_main_thread(messagebox.showerror, "Erro", error_msg)
            except ValueError: 
                error_msg = "Resposta inválida do servidor (não é JSON válido)."
                self._run_on_main_thread(self.update_status, error_msg, error=True)
                self._run_on_main_thread(messagebox.showerror, "Erro", error_msg)

        threading.Thread(target=thread_editar_aluno, daemon=True).start()
            
    def excluir(self):
        def thread_excluir_aluno():
            if not self.auth_token:
                self._run_on_main_thread(messagebox.showerror, "Não Autenticado", "Faça login para excluir alunos.")
                return

            aluno_id = self.entry_id.get().strip()
            if not aluno_id or not aluno_id.isdigit():
                self._run_on_main_thread(self.update_status, "Informe um ID válido para excluir", error=True)
                self._run_on_main_thread(messagebox.showwarning, "Atenção", "Informe um ID válido para excluir.")
                return
                
            try:
                self._run_on_main_thread(self.update_status, f"Excluindo aluno ID {aluno_id}...")
                response = requests.delete(f"{BASE_ALUNOS_URL}{aluno_id}", headers=self._get_headers()) # Envia o token
                data = response.json()
                
                if response.status_code == 200:
                    self._run_on_main_thread(messagebox.showinfo, "Sucesso", "Aluno excluído com sucesso.")
                    self._run_on_main_thread(self.limpar_campos)
                    self._run_on_main_thread(self.atualizar_tabela)
                    self._run_on_main_thread(self.update_status, f"Aluno ID {aluno_id} excluído")
                else:
                    error_msg = data.get('mensagem', f'Erro ao excluir aluno (Status: {response.status_code})')
                    self._run_on_main_thread(self.update_status, f"Erro: {error_msg}", error=True)
                    self._run_on_main_thread(messagebox.showerror, "Erro", error_msg)
                    
            except requests.exceptions.RequestException as e:
                error_msg = f"Erro de conexão: {str(e)}"
                self._run_on_main_thread(self.update_status, error_msg, error=True)
                self._run_on_main_thread(messagebox.showerror, "Erro", error_msg)
            except ValueError: 
                error_msg = "Resposta inválida do servidor (não é JSON válido)."
                self._run_on_main_thread(self.update_status, error_msg, error=True)
                self._run_on_main_thread(messagebox.showerror, "Erro", error_msg)
        
        aluno_id = self.entry_id.get().strip()
        if not aluno_id or not aluno_id.isdigit():
            self.update_status("Informe um ID válido para excluir", error=True)
            messagebox.showwarning("Atenção", "Informe um ID válido para excluir.")
            return
        
        resposta = messagebox.askyesno(
            "Confirmação", 
            f"Deseja realmente excluir o aluno {aluno_id}?",
            icon='warning'
        )
        
        if resposta:
            threading.Thread(target=thread_excluir_aluno, daemon=True).start()
            
    def selecionar_aluno(self, event):
        item_selecionado = self.tabela.selection()
        if item_selecionado:
            valores = self.tabela.item(item_selecionado)['values']
            if valores:
                self.limpar_campos() 
                self.entry_id.config(state='normal')
                self.entry_id.insert(0, valores[0])
                self.entry_id.config(state='readonly') 

                self.entry_nome.insert(0, valores[1])
                self.entry_matricula.insert(0, valores[2])
                self.entry_curso.insert(0, valores[3])
                self.entry_email.insert(0, valores[4])
                self.update_status(f"Aluno ID {valores[0]} selecionado")

if __name__ == "__main__":
    root = tk.Tk()
    try:
        app = AlunoApp(root)
        root.mainloop()
    except Exception as e:
        messagebox.showerror("Erro Fatal", f"O aplicativo encontrou um erro inesperado: {str(e)}")

