# Enterprise Integration Guide - AI Test Data Generator

This guide shows how to integrate the AI Test Data Generator service into enterprise applications.

## Quick Start

The service exposes a RESTful API on port `9090`. Enterprise applications call it via HTTP.

**Base URL**: `http://localhost:9090` (or `http://server-ip:9090` for network access)

**API Endpoint**: `POST /api/v1/generate/from-json`

## Supported Integration Methods

1. **Direct HTTP Calls** (all languages)
2. **.NET / C#** - HttpClient example
3. **Python** - requests example
4. **JavaScript / Node.js** - fetch example
5. **Java** - HttpURLConnection example
6. **PowerShell** - Invoke-WebRequest example

---

## 1. Direct HTTP Call (cURL)

The simplest way to test the API:

```bash
curl -X POST http://localhost:9090/api/v1/generate/from-json \
  -H "Content-Type: application/json" \
  -d @SampleInput.json \
  -o SampleOutput.json
```

Or using PowerShell:

```powershell
$body = Get-Content 'SampleInput.json' -Raw | ConvertFrom-Json | ConvertTo-Json
Invoke-WebRequest -Uri "http://localhost:9090/api/v1/generate/from-json" `
  -Method POST `
  -Headers @{"Content-Type"="application/json"} `
  -Body $body `
  -OutFile "SampleOutput.json" `
  -UseBasicParsing
```

---

## 2. .NET / C# Integration

### Example: Basic Usage

```csharp
using System;
using System.Net.Http;
using System.Text.Json;
using System.Threading.Tasks;

public class TestDataGeneratorClient
{
    private static readonly string ApiBaseUrl = "http://localhost:9090";
    private static readonly HttpClient Client = new HttpClient();

    public static async Task<string> GenerateTestDataAsync(string jsonInput)
    {
        try
        {
            // Prepare request
            var request = new HttpRequestMessage(HttpMethod.Post, 
                $"{ApiBaseUrl}/api/v1/generate/from-json")
            {
                Content = new StringContent(
                    jsonInput, 
                    System.Text.Encoding.UTF8, 
                    "application/json")
            };

            // Send request
            var response = await Client.SendAsync(request);
            response.EnsureSuccessStatusCode();

            // Read response
            var responseBody = await response.Content.ReadAsStringAsync();
            return responseBody;
        }
        catch (HttpRequestException ex)
        {
            Console.WriteLine($"API Error: {ex.Message}");
            throw;
        }
    }

    public static async Task Main()
    {
        // Read sample input
        var inputJson = System.IO.File.ReadAllText("SampleInput.json");

        // Call service
        var outputJson = await GenerateTestDataAsync(inputJson);

        // Save result
        System.IO.File.WriteAllText("SampleOutput.json", outputJson);
        Console.WriteLine("✓ Test data generated successfully!");
    }
}
```

### Example: Async with Polly (Resilience)

```csharp
using Polly;
using System.Net;

var retryPolicy = Policy
    .Handle<HttpRequestException>()
    .OrResult<HttpResponseMessage>(r => !r.IsSuccessStatusCode)
    .WaitAndRetryAsync(
        retryCount: 3,
        sleepDurationProvider: attempt => 
            TimeSpan.FromSeconds(Math.Pow(2, attempt)),
        onRetry: (outcome, timespan) => 
            Console.WriteLine($"Retry attempt after {timespan.TotalSeconds}s"));

var response = await retryPolicy.ExecuteAsync(async () =>
{
    return await Client.PostAsync(
        $"{ApiBaseUrl}/api/v1/generate/from-json",
        new StringContent(jsonInput, Encoding.UTF8, "application/json"));
});
```

---

## 3. Python Integration

### Example: Basic Usage

```python
import requests
import json
from pathlib import Path

class TestDataGeneratorClient:
    def __init__(self, api_url: str = "http://localhost:9090"):
        self.api_url = api_url
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
    
    def generate_from_json(self, input_data: dict) -> dict:
        """Generate test data from JSON template"""
        try:
            response = self.session.post(
                f"{self.api_url}/api/v1/generate/from-json",
                json=input_data,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"API Error: {e}")
            raise
    
    def generate_from_excel(self, excel_file_path: str) -> dict:
        """Generate test data from Excel TDM file"""
        with open(excel_file_path, 'rb') as f:
            files = {'file': f}
            try:
                response = self.session.post(
                    f"{self.api_url}/api/v1/generate/from-excel",
                    files=files,
                    timeout=30
                )
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                print(f"API Error: {e}")
                raise
    
    def health_check(self) -> bool:
        """Check if service is available"""
        try:
            response = self.session.get(
                f"{self.api_url}/api/v1/health",
                timeout=5
            )
            return response.status_code == 200
        except:
            return False

