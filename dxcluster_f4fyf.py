import tkinter as tk
from tkinter import ttk
import telnetlib, threading, math, os, socket, json, sys
from datetime import datetime, timezone

# --- CONFIGURATION CHEMINS ---
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

CONFIG_FILE = "config_radio.json"
CTY_DAT = resource_path("cty.dat")

# --- COULEURS HIGH-TECH ---
COLORS = {
    "bg": "#0d1117", "panel": "#161b22", "text": "#e6edf3",
    "accent": "#58a6ff", "neon_green": "#39ff14", "neon_red": "#ff3131",
    "EU": "#58a6ff", "NA": "#ffb454", "AF": "#ff79c6", "AS": "#bd93f9", "SA": "#50fa7b", "OC": "#8be9fd"
}

def get_band(freq_khz):
    f = float(freq_khz)
    bands = {
        (1800, 2000): "160m", (3500, 3800): "80m", (7000, 7200): "40m",
        (10100, 10150): "30m", (14000, 14350): "20m", (18068, 18168): "17m",
        (21000, 21450): "15m", (24890, 24990): "12m", (28000, 29700): "10m",
        (144000, 148000): "2m", (430000, 450000): "70cm", (1240000, 1300000): "23cm"
    }
    for (low, high), name in bands.items():
        if low <= f <= high: return name
    return "Autre"

