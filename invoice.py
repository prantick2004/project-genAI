import os
import json
import time
import mimetypes
import fitz
from google import genai
from google.genai import types
from dotenv import load_dotenv

# ---------- 1. pick newest file from uploads ----------
upload_folder = "uploads"
files = os.listdir(upload_folder)
full_paths = [os.path.join(upload_folder, f) for f in files]
file_path = max(full_paths, key=os.path.getmtime)
print("File found:", file_path)

# ---------- 2. read invoice text ----------
doc = fitz.open(file_path)
text = ""
for page in doc:
    text += page.get_text()

print("Pages:", len(doc))
print("Text length:", len(text.strip()))

# no text found = scanned invoice (image). Send the file itself to Gemini.
is_scanned = len(text.strip()) < 50
file_part = None

if is_scanned:
    print("Scanned invoice found. Sending the file directly to Gemini.")
    mime_type = mimetypes.guess_type(file_path)[0] or "application/pdf"
    with open(file_path, "rb") as f:
        file_part = types.Part.from_bytes(data=f.read(), mime_type=mime_type)

# ---------- 3. Gemini helper (try models one by one) ----------
load_dotenv()
client = genai.Client(
    api_key=os.getenv("GOOGLE_API_KEY"),
    http_options=types.HttpOptions(timeout=60000),
)

MODELS = ["gemini-3.5-flash-lite", "gemini-3.1-flash-lite", "gemini-3.8-flash"]


def call_gemini(prompt, as_json=False, file_part=None):
    config = types.GenerateContentConfig(temperature=0)
    if as_json:
        config = types.GenerateContentConfig(
            temperature=0,
            response_mime_type="application/json",
        )

    contents = [file_part, prompt] if file_part else prompt

    for model_name in MODELS:
        for attempt in range(2):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=contents,
                    config=config,
                )
                print("(answered by:", model_name + ")")
                return response.text
            except Exception as e:
                print(f"{model_name} attempt {attempt + 1} failed: {e}")
                time.sleep(3)
    return None


# ---------- 4. extract invoice details ----------
if is_scanned:
    source_block = "The document is attached as a file. Read it from the file."
else:
    source_block = f"Document text:\n{text}"

prompt = f"""
Extract the details from this document.
The document can contain MORE THAN ONE separate bill (Tax Invoice, Bill of Supply, etc).
Each bill with its own number is one entry. Extract every bill.

Rules:
- "items" must contain ONLY the billed line items from the main charges table of that bill.
- Do NOT put "details of goods transported" or any shipping/consignment table into items.
- Tax can be CGST + SGST, or IGST. Fill only what the bill shows, others null.
- invoice_number must be only the number itself, without symbols like "#".
- Copy numbers exactly as printed. If a number is not clear to read, use null.

Return ONLY JSON in this format:
{{
  "invoices": [
    {{
      "document_type": "",
      "invoice_number": "",
      "order_id": "",
      "invoice_date": "",
      "vendor_name": "",
      "customer_name": "",
      "currency": "",
      "items": [{{"name": "", "quantity": 0, "unit_price": 0, "discount": 0, "taxable_value": 0, "cgst": 0, "sgst": 0, "igst": 0, "amount": 0}}],
      "total_amount": 0
    }}
  ]
}}
If a field is missing in the bill, use null. Do not guess.

{source_block}
"""

answer = call_gemini(prompt, as_json=True, file_part=file_part)

if answer is None:
    raise SystemExit("All models busy, try again in a minute.")

# ---------- 5. show result ----------
data = json.loads(answer)
invoices = data.get("invoices") or []
print("\nBills found:", len(invoices))

for n, inv in enumerate(invoices, start=1):
    print(f"\n===== BILL {n}: {inv.get('document_type')} =====")
    print("Number        :", inv.get("invoice_number"))
    print("Order ID      :", inv.get("order_id"))
    print("Date          :", inv.get("invoice_date"))
    print("Vendor        :", inv.get("vendor_name"))
    print("Customer      :", inv.get("customer_name"))

    print("\nItems:")
    for item in inv.get("items") or []:
        print(f"  - {item.get('name')}")
        print(f"      qty: {item.get('quantity')} | price: {item.get('unit_price')} | discount: {item.get('discount')}")
        print(f"      taxable: {item.get('taxable_value')} | CGST: {item.get('cgst')} | SGST: {item.get('sgst')} | IGST: {item.get('igst')}")
        print(f"      amount: {item.get('amount')}")

    print("\nTotal:", inv.get("total_amount"), inv.get("currency"))

# ---------- 6. ask anything more ----------
print("\n-----------------------------------------")
print("Do you want to know anything more about these bills?")
print("Type your question. Type 'exit' to stop.")

history = []

if is_scanned:
    original_block = ""
else:
    original_block = f"Original invoice text (use only if the data above is missing something):\n{text}"

while True:
    try:
        question = input("\nAsk: ").strip()
    except (EOFError, KeyboardInterrupt):
        break

    if question == "":
        continue
    if question.lower() in ("exit", "quit"):
        break

    history_text = ""
    for q, a in history[-5:]:
        history_text += f"User: {q}\nAssistant: {a}\n"

    chat_prompt = f"""
You are a helpful invoice assistant. Answer the user's question using ONLY the invoice data below.
If the answer can not be found, say: "I could not find that in the invoice."
Do not make up information. When adding numbers, calculate carefully.
Keep the answer short and clear.

Extracted invoice data:
{json.dumps(invoices, indent=2)}

{original_block}

Previous chat:
{history_text}

User Question:
{question}

Answer:
"""

    reply = call_gemini(chat_prompt)
    if reply is None:
        reply = "Server busy, please ask again in a minute."

    print("\nAnswer:", reply)
    history.append((question, reply))

print("\nBye!")