# Usage
if __name__ == "__main__":
    client = TestDataGeneratorClient()
    
    # Check service health
    if not client.health_check():
        print("ERROR: Service is not running on http://localhost:9090")
        exit(1)
    
    # Load sample input
    with open('SampleInput.json') as f:
        input_data = json.load(f)
    
    # Generate test data
    output_data = client.generate_from_json(input_data)
    
    # Save result
    Path('SampleOutput.json').write_text(json.dumps(output_data, indent=2))
    print("✓ Test data generated successfully!")
```

### Example: Async with Retry (using aiohttp)

```python
import aiohttp
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential

class AsyncTestDataGeneratorClient:
    def __init__(self, api_url: str = "http://localhost:9090"):
        self.api_url = api_url
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def generate_from_json(self, input_data: dict) -> dict:
        """Generate test data (with automatic retries)"""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.api_url}/api/v1/generate/from-json",
                json=input_data,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                response.raise_for_status()
                return await response.json()

# Usage
async def main():
    client = AsyncTestDataGeneratorClient()
    
    with open('SampleInput.json') as f:
        input_data = json.load(f)
    
    output_data = await client.generate_from_json(input_data)
    Path('SampleOutput.json').write_text(json.dumps(output_data, indent=2))
    print("✓ Test data generated successfully!")

asyncio.run(main())
```

---

## 4. JavaScript / Node.js Integration

### Example: Basic Usage

```javascript
const axios = require('axios');
const fs = require('fs').promises;

class TestDataGeneratorClient {
    constructor(apiUrl = 'http://localhost:9090') {
        this.apiUrl = apiUrl;
        this.client = axios.create({
            baseURL: apiUrl,
            headers: {
                'Content-Type': 'application/json'
            },
            timeout: 30000
        });
    }

    async generateFromJson(inputData) {
        try {
            const response = await this.client.post(
                '/api/v1/generate/from-json',
                inputData
            );
            return response.data;
        } catch (error) {
            console.error('API Error:', error.message);
            throw error;
        }
    }

    async healthCheck() {
        try {
            const response = await this.client.get('/api/v1/health');
            return response.status === 200;
        } catch {
            return false;
        }
    }
}

// Usage
async function main() {
    const client = new TestDataGeneratorClient();

    // Check service health
    const isHealthy = await client.healthCheck();
    if (!isHealthy) {
        console.error('ERROR: Service is not running on http://localhost:9090');
        process.exit(1);
    }

    // Load sample input
    const inputData = JSON.parse(await fs.readFile('SampleInput.json', 'utf-8'));

    // Generate test data
    const outputData = await client.generateFromJson(inputData);

    // Save result
    await fs.writeFile('SampleOutput.json', JSON.stringify(outputData, null, 2));
    console.log('✓ Test data generated successfully!');
}

main().catch(console.error);
```

### Example: TypeScript

```typescript
interface TestDataGeneratorConfig {
    apiUrl: string;
    timeout: number;
}

class TestDataGenerator {
    private config: TestDataGeneratorConfig;

    constructor(config: Partial<TestDataGeneratorConfig> = {}) {
        this.config = {
            apiUrl: config.apiUrl ?? 'http://localhost:9090',
            timeout: config.timeout ?? 30000
        };
    }

    async generate(input: Record<string, any>): Promise<Record<string, any>> {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), this.config.timeout);

        try {
            const response = await fetch(
                `${this.config.apiUrl}/api/v1/generate/from-json`,
                {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(input),
                    signal: controller.signal
                }
            );

            if (!response.ok) {
                throw new Error(`API Error: ${response.statusText}`);
            }

            return await response.json();
        } finally {
            clearTimeout(timeoutId);
        }
    }
}

// Usage
const generator = new TestDataGenerator();
const output = await generator.generate(inputData);
```

---

## 5. Java Integration

### Example: HttpClient

```java
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import com.fasterxml.jackson.databind.ObjectMapper;

public class TestDataGeneratorClient {
    private static final String API_URL = "http://localhost:9090";
    private static final HttpClient httpClient = HttpClient.newBuilder()
        .version(HttpClient.Version.HTTP_2)
        .build();
    private static final ObjectMapper objectMapper = new ObjectMapper();

    public static String generateTestData(String jsonInput) throws Exception {
        HttpRequest request = HttpRequest.newBuilder()
            .uri(new URI(API_URL + "/api/v1/generate/from-json"))
            .POST(HttpRequest.BodyPublishers.ofString(jsonInput))
            .header("Content-Type", "application/json")
            .timeout(java.time.Duration.ofSeconds(30))
            .build();

        HttpResponse<String> response = httpClient.send(
            request,
            HttpResponse.BodyHandlers.ofString()
        );

        if (response.statusCode() != 200) {
            throw new RuntimeException("API Error: " + response.statusCode());
        }

        return response.body();
    }

