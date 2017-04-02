# Fireball

```
{
    "method": "s3",
    "output": "s3://dlcs-pdf/2/1/pdf-item/abcd1/0/result.pdf",
    "pages": [
        {
            "type": "pdf",
            "method": "download",
            "input": "https://wellcomelibrary.org/service/pdf-cover/abcd1"
        },
        {
            "type", "jpg",
            "method", "s3",
            "input": "s3://dlcs-thumbs/2/1/xyz1/low.jpg"
        },
        {
            "type": "redacted"
        },
        {
            "type": "missing"
        }
    ],
    "customTypes": {
        "redacted": {
            "message": "This page has been removed."
        },
        "missing": {
            "message": "This page is missing."
        }
    }
}
```

