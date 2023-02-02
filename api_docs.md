# Whisper Api

## General notes

`progress` is always 0.

## POST /transcription/job

Create a new Job

### Input Sample

```json
{    
	"path": "/home/user/track_109473_media_en.mp3",    
	"language": "en",    
	"format": "vtt", // Optional, see below    
	"callback": "http://url.to.hit.on.complete/", // Optional    
	"output_path": "/lajksd/lasjd/", // MUST BE A FOLDER!    
	"model": "tiny"
}
```

### Valid Values:

*language:* af,am,ar,as,az,ba,be,bg,bn,bo,br,bs,ca,cs,cy,da,de,el,en,es,et,eu,fa,fi,fo,fr,gl,gu,ha,haw,he,hi,hr,ht,hu,hy,id,is,it,ja,jw,ka,kk,km,kn,ko,la,lb,ln,lo,lt,lv,mg,mi,mk,ml,mn,mr,ms,mt,my,ne,nl,nn,no,oc,pa,pl,ps,pt,ro,ru,sa,sd,si,sk,sl,sn,so,sq,sr,su,sv,sw,ta,te,tg,th,tk,tl,tr,tt,uk,ur,uz,vi,yi,yo,zh

*format*: txt,vtt,srt,tsv,json,all Default: txt

*Model*: tiny.en,tiny,base.en,base,small.en,small,medium.en,medium,large-v1,large-v2,large Default: large-v2

### Callback

The specified URL will be called with a POST request. This will include the transcription in TXT format. The actual output is written to disk.

Sample Content:

```json
{    
	"id": "d2877e71-4cc3-491c-a3b5-0f4cb6d3845e",
  "path": "/home/user/track_109473_media_en.mp3",
	"language": "en",    
	"format": "txt",    
	"output_path": "",    
	"progress": 0,    
	"status": "COMPLETED",    
	"result": "",    
	"callback": "https://webhook.site/74640c5e-266a-46f3-a1fc-2ca0d774b4a7",    
	"model": "large-v2",    
	"Duration": 0
}
```

### Return sample

```json
{
    "id": "0b8416ec-f45d-41d4-b464-b77c40f81256",
    "path": "/home/user/track_109473_media_en.mp3",
    "language": "en",
    "format": "vtt",
    "progress": 0,
    "status": "QUEUED",
    "result": "",
    "callback": ""
}
```

## GET /transcription/job/:id

Example: `/transcription/job/73f38ffe-f932-48f2-9a1a-d547166c856a`

### Sample result

```json
{
    "id": "73f38ffe-f932-48f2-9a1a-d547166c856a",
    "path": "/home/user/track_109473_media_en.mp3",
    "language": "en",
    "format": "vtt",
    "output_path": "",
    "progress": 0,
    "status": "QUEUED",
    "result": "TEXT",
    "callback": "https://webhook.site/74640c5e-266a-46f3-a1fc-2ca0d774b4a7",
    "model": "",
    "Duration": 0
}
```

## DELETE /transcription/job/:id

Note: Only queued jobs can be deleted, not running or completed ones Example: `/transcription/job/73f38ffe-f932-48f2-9a1a-d547166c856a`

## GET /transcription/jobs

Get a list of all jobs. **Note**: Only the last 10 completed jobs are kept in memory to prevent overload

### Sample output

```json
[
    {
        "id": "0b8416ec-f45d-41d4-b464-b77c40f81256",
        "path": "/home/user/track_109473_media_en.mp3",
        "language": "en",
        "format": "vtt",
        "progress": 0,
        "status": "FAILED",
        "result": "",
        "callback": ""
    },
    {
        "id": "c0e796c6-3528-46b4-98a5-d432347ca343",
        "path": "/home/user/track_109473_media_en.mp3",
        "language": "en",
        "format": "vtt",
        "progress": 0,
        "status": "RUNNING",
        "result": "",
        "callback": ""
    }
]
```

## GET /smi

Display graphic card status. Not meant for machine consumption!

Sample:

```jsx
Thu Feb  2 15:15:16 2023       
+-----------------------------------------------------------------------------+
| NVIDIA-SMI 470.161.03   Driver Version: 470.161.03   CUDA Version: 11.4     |
|-------------------------------+----------------------+----------------------+
| GPU  Name        Persistence-M| Bus-Id        Disp.A | Volatile Uncorr. ECC |
| Fan  Temp  Perf  Pwr:Usage/Cap|         Memory-Usage | GPU-Util  Compute M. |
|                               |                      |               MIG M. |
|===============================+======================+======================|
|   0  NVIDIA GeForce ...  On   | 00000000:17:00.0 Off |                  N/A |
| 30%   39C    P8    27W / 350W |      1MiB / 24259MiB |      0%      Default |
|                               |                      |                  N/A |
+-------------------------------+----------------------+----------------------+
                                                                               
+-----------------------------------------------------------------------------+
| Processes:                                                                  |
|  GPU   GI   CI        PID   Type   Process name                  GPU Memory |
|        ID   ID                                                   Usage      |
|=============================================================================|
|  No running processes found                                                 |
+-----------------------------------------------------------------------------+
```

## GET /stats

Get some basic stats about the queue and processed jobs

### Sample

```jsx
{
	"Queued": 0,
	"Running": 0,
	"Processed": 1
}
```
