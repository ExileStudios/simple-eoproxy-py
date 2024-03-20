import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from net.Packet import Packet

class PacketEditorGUI:
    BYTE_COLORS = ["#0000FF", "#008000", "#800080", "#800000", "#808000", "#008080", "#000080", "#800080"]

    def __init__(self, on_resend_callback, on_close_callback):
        self.master = tk.Tk()
        self.master.title("Packet Editor")
        self.on_resend_callback = on_resend_callback
        self.on_close_callback = on_close_callback

        self.style = ttk.Style()
        self.style.theme_use('clam')

        self.style.configure("Treeview", background="#E8E8E8", foreground="#333333",
                             rowheight=25, fieldbackground="#E8E8E8")
        self.style.map('Treeview', background=[('selected', '#D3D3D3')])
        
        self.content_frame = ttk.Frame(self.master)
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.packet_list = ttk.Treeview(self.content_frame, columns=("Direction", "Family", "Action", "Length"), show="headings")
        self.packet_list.heading("Direction", text="Direction")
        self.packet_list.heading("Family", text="Family")
        self.packet_list.heading("Action", text="Action")
        self.packet_list.heading("Length", text="Length")
        self.packet_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.packet_list.bind("<ButtonRelease-1>", self.on_packet_select)

        self.tree_scroll = ttk.Scrollbar(self.content_frame, orient="vertical", command=self.packet_list.yview)
        self.tree_scroll.pack(side=tk.LEFT, fill="y")
        self.packet_list.configure(yscrollcommand=self.tree_scroll.set)

        self.editor = scrolledtext.ScrolledText(self.content_frame, wrap=tk.WORD, background="#F0F0F0", font=("Courier New", 10))
        self.editor.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.resend_button = ttk.Button(self.master, text="Resend Packet", command=self.resend_packet)
        self.resend_button.pack(pady=5)

        self.selected_packet_id = None
        self.packets = {}

        self.master.protocol("WM_DELETE_WINDOW", self.on_close)

    def add_packet(self, direction, op_name, ac_name, op, ac, data):
        packet_id = len(self.packets) + 1
        packet_length = len(data) // 2
        self.packets[packet_id] = {"direction": direction, "family": op_name, "action": ac_name, "data": data, "length": packet_length, "family_val": op, "action_val": ac}
        self.packet_list.insert("", "end", iid=str(packet_id), values=(direction, op_name, ac_name, packet_length))
        self.packet_list.see(packet_id)

    def on_packet_select(self, event):
        selection = self.packet_list.selection()
        if selection:
            packet_id = selection[0]
            self.selected_packet_id = int(packet_id)
            packet = self.packets[int(packet_id)]
            data_formatted = ' '.join([packet["data"][i:i+2] for i in range(0, len(packet["data"]), 2)])

            self.editor.delete("1.0", tk.END)
            start_index = "1.0"

            for byte in data_formatted.split():
                tag_name = f"byte_{byte}"
                self.editor.insert(tk.END, byte + " ", tag_name)
                start_index = self.editor.index(f"{start_index}+{len(byte) + 1}c")

                if byte == "FE":
                    self.editor.tag_config(tag_name, foreground="#505050")
                elif byte == "FF":
                    self.editor.tag_config(tag_name, foreground="#FF0000")
                else:
                    self.editor.tag_config(tag_name, foreground=self.get_color_for_byte(byte))

    def get_color_for_byte(self, byte):
        byte_val = int(byte, 16)
        return self.BYTE_COLORS[byte_val]

    def resend_packet(self):
        if self.selected_packet_id:
            packet_info = self.packets.get(int(self.selected_packet_id))
            if packet_info:
                edited_hex = self.editor.get("1.0", tk.END).strip().replace(" ", "")
                try:
                    edited_data = bytes.fromhex(edited_hex)
                    if packet_info["family_val"] is not None and packet_info["action_val"] is not None:
                        full_data = [packet_info["action_val"], packet_info["family_val"]] + list(edited_data)
                        new_packet = Packet(bytes(full_data))
                        new_packet.set_id(packet_info["family_val"], packet_info["action_val"])
                        is_client = packet_info["direction"] == "[C->S]"
                        self.on_resend_callback(new_packet, is_client)
                except ValueError:
                    messagebox.showerror("Error", "Invalid packet data")
        else:
            messagebox.showinfo("Info", "Please select a packet to edit and resend.")

    def on_close(self):
        self.on_close_callback()
        self.master.destroy()

    def run(self):
        self.master.mainloop()
