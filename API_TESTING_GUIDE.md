# 🚀 API Testing Guide - Quran Video Generator

## ✅ Server Status: **RUNNING**

The FastAPI server is live at:
- **Base URL**: `http://localhost:8000`
- **API Documentation**: `http://localhost:8000/docs` (Interactive Swagger UI)
- **Alternative Docs**: `http://localhost:8000/redoc`

---

## 📍 Available Endpoints

### 1. **Root Endpoint** (Health Check)
```bash
curl http://localhost:8000/
```

**Expected Response:**
```json
{
  "message": "Welcome to the Quran Video Generator API (API-Driven). Use POST /generate_video for single or multiple Ayahs."
}
```

---

### 2. **Generate Video** (Submit Job)

**Endpoint:** `POST /generate_video`

#### Example 1: Single Ayah (Al-Fatiha, Verse 1)
```bash
curl -X POST http://localhost:8000/generate_video \
  -H "Content-Type: application/json" \
  -d '{
    "surah": 1,
    "start_ayah": 1,
    "end_ayah": 1,
    "reciter_key": "mishary_alafasy",
    "translation_key": "en_sahih",
    "background_id": "calm_image"
  }'
```

#### Example 2: Full Surah Al-Fatiha (7 verses)
```bash
curl -X POST http://localhost:8000/generate_video \
  -H "Content-Type: application/json" \
  -d '{
    "surah": 1,
    "start_ayah": 1,
    "end_ayah": 7,
    "reciter_key": "mishary_alafasy",
    "translation_key": "en_sahih",
    "background_id": "nature_video"
  }'
```

#### Example 3: Custom Filename
```bash
curl -X POST http://localhost:8000/generate_video \
  -H "Content-Type: application/json" \
  -d '{
    "surah": 2,
    "start_ayah": 1,
    "end_ayah": 5,
    "reciter_key": "mishary_alafasy",
    "translation_key": "en_yusufali",
    "background_id": "geometric_pattern",
    "output_filename": "my_quran_video"
  }'
```

**Expected Response:**
```json
{
  "message": "Multi-ayah video generation job accepted.",
  "job_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Note:** Save the `job_id` - you'll need it to check the status!

---

### 3. **Check Job Status**

**Endpoint:** `GET /jobs/{job_id}/status`

```bash
# Replace {job_id} with your actual job ID
curl http://localhost:8000/jobs/550e8400-e29b-41d4-a716-446655440000/status
```

**Response Examples:**

**Queued:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "queued",
  "detail": "Pending execution"
}
```

**Processing:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "detail": "Fetching data for Ayahs..."
}
```

**Completed:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "output_path": "/home/user/QuranSharingApp/quran_video_server_api/output/S1_A1-7_550e8400.mp4"
}
```

**Failed:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "failed",
  "detail": "API Error: Failed to fetch data..."
}
```

---

## 🎬 Complete Testing Workflow

### Step 1: Submit a Job
```bash
JOB_RESPONSE=$(curl -s -X POST http://localhost:8000/generate_video \
  -H "Content-Type: application/json" \
  -d '{
    "surah": 1,
    "start_ayah": 1,
    "end_ayah": 1,
    "reciter_key": "mishary_alafasy",
    "translation_key": "en_sahih",
    "background_id": "calm_image"
  }')

echo "$JOB_RESPONSE"
```

### Step 2: Extract Job ID
```bash
JOB_ID=$(echo $JOB_RESPONSE | python -c "import sys, json; print(json.load(sys.stdin)['job_id'])")
echo "Job ID: $JOB_ID"
```

### Step 3: Poll for Status
```bash
# Check status every 5 seconds
while true; do
  STATUS=$(curl -s http://localhost:8000/jobs/$JOB_ID/status | python -m json.tool)
  echo "$STATUS"

  # Check if completed or failed
  if echo "$STATUS" | grep -q '"status": "completed"'; then
    echo "✅ Job completed!"
    break
  elif echo "$STATUS" | grep -q '"status": "failed"'; then
    echo "❌ Job failed!"
    break
  fi

  sleep 5
done
```

---

## 🧪 Testing the New Components

### Test Database Persistence
```bash
# 1. Submit a job and note the job_id
JOB_ID="your-job-id-here"

# 2. Check the database directly
sqlite3 /home/user/QuranSharingApp/quran_video_server_api/quran_video_jobs.db \
  "SELECT job_id, status, surah, start_ayah, end_ayah FROM video_jobs WHERE job_id='$JOB_ID';"
```

### Test Input Validation
```bash
# Should FAIL - Invalid surah
curl -X POST http://localhost:8000/generate_video \
  -H "Content-Type: application/json" \
  -d '{
    "surah": 999,
    "start_ayah": 1,
    "end_ayah": 1,
    "reciter_key": "mishary_alafasy",
    "translation_key": "en_sahih",
    "background_id": "calm_image"
  }'

