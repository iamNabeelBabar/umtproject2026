# OCR Timetable API — Frontend Integration Guide

## API Overview

| Property | Value |
|----------|-------|
| **Endpoint** | `POST /ocr/extract-timetable-multi` |
| **Content-Type** | `multipart/form-data` |
| **Min Images** | 1 (required) |
| **Max Images** | 5 |
| **Allowed Formats** | PNG, JPG, JPEG |

### Field Names

| Field | Required |
|-------|----------|
| `file1` | ✅ Required |
| `file2` | Optional |
| `file3` | Optional |
| `file4` | Optional |
| `file5` | Optional |

> ⚠️ **Important:** Always start from `file1`. Do not skip numbers (e.g., don't send `file1` + `file3` without `file2`).

---

## Response

**Success `200 OK`:**
```json
{
  "timetable": { ... }
}
```

**Error Responses:**

| Status | Reason |
|--------|--------|
| `400` | No file provided / unsupported type / empty file |
| `500` | Internal server error during extraction |

```json
{ "detail": "Error message here" }
```

---

## 1. Vanilla JavaScript

```html
<input type="file" id="fileInput" multiple accept="image/png, image/jpeg" />
<button onclick="uploadFiles()">Extract Timetable</button>
```

```javascript
async function uploadFiles() {
  const input = document.getElementById('fileInput');
  const files = Array.from(input.files).slice(0, 5); // max 5

  if (files.length === 0) {
    alert('Please select at least one image.');
    return;
  }

  const formData = new FormData();
  files.forEach((file, index) => {
    formData.append(`file${index + 1}`, file);
  });

  try {
    const response = await fetch('http://localhost:8000/ocr/extract-timetable-multi', {
      method: 'POST',
      body: formData,
      // ❌ Do NOT set Content-Type manually — browser sets it with boundary automatically
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail);
    }

    const result = await response.json();
    console.log('Extracted timetable:', result);

  } catch (err) {
    console.error('Upload failed:', err.message);
  }
}
```

---

## 2. React (Fetch API)

```jsx
import { useState } from 'react';

export default function TimetableUploader() {
  const [files, setFiles] = useState([]);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleFileChange = (e) => {
    const selected = Array.from(e.target.files).slice(0, 5);
    setFiles(selected);
  };

  const handleUpload = async () => {
    if (files.length === 0) return;

    const formData = new FormData();
    files.forEach((file, index) => {
      formData.append(`file${index + 1}`, file);
    });

    setLoading(true);
    setError(null);

    try {
      const response = await fetch('http://localhost:8000/ocr/extract-timetable-multi', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail);
      }

      const data = await response.json();
      setResult(data);

    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <input
        type="file"
        multiple
        accept="image/png,image/jpeg"
        onChange={handleFileChange}
      />
      <p>{files.length} / 5 image(s) selected</p>

      <button onClick={handleUpload} disabled={loading || files.length === 0}>
        {loading ? 'Extracting...' : 'Extract Timetable'}
      </button>

      {error && <p style={{ color: 'red' }}>Error: {error}</p>}
      {result && <pre>{JSON.stringify(result, null, 2)}</pre>}
    </div>
  );
}
```

---

## 3. React (Axios)

```bash
npm install axios
```

```jsx
import { useState } from 'react';
import axios from 'axios';

export default function TimetableUploader() {
  const [files, setFiles] = useState([]);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleFileChange = (e) => {
    setFiles(Array.from(e.target.files).slice(0, 5));
  };

  const handleUpload = async () => {
    if (files.length === 0) return;

    const formData = new FormData();
    files.forEach((file, index) => {
      formData.append(`file${index + 1}`, file);
    });

    setLoading(true);
    setError(null);

    try {
      const { data } = await axios.post(
        'http://localhost:8000/ocr/extract-timetable-multi',
        formData,
        { headers: { 'Content-Type': 'multipart/form-data' } }
      );
      setResult(data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Upload failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <input type="file" multiple accept="image/png,image/jpeg" onChange={handleFileChange} />
      <p>{files.length} / 5 image(s) selected</p>
      <button onClick={handleUpload} disabled={loading || files.length === 0}>
        {loading ? 'Extracting...' : 'Extract Timetable'}
      </button>
      {error && <p style={{ color: 'red' }}>{error}</p>}
      {result && <pre>{JSON.stringify(result, null, 2)}</pre>}
    </div>
  );
}
```

---

## 4. Flutter (Dart)

### pubspec.yaml
```yaml
dependencies:
  http: ^1.2.0
  image_picker: ^1.0.7
```

### iOS — Info.plist
```xml
<key>NSPhotoLibraryUsageDescription</key>
<string>Required to upload timetable images</string>
<key>NSCameraUsageDescription</key>
<string>Required to capture timetable images</string>
```

### Android — AndroidManifest.xml
```xml
<uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE"/>
<uses-permission android:name="android.permission.CAMERA"/>
```

### API Service — `timetable_service.dart`
```dart
import 'dart:io';
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:http_parser/http_parser.dart';

class TimetableService {
  static const String baseUrl = 'http://10.0.2.2:8000'; // Android emulator
  // Use your machine's local IP for physical devices: 'http://192.168.x.x:8000'

  static Future<Map<String, dynamic>> extractTimetable(List<File> images) async {
    if (images.isEmpty || images.length > 5) {
      throw Exception('Provide between 1 and 5 images.');
    }

    final uri = Uri.parse('$baseUrl/ocr/extract-timetable-multi');
    final request = http.MultipartRequest('POST', uri);

    for (int i = 0; i < images.length; i++) {
      final ext = images[i].path.split('.').last.toLowerCase();
      final mime = ext == 'png' ? MediaType('image', 'png') : MediaType('image', 'jpeg');

      request.files.add(await http.MultipartFile.fromPath(
        'file${i + 1}',
        images[i].path,
        contentType: mime,
      ));
    }

    final streamed = await request.send();
    final response = await http.Response.fromStream(streamed);

    if (response.statusCode == 200) {
      return jsonDecode(response.body) as Map<String, dynamic>;
    } else {
      final err = jsonDecode(response.body);
      throw Exception(err['detail'] ?? 'Unknown error');
    }
  }
}
```

### Upload Screen — `upload_screen.dart`
```dart
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'timetable_service.dart';

class UploadScreen extends StatefulWidget {
  const UploadScreen({super.key});

  @override
  State<UploadScreen> createState() => _UploadScreenState();
}

class _UploadScreenState extends State<UploadScreen> {
  final ImagePicker _picker = ImagePicker();
  final List<File> _images = [];
  bool _loading = false;
  Map<String, dynamic>? _result;
  String? _error;

  Future<void> _pickImages() async {
    final picked = await _picker.pickMultiImage(imageQuality: 90);
    if (picked.isEmpty) return;

    final remaining = 5 - _images.length;
    final toAdd = picked.take(remaining).map((x) => File(x.path)).toList();

    setState(() {
      _images.addAll(toAdd);
      _error = null;
    });
  }

  Future<void> _upload() async {
    if (_images.isEmpty) return;
    setState(() { _loading = true; _error = null; });

    try {
      final result = await TimetableService.extractTimetable(_images);
      setState(() { _result = result; });
    } catch (e) {
      setState(() { _error = e.toString(); });
    } finally {
      setState(() { _loading = false; });
    }
  }

  void _removeImage(int index) {
    setState(() => _images.removeAt(index));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Timetable OCR')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Image preview grid
            if (_images.isNotEmpty)
              SizedBox(
                height: 120,
                child: ListView.builder(
                  scrollDirection: Axis.horizontal,
                  itemCount: _images.length,
                  itemBuilder: (_, i) => Stack(
                    children: [
                      Padding(
                        padding: const EdgeInsets.only(right: 8),
                        child: Image.file(_images[i], height: 110, width: 90, fit: BoxFit.cover),
                      ),
                      Positioned(
                        top: 0, right: 8,
                        child: GestureDetector(
                          onTap: () => _removeImage(i),
                          child: const CircleAvatar(
                            radius: 10,
                            backgroundColor: Colors.red,
                            child: Icon(Icons.close, size: 12, color: Colors.white),
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ),

            const SizedBox(height: 12),

            // Pick images button
            OutlinedButton.icon(
              onPressed: _images.length >= 5 ? null : _pickImages,
              icon: const Icon(Icons.add_photo_alternate),
              label: Text('Add Images (${_images.length}/5)'),
            ),

            const SizedBox(height: 12),

            // Upload button
            ElevatedButton(
              onPressed: _loading || _images.isEmpty ? null : _upload,
              child: _loading
                  ? const CircularProgressIndicator(color: Colors.white)
                  : const Text('Extract Timetable'),
            ),

            // Error
            if (_error != null) ...[
              const SizedBox(height: 12),
              Text(_error!, style: const TextStyle(color: Colors.red)),
            ],

            // Result
            if (_result != null) ...[
              const SizedBox(height: 16),
              const Text('Result:', style: TextStyle(fontWeight: FontWeight.bold)),
              const SizedBox(height: 8),
              Expanded(
                child: SingleChildScrollView(
                  child: Text(_result.toString()),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
```

---

## 5. Python (requests)

```python
import requests

def extract_timetable(image_paths: list[str]) -> dict:
    url = "http://localhost:8000/ocr/extract-timetable-multi"
    
    open_files = []
    files = {}

    try:
        for i, path in enumerate(image_paths[:5]):
            ext = path.rsplit(".", 1)[-1].lower()
            mime = "image/png" if ext == "png" else "image/jpeg"
            f = open(path, "rb")
            open_files.append(f)
            files[f"file{i + 1}"] = (path.split("/")[-1], f, mime)

        response = requests.post(url, files=files)
        response.raise_for_status()
        return response.json()

    finally:
        for f in open_files:
            f.close()

# Usage
result = extract_timetable(["timetable1.png", "timetable2.jpg"])
print(result)
```

---

## 6. cURL

```bash
# Single image
curl -X POST "http://localhost:8000/ocr/extract-timetable-multi" \
  -F "file1=@timetable1.png;type=image/png"

# Multiple images
curl -X POST "http://localhost:8000/ocr/extract-timetable-multi" \
  -F "file1=@timetable1.png;type=image/png" \
  -F "file2=@timetable2.jpg;type=image/jpeg" \
  -F "file3=@timetable3.png;type=image/png"
```

---

## Common Mistakes

| ❌ Mistake | ✅ Fix |
|-----------|--------|
| Setting `Content-Type: application/json` | Let browser/library set `multipart/form-data` automatically |
| Using field name `files[]` or `file` | Use `file1`, `file2`, ... `file5` exactly |
| Skipping numbers e.g. `file1` + `file3` | Always use sequential numbers starting from `file1` |
| Sending more than 5 files | Limit to 5; slice the array before building `FormData` |
| Sending non-image files | Only PNG and JPG/JPEG are accepted |
| Using `http://localhost:8000` on Android device | Use your machine's local IP e.g. `http://192.168.1.x:8000` |