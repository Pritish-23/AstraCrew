# Custom Target Implementation - Quick Reference

## 🎯 What's New

AstraCrew can now test **your actual LLM application** by sending attack probes to your HTTP endpoint!

## 🚀 Quick Start Examples

### 1. Test Local Application (Simplest)
```bash
python main.py --custom-endpoint http://localhost:8000/chat
```

### 2. Test with Authentication
```bash
python main.py \
  --custom-endpoint https://api.myapp.com/chat \
  --custom-auth-type bearer \
  --custom-auth-value "your-token-here"
```

### 3. Custom Request/Response Fields
```bash
python main.py \
  --custom-endpoint http://localhost:8000/api/chat \
  --custom-payload-field "user_message" \
  --custom-response-field "assistant_reply"
```

### 4. Use Configuration File
```bash
# Create config/my_app.json
python main.py --custom-config-file config/my_app.json
```

### 5. Streamlit UI
```bash
streamlit run app.py
# Select "Custom HTTP Endpoint" → Enter URL → Run Campaign
```

## 📋 All Custom Endpoint Flags

| Flag | Description | Example |
|------|-------------|---------|
| `--custom-endpoint` | Your API URL | `http://localhost:8000/chat` |
| `--custom-auth-type` | Auth method: `none`, `bearer`, `api_key`, `basic` | `bearer` |
| `--custom-auth-value` | Token/credentials | `sk-proj-abc123...` |
| `--custom-payload-field` | JSON field for probe | `message` |
| `--custom-response-field` | JSON path for response | `response` or `data.message` |
| `--custom-http-method` | HTTP method | `POST` or `GET` |
| `--custom-timeout` | Request timeout (seconds) | `30` |
| `--custom-config-file` | Path to JSON config | `config/my_app.json` |

## 📝 Example Config File

```json
{
  "endpoint_url": "http://localhost:8000/chat",
  "auth_type": "bearer",
  "auth_value": "your-token-here",
  "payload_field": "message",
  "response_field": "response",
  "http_method": "POST",
  "timeout_seconds": 30,
  "application_name": "My App",
  "application_domain": "Customer Support"
}
```

## 🔧 Your API Requirements

### Request Format
```json
POST /chat
{
  "message": "user input here"
}
```

### Response Format
```json
{
  "response": "assistant response here"
}
```

## 📊 What Gets Tested

All **13 OWASP LLM probes** are sent to your endpoint:
- ✅ Prompt Injection attacks (6 probes)
- ✅ Obfuscation bypasses (4 probes)  
- ✅ Persona manipulation (3 probes)

## 🎯 Example Use Cases

### Local FastAPI Development
```bash
# Terminal 1: Start your app
uvicorn app:app --port 8000

# Terminal 2: Run audit
python main.py --custom-endpoint http://localhost:8000/chat
```

### Production API with Auth
```bash
python main.py \
  --custom-endpoint https://api.production.com/v1/assistant \
  --custom-auth-type api_key \
  --custom-auth-value "prod_key_xyz" \
  --export-pdf reports/production_audit.pdf
```

### Different JSON Structure
```bash
# Your API returns: {"data": {"reply": "..."}}
python main.py \
  --custom-endpoint http://localhost:8000/chat \
  --custom-response-field "data.reply"
```

## 📖 Full Documentation

- **Complete Guide**: See [docs/CUSTOM_TARGETS.md](docs/CUSTOM_TARGETS.md)
- **Config Examples**: See [config/](config/)
- **API Setup**: See [config/README.md](config/README.md)

## ✅ Backward Compatibility

All existing functionality still works:
```bash
# Built-in targets (unchanged)
python main.py --mode deterministic
python main.py --targets MOCK,RAG,AGENTIC

# Streamlit with built-in targets (unchanged)
streamlit run app.py
```

## 🎉 You're Ready!

1. ✅ Implementation complete
2. ✅ CLI flags added
3. ✅ Streamlit UI updated
4. ✅ Documentation created
5. ✅ Example configs provided

**Try it now:**
```bash
python main.py --custom-endpoint http://localhost:8000/chat
```