# Should FAIL - Al-Fatiha only has 7 ayahs
curl -X POST http://localhost:8000/generate_video \
  -H "Content-Type: application/json" \
  -d '{
    "surah": 1,
    "start_ayah": 1,
    "end_ayah": 999,
    "reciter_key": "mishary_alafasy",
    "translation_key": "en_sahih",
    "background_id": "calm_image"
  }'

# Should FAIL - Invalid reciter
curl -X POST http://localhost:8000/generate_video \
  -H "Content-Type: application/json" \
  -d '{
    "surah": 1,
    "start_ayah": 1,
    "end_ayah": 7,
    "reciter_key": "invalid_reciter",
    "translation_key": "en_sahih",
    "background_id": "calm_image"
  }'
```

---

## 📋 Valid Configuration Options

### Reciters (`reciter_key`)
- `mishary_alafasy` ⭐ (Has confirmed word timestamps)
- `sudais`
- `ghamdi`
- `husary_mujawwad`
- `shatri`
- `shuraim`
- `minshawi_mujawwad`
- `ajamy`
- `rifai`
- `basfar`
- `shaatree`
- `tablawy`
- `dussary`
- `abdulbaset_mujawwad`

### Translations (`translation_key`)
- `en_sahih` - Sahih International
- `en_yusufali` - Abdullah Yusuf Ali
- `en_pickthall` - Pickthall
- `en_hilali` - Hilali & Khan
- `en_arberry` - A. J. Arberry
- `en_daryabadi` - Abdul Majid Daryabadi
- `en_transliteration` - English Transliteration

### Backgrounds (`background_id`)
- `nature_video` - MP4 nature video
- `calm_image` - Calm JPEG image
- `space_nebula` - Space nebula MP4
- `geometric_pattern` - Geometric PNG pattern
- `kaaba_blur` - Blurred Kaaba image

**Note:** Background files must exist in `quran_video_server_api/data/sample_backgrounds/`

---

## 🔍 Surah-Ayah Limits

Here are some common surahs and their ayah counts:

| Surah | Name | Ayah Count |
|-------|------|------------|
| 1 | Al-Fatiha | 7 |
| 2 | Al-Baqarah | 286 |
| 3 | Ali 'Imran | 200 |
| 18 | Al-Kahf | 110 |
| 36 | Ya-Sin | 83 |
| 55 | Ar-Rahman | 78 |
| 67 | Al-Mulk | 30 |
| 112 | Al-Ikhlas | 4 |
| 113 | Al-Falaq | 5 |
| 114 | An-Nas | 6 |

**Full list available in:** `config_new.py` → `SURAH_AYAH_COUNTS`

---

## 🐛 Troubleshooting

### Server Not Responding
```bash
# Check if server is running
ps aux | grep uvicorn

# Check server logs
tail -f /tmp/uvicorn.log  # If you redirected logs
```

### Job Stuck in "queued"
```bash
# Check background tasks are processing
curl http://localhost:8000/jobs/{job_id}/status

# The current implementation processes jobs in the background
# If stuck, check the server logs for errors
```

### Database Issues
```bash
# Check database file exists
ls -lh /home/user/QuranSharingApp/quran_video_server_api/quran_video_jobs.db

# View all jobs
sqlite3 /home/user/QuranSharingApp/quran_video_server_api/quran_video_jobs.db \
  "SELECT job_id, status, created_at FROM video_jobs ORDER BY created_at DESC LIMIT 10;"
```

---

## 📊 Using the Interactive API Docs

The easiest way to test is using the **Swagger UI**:

1. Open in browser: `http://localhost:8000/docs`
2. Click on any endpoint to expand it
3. Click "Try it out"
4. Fill in the parameters
5. Click "Execute"
6. See the response below!

---

## 💡 Pro Tips

1. **Save Job IDs**: Keep track of your job IDs to check status later
2. **Start Small**: Test with single ayahs before trying full surahs
3. **Check Backgrounds**: Make sure background files exist before submitting jobs
4. **Monitor Logs**: Watch the server output for detailed progress
5. **Use Mishary Alafasy**: This reciter has confirmed word timestamps

---

## 🎉 Example Success Flow

```bash
# 1. Submit job for Al-Fatiha
curl -X POST http://localhost:8000/generate_video \
  -H "Content-Type: application/json" \
  -d '{
    "surah": 1,
    "start_ayah": 1,
    "end_ayah": 7,
    "reciter_key": "mishary_alafasy",
    "translation_key": "en_sahih",
    "background_id": "calm_image"
  }'

# Response: {"message": "...", "job_id": "abc-123"}

# 2. Check status (wait a few seconds between checks)
curl http://localhost:8000/jobs/abc-123/status

# 3. When completed, find your video at:
ls -lh /home/user/QuranSharingApp/quran_video_server_api/output/
```

---

**Server Running At:** `http://localhost:8000`
**API Docs:** `http://localhost:8000/docs`

Happy Testing! 🚀
