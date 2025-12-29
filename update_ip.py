import sys
import re
import os


def update_file(file_path, search_pattern, replacement_string):
    """
    Reads a file, searches for a regex pattern, and replaces it.
    """
    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}")
        return

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Perform substitution
        new_content, count = re.subn(search_pattern, replacement_string, content)

        if count > 0:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(new_content)
            print(f"✅ Updated {file_path} ({count} occurrences)")
        else:
            print(
                f"ℹ️  No changes needed for {file_path} (Pattern not found or already matches)"
            )

    except Exception as e:
        print(f"❌ Error updating {file_path}: {e}")


def main():
    if len(sys.argv) != 2:
        print("Usage: python update_ip.py <NEW_IP_ADDRESS>")
        print("Example: python update_ip.py 192.168.1.50")
        sys.exit(1)

    new_ip = sys.argv[1]

    # Basic IP validation
    if not re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", new_ip):
        print("Error: Invalid IP address format.")
        sys.exit(1)

    print(f"🔄 Configuring project for IP: {new_ip}...\n")

    # 1. Frontend Config (frontend/src/config/constants.ts)
    # Replace relative API_BASE_URL with absolute URL
    # Matches: export const API_BASE_URL = '/api/v1'; OR export const API_BASE_URL = 'http://...';
    update_file(
        os.path.join("frontend", "src", "config", "constants.ts"),
        r"(export const API_BASE_URL = )('.*')(;)",
        r"\g<1>'http://" + new_ip + r":8000/api/v1'\g<3>",
    )

    # 2. AI Main (ai/main.py)
    # Replace localhost:3000 with new IP:3000 in CORS
    update_file(
        os.path.join("ai", "main.py"),
        r"(http://)localhost(:3000)",
        r"\g<1>" + new_ip + r"\g<2>",
    )

    # 3. AI AgentOS Server (ai/agentoss_server_v2.py)
    # Replace localhost:3000 with new IP:3000 in CORS
    update_file(
        os.path.join("ai", "agentoss_server_v2.py"),
        r"(http://)localhost(:3000)",
        r"\g<1>" + new_ip + r"\g<2>",
    )

    print("\n✨ Configuration complete!")


if __name__ == "__main__":
    main()
