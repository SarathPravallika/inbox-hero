# inbox-hero

https://github.com/SarathPravallika/inbox-hero

An agentic system that takes an inbox from unread to empty by deciding what to do
with every message - doing the parts it should do, and refusing the parts it should not.

---

## Setup

Python 3.14.2, run from the project root.

```bash
cd inbox-hero

python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env              # put your API key in it
```

## Tests

No API key, no installed packages.

```bash
python demo.py --test
```
