import os
import requests
import sys

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
PARQUET_PATH = os.path.join(DATA_DIR, "fronkon_games.parquet")
PARQUET_URL = "https://huggingface.co/datasets/FronkonGames/steam-games-dataset/resolve/main/data/train-00000-of-00001.parquet"


def download_latest_dataset():
    os.makedirs(DATA_DIR, exist_ok=True)
    if os.path.exists(PARQUET_PATH) and os.path.getsize(PARQUET_PATH) > 10_000_000:
        print(f"Latest dataset already present at: {PARQUET_PATH} ({os.path.getsize(PARQUET_PATH) / 1024 / 1024:.1f} MB)")
        return PARQUET_PATH

    print(f"Downloading latest 140,000+ Steam games dataset from Hugging Face...")
    print(f"Source: {PARQUET_URL}")

    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(PARQUET_URL, headers=headers, stream=True, timeout=60)
    response.raise_for_status()

    total_size = int(response.headers.get("content-length", 0))
    downloaded = 0
    chunk_size = 1024 * 1024  # 1MB chunks

    with open(PARQUET_PATH, "wb") as f:
        for chunk in response.iter_content(chunk_size=chunk_size):
            if chunk:
                f.write(chunk)
                downloaded += len(chunk)
                if total_size > 0:
                    percent = (downloaded / total_size) * 100
                    sys.stdout.write(f"\rProgress: {downloaded / 1024 / 1024:.1f} MB / {total_size / 1024 / 1024:.1f} MB ({percent:.1f}%)")
                    sys.stdout.flush()
                else:
                    sys.stdout.write(f"\rDownloaded: {downloaded / 1024 / 1024:.1f} MB")
                    sys.stdout.flush()

    print("\nDownload finished successfully!")
    return PARQUET_PATH


if __name__ == "__main__":
    download_latest_dataset()
