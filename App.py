from flask import Flask, request, render_template_string
from twilio.twiml.messaging_response import MessagingResponse
import sqlite3
import re

app = Flask(__name__)

def init_db():
    conn = sqlite3.connect('pushti_invoices.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS invoices
                 (invoice_no TEXT, party TEXT, product TEXT, qty INTEGER, free_qty INTEGER, grand_total REAL, date TEXT)''')
    # Add sample data for HANUMAN with correct 28k total
    c.execute("DELETE FROM invoices WHERE invoice_no='A001076'")
    c.execute("INSERT INTO invoices VALUES ('A001076','HANUMAN BEAUTY CENTRE','INSIGHT LG 43 14',10,2,28450,'24-09-2026')")
    c.execute("INSERT INTO invoices VALUES ('A001076','HANUMAN BEAUTY CENTRE','INSIGHT LG 43 07',15,3,28450,'24-09-2026')")
    c.execute("INSERT INTO invoices VALUES ('A001026','LAKSHMI NARASIMNA ENTERPRISES','NAIL POLISH 208',432,0,35000,'10-09-2026')")
    c.execute("INSERT INTO invoices VALUES ('A001063','LAKSHMI NARASIMNA ENTERPRISES','NAIL POLISH 208',2160,0,38000,'15-09-2026')")
    conn.commit()
    conn.close()

init_db()

HTML_PAGE = """
<html><body style="font-family:sans-serif;padding:20px">
<h2>Pushti Invoice Bot - Search</h2>
<form method="post">
Product: <input name="product" placeholder="e.g. 208 or LG 43 14">
Party: <input name="party" placeholder="e.g. LAKSHMI or HANUMAN">
<button type="submit">Search</button>
</form>
<h3>{{result}}</h3>
</body></html>
"""

@app.route("/", methods=["GET","POST"])
def home():
    result = "Type product and party to search"
    if request.method == "POST":
        prod = request.form.get("product","")
        party = request.form.get("party","")
        conn = sqlite3.connect('pushti_invoices.db')
        c = conn.cursor()
        c.execute("SELECT party,invoice_no,product,qty,free_qty,grand_total FROM invoices WHERE product LIKE ? AND party LIKE ?", (f"%{prod}%", f"%{party}%"))
        rows = c.fetchall()
        conn.close()
        if not rows:
            result = f"Not billed - No results for {prod} in {party}"
        else:
            result = ""
            for p,i,pr,q,f,gt in rows:
                result += f"{pr} | {p} | {i} | {q} qty | Total Rs.{gt} <br>"
    return render_template_string(HTML_PAGE, result=result)

@app.route("/webhook", methods=["POST"])
def webhook():
    incoming = request.values.get("Body","").strip().lower()
    resp = MessagingResponse()
    msg = resp.message()
    conn = sqlite3.connect('pushti_invoices.db')
    c = conn.cursor()
    if " in " in incoming:
        prod, party = incoming.split(" in ")
        c.execute("SELECT party,invoice_no,product,qty,free_qty,grand_total FROM invoices WHERE product LIKE ? AND party LIKE ?", (f"%{prod}%", f"%{party}%"))
    else:
        c.execute("SELECT party,invoice_no,product,qty,free_qty,grand_total FROM invoices WHERE product LIKE ?", (f"%{incoming}%",))
    rows = c.fetchall()
    conn.close()
    if not rows:
        msg.body(f"Not billed - {incoming}")
    else:
        txt = f"Found {len(rows)}:\n"
        for p,i,pr,q,f,gt in rows[:5]:
            txt+=f"{pr[:30]} | {p[:15]} | {i} | {q} qty | Rs.{gt}\n"
        msg.body(txt)
    return str(resp)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