def load_cty_dat(filename):
    dxcc_map = {}
    if not os.path.exists(filename): return {}
    try:
        with open(filename, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if not line or line.startswith('*'): i += 1; continue
            parts = line.split(':')
            if len(parts) >= 8:
                country, cont, lat, lon = parts[0], parts[3], float(parts[4] or 0), float(parts[5] or 0)
                main_p = parts[7].strip()
                all_p = ""
                i += 1
                while i < len(lines):
                    p_l = lines[i].strip(); all_p += p_l
                    if p_l.endswith(';'): break
                    i += 1
                prefixes = all_p.replace(';', '').split(',')
                prefixes.append(main_p)
                for p in prefixes:
                    p = p.strip().split('(')[0].split('[')[0].strip('=')
                    if p: dxcc_map[p] = {'name': country, 'cont': cont, 'lat': lat, 'lon': lon}
            i += 1
    except: pass
    return dxcc_map

class DXClusterApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("RADIO OPERATOR TERMINAL - F4FYF")
        self.geometry("1300x800")
        self.configure(bg=COLORS["bg"])
        
        self.dxcc_dict = load_cty_dat(CTY_DAT)
        self.current_rig_freq = 0.0
        self.running = False
        
        # IMPORTANT: On initialise le widget Tree à None pour éviter l'AttributeError
        self.tree = None 
        
        self.setup_styles()
        self.setup_ui()
        self.load_config()
        self.update_clocks()
        
        # On lance les threads après que l'UI soit prête
        threading.Thread(target=self.rig_loop, daemon=True).start()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background=COLORS["bg"], foreground=COLORS["text"], fieldbackground=COLORS["bg"], borderwidth=0, font=("Consolas", 10))
        style.configure("Treeview.Heading", background=COLORS["panel"], foreground=COLORS["accent"], borderwidth=1, font=("Consolas", 10, "bold"))
        style.map("Treeview", background=[('selected', COLORS["accent"])])

    def setup_ui(self):
        # --- SIDE PANEL ---
        side = tk.Frame(self, width=220, bg=COLORS["panel"], padx=15, pady=15)
        side.pack(side="left", fill="y")

        tk.Label(side, text="SYSTEM CONFIG", fg=COLORS["accent"], bg=COLORS["panel"], font=("Consolas", 11, "bold")).pack(pady=(0,15))
        self.ent_host = self.create_input(side, "CLUSTER HOST")
        self.ent_port = self.create_input(side, "PORT")
        self.ent_call = self.create_input(side, "CALLSIGN")
        self.ent_loc = self.create_input(side, "MY LOCATOR")
        
        self.btn_conn = tk.Button(side, text="INITIALIZE", bg=COLORS["bg"], fg=COLORS["neon_green"], font=("Consolas", 10, "bold"), relief="flat", bd=2, command=self.toggle_connection)
        self.btn_conn.pack(fill="x", pady=20)

        self.filter_cont = self.create_input(side, "CONTINENT")
        self.filter_mode = self.create_input(side, "MODE")
        self.filter_country = self.create_input(side, "COUNTRY")

        self.ent_rig_host = self.create_input(side, "RIG HOST")
        self.ent_rig_port = self.create_input(side, "RIG PORT")
        self.l_rig_status = tk.Label(side, text="RIG: OFFLINE", fg=COLORS["neon_red"], bg=COLORS["panel"], font=("Consolas", 9, "bold"))
        self.l_rig_status.pack(side="bottom", pady=10)

        # --- MAIN AREA ---
        main = tk.Frame(self, bg=COLORS["bg"])
        main.pack(side="right", fill="both", expand=True)

        head = tk.Frame(main, bg=COLORS["bg"], pady=10)
        head.pack(fill="x")
        
        band_frame = tk.Frame(head, bg=COLORS["bg"])
        band_frame.pack(side="left", padx=20)
        tk.Label(band_frame, text="SIGNAL SPECTRUM", fg=COLORS["accent"], bg=COLORS["bg"], font=("Consolas", 8, "bold")).grid(row=0, column=0, columnspan=7, sticky="w", pady=(0,5))
        
        self.bands_filter = {b: tk.BooleanVar(value=True) for b in ["160m", "80m", "40m", "30m", "20m", "17m", "15m", "12m", "10m", "2m", "70cm", "Autre"]}
        for i, (b, var) in enumerate(self.bands_filter.items()):
            tk.Checkbutton(band_frame, text=b, variable=var, bg=COLORS["bg"], fg=COLORS["accent"], selectcolor=COLORS["bg"], activebackground=COLORS["bg"], relief="flat", highlightthickness=0, font=("Consolas", 9)).grid(row=i//7+1, column=i%7, sticky="w")

        clk_frame = tk.Frame(head, bg=COLORS["bg"])
        clk_frame.pack(side="right", padx=20)
        self.l_loc = tk.Label(clk_frame, font=("Consolas", 16, "bold"), bg=COLORS["bg"], fg=COLORS["text"]); self.l_loc.pack()
        self.l_utc = tk.Label(clk_frame, font=("Consolas", 16, "bold"), bg=COLORS["bg"], fg=COLORS["accent"]); self.l_utc.pack()

        # --- TABLEAU ---
        cols = ("Time", "Freq", "Call", "Entity", "Cont", "Mode", "Dist", "Az")
        self.tree = ttk.Treeview(main, columns=cols, show="headings", cursor="hand2")
        for c in cols: 
            self.tree.heading(c, text=c)
            self.tree.column(c, width=90, anchor="center")
        self.tree.column("Entity", width=220)
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)

        # Liaison du double-clic pour le QSY
        self.tree.bind("<Double-1>", self.on_tree_double_click)

        for code, color in COLORS.items():
            if len(code) == 2: self.tree.tag_configure(code, foreground=color)
        self.tree.tag_configure('near', background="#443300", foreground="#ffffff")

    def create_input(self, parent, label):
        tk.Label(parent, text=label, bg=COLORS["panel"], fg=COLORS["text"], font=("Consolas", 8)).pack(anchor="w")
        ent = tk.Entry(parent, bg=COLORS["bg"], fg=COLORS["neon_green"], insertbackground="white", relief="flat", highlightthickness=1, highlightbackground="#30363d")
        ent.pack(fill="x", pady=(0,8))
        return ent

    def on_tree_double_click(self, event):
        """ Envoie la fréquence du spot sélectionné à la radio """
        selection = self.tree.selection()
        if not selection: return
        
        item = selection[0]
        freq_khz = self.tree.item(item, "values")[1]
        freq_hz = int(float(freq_khz) * 1000)
        
        def send_qsy():
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(1.0)
                    s.connect((self.ent_rig_host.get().strip(), int(self.ent_rig_port.get().strip())))
                    s.sendall(f"F {freq_hz}\n".encode())
            except: pass

        threading.Thread(target=send_qsy, daemon=True).start()

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    c = json.load(f)
                    self.ent_host.insert(0, c.get("host", "dxc.f5len.org"))
                    self.ent_port.insert(0, c.get("port", "7000"))
                    self.ent_call.insert(0, c.get("call", "F4FYF"))
                    self.ent_loc.insert(0, c.get("loc", "JN25"))
                    self.ent_rig_host.insert(0, c.get("rig_host", "127.0.0.1"))
                    self.ent_rig_port.insert(0, c.get("rig_port", "4532"))
            except: pass

    def save_config(self):
        config = {
            "host": self.ent_host.get(), "port": self.ent_port.get(),
            "call": self.ent_call.get(), "loc": self.ent_loc.get(),
            "rig_host": self.ent_rig_host.get(), "rig_port": self.ent_rig_port.get()
        }
        with open(CONFIG_FILE, "w") as f: json.dump(config, f)

    def update_clocks(self):
        self.l_loc.config(text=f"L: {datetime.now().strftime('%H:%M:%S')}")
        self.l_utc.config(text=f"Z: {datetime.now(timezone.utc).strftime('%H:%M:%S')}")
        self.after(1000, self.update_clocks)

    def rig_loop(self):
        while True:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(1.5)
                    s.connect((self.ent_rig_host.get().strip(), int(self.ent_rig_port.get().strip())))
                    s.sendall(b"f\n")
                    data = s.recv(1024).decode().strip()
                    if data:
                        freq_raw = "".join(filter(str.isdigit, data))
                        if freq_raw:
                            self.current_rig_freq = float(freq_raw) / 1000.0
                            self.l_rig_status.config(text=f"RIG: {self.current_rig_freq:.1f} KHZ", fg=COLORS["neon_green"])
            except:
                self.l_rig_status.config(text="RIG: OFFLINE", fg=COLORS["neon_red"])
            threading.Event().wait(2)

    def toggle_connection(self):
        if not self.running:
            self.save_config()
            self.running = True
            self.btn_conn.config(text="TERMINATE", fg=COLORS["neon_red"])
            threading.Thread(target=self.cluster_thread, daemon=True).start()
        else:
            self.running = False
            self.btn_conn.config(text="INITIALIZE", fg=COLORS["neon_green"])

    def cluster_thread(self):
        try:
            tn = telnetlib.Telnet(self.ent_host.get(), int(self.ent_port.get()))
            tn.write(f"{self.ent_call.get()}\n".encode('ascii'))
            while self.running:
                line = tn.read_until(b"\n").decode('ascii', errors='ignore')
                if "DX de" in line: self.parse_line(line)
        except: pass

    def parse_line(self, data):
        if not self.tree: return # Sécurité contre AttributeError
        try:
            p = data.split()
            f_val = float(p[3])
            dx_call = p[4].replace(':', '').split('/')[0]
            band = get_band(f_val)
            if not self.bands_filter[band].get(): return
            mode = "FT8" if "FT8" in data.upper() else ("CW" if (f_val*100)%10 < 5 else "SSB")
            
            prefix = ""
            for l in range(len(dx_call), 0, -1):
                if dx_call[:l] in self.dxcc_dict: prefix = dx_call[:l]; break
            info = self.dxcc_dict.get(prefix, {'name': 'Unknown', 'cont': '??', 'lat': 0, 'lon': 0})
            
            if self.filter_cont.get() and self.filter_cont.get().upper() != info['cont']: return
            if self.filter_mode.get() and self.filter_mode.get().upper() not in mode.upper(): return
            if self.filter_country.get() and self.filter_country.get().upper() not in info['name'].upper(): return

            loc = self.ent_loc.get().upper()
            m_lon = (ord(loc[0])-65)*20-180 + (ord(loc[2])-48)*2 + 1
            m_lat = (ord(loc[1])-65)*10-90 + (ord(loc[3])-48)*1 + 0.5
            rl1, rl2, rlo1, rlo2 = map(math.radians, [m_lat, info['lat'], m_lon, info['lon']])
            dist = 6371 * 2 * math.asin(math.sqrt(math.sin((rl2-rl1)/2)**2 + math.cos(rl1)*math.cos(rl2)*math.sin((rlo2-rlo1)/2)**2))
            y, x = math.sin(rlo2-rlo1)*math.cos(rl2), math.cos(rl1)*math.sin(rl2)-math.sin(rl1)*math.cos(rl2)*math.cos(rlo2-rlo1)
            az = (math.degrees(math.atan2(y, x)) + 360) % 360
            
            tags = [info['cont']]
            if abs(self.current_rig_freq - f_val) < 5.0: tags.append('near')
            
            row = (datetime.now(timezone.utc).strftime("%H:%M"), f"{f_val:.1f}", dx_call, info['name'], info['cont'], mode, f"{int(dist)}km", f"{int(az)}°")
            self.after(0, lambda: self.tree.insert("", 0, values=row, tags=tags))
            if len(self.tree.get_children()) > 100: self.tree.delete(self.tree.get_children()[-1])
        except: pass

if __name__ == "__main__":
    app = DXClusterApp(); app.mainloop()
