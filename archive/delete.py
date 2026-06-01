from internetarchive import get_item, delete
import os

identifier = "Fazail-e-Sadqaat-Malayalam-Audio"

def delete_from_archive():
    access_key = os.environ.get("IA_ACCESS_KEY")
    secret_key = os.environ.get("IA_SECRET_KEY")

    print(f"\n⚠️  DELETE OPERATION")
    print(f"   Item: https://archive.org/details/{identifier}")
    print(f"   This will remove ONLY Malayalam_Chapters files from the item.\n")

    if not access_key or not secret_key:
        print("✗ Missing credentials. Set IA_ACCESS_KEY and IA_SECRET_KEY environment variables.")
        return

    try:
        item = get_item(identifier)
        all_files = list(item.get_files())

        files_to_delete = [f.name for f in all_files if f.name.startswith("Malayalam_Chapters/")]

        if not files_to_delete:
            print("✓ No content files in Malayalam_Chapters/ to delete.")
            return

        print(f"Found {len(files_to_delete)} file(s) to delete:")
        for name in files_to_delete:
            print(f"   - {name}")

        response = delete(
            identifier,
            files=files_to_delete,
            access_key=access_key,
            secret_key=secret_key,
            verbose=True
        )

        print(f"\n✓ DELETE COMPLETED")
        print(f"  View at: https://archive.org/details/{identifier}")
    except Exception as error:
        print(f"\n✗ ERROR: {error}")

if __name__ == "__main__":
    delete_from_archive()