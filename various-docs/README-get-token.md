You need to create a **Personal Access Token (PAT)** from GitHub's website. Here's how:

**Step 1: Create the token on GitHub:**
1. Go to **GitHub.com** (on any device with a browser)
2. Click your profile picture → **Settings**
3. Scroll down to **Developer settings** (left sidebar)
4. Click **Personal access tokens** → **Tokens (classic)**
5. Click **Generate new token** → **Generate new token (classic)**
6. Give it a name like "Ubuntu Server CLI"
7. **Select scopes** (permissions):
   - `repo` (full repository access)
   - `workflow` (if you use GitHub Actions)
   - `write:org` (if working with organization repos)
8. Click **Generate token**
9. **Copy the token immediately** (you can't see it again!)

**Step 2: Create token.txt file on your Ubuntu box:**

```bash
# Create the file with your token
echo "ghp_your_token_here" > token.txt

# Or use nano/vim to create it
nano token.txt
# Paste your token, save and exit

# Make sure it's secure
chmod 600 token.txt
```

**Step 3: Authenticate:**

```bash
gh auth login --with-token < token.txt

# Clean up the token file for security
rm token.txt
```

**Alternative: Direct paste method:**

```bash
# This will prompt you to paste the token
gh auth login --with-token
# Paste your token and press Enter, then Ctrl+D
```

**Your token will look like:** `ghp_1234567890abcdef...` (starts with `ghp_`)

Think of the Personal Access Token like a special password that gives the GitHub CLI permission to act on your behalf. It's more secure than using your regular password because you can revoke it anytime and it has specific limited permissions.

**Security tip:** Delete the `token.txt` file after authentication since the token is now stored securely by the GitHub CLI.