    public static void main(String[] args) throws Exception {
        String inputJson = new String(
            java.nio.file.Files.readAllBytes(
                java.nio.file.Paths.get("SampleInput.json")
            )
        );

        String outputJson = generateTestData(inputJson);

        java.nio.file.Files.write(
            java.nio.file.Paths.get("SampleOutput.json"),
            outputJson.getBytes()
        );

        System.out.println("✓ Test data generated successfully!");
    }
}
```

---

## 6. PowerShell Integration

### Example: Basic

```powershell
# Simple POST request
$uri = "http://localhost:9090/api/v1/generate/from-json"
$body = Get-Content 'SampleInput.json' | ConvertFrom-Json | ConvertTo-Json

$response = Invoke-WebRequest -Uri $uri `
    -Method POST `
    -Headers @{"Content-Type"="application/json"} `
    -Body $body `
    -UseBasicParsing

$response.Content | Out-File 'SampleOutput.json'
Write-Host "✓ Test data generated successfully!"
```

### Example: Function with Retry Logic

```powershell
function Invoke-GenerateTestData {
    param(
        [Parameter(Mandatory=$true)]
        [string]$InputJsonPath,
        
        [Parameter(Mandatory=$false)]
        [string]$OutputJsonPath = "SampleOutput.json",
        
        [Parameter(Mandatory=$false)]
        [string]$ApiUrl = "http://localhost:9090",
        
        [Parameter(Mandatory=$false)]
        [int]$MaxRetries = 3
    )

    $uri = "$ApiUrl/api/v1/generate/from-json"
    $body = Get-Content $InputJsonPath | ConvertFrom-Json | ConvertTo-Json

    for ($attempt = 1; $attempt -le $MaxRetries; $attempt++) {
        try {
            Write-Host "Attempt $attempt/$MaxRetries..."
            
            $response = Invoke-WebRequest -Uri $uri `
                -Method POST `
                -Headers @{"Content-Type"="application/json"} `
                -Body $body `
                -UseBasicParsing `
                -TimeoutSec 30

            $response.Content | Out-File $OutputJsonPath
            Write-Host "✓ Test data generated successfully!" -ForegroundColor Green
            return $true
        }
        catch {
            if ($attempt -lt $MaxRetries) {
                Write-Host "Error: $($_.Exception.Message). Retrying in $([Math]::Pow(2,$attempt)) seconds..." -ForegroundColor Yellow
                Start-Sleep -Seconds ([Math]::Pow(2,$attempt))
            }
            else {
                Write-Host "Error: Failed after $MaxRetries attempts" -ForegroundColor Red
                return $false
            }
        }
    }
}

# Usage
Invoke-GenerateTestData -InputJsonPath "SampleInput.json" -OutputJsonPath "SampleOutput.json"
```

---

## API Endpoints Reference

### 1. Generate from JSON

```http
POST /api/v1/generate/from-json
Content-Type: application/json

{
  "fields": [
    {
      "name": "customer_id",
      "sample_value": "C001234"
    },
    {
      "name": "email",
      "sample_value": "john.doe@example.com"
    }
  ],
  "num_records": 5
}
```

**Response** (200 OK):
```json
{
  "fields": {
    "customer_id": ["C001234", "C002456", ...],
    "email": ["john.doe@example.com", "jane.smith@example.com", ...]
  },
  "num_records": 5
}
```

### 2. Generate from Excel

```http
POST /api/v1/generate/from-excel
Content-Type: multipart/form-data

[Binary Excel file]
```

**Response** (200 OK): Generated data JSON

### 3. Health Check

```http
GET /api/v1/health
```

**Response** (200 OK):
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "services": {
    "embedding_engine": "ready",
    "faiss_index": "ready",
    "generator": "ready"
  }
}
```

### 4. API Documentation

Interactive Swagger UI available at:
```
http://localhost:9090/docs
```

---

## Error Handling

### Common Error Responses

| Code | Meaning | Action |
|------|---------|--------|
| 200 | Success | Process response |
| 400 | Bad Request | Check JSON format |
| 422 | Validation Error | Check required fields |
| 500 | Server Error | Check logs, restart service |
| 503 | Service Unavailable | Check if service is running |

### Example Error Response

```json
{
  "detail": [
    {
      "loc": ["body", "fields"],
      "msg": "value is not a valid list",
      "type": "type_error.list"
    }
  ]
}
```

---

## Performance Tuning

### Concurrent Requests

Default configuration supports ~10 concurrent requests. To increase:

```powershell
# Modify NSSM configuration
nssm set AITestDataGenerator AppParameters --workers 4
```

Or modify `start.py` uvicorn workers.

### Timeout Configuration

Default timeout is 30 seconds. Adjust in your client code for large datasets.

### Caching

The service caches semantic classifications. Re-submissions of identical fields are faster.

---

## Support

- **API Docs**: http://localhost:9090/docs
- **Logs**: `C:\ProgramData\AITestDataGenerator\logs\service.log`
- **Deployment Guide**: See [DEPLOYMENT.md](DEPLOYMENT.md)